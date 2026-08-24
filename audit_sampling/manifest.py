"""王二审计抽凭 v1.2.0-beta 的单文件任务记录协议。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import ensure_runtime_dirs, job_dir


def new_job_id() -> str:
    """沿用现有工具的 8 位任务 ID 习惯。"""

    return str(uuid.uuid4())[:8]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_manifest(job_id: str, mode: str, files: list[Path]) -> dict[str, Any]:
    """创建任务初始 manifest；字段和 OCR 数据在处理阶段追加。"""

    return {
        "schema_version": "1.0",
        "job": {
            "job_id": job_id,
            "mode": mode,
            "status": "created",
            "created_at": utc_now(),
        },
        "files": [
            {
                "file_id": f"file_{index:03d}",
                "name": path.name,
                "source_path": str(path),
                "page_count": None,
                "status": "pending",
                "error": None,
            }
            for index, path in enumerate(files, start=1)
        ],
        "pages": [],
        "ocr": [],
        "review": {
            "stage": "pending",
            "agent_corrections": 0,
            "fields_using_raw_evidence": 0,
        },
        "fields": [],
        "summary": {
            "file_count": len(files),
            "page_count": 0,
            "field_count": 0,
            "review_count": 0,
            "failed_count": 0,
        },
        "artifacts": {
            "excel": None,
            "preview_url": None,
        },
    }


def manifest_path(job_id: str) -> Path:
    return job_dir(job_id) / "manifest.json"


def save_manifest(job_id: str, manifest: dict[str, Any]) -> Path:
    ensure_runtime_dirs()
    target_dir = job_dir(job_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = manifest_path(job_id)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_manifest(job_id: str) -> dict[str, Any]:
    path = manifest_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"任务不存在: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))
