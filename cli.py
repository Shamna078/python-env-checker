"""Command-line environment diagnostics."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import platform
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {"required_env": [], "tools": ["git", "python"]}


def load_config(path: str | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_CONFIG.copy()
    config_path = Path(path)
    if not config_path.exists() or not config_path.is_file():
        raise ValueError(f"Configuration path is missing or is not a file: {path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON configuration: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Configuration must be a JSON object.")
    required_keys = {"required_env", "tools"}
    if not set(data).issubset(required_keys):
        unknown = sorted(set(data) - required_keys)
        raise ValueError(f"Unknown configuration key(s): {', '.join(unknown)}")
    for key in required_keys:
        if key in data and (not isinstance(data[key], list) or
                             not all(isinstance(item, str) and item.strip()
                                     for item in data[key])):
            raise ValueError(f"'{key}' must be a list of non-empty strings.")
    result = DEFAULT_CONFIG.copy()
    result.update(data)
    return result


def check_environment(config: dict[str, Any], disk_path: str = ".") -> dict[str, Any]:
    required_env = config.get("required_env", [])
    tools = config.get("tools", [])

    env_results = {
        name: bool(os.environ.get(name))
        for name in required_env
    }
    tool_results = {
        name: shutil.which(name) is not None
        for name in tools
    }

    try:
        disk = shutil.disk_usage(disk_path)
        disk_result = {
            "path": str(Path(disk_path).resolve()),
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "ok": True,
        }
    except (OSError, ValueError) as exc:
        disk_result = {
            "path": disk_path,
            "ok": False,
            "error": str(exc),
        }

    checks_ok = (
        all(env_results.values())
        and all(tool_results.values())
        and disk_result["ok"]
    )
    return {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "minimum_version": "3.9",
            "ok": sys.version_info >= (3, 9),
        },
        "disk": disk_result,
        "environment_variables": env_results,
        "developer_tools": tool_results,
        "overall_ok": checks_ok and sys.version_info >= (3, 9),
    }


def human_report(report: dict[str, Any]) -> str:
    lines = [
        "Python Environment Checker",
        "=" * 28,
        f"Python: {report['python']['version']} "
        f"({'OK' if report['python']['ok'] else 'FAIL'})",
        f"Executable: {report['python']['executable']}",
    ]
    disk = report["disk"]
    if disk["ok"]:
        lines.append(
            f"Disk: {disk['free_bytes'] / (1024 ** 3):.2f} GiB free "
            f"at {disk['path']} (OK)"
        )
    else:
        lines.append(f"Disk: FAIL - {disk['error']}")
    lines.append("Environment variables:")
    if report["environment_variables"]:
        lines.extend(
            f"  {name}: {'OK' if present else 'MISSING'}"
            for name, present in report["environment_variables"].items()
        )
    else:
        lines.append("  No required variables configured.")
    lines.append("Developer tools:")
    if report["developer_tools"]:
        lines.extend(
            f"  {name}: {'FOUND' if found else 'MISSING'}"
            for name, found in report["developer_tools"].items()
        )
    else:
        lines.append("  No tools configured.")
    lines.append(f"Overall: {'PASS' if report['overall_ok'] else 'FAIL'}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="env-checker",
        description="Inspect Python and development environment readiness.",
    )
    parser.add_argument("--config", help="Path to optional JSON configuration.")
    parser.add_argument("--json", action="store_true",
                        help="Print structured JSON instead of a text report.")
    parser.add_argument("--output", help="Write structured JSON report to this file.")
    parser.add_argument("--disk-path", default=".",
                        help="Path whose disk space should be checked (default: current directory).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    report = check_environment(config, args.disk_path)
    rendered_json = json.dumps(report, indent=2)
    if args.output:
        try:
            Path(args.output).write_text(rendered_json + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"Could not write report: {exc}", file=sys.stderr)
            return 2

    print(rendered_json if args.json else human_report(report))
    return 0 if report["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
