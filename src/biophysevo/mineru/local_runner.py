"""Local MinerU CLI runner.

Fallback when no MinerU API key is available. Shells out to the ``mineru``
binary if present. Tests stub ``subprocess.run`` so no real CLI is required.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .normalize_outputs import mineru_content_list_to_payload


@dataclass
class LocalRunnerConfig:
    cli: str = "mineru"
    extra_args: list[str] | None = None


class LocalRunnerError(RuntimeError):
    pass


class LocalMinerURunner:
    def __init__(self, config: LocalRunnerConfig | None = None) -> None:
        self.config = config or LocalRunnerConfig()

    @property
    def is_available(self) -> bool:
        return shutil.which(self.config.cli) is not None

    def parse_pdf(self, pdf_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
        """Run the local MinerU CLI and adapt its output into a payload dict.

        MinerU 2.x is invoked as ``mineru -p <pdf> -o <out_dir>`` and writes a
        nested tree ``<out_dir>/<stem>/<backend>/<stem>_content_list.json`` plus
        a sibling ``<stem>.md``. We locate the content-list (backend-subdir
        agnostic), read the markdown if present, and return the canonical
        payload shape consumed by ``normalize_mineru_payload``.
        """
        if not self.is_available:
            raise LocalRunnerError(
                f"local MinerU CLI {self.config.cli!r} not found on PATH"
            )
        pdf_path = Path(pdf_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [self.config.cli, "-p", str(pdf_path), "-o", str(out_dir)]
        cmd.extend(self.config.extra_args or [])
        completed = subprocess.run(cmd, capture_output=True, text=True)
        if completed.returncode != 0:
            raise LocalRunnerError(
                f"mineru exited {completed.returncode}: {completed.stderr[:300]}"
            )

        content_list_path = next(out_dir.rglob("*_content_list.json"), None)
        if content_list_path is None:
            raise LocalRunnerError(
                f"local mineru produced no *_content_list.json under {out_dir}"
            )
        content_list = json.loads(content_list_path.read_text())

        md_path = next(content_list_path.parent.glob("*.md"), None)
        markdown = md_path.read_text() if md_path is not None else ""

        return mineru_content_list_to_payload(content_list, markdown=markdown)
