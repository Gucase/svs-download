import argparse
import base64
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import license_manager as lm


def encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


class LicenseFileTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.state = self.root / "state.json"
        self.public = self.root / "public.pem"
        self.key = Ed25519PrivateKey.generate()
        self.public.write_bytes(self.key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        self.file = self.root / "测试 order.svslicense"
        self.payload = {"product": lm.PRODUCT, "version": 2, "license_type": "lifetime",
                        "license_id": "test-order-1", "customer": "order-1", "issued_at": 1788192000}
        self.write_license()

    def sign(self, payload):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return {"format": "svs-license", "version": 1, "payload": payload,
                "signature": encode(self.key.sign(data))}

    def write_license(self, payload=None):
        self.file.write_text(json.dumps(self.sign(payload or self.payload)), encoding="utf-8")

    def call(self, function, expected=0, **kwargs):
        args = argparse.Namespace(state=str(self.state), public_key=str(self.public), **kwargs)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            function(args)
        self.assertEqual(raised.exception.code, expected)
        return json.loads(output.getvalue())

    def activate(self):
        return self.call(lm.command_import_license, file=str(self.file))

    def status(self):
        return self.call(lm.command_status)

    def reserve(self, usage, expected=0):
        return self.call(lm.command_reserve, expected=expected, usage_id=usage, artifact_sha256="a" * 64)

    def commit(self, usage):
        return self.call(lm.command_commit, usage_id=usage)

    def exhaust_trial(self):
        for i in range(3):
            self.reserve(str(i))
            self.commit(str(i))

    def test_three_figures_then_purchase(self):
        self.exhaust_trial()
        result = self.reserve("four", expected=4)
        self.assertTrue(result["purchase_required"])
        self.assertIn("39", result["message"])
        self.assertEqual(self.status()["free_remaining"], 0)

    def test_pending_free_reservations_do_not_allow_fourth(self):
        for i in range(3):
            self.reserve(str(i))
        self.assertEqual(self.reserve("four", expected=2)["error"], "FREE_FIGURES_RESERVED")
        self.assertEqual(self.status()["free_available"], 0)
        self.call(lm.command_cancel, usage_id="1")
        self.assertEqual(self.reserve("four")["source"], "free")

    def test_failure_and_same_figure_retry_are_free(self):
        self.reserve("same")
        self.call(lm.command_cancel, usage_id="same")
        self.assertEqual(self.status()["free_used"], 0)
        self.reserve("same")
        self.commit("same")
        self.assertTrue(self.reserve("same")["reused"])
        self.commit("same")
        self.assertEqual(self.status()["free_used"], 1)

    def test_import_is_idempotent_and_file_can_be_moved(self):
        self.assertFalse(self.activate()["reused"])
        first = self.state.read_bytes()
        self.assertTrue(self.activate()["reused"])
        self.assertEqual(self.state.read_bytes(), first)
        self.file.unlink()
        self.assertTrue(self.status()["unlimited"])

    def test_buyout_after_trial_allows_100_new_figures_without_credits(self):
        self.exhaust_trial()
        self.activate()
        for i in range(100):
            result = self.reserve("paid-%d" % i)
            self.assertEqual(result["source"], "lifetime")
            self.assertEqual(result["cost"], 0)
            self.assertEqual(self.commit("paid-%d" % i)["cost"], 0)
        status = self.status()
        self.assertTrue(status["unlimited"])
        self.assertEqual(status["cost_per_figure"], 0)
        self.assertEqual(status["free_used"], 3)

    def test_buyout_before_trial_preserves_free_allowance(self):
        self.activate()
        self.reserve("first")
        self.commit("first")
        self.assertEqual(self.status()["free_used"], 0)

    def test_old_credit_records_retained_but_do_not_unlock(self):
        self.exhaust_trial()
        state = json.loads(self.state.read_text())
        state["licenses"]["old-order"] = {"credits": 1000000}
        state["reservations"]["old-pending"] = {"source": "license", "cost": 10, "license_id": "old-order"}
        self.state.write_text(json.dumps(state))
        self.reserve("no-buyout", expected=4)
        with self.assertRaisesRegex(RuntimeError, "BUYOUT_FILE_REQUIRED"):
            self.reserve("old-pending")
        self.assertFalse(self.status()["unlimited"])
        self.activate()
        self.assertEqual(self.reserve("old-pending")["cost"], 0)
        self.assertEqual(self.commit("old-pending")["cost"], 0)
        self.assertEqual(json.loads(self.state.read_text())["licenses"]["old-order"]["credits"], 1000000)

    def test_old_key_command_is_not_supported(self):
        result = subprocess.run([sys.executable, lm.__file__, "--state", str(self.state),
                                 "activate", "--key", "SVSKEY1.test.test"], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.state.exists())

    def test_tampered_file_is_rejected_without_state_change(self):
        doc = json.loads(self.file.read_text())
        doc["payload"]["customer"] = "tampered"
        self.file.write_text(json.dumps(doc))
        with self.assertRaisesRegex(RuntimeError, "SIGNATURE_INVALID"):
            self.activate()
        self.assertFalse(self.state.exists())

    def test_wrong_signing_key_is_rejected(self):
        self.public.write_bytes(Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        with self.assertRaisesRegex(RuntimeError, "SIGNATURE_INVALID"):
            self.activate()

    def test_signed_wrong_product_version_and_entitlement_rejected(self):
        changes = ({"product": "other"}, {"version": 3}, {"license_type": "credits"},
                   {"credits": 100}, {"expires_at": 0}, {"license_id": ""}, {"issued_at": True})
        for change in changes:
            with self.subTest(change=change):
                self.write_license(dict(self.payload, **change))
                with self.assertRaises(RuntimeError):
                    self.activate()

    def test_signed_state_is_reverified(self):
        self.activate()
        state = json.loads(self.state.read_text())
        state["licenses"][self.payload["license_id"]]["signed_license"]["payload"]["customer"] = "changed"
        self.state.write_text(json.dumps(state))
        with self.assertRaisesRegex(RuntimeError, "SIGNATURE_INVALID"):
            self.reserve("blocked")

    def test_plain_unlimited_flag_does_not_grant_buyout(self):
        self.exhaust_trial()
        state = json.loads(self.state.read_text())
        state["licenses"]["fake"] = {"unlimited": True, "license_type": "lifetime"}
        self.state.write_text(json.dumps(state))
        self.assertFalse(self.status()["unlimited"])
        self.reserve("blocked", expected=4)

    def test_malformed_large_and_missing_files_fail(self):
        for data in ("not json", "{}", "x" * 65537):
            self.file.write_text(data)
            with self.assertRaises(RuntimeError):
                self.activate()
        self.file.unlink()
        with self.assertRaises(OSError):
            self.activate()

    def test_same_id_different_signed_license_cannot_replace(self):
        self.activate()
        self.write_license(dict(self.payload, customer="different"))
        with self.assertRaisesRegex(RuntimeError, "ID_COLLISION"):
            self.activate()

    def test_cli_import_reports_no_signature_or_customer(self):
        completed = subprocess.run([sys.executable, "-X", "utf8", lm.__file__, "--state", str(self.state),
                                    "--public-key", str(self.public), "import-license", "--file", str(self.file)],
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["unlimited"])
        self.assertNotIn("signature", result)
        self.assertNotIn("customer", result)


if __name__ == "__main__":
    unittest.main()
