#!/usr/bin/env python3
"""HTTPS licensing client for the Scientific Vector Studio service."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
import urllib.parse
import uuid
from pathlib import Path
from typing import Any


PURCHASE_MESSAGE = (
    "欢迎关注“队长的生物实验室”微信公众号/小红书。\n"
    "添加队长的笔记本微信（XBBen01），购买 Key。\n"
    "100积分=10元；500积分=45元；1000积分=85元。"
)


def default_config_path() -> Path:
    root = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".config")
    return Path(root) / "ScientificVectorStudio" / "online-license.json"


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError("ONLINE_LICENSE_NOT_ACTIVATED")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not all(data.get(key) for key in ("server_url", "api_key", "device_id")):
        raise RuntimeError("ONLINE_LICENSE_CONFIG_INVALID")
    return data


def write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="online-license-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def request(server_url: str, path: str, payload: dict[str, Any] | None, config: dict[str, Any] | None = None, method: str = "POST") -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if config:
        headers["X-SVS-Key"] = config["api_key"]
        headers["X-SVS-Device"] = config["device_id"]
    req = urllib.request.Request(server_url.rstrip("/") + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            error = json.loads(raw)
        except json.JSONDecodeError:
            error = {"message": raw}
        if exc.code == 402 or error.get("error") == "PURCHASE_REQUIRED":
            print(json.dumps({"ok": False, "purchase_required": True, "message": PURCHASE_MESSAGE}, ensure_ascii=False))
            raise SystemExit(4)
        raise RuntimeError(f"LICENSE_SERVER_HTTP_{exc.code}|{error.get('message') or error.get('error')}") from exc


def command_activate(args: argparse.Namespace) -> None:
    path = Path(args.config).expanduser().resolve()
    parsed = urllib.parse.urlparse(args.server)
    if parsed.scheme != "https" and parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError("HTTPS_LICENSE_SERVER_REQUIRED")
    device_id = args.device_id or "device-" + uuid.uuid4().hex
    result = request(
        args.server,
        "/v1/activate",
        {"activation_code": args.code, "device_id": device_id},
    )
    write_config(path, {"server_url": args.server.rstrip("/"), "api_key": result["api_key"], "device_id": device_id})
    print(json.dumps({"ok": True, "mode": "online", "device_id": device_id}, ensure_ascii=False))


def command_api(args: argparse.Namespace) -> None:
    config = read_config(Path(args.config).expanduser().resolve())
    if args.command == "status":
        result = request(config["server_url"], "/v1/usage/status", None, config, method="GET")
    else:
        payload = {"usage_id": args.usage_id}
        if args.command == "reserve":
            payload["artifact_sha256"] = args.artifact_sha256
        result = request(config["server_url"], f"/v1/usage/{args.command}", payload, config)
    print(json.dumps({"ok": True, "mode": "online", **result}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scientific Vector Studio online licensing client")
    parser.add_argument("--config", default=str(default_config_path()))
    subparsers = parser.add_subparsers(dest="command", required=True)
    activate = subparsers.add_parser("activate")
    activate.add_argument("--server", required=True)
    activate.add_argument("--code", required=True)
    activate.add_argument("--device-id")
    activate.set_defaults(func=command_activate)
    reserve = subparsers.add_parser("reserve")
    reserve.add_argument("--usage-id", required=True)
    reserve.add_argument("--artifact-sha256", required=True)
    reserve.set_defaults(func=command_api)
    for name in ("commit", "cancel"):
        command = subparsers.add_parser(name)
        command.add_argument("--usage-id", required=True)
        command.set_defaults(func=command_api)
    status = subparsers.add_parser("status")
    status.set_defaults(func=command_api)
    return parser


def main() -> None:
    try:
        args = build_parser().parse_args()
        args.func(args)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
