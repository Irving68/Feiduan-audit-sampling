"""Agent 字段到 OCR 词级坐标的本地匹配。"""

from __future__ import annotations

import re
from typing import Any


def _clean(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("，", ",").replace("¥", "").replace("￥", "").replace("元", "")


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _is_amount(name: str) -> bool:
    return any(word in name for word in ("金额", "税额", "合计", "价税"))


def _matches(field_name: str, value: str, candidate: str) -> bool:
    left, right = _clean(value), _clean(candidate)
    if not left or not right:
        return False
    if _is_amount(field_name):
        left_digits, right_digits = _digits(left), _digits(right)
        return bool(left_digits) and left_digits == right_digits and ("-" in left) == ("-" in right)
    return left in right or (right in left and len(right) / max(len(left), 1) >= 0.8)


def _find_evidence(manifest: dict[str, Any], field: dict[str, Any]) -> list[dict[str, Any]]:
    """按原始 OCR 值/来源片段定位，避免 Agent 修正值破坏坐标绑定。"""
    word_ids = [str(item) for item in field.get("evidence_word_ids", []) or []]
    if word_ids:
        selected = []
        selected_page = None
        wanted = set(word_ids)
        for page in manifest.get("ocr", []):
            page_words = [word for word in page.get("words", []) or [] if str(word.get("word_id")) in wanted]
            if page_words:
                if selected_page is not None and page.get("page_id") != selected_page.get("page_id"):
                    return []
                selected_page = page
                selected.extend(page_words)
        if selected_page is not None and len(selected) == len(wanted):
            order = {word_id: index for index, word_id in enumerate(word_ids)}
            selected.sort(key=lambda word: order.get(str(word.get("word_id")), len(order)))
            return [{"page": selected_page, "words": selected, "matched_by": "evidence_word_ids"}]

    candidates = []
    for key in ("raw_value", "source_text", "value"):
        value = str(field.get(key, "") or "").strip()
        if value:
            candidates.append((key, value))
    for key, value in candidates:
        evidence: list[dict[str, Any]] = []
        for page in _candidate_pages(manifest, field):
            words = page.get("words", []) or []
            singles = [word for word in words if _matches(field.get("name", ""), value, word.get("text", ""))]
            if singles:
                evidence.extend({"page": page, "words": [word], "matched_by": key} for word in singles)
                continue
            seen: set[tuple[str, ...]] = set()
            for start in range(len(words)):
                for size in range(2, min(8, len(words) - start) + 1):
                    chunk = words[start:start + size]
                    candidate = "".join(str(word.get("text", "")) for word in chunk)
                    if _matches(field.get("name", ""), value, candidate):
                        ids = tuple(str(word.get("word_id", "")) for word in chunk)
                        if ids not in seen:
                            evidence.append({"page": page, "words": chunk, "matched_by": key})
                            seen.add(ids)
                        break
        if evidence:
            return evidence
    return []


def _union(boxes: list[dict[str, Any]]) -> dict[str, int] | None:
    valid = [box for box in boxes if isinstance(box, dict) and box.get("width") and box.get("height")]
    if not valid:
        return None
    left = min(int(box["left"]) for box in valid)
    top = min(int(box["top"]) for box in valid)
    right = max(int(box["left"]) + int(box["width"]) for box in valid)
    bottom = max(int(box["top"]) + int(box["height"]) for box in valid)
    return {"left": left, "top": top, "width": right - left, "height": bottom - top}


def _candidate_pages(manifest: dict[str, Any], field: dict[str, Any]) -> list[dict[str, Any]]:
    page_hint = field.get("page_hint")
    file_name = field.get("file", "")
    file_id = field.get("file_id", "")
    pages = manifest.get("ocr", [])
    narrowed = []
    for page in pages:
        if page_hint is not None and page.get("source_page") != page_hint:
            continue
        if file_id and page.get("file_id") != file_id:
            continue
        if not file_id and file_name and page.get("file", page.get("filename", "")) not in (file_name, ""):
            continue
        narrowed.append(page)
    return narrowed or list(pages)


def _hinted_page(manifest: dict[str, Any], field: dict[str, Any]) -> dict[str, Any] | None:
    """在文字无法匹配时，仅用唯一的文件+页码提示保留页面跳转。"""

    page_hint = field.get("page_hint")
    file_name = str(field.get("file", "") or "")
    file_id = str(field.get("file_id", "") or "")
    if page_hint is None or not (file_id or file_name):
        return None
    candidates = [
        page for page in manifest.get("ocr", [])
        if page.get("source_page") == page_hint
        and ((file_id and page.get("file_id") == file_id)
             or (not file_id and page.get("file", page.get("filename", "")) == file_name))
    ]
    return candidates[0] if len(candidates) == 1 else None


def match_fields(manifest: dict[str, Any], fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为字段追加证据 token、bbox 和匹配状态。"""

    result: list[dict[str, Any]] = []
    for index, field in enumerate(fields, start=1):
        item = dict(field)
        item["field_id"] = f"field_{index:04d}"
        evidence = _find_evidence(manifest, item)
        if evidence:
            evidence.sort(key=lambda entry: len(entry["words"]))
            best = evidence[0]
            page = best["page"]
            matched_words = best["words"]
            boxes = [word.get("bbox") for word in matched_words]
            item["page"] = page.get("source_page", item.get("page_hint"))
            item["page_id"] = page.get("page_id")
            item["file_id"] = page.get("file_id")
            item["evidence_source"] = best.get("matched_by", "value")
            item["evidence_word_ids"] = [word.get("word_id") for word in matched_words]
            item["bboxes"] = [box for box in boxes if box]
            item["bbox"] = _union(item["bboxes"])
            item["status"] = "confirmed" if len(evidence) == 1 else "ambiguous"
            weights = [max(len(str(word.get("text", "") or "")), 1) for word in matched_words]
            weighted = sum(float(word.get("confidence", 0) or 0) * weight for word, weight in zip(matched_words, weights))
            item["ocr_confidence"] = weighted / max(sum(weights), 1)
        else:
            page = _hinted_page(manifest, item)
            if page:
                item["page"] = page.get("source_page", item.get("page_hint"))
                item["page_id"] = page.get("page_id")
                item["file_id"] = page.get("file_id")
            item["evidence_word_ids"] = []
            item["bboxes"] = []
            item["bbox"] = None
            item["status"] = "missing"
            item["ocr_confidence"] = 0.0
        item["agent_confidence"] = float(item.get("confidence", 0) or 0)
        if item.get("status") == "missing":
            item["confidence"] = 0.0
        else:
            item["confidence"] = min(item["agent_confidence"], float(item.get("ocr_confidence", 0) or 0))
        reasons = []
        if item.get("protocol_error"):
            reasons.append("协议异常")
        if item.get("status") == "ambiguous":
            reasons.append("证据歧义")
        elif item.get("status") == "missing":
            reasons.append("字段缺失" if not str(item.get("value", "") or "").strip() else "证据缺失")
        if float(item.get("ocr_confidence", 0) or 0) < .9 and item.get("status") != "missing":
            reasons.append("OCR低")
        item["review_reasons"] = list(dict.fromkeys(reasons))
        item["review_reason"] = item["review_reasons"][0] if item["review_reasons"] else ""
        result.append(item)
    return result
