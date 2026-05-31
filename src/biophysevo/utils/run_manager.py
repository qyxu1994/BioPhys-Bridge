"""Run folder management per plan-v1 section 6.

Layout:
    runs/<timestamp>_<name>/
        config.yaml
        command.txt
        stdout.log
        stderr.log
        manifest.jsonl
        checkpoints/
        metrics.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .checkpoints import CheckpointStore
from .io import safe_jsonl_writer


def timestamp() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")


class RunManager:
    def __init__(
        self,
        run_dir: str | Path,
        *,
        config: dict | None = None,
        command: str | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "checkpoints").mkdir(exist_ok=True)

        if config is not None:
            (self.run_dir / "config.yaml").write_text(
                yaml.safe_dump(config, sort_keys=True)
            )
        if command is not None:
            (self.run_dir / "command.txt").write_text(command + "\n")

        self.manifest = safe_jsonl_writer(self.run_dir / "manifest.jsonl")

    @classmethod
    def create(
        cls,
        root: str | Path,
        name: str,
        *,
        config: dict | None = None,
        command: str | None = None,
    ) -> "RunManager":
        """Build ``runs/<ts>_<name>/`` under ``root`` and return a manager."""
        run_dir = Path(root) / f"{timestamp()}_{name}"
        return cls(run_dir, config=config, command=command)

    def checkpoint_store(self, name: str = "items") -> CheckpointStore:
        return CheckpointStore(self.run_dir / "checkpoints" / f"{name}.jsonl")

    def write_metrics(self, metrics: dict[str, Any]) -> None:
        (self.run_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, sort_keys=True)
        )

    def close(self) -> None:
        self.manifest.close()

    def __enter__(self) -> "RunManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def add_common_run_flags(parser: argparse.ArgumentParser) -> None:
    """Inject the standard ``--run-dir --resume --limit --dry-run`` flags."""
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Run folder. Defaults to runs/<timestamp>_<name>/ under repo root.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")


def resolve_run_dir(args: argparse.Namespace, default_name: str) -> Path:
    if args.run_dir is not None:
        return Path(args.run_dir)
    return Path("runs") / f"{timestamp()}_{default_name}"


def command_string(argv: list[str] | None = None) -> str:
    argv = argv if argv is not None else sys.argv
    return " ".join(argv)
