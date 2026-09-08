"""Command-line orchestration for the AetherFlow UE5 Remote Control bridge."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from remote_client import RemoteControlClient, RemoteControlConfig, RemoteControlError


def _python_bootstrap(ue_bridge_dir: Path, manifest_path: Path, registry_path: Path | None, clear_previous: bool) -> str:
    module_dir = str(ue_bridge_dir.resolve()).replace("\\", "/").replace("'", "\\'")
    manifest = str(manifest_path.resolve()).replace("\\", "/").replace("'", "\\'")
    registry = "None" if registry_path is None else "r'{}'".format(str(registry_path.resolve()).replace("\\", "/").replace("'", "\\'"))
    flag = "True" if clear_previous else "False"
    return (
        "import sys; "
        f"sys.path.insert(0, r'{module_dir}'); "
        "from aetherflow_ue5_bridge import sync_manifest; "
        f"print(sync_manifest(r'{manifest}', registry_path={registry}, clear_previous={flag}))"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize AetherFlow with Unreal Editor.")
    parser.add_argument("--manifest", required=True, help="Path to AetherFlow manifest.json")
    parser.add_argument("--asset-registry", default=None, help="Path to project-owned UE5 asset registry JSON")
    parser.add_argument("--ue-python-dir", default=None, help="Directory containing aetherflow_ue5_bridge.py")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30010)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--keep-generated", action="store_true", help="Do not remove previous AetherFlow bridge actors")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable result")
    args = parser.parse_args(argv)

    manifest = Path(args.manifest).resolve()
    if not manifest.is_file():
        print(f"ERROR: manifest does not exist: {manifest}", file=sys.stderr)
        return 2

    registry = Path(args.asset_registry).resolve() if args.asset_registry else None
    if registry is not None and not registry.is_file():
        print(f"ERROR: asset registry does not exist: {registry}", file=sys.stderr)
        return 2

    ue_python_dir = Path(args.ue_python_dir).resolve() if args.ue_python_dir else Path(__file__).resolve() / "ue5"
    script = ue_python_dir / "aetherflow_ue5_bridge.py"
    if not script.is_file():
        print(f"ERROR: UE bridge script does not exist: {script}", file=sys.stderr)
        return 2

    client = RemoteControlClient(RemoteControlConfig(host=args.host, port=args.port, timeout_s=args.timeout))
    try:
        info = client.info()
        code = _python_bootstrap(ue_python_dir, manifest, registry, not args.keep_generated)
        result = client.execute_python_code(code)
    except RemoteControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    payload = {
        "ok": True,
        "remote_control": {"host": args.host, "port": args.port},
        "http_routes": len((info or {}).get("HttpRoutes", [])),
        "manifest": str(manifest),
        "asset_registry": str(registry) if registry else None,
        "ue_bridge": str(script),
        "execute_result": result,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("AetherFlow UE5 Bridge: PASS")
        print(f"Manifest: {manifest}")
        print(f"Asset registry: {registry or 'not supplied (marker fallback)'}")
        print(f"Remote Control: {args.host}:{args.port}")
        print(f"UE bridge: {script}")
        print(f"Execute result: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
