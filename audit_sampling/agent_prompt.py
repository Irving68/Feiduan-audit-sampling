"""面向 Cowork/WorkBuddy 的通用审计字段提取提示。"""
from __future__ import annotations

from typing import Any


def build_agent_prompt(request: dict[str, Any]) -> str:
    mode = "整套资料" if request.get("mode") == "whole-set" else "非整套资料"
    keywords = request.get("keywords") or "未指定，请自行判断具有审计价值的关键字段"
    chunks = []
    for page in request.get("pages", []):
        words = "\n".join(
            f"{word.get('word_id', '')} | {float(word.get('confidence', 0) or 0):.4f} | {word.get('text', '')}"
            for word in page.get("words", [])
        )
        chunks.append(
            f"【文件：{page.get('file', '')}｜file_id={page.get('file_id', '')}｜第{page.get('page', '')}页｜page_id={page.get('page_id', '')}】\n"
            f"OCR文字块（word_id | OCR置信度 | 原文）：\n{words}"
        )
    ocr_text = "\n\n".join(chunks)
    return f"""你是一位资深财务审计师。王二审计抽凭 v1.2.0-beta 已在本地完成 PaddleOCR；你只能分析下方 OCR 文本，禁止读取或请求原始图片。

处理模式：{mode}
用户关键词：{keywords}

任务：
1. 按文件和页码判断真实文档类型，不要仅凭零散关键词虚构文档。
2. 同一张/同一实例中的字段使用相同 group_id；不同文档实例必须使用不同 group_id。
3. 自动提取具有审计价值的关键字段，只返回 importance=high 的字段。金额去掉币种符号和“元”，保留数字、小数点及负号。
4. 每个字段必须保留准确的 file、file_id、page_hint、OCR来源原文 source_text 和 confidence。
5. evidence_word_ids 必须引用上方真实 word_id，并准确覆盖该字段的原始证据；同页出现重复金额或文字时，必须选择正确实例对应的 word_id。
6. 若你修正了 OCR，请同时填写 raw_value（OCR 原始值）和 correction（修正说明）；不要覆盖或改写 source_text。value 写最终修正值，evidence_word_ids 仍引用原始 OCR 证据。
7. 输出前检查金额、人名、公司名、账号、编号是否串位；不要合并不同文件或不同实例。

只返回严格 JSON，不要 Markdown，不要解释：
{{
  "fields": [
    {{
      "document_type": "资料类型",
      "file": "必须与输入文件名完全一致",
      "file_id": "输入中对应的file_id",
      "group_id": "例如 文件名-g001",
      "name": "字段名",
      "value": "字段值",
      "raw_value": "OCR原始值；未修正时与value相同",
      "page_hint": 1,
      "source_text": "该值所在的OCR原文",
      "correction": "修正说明；无修正填空字符串",
      "evidence_word_ids": ["file_001_p001_w001"],
      "confidence": 0.95,
      "importance": "high"
    }}
  ]
}}

OCR文本：
{ocr_text}
"""
