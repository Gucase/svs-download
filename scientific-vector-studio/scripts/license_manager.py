#!/usr/bin/env python3
"""Local usage ledger and signed activation-key verifier.

The public skill contains only an Ed25519 public key. The private signing key
belongs in the separate owner-only admin tool and must never be distributed.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


PRODUCT = "scientific-vector-studio"
STATE_VERSION = 1
FREE_FIGURES = 3
COST_PER_FIGURE = 10
PURCHASE_MESSAGE = (
    "欢迎关注“队长的生物实验室”微信公众号/小红书。\n"
    "添加队长的笔记本微信（XBBen01），购买 Key。\n"
    "100积分=10元；500积分=45元；1000积分=85元。"
)


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
        "cost_per_figure": COST_PER_FIGURE,
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


def _parse_and_verify_key(token: str, public_key_path: Path) -> dict[str, Any]:
    try:
        prefix, payload_part, signature_part = token.strip().split(".")
    except ValueError as exc:
        raise RuntimeError("ACTIVATION_KEY_FORMAT_INVALID") from exc
    if prefix != "SVSKEY1":
        raise RuntimeError("ACTIVATION_KEY_VERSION_INVALID")
    if not public_key_path.exists():
        raise RuntimeError("PAID_LICENSING_NOT_INITIALIZED")
    try:
        from cryptography.hazmat.primitives import serialization
    except ImportError as exc:
        raise RuntimeError("CRYPTOGRAPHY_DEPENDENCY_REQUIRED") from exc
    payload_bytes = _b64decode(payload_part)
    signature = _b64decode(signature_part)
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    try:
        public_key.verify(signature, payload_bytes)
    except Exception as exc:
        raise RuntimeError("ACTIVATION_KEY_SIGNATURE_INVALID") from exc
    payload = json.loads(payload_bytes.decode("utf-8"))
    if payload.get("product") != PRODUCT or payload.get("version") != 1:
        raise RuntimeError("ACTIVATION_KEY_PRODUCT_INVALID")
    credits = payload.get("credits")
    if not isinstance(credits, int) or credits <= 0 or credits % COST_PER_FIGURE != 0:
        raise RuntimeError("ACTIVATION_KEY_CREDITS_INVALID")
    license_id = payload.get("license_id")
    if not isinstance(license_id, str) or not license_id.strip():
        raise RuntimeError("ACTIVATION_KEY_ID_INVALID")
    return payload


def _used_for_license(state: dict[str, Any], license_id: str) -> int:
    completed = sum(
        int(item.get("cost", 0))
        for item in state["completed"].values()
        if item.get("source") == "license" and item.get("license_id") == license_id
    )
    reserved = sum(
        int(item.get("cost", 0))
        for item in state["reservations"].values()
        if item.get("source") == "license" and item.get("license_id") == license_id
    )
    return completed + reserved


def _free_used(state: dict[str, Any]) -> int:
    return sum(1 for item in state["completed"].values() if item.get("source") == "free")


def _emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    raise SystemExit(exit_code)


def command_activate(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    public_key_path = Path(args.public_key).expanduser().resolve()
    payload = _parse_and_verify_key(args.key, public_key_path)
    license_id = payload["license_id"]
    fingerprint = hashlib.sha256(args.key.strip().encode("utf-8")).hexdigest()
    with _locked_state(state_path) as state:
        existing = state["licenses"].get(license_id)
        if existing and existing.get("key_fingerprint") != fingerprint:
            raise RuntimeError("ACTIVATION_KEY_ID_COLLISION")
        state["licenses"][license_id] = {
            "credits": payload["credits"],
            "issued_at": payload.get("issued_at"),
            "customer": payload.get("customer"),
            "key_fingerprint": fingerprint,
            "activated_at": int(time.time()),
        }
        _write_state(state_path, state)
    _emit({"ok": True, "license_id": license_id, "credits": payload["credits"]})


def command_reserve(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    usage_id = args.usage_id.strip()
    if not usage_id:
        raise RuntimeError("USAGE_ID_REQUIRED")
    artifact_hash = args.artifact_sha256.lower().strip()
    with _locked_state(state_path) as state:
        if usage_id in state["completed"]:
            _emit({"ok": True, "reused": True, "usage_id": usage_id, "cost": 0})
        if usage_id in state["reservations"]:
            reservation = state["reservations"][usage_id]
            _emit({"ok": True, "reused": False, "usage_id": usage_id, **reservation})
        if _free_used(state) < FREE_FIGURES:
            reservation = {
                "source": "free",
                "cost": 0,
                "artifact_sha256": artifact_hash,
                "reserved_at": int(time.time()),
            }
        else:
            reservation = None
            for license_id, license_data in state["licenses"].items():
                available = int(license_data["credits"]) - _used_for_license(state, license_id)
                if available >= COST_PER_FIGURE:
                    reservation = {
                        "source": "license",
                        "license_id": license_id,
                        "cost": COST_PER_FIGURE,
                        "artifact_sha256": artifact_hash,
                        "reserved_at": int(time.time()),
                    }
                    break
            if reservation is None:
                _emit(
                    {
                        "ok": False,
                        "purchase_required": True,
                        "message": PURCHASE_MESSAGE,
                        "free_remaining": 0,
                        "credits_required": COST_PER_FIGURE,
                    },
                    exit_code=4,
                )
        state["reservations"][usage_id] = reservation
        _write_state(state_path, state)
    _emit({"ok": True, "reused": False, "usage_id": usage_id, **reservation})


def command_commit(args: argparse.Namespace) -> None:
    state_path = Path(args.state).expanduser().resolve()
    with _locked_state(state_path) as state:
        if args.usage_id in state["completed"]:
            _emit({"ok": True, "reused": True, "usage_id": args.usage_id})
        reservation = state["reservations"].pop(args.usage_id, None)
        if reservation is None:
            raise RuntimeError("USAGE_RESERVATION_NOT_FOUND")
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
        licenses = []
        for license_id, license_data in state["licenses"].items():
            used = _used_for_license(state, license_id)
            licenses.append(
                {
                    "license_id": license_id,
                    "credits_total": int(license_data["credits"]),
                    "credits_available": max(0, int(license_data["credits"]) - used),
                }
            )
        payload = {
            "ok": True,
            "free_limit": FREE_FIGURES,
            "free_used": _free_used(state),
            "free_remaining": max(0, FREE_FIGURES - _free_used(state)),
            "cost_per_figure": COST_PER_FIGURE,
            "licenses": licenses,
            "pending_reservations": len(state["reservations"]),
        }
    _emit(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scientific Vector Studio license manager")
    parser.add_argument("--state", default=str(_default_state_path()))
    parser.add_argument("--public-key", default=str(_default_public_key_path()))
    subparsers = parser.add_subparsers(dest="command", required=True)

    activate = subparsers.add_parser("activate")
    activate.add_argument("--key", required=True)
    activate.set_defaults(func=command_activate)

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
    except RuntimeError as exc:
        _emit({"ok": False, "error": str(exc)}, exit_code=2)


if __name__ == "__main__":
    main()
