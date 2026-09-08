"""Preset-based AetherFlow Remote Control entrypoint.

This is the preferred bootstrap when UE blocks direct remote access to the
PythonScriptLibrary. It uses the explicit Remote Control Preset surface.
"""
from __future__ import annotations

import argparse
import json
import sys

from remote_client import RemoteControlClient, RemoteControlConfig, RemoteControlError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test/control UE5 through AetherFlowRemote preset.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30010)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--preset", default="AetherFlowRemote")
    parser.add_argument("--function", default="AetherFlow_Test")
    parser.add_argument("--list", action="store_true", help="List available Remote Control presets")
    parser.add_argument("--describe", action="store_true", help="Describe the selected preset")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    client = RemoteControlClient(RemoteControlConfig(host=args.host, port=args.port, timeout_s=args.timeout))

    try:
        info = client.info()
        if args.list:
            result = client.presets()
            action = "list-presets"
        elif args.describe:
            result = client.preset(args.preset)
            action = "describe-preset"
        else:
            result = client.call_preset_function(args.preset, args.function)
            action = "call-preset-function"
    except RemoteControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    payload = {
        "ok": True,
        "action": action,
        "remote_control": {"host": args.host, "port": args.port},
        "http_routes": len((info or {}).get("HttpRoutes", [])),
        "preset": args.preset,
        "function": args.function,
        "result": result,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("AetherFlow UE5 preset bridge: PASS")
        print(f"Action: {action}")
        print(f"Remote Control: {args.host}:{args.port}")
        print(f"Preset: {args.preset}")
        print(f"Function: {args.function}")
        print(f"Result: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
