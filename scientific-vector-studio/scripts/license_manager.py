#!/usr/bin/env python3
"""Three-figure trial and signed, unlimited buyout-file verifier.

The public skill contains only an Ed25519 public key. The private signing key
belongs in the separate owner-only admin tool and must never be distributed.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


PRODUCT = "scientific-vector-studio"
STATE_VERSION = 1
FREE_FIGURES = 3
PURCHASE_MESSAGE = (
    "欢迎关注“队长的生物实验室”微信公众号/小红书。\n"
    "3 张免费体验已用完。39 元一次买断，绑定一台电脑不限绘图次数；同机 Illustrator/PowerPoint 共用。\n"
    "添加队长的笔记本微信（XBBen01），提供机器码购买 SVS 买断授权文件。\n"
    "不限次仅指 SVS 授权，不包含 Codex/API、Illustrator 等第三方费用或使用额度。"
)
MACHINE_CODE_RE = re.compile(r"^SVS-MACHINE-1\.[0-9a-f]{64}$")


def _machine_identity() -> tuple[str, str]:
    """Return a stable OS installation identifier; never use MAC addresses."""
    system = platform.system()
    if system == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                value = winreg.QueryValueEx(key, "MachineGuid")[0]
        except OSError as exc:
            raise RuntimeError("MACHINE_ID_UNAVAILABLE") from exc
    elif system == "Darwin":
        try:
            output = subprocess.run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], check=True,
                                    capture_output=True, text=True, timeout=10).stdout
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', output)
            if not match:
                raise ValueError("UUID missing")
            value = match.group(1)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise RuntimeError("MACHINE_ID_UNAVAILABLE") from exc
    elif system == "Linux":
        source = next((path for path in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id"))
                       if path.is_file()), None)
        if source is None:
            raise RuntimeError("MACHINE_ID_UNAVAILABLE")
        value = source.read_text(encoding="ascii").strip()
    else:
        raise RuntimeError("MACHINE_PLATFORM_UNSUPPORTED")
    value = str(value).strip().lower()
    if not value:
        raise RuntimeError("MACHINE_ID_UNAVAILABLE")
    return system.lower(), value


def _local_machine_code() -> str:
    system, identity = _machine_identity()
    digest = hashlib.sha256(("svs-machine-v1\0" + system + "\0" + identity).encode("utf-8")).hexdigest()
    return "SVS-MACHINE-1." + digest


def command_machine_code(_args: argparse.Namespace) -> None:
    _emit({"ok": True, "machine_code": _local_machine_code(), "platform": platform.system().lower(),
           "privacy": "仅输出本机标识的单向哈希，不输出原始设备标识。"})


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _default_state_path() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        root = str(Path.home() / ".local" / "share")
    return Path(root) / "ScientificVectorStudio" / "license-state.json"


def _default_public_key_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "license-public-key.pem"


def _empty_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "free_figure_limit": FREE_FIGURES,
        "licenses": {},
        "reservations": {},
        "completed": {},
    }


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != STATE_VERSION:
        raise RuntimeError("LICENSE_STATE_VERSION_UNSUPPORTED")
    for key in ("licenses", "reservations", "completed"):
        if not isinstance(state.get(key), dict):
            raise RuntimeError("LICENSE_STATE_INVALID")
    return state


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="license-state-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


@contextmanager
def _locked_state(path: Path) -> Iterator[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield _read_state(path)
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _verify_license_document(document: Any, public_key_path: Path) -> dict[str, Any]:
    """Validate a signed buyout document, including when reloaded from the ledger."""
    if not isinstance(document, dict) or document.get("format") != "svs-license" or document.get("version") != 1:
        raise RuntimeError("LICENSE_FILE_FORMAT_INVALID")
    payload = document.get("payload")
    signature = document.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        raise RuntimeError("LICENSE_FILE_FORMAT_INVALID")
    if not public_key_path.is_file():
        raise RuntimeError("PAID_LICENSING_NOT_INITIALIZED")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise RuntimeError("CRYPTOGRAPHY_DEPENDENCY_REQUIRED") from exc
    try:
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Wrong key type")
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        public_key.verify(_b64decode(signature), data)
    except Exception as exc:
        raise RuntimeError("LICENSE_FILE_SIGNATURE_INVALID") from exc
    if payload.get("product") != PRODUCT or payload.get("version") != 3:
        raise RuntimeError("LICENSE_FILE_PRODUCT_INVALID")
    if payload.get("license_type") != "lifetime" or "credits" in payload or "expires_at" in payload:
        raise RuntimeError("LICENSE_FILE_ENTITLEMENT_INVALID")
    if not isinstance(payload.get("license_id"), str) or not payload["license_id"].strip():
        raise RuntimeError("LICENSE_FILE_ID_INVALID")
    if not isinstance(payload.get("customer"), str) or not payload["customer"].strip():
        raise RuntimeError("LICENSE_FILE_CUSTOMER_INVALID")
    if type(payload.get("issued_at")) is not int or payload["issued_at"] <= 0:
        raise RuntimeError("LICENSE_FILE_DATE_INVALID")
    machine_code = payload.get("machine_code")
    if not isinstance(machine_code, str) or not MACHINE_CODE_RE.fullmatch(machine_code):
        raise RuntimeError("LICENSE_FILE_MACHINE_CODE_INVALID")
    return payload


def _lifetime_license(state: dict[str, Any], public_key_path: Path) -> str | None:
    found = None
    mismatched = False
    for license_id, entry in state["licenses"].items():
        if "signed_license" not in entry:
            continue  # Historical entries are retained as data, not paid entitlement.
        if entry["signed_license"].get("payload", {}).get("version") == 2:
            continue  # Unbound v0.4 files require explicit reissuance, never automatic binding.
        payload = _verify_license_document(entry["signed_license"], public_key_path)
        if payload["license_id"] != license_id:
            raise RuntimeError("LICENSE_STATE_INVALID")
        if payload["machine_code"] != _local_machine_code():
            mismatched = True
            continue
        found = found or license_id
    if mismatched and not found:
        raise RuntimeError("LICENSE_MACHINE_MISMATCH")
    return found


def command_import_license(args: argparse.Namespace) -> None:
    source = Path(args.file).expanduser().resolve()
    if source.stat().st_size > 65536:
        raise RuntimeError("LICENSE_FILE_TOO_LARGE")
    try:
        document = json.loads(source.read_text(encoding="utf-8-sig"))
    except (UnicodeError, ValueError) as exc:
        raise RuntimeError("LICENSE_FILE_FORMAT_INVALID") from exc
    payload = _verify_license_document(document, Path(args.public_key).expanduser().resolve())
    if payload["machine_code"] != _local_machine_code():
        raise RuntimeError("LICENSE_MACHINE_MISMATCH")
    license_id = payload["license_id"]
    fingerprint = hashlib.sha256(json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    state_path = Path(args.state).expanduser().resolve()
    with _locked_state(state_path) as state:
        existing = state["licenses"].get(license_id)
        if existing and existing.get("key_fingerprint") != fingerprint:
            raise RuntimeError("ACTIVATION_KEY_ID_COLLISION")
        state["licenses"][license_id] = {
            "signed_license": document, "key_fingerprint": fingerprint,
            "activated_at": existing.get("activated_at", int(time.time())) if existing else int(time.time()),
        }
        _write_state(state_path, state)
    _emit({"ok": True, "license_id": license_id, "license_type": "lifetime", "unlimited": True, "machine_bound": True,
           "reused": bool(existing), "message": "买断授权已激活，SVS 不限绘图次数。"})


def _free_used(state: dict[str, Any]) -> int:
    return sum(1 for item in state["completed"].values() if item.get("source") == "free")


def _emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    raise SystemExit(exit_code)


def command_reserve(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    usage_id = args.usage_id.strip()
    if not usage_id:
        raise RuntimeError("USAGE_ID_REQUIRED")
    artifact_hash = args.artifact_sha256.lower().strip()
    with _locked_state(state_path) as state:
        lifetime = _lifetime_license(state, Path(args.public_key).expanduser().resolve())
        if usage_id in state["completed"]:
            _emit({"ok": True, "reused": True, "usage_id": usage_id, "cost": 0})
        if usage_id in state["reservations"]:
            reservation = state["reservations"][usage_id]
            if lifetime:
                reservation.update(source="lifetime", license_id=lifetime, cost=0)
                _write_state(state_path, state)
            elif reservation.get("source") != "free" or reservation.get("cost", 0) != 0:
                raise RuntimeError("BUYOUT_FILE_REQUIRED_FOR_OLD_RESERVATION")
            _emit({"ok": True, "reused": False, "usage_id": usage_id, **reservation})
        pending_free = sum(1 for item in state["reservations"].values() if item.get("source") == "free")
        if lifetime:
            reservation = {"source": "lifetime", "license_id": lifetime, "cost": 0,
                           "artifact_sha256": artifact_hash, "reserved_at": int(time.time())}
        elif _free_used(state) + pending_free < FREE_FIGURES:
            reservation = {
                "source": "free",
                "cost": 0,
                "artifact_sha256": artifact_hash,
                "reserved_at": int(time.time()),
            }
        else:
            if _free_used(state) < FREE_FIGURES and pending_free:
                _emit({"ok": False, "error": "FREE_FIGURES_RESERVED",
                       "message": "免费名额已被进行中的绘图占用，请先完成或取消这些绘图。"}, exit_code=2)
            _emit({"ok": False, "purchase_required": True, "message": PURCHASE_MESSAGE,
                   "free_remaining": 0, "buyout_price_cny": 39}, exit_code=4)
        state["reservations"][usage_id] = reservation
        _write_state(state_path, state)
    _emit({"ok": True, "reused": False, "usage_id": usage_id, **reservation})


def command_commit(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    with _locked_state(state_path) as state:
        lifetime = _lifetime_license(state, Path(args.public_key).expanduser().resolve())
        if args.usage_id in state["completed"]:
            _emit({"ok": True, "reused": True, "usage_id": args.usage_id})
        reservation = state["reservations"].pop(args.usage_id, None)
        if reservation is None:
            raise RuntimeError("USAGE_RESERVATION_NOT_FOUND")
        if lifetime:
            reservation.update(source="lifetime", license_id=lifetime, cost=0)
        elif reservation.get("source") != "free" or reservation.get("cost", 0) != 0:
            raise RuntimeError("LIFETIME_LICENSE_REQUIRED")
        reservation["completed_at"] = int(time.time())
        state["completed"][args.usage_id] = reservation
        _write_state(state_path, state)
    _emit({"ok": True, "reused": False, "usage_id": args.usage_id, "cost": reservation["cost"]})


def command_cancel(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    with _locked_state(state_path) as state:
        removed = state["reservations"].pop(args.usage_id, None) is not None
        if removed:
            _write_state(state_path, state)
    _emit({"ok": True, "cancelled": removed, "usage_id": args.usage_id})


def command_status(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    with _locked_state(state_path) as state:
        lifetime = _lifetime_license(state, Path(args.public_key).expanduser().resolve())
        licenses = []
        for license_id, license_data in state["licenses"].items():
            if license_id == lifetime:
                licenses.append({"license_id": license_id, "license_type": "lifetime", "unlimited": True, "machine_bound": True})
                continue
        payload = {
            "ok": True,
            "license_type": "lifetime" if lifetime else "trial",
            "unlimited": bool(lifetime),
            "machine_bound": bool(lifetime),
            "unbound_license_needs_reissue": any(
                entry.get("signed_license", {}).get("payload", {}).get("version") == 2
                for entry in state["licenses"].values()),
            "free_limit": FREE_FIGURES,
            "free_used": _free_used(state),
            "free_remaining": max(0, FREE_FIGURES - _free_used(state)),
            "free_available": max(0, FREE_FIGURES - _free_used(state) - sum(
                1 for item in state["reservations"].values() if item.get("source") == "free")),
            "cost_per_figure": 0,
            "buyout_price_cny": 39,
            "free_reserved": sum(1 for item in state["reservations"].values() if item.get("source") == "free"),
            "licenses": licenses,
            "pending_reservations": len(state["reservations"]),
        }
    _emit(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scientific Vector Studio license manager")
    parser.add_argument("--state", default=str(_default_state_path()))
    parser.add_argument("--public-key", default=str(_default_public_key_path()))
    subparsers = parser.add_subparsers(dest="command", required=True)

    machine_code = subparsers.add_parser("machine-code", help="Print an anonymized local machine code")
    machine_code.set_defaults(func=command_machine_code)

    import_license = subparsers.add_parser("import-license", help="Import an offline buyout authorization file")
    import_license.add_argument("--file", required=True)
    import_license.set_defaults(func=command_import_license)

    reserve = subparsers.add_parser("reserve")
    reserve.add_argument("--usage-id", required=True)
    reserve.add_argument("--artifact-sha256", required=True)
    reserve.set_defaults(func=command_reserve)

    for name, function in (("commit", command_commit), ("cancel", command_cancel)):
        command = subparsers.add_parser(name)
        command.add_argument("--usage-id", required=True)
        command.set_defaults(func=function)

    status = subparsers.add_parser("status")
    status.set_defaults(func=command_status)
    return parser


def main() -> None:
    try:
        args = build_parser().parse_args()
        args.func(args)
    except (RuntimeError, OSError, ValueError) as exc:
        _emit({"ok": False, "error": str(exc)}, exit_code=2)


if __name__ == "__main__":
    main()
