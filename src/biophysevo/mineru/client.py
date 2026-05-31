"""MinerU v4 API client.

Implements the real asynchronous `mineru.net/api/v4` flow:

    1. POST /file-urls/batch        -> {batch_id, file_urls:[presigned PUT url]}
    2. PUT  <presigned url>         (upload the PDF bytes; no auth header)
    3. GET  /extract-results/batch/<batch_id>  (poll until state == "done")
    4. GET  <full_zip_url>          (download the result ZIP)

The ZIP carries the same `*_content_list.json` + markdown that the local CLI
produces, so we reuse ``mineru_content_list_to_payload`` to return the
canonical payload our pipeline expects. Tests mock the ``requests`` calls.
"""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .normalize_outputs import mineru_content_list_to_payload


class MinerUAPIError(RuntimeError):
    pass


@dataclass
class MinerUClientConfig:
    base_url: str = "https://mineru.net/api/v4"
    timeout_seconds: int = 300
    api_key_env: str = "MINERU_API_KEY"
    language: str = "en"
    enable_formula: bool = True
    enable_table: bool = True
    is_ocr: bool = False
    poll_interval_seconds: float = 3.0
    max_poll_attempts: int = 200


class MinerUClient:
    """Submits one PDF through the MinerU v4 batch API and returns its payload."""

    def __init__(self, config: MinerUClientConfig | None = None) -> None:
        self.config = config or MinerUClientConfig()
        self._api_key = os.environ.get(self.config.api_key_env, "")

    @property
    def has_credentials(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def parse_pdf(self, pdf_path: str | Path) -> dict[str, Any]:
        """Send one PDF and return the normalized MinerU payload.

        Shape: ``{"markdown": str, "json": dict, "tables": [...],
        "formulas": [...], "figures": [...]}``.
        """
        if not self.has_credentials:
            raise MinerUAPIError(
                f"{self.config.api_key_env} is not set; cannot call MinerU API."
            )
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        batch_id, upload_url = self._request_upload_url(pdf_path.name)
        self._upload(upload_url, pdf_path.read_bytes())
        zip_url = self._poll_for_zip(batch_id, pdf_path.name)
        zip_bytes = self._download(zip_url)
        return self._zip_to_payload(zip_bytes)

    # -- steps ---------------------------------------------------------------

    def _request_upload_url(self, file_name: str) -> tuple[str, str]:
        body = {
            "enable_formula": self.config.enable_formula,
            "enable_table": self.config.enable_table,
            "language": self.config.language,
            "files": [{"name": file_name, "is_ocr": self.config.is_ocr}],
        }
        resp = requests.post(
            f"{self.config.base_url}/file-urls/batch",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=body,
            timeout=self.config.timeout_seconds,
        )
        data = self._json_or_raise(resp, "requesting upload URLs")
        batch_id = data.get("batch_id")
        urls = data.get("file_urls") or []
        if not batch_id or not urls:
            raise MinerUAPIError(f"upload-URL response missing batch_id/file_urls: {data}")
        return batch_id, urls[0]

    def _upload(self, url: str, pdf_bytes: bytes) -> None:
        resp = requests.put(url, data=pdf_bytes, timeout=self.config.timeout_seconds)
        if resp.status_code >= 400:
            raise MinerUAPIError(
                f"PDF upload failed ({resp.status_code}): {getattr(resp, 'text', '')[:300]}"
            )

    def _poll_for_zip(self, batch_id: str, file_name: str) -> str:
        url = f"{self.config.base_url}/extract-results/batch/{batch_id}"
        for _ in range(self.config.max_poll_attempts):
            resp = requests.get(url, headers=self._headers(), timeout=self.config.timeout_seconds)
            data = self._json_or_raise(resp, "polling extract results")
            result = self._select_result(data.get("extract_result") or [], file_name)
            state = result.get("state")
            if state == "done":
                zip_url = result.get("full_zip_url")
                if not zip_url:
                    raise MinerUAPIError(f"done but no full_zip_url: {result}")
                return zip_url
            if state == "failed":
                raise MinerUAPIError(
                    f"MinerU parse failed: {result.get('err_msg') or result}"
                )
            time.sleep(self.config.poll_interval_seconds)
        raise MinerUAPIError(
            f"MinerU parse did not finish after {self.config.max_poll_attempts} polls"
        )

    def _download(self, zip_url: str) -> bytes:
        resp = requests.get(zip_url, timeout=self.config.timeout_seconds)
        if resp.status_code >= 400:
            raise MinerUAPIError(f"result download failed ({resp.status_code})")
        return resp.content

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _select_result(results: list[dict], file_name: str) -> dict:
        for r in results:
            if r.get("file_name") == file_name:
                return r
        return results[0] if results else {}

    @staticmethod
    def _json_or_raise(resp: Any, what: str) -> dict:
        if resp.status_code >= 400:
            raise MinerUAPIError(
                f"MinerU API error {what} ({resp.status_code}): "
                f"{getattr(resp, 'text', '')[:300]}"
            )
        body = resp.json()
        if body.get("code") not in (0, None):
            raise MinerUAPIError(
                f"MinerU API error {what}: {body.get('msg') or body.get('message') or body}"
            )
        return body.get("data") or {}

    @staticmethod
    def _zip_to_payload(zip_bytes: bytes) -> dict[str, Any]:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            cl_name = next((n for n in names if n.endswith("_content_list.json")), None)
            if cl_name is None:
                raise MinerUAPIError(
                    f"result ZIP has no *_content_list.json (members: {names})"
                )
            content_list = json.loads(zf.read(cl_name).decode("utf-8"))
            md_name = _pick_markdown(names)
            markdown = zf.read(md_name).decode("utf-8") if md_name else ""
        return mineru_content_list_to_payload(content_list, markdown=markdown)


def _pick_markdown(names: list[str]) -> str | None:
    """Prefer ``full.md``, else any ``*.md`` in the ZIP."""
    md = [n for n in names if n.endswith(".md")]
    if not md:
        return None
    for n in md:
        if Path(n).name == "full.md":
            return n
    return md[0]


@dataclass
class MinerUAgentConfig:
    # Token-free Agent lightweight API, rate-limited by IP. Markdown-only output.
    base_url: str = "https://mineru.net/api/v1/agent"
    timeout_seconds: int = 300
    language: str = "en"
    enable_table: bool = True
    enable_formula: bool = True
    is_ocr: bool = False
    page_range: str | None = None
    poll_interval_seconds: float = 3.0
    max_poll_attempts: int = 200


class MinerUAgentClient:
    """MinerU Agent lightweight API client (no token; IP-rate-limited).

    Flow: ``POST /parse/file`` -> ``{task_id, file_url}`` -> ``PUT`` the PDF
    bytes to ``file_url`` -> poll ``GET /parse/{task_id}`` until ``done`` ->
    download ``markdown_url``. Output is markdown only (no tables/formulas/
    figures), so those payload lists come back empty.
    """

    def __init__(self, config: MinerUAgentConfig | None = None) -> None:
        self.config = config or MinerUAgentConfig()

    def parse_pdf(self, pdf_path: str | Path) -> dict[str, Any]:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        task_id, upload_url = self._submit(pdf_path.name)
        self._upload(upload_url, pdf_path.read_bytes())
        markdown_url = self._poll_for_markdown(task_id)
        markdown = self._download_text(markdown_url)
        return {
            "markdown": markdown,
            "json": {},
            "tables": [],
            "formulas": [],
            "figures": [],
        }

    def _submit(self, file_name: str) -> tuple[str, str]:
        body: dict[str, Any] = {
            "file_name": file_name,
            "language": self.config.language,
            "enable_table": self.config.enable_table,
            "enable_formula": self.config.enable_formula,
            "is_ocr": self.config.is_ocr,
        }
        if self.config.page_range:
            body["page_range"] = self.config.page_range
        resp = requests.post(
            f"{self.config.base_url}/parse/file",
            headers={"Content-Type": "application/json"},
            json=body,
            timeout=self.config.timeout_seconds,
        )
        data = _agent_json_or_raise(resp, "submitting file")
        task_id = data.get("task_id")
        file_url = data.get("file_url")
        if not task_id or not file_url:
            raise MinerUAPIError(f"submit response missing task_id/file_url: {data}")
        return task_id, file_url

    def _upload(self, url: str, pdf_bytes: bytes) -> None:
        resp = requests.put(url, data=pdf_bytes, timeout=self.config.timeout_seconds)
        if resp.status_code >= 400:
            raise MinerUAPIError(
                f"PDF upload failed ({resp.status_code}): {getattr(resp, 'text', '')[:300]}"
            )

    def _poll_for_markdown(self, task_id: str) -> str:
        url = f"{self.config.base_url}/parse/{task_id}"
        for _ in range(self.config.max_poll_attempts):
            resp = requests.get(url, timeout=self.config.timeout_seconds)
            data = _agent_json_or_raise(resp, "polling task")
            state = data.get("state")
            if state == "done":
                md_url = data.get("markdown_url")
                if not md_url:
                    raise MinerUAPIError(f"done but no markdown_url: {data}")
                return md_url
            if state == "failed":
                raise MinerUAPIError(
                    f"MinerU parse failed: {data.get('err_msg') or data}"
                )
            time.sleep(self.config.poll_interval_seconds)
        raise MinerUAPIError(
            f"MinerU parse did not finish after {self.config.max_poll_attempts} polls"
        )

    def _download_text(self, url: str) -> str:
        resp = requests.get(url, timeout=self.config.timeout_seconds)
        if resp.status_code >= 400:
            raise MinerUAPIError(f"markdown download failed ({resp.status_code})")
        return resp.text


def _agent_json_or_raise(resp: Any, what: str) -> dict:
    if resp.status_code >= 400:
        raise MinerUAPIError(
            f"MinerU Agent API error {what} ({resp.status_code}): "
            f"{getattr(resp, 'text', '')[:300]}"
        )
    body = resp.json()
    if body.get("code") not in (0, None):
        raise MinerUAPIError(
            f"MinerU Agent API error {what}: "
            f"{body.get('msg') or body.get('message') or body}"
        )
    return body.get("data") or {}
