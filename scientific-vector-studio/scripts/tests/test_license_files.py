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
from unittest.mock import patch

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
        self.machine_code = lm._local_machine_code()
        self.payload = {"product": lm.PRODUCT, "version": 3, "license_type": "lifetime", "machine_code": self.machine_code,
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
        for i in range(lm.FREE_FIGURES):
            self.reserve(str(i))
            self.commit(str(i))

    def test_one_figure_then_purchase(self):
        self.exhaust_trial()
        result = self.reserve("second", expected=4)
        self.assertTrue(result["purchase_required"])
        self.assertIn("39", result["message"])
        self.assertEqual(self.status()["free_remaining"], 0)

    def test_pending_free_reservation_does_not_allow_second(self):
        self.reserve("first")
        self.assertEqual(self.reserve("second", expected=2)["error"], "FREE_FIGURES_RESERVED")
        self.assertEqual(self.status()["free_available"], 0)
        self.call(lm.command_cancel, usage_id="first")
        self.assertEqual(self.reserve("second")["source"], "free")

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
        self.assertEqual(status["free_used"], 1)

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
        changes = ({"product": "other"}, {"version": 4}, {"license_type": "credits"},
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

    def test_copying_file_to_other_machine_is_rejected_before_state_write(self):
        with patch.object(lm, "_local_machine_code", return_value="SVS-MACHINE-1." + "b" * 64):
            with self.assertRaisesRegex(RuntimeError, "LICENSE_MACHINE_MISMATCH"):
                self.activate()
        self.assertFalse(self.state.exists())

    def test_copying_activated_state_is_rejected_on_use(self):
        self.activate()
        with patch.object(lm, "_local_machine_code", return_value="SVS-MACHINE-1." + "b" * 64):
            with self.assertRaisesRegex(RuntimeError, "LICENSE_MACHINE_MISMATCH"):
                self.reserve("copied")
            with self.assertRaisesRegex(RuntimeError, "LICENSE_MACHINE_MISMATCH"):
                self.status()

    def test_machine_code_is_signed(self):
        document = json.loads(self.file.read_text())
        document["payload"]["machine_code"] = "SVS-MACHINE-1." + "b" * 64
        self.file.write_text(json.dumps(document))
        with self.assertRaisesRegex(RuntimeError, "SIGNATURE_INVALID"):
            self.activate()

    def test_unbound_license_requires_reissue_and_does_not_block_new_file(self):
        old = dict(self.payload, version=2, license_id="old-unbound")
        old.pop("machine_code")
        self.write_license(old)
        with self.assertRaisesRegex(RuntimeError, "PRODUCT_INVALID"):
            self.activate()
        state = lm._empty_state()
        state["licenses"]["old-unbound"] = {"signed_license": self.sign(old)}
        self.state.write_text(json.dumps(state))
        self.assertFalse(self.status()["unlimited"])
        self.assertTrue(self.status()["unbound_license_needs_reissue"])
        self.write_license()
        self.activate()
        self.assertTrue(self.status()["machine_bound"])

    def test_invalid_machine_code_in_signed_file_is_rejected(self):
        for value in (None, "", "bad", [self.machine_code]):
            self.write_license(dict(self.payload, machine_code=value))
            with self.assertRaisesRegex(RuntimeError, "MACHINE_CODE_INVALID"):
                self.activate()

    def test_machine_code_is_stable_scoped_hash_not_raw_identity(self):
        with patch.object(lm, "_machine_identity", return_value=("windows", "test-raw-device-id")):
            first = lm._local_machine_code()
            self.assertEqual(first, lm._local_machine_code())
            self.assertTrue(lm.MACHINE_CODE_RE.fullmatch(first))
            self.assertNotIn("test-raw-device-id", first)
        with patch.object(lm, "_machine_identity", return_value=("windows", "other-device")):
            self.assertNotEqual(first, lm._local_machine_code())

    def test_machine_code_command_does_not_create_usage_state(self):
        result = self.call(lm.command_machine_code)
        self.assertEqual(result["machine_code"], self.machine_code)
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
