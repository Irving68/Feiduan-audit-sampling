"""Agent 输入/输出协议适配。

字段名称和字段数量保持动态；只统一交接结构。
同时兼容现有主流程的 document_groups/audit_key_fields 结果，避免重复设计字段提取。
"""

from __future__ import annotations

import json
import re
from typing import Any


class AgentProtocolError(ValueError):
    """Agent 返回内容不符合结构化协议。"""


def _parse_json_text(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise AgentProtocolError("Agent 输出不是有效 JSON")
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AgentProtocolError(f"Agent JSON 解析失败: {exc}") from exc
    if not isinstance(value, dict):
        raise AgentProtocolError("Agent JSON 顶层必须是对象")
    return value


def _number_or_default(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_word_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_field(field: dict[str, Any], document_type: str, page_hint: Any = None, file_name: str = "", group_id: str = "") -> dict[str, Any]:
    """将新旧字段结构统一为 王二审计抽凭 v1.2.0-beta 内部结构。"""

    name = str(field.get("name", field.get("field", "")) or "").strip()
    value = field.get("value", "")
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, ensure_ascii=False)
    else:
        value = str(value) if value is not None else ""

    raw_page = field.get("page_hint", field.get("page", page_hint))
    try:
        normalized_page = int(raw_page) if raw_page is not None else None
    except (TypeError, ValueError):
        normalized_page = None

    confidence = max(0.0, min(1.0, _number_or_default(field.get("confidence", 0.0))))
    raw_value = field.get("raw_value", field.get("ocr_value", field.get("source_value", "")))
    if raw_value is None:
        raw_value = ""
    elif not isinstance(raw_value, str):
        raw_value = str(raw_value)
    return {
        "document_type": document_type or "未知资料",
        "file": str(field.get("file", field.get("filename", file_name)) or ""),
        "file_id": str(field.get("file_id", "") or ""),
        "group_id": str(field.get("group_id", field.get("instance_id", group_id)) or ""),
        "name": name or "未命名字段",
        "value": value,
        "raw_value": raw_value,
        "page_hint": normalized_page,
        "source_text": str(field.get("source_text", field.get("source", "")) or ""),
        "correction": str(field.get("correction", field.get("correction_note", "")) or ""),
        "evidence_word_ids": _normalize_word_ids(field.get("evidence_word_ids", field.get("word_ids"))),
        "review_status": str(field.get("review_status", "reviewed") or "reviewed"),
        "confidence": confidence,
        "importance": str(field.get("importance", "high") or "high").lower(),
    }


def normalize_agent_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """把 Agent 输出转换成动态字段列表。

    支持两种输入：
    1. 新协议：{"fields": [{"name": ..., "value": ...}]}
    2. 现有主流程：{"document_groups": [{"doc_type": ..., "audit_key_fields": [...]}]}
    """

    fields: list[dict[str, Any]] = []
    direct_fields = payload.get("fields")
    if isinstance(direct_fields, list):
        payload_document_type = str(payload.get("document_type", "") or "")
        for item in direct_fields:
            if isinstance(item, dict):
                fields.append(_normalize_field(item, str(item.get("document_type", payload_document_type)), group_id=str(item.get("group_id", item.get("instance_id", "direct_default")))))

    groups = payload.get("document_groups")
    if isinstance(groups, list):
        for group_index, group in enumerate(groups, start=1):
            if not isinstance(group, dict):
                continue
            doc_type = str(group.get("doc_type", group.get("document_type", "未知资料")) or "未知资料")
            group_page = group.get("page")
            group_file = str(group.get("file", group.get("filename", "")) or "")
            group_id = str(group.get("group_id", group.get("instance_id", f"group_{group_index:04d}")) or "")
            raw_fields = group.get("audit_key_fields", group.get("fields", []))
            if not isinstance(raw_fields, list):
                continue
            for item in raw_fields:
                if isinstance(item, dict):
                    fields.append(_normalize_field(item, doc_type, group_page, group_file, group_id))

    if not fields:
        raise AgentProtocolError("Agent 输出中没有可用字段")
    return fields


def validate_agent_fields(manifest: dict[str, Any], fields: list[dict[str, Any]]) -> list[str]:
    """校验 Agent 结果能否唯一绑定到本次任务的 OCR 证据。"""

    errors: list[str] = []
    files = manifest.get("files", [])
    file_ids = {str(item.get("file_id", "")): item for item in files}
    names: dict[str, list[dict[str, Any]]] = {}
    for item in files:
        names.setdefault(str(item.get("name", "")), []).append(item)

    word_locations: dict[str, dict[str, Any]] = {}
    for page in manifest.get("ocr", []):
        for word in page.get("words", []) or []:
            word_id = str(word.get("word_id", "") or "")
            if word_id:
                word_locations[word_id] = page

    for index, field in enumerate(fields, start=1):
        prefix = f"字段 {index}（{field.get('name') or '未命名'}）"
        for key, label in (
            ("document_type", "document_type"),
            ("group_id", "group_id"),
            ("name", "name"),
            ("value", "value"),
            ("source_text", "source_text"),
        ):
            if not str(field.get(key, "") or "").strip():
                errors.append(f"{prefix} 缺少 {label}")

        file_name = str(field.get("file", "") or "")
        file_id = str(field.get("file_id", "") or "")
        if file_name not in names:
            errors.append(f"{prefix} 的 file 不属于本次任务: {file_name or '<空>'}")
        elif len(names[file_name]) > 1 and not file_id:
            errors.append(f"{prefix} 使用了重名文件，必须返回 file_id")
        if file_id and file_id not in file_ids:
            errors.append(f"{prefix} 的 file_id 无效: {file_id}")
        elif file_id and file_name and str(file_ids[file_id].get("name", "")) != file_name:
            errors.append(f"{prefix} 的 file 与 file_id 不一致")

        page_hint = field.get("page_hint")
        if page_hint is None:
            errors.append(f"{prefix} 缺少 page_hint")

        word_ids = field.get("evidence_word_ids", []) or []
        if not word_ids:
            errors.append(f"{prefix} 缺少 evidence_word_ids，无法稳定绑定高亮坐标")
            continue
        pages = []
        for word_id in word_ids:
            page = word_locations.get(str(word_id))
            if page is None:
                errors.append(f"{prefix} 引用了不存在的 evidence_word_id: {word_id}")
            else:
                pages.append(page)
        page_ids = {str(page.get("page_id", "")) for page in pages}
        if len(page_ids) > 1:
            errors.append(f"{prefix} 的 evidence_word_ids 跨越多个页面")
        if pages:
            page = pages[0]
            if page_hint is not None and page.get("source_page") != page_hint:
                errors.append(f"{prefix} 的 page_hint 与证据页不一致")
            page_file_id = str(page.get("file_id", "") or "")
            page_file = str(page.get("filename", "") or "")
            if file_id and page_file_id != file_id:
                errors.append(f"{prefix} 的 file_id 与证据文件不一致")
            elif file_name and page_file != file_name:
                errors.append(f"{prefix} 的 file 与证据文件不一致")

        if field.get("correction") and not str(field.get("raw_value", "") or "").strip():
            errors.append(f"{prefix} 修正了 OCR，但缺少 raw_value")
    return errors


def normalize_agent_text(raw: str) -> list[dict[str, Any]]:
    return normalize_agent_payload(_parse_json_text(raw))
