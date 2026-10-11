from __future__ import annotations

import argparse
import getpass
import json

from .client import authenticate
from .service import GarminService


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def auth_command() -> None:
    email = input("Garmin 中国区账号邮箱: ").strip()
    password = getpass.getpass("Garmin 密码（仅发送给 Garmin，并保存至 Windows 凭据管理器）: ")
    session = authenticate(email, password, lambda: input("Garmin MFA 验证码: ").strip())
    _print({"status": "authenticated", "region": "garmin.cn", "profile": session.api.get_full_name()})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="garmin-cn-sync")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("auth", help="Interactive Garmin China authentication")
    sync_parser = commands.add_parser("sync", help="Sync Garmin China into local SQLite")
    sync_parser.add_argument("--health-days", type=int, default=2)
    sync_parser.add_argument("--activity-days", type=int, default=7)
    sync_parser.add_argument("--bootstrap", action="store_true")
    commands.add_parser("status", help="Show local status")
    commands.add_parser("import-files", help="Import FIT/TCX fallback files")
    commands.add_parser("serve", help="Run MCP stdio server")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "auth":
        auth_command()
        return
    if args.command == "serve":
        from .server import main as serve
        serve()
        return
    service = GarminService()
    if args.command == "status":
        _print(service.status())
    elif args.command == "import-files":
        _print(service.import_files())
    elif args.command == "sync":
        _print(service.sync_now(health_days=30 if args.bootstrap else args.health_days,
                                activity_days=365 if args.bootstrap else args.activity_days))


if __name__ == "__main__":
    main()
