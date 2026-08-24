"""本地 PaddleOCR 页面处理器。

只负责：
1. 将 PDF 拆成任务目录中的页面图片；
2. 使用 PaddleOCR 生成文字和完整词级坐标；
3. 返回可写入 manifest.json 的页面/OCR 数据。

Agent、字段提取、Excel 和预览渲染不在本模块内。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

import fitz
from PIL import Image, ImageOps


ProgressCallback = Callable[[dict[str, Any]], None]


def _normalize_words(record: Any) -> list[dict[str, Any]]:
    """兼容 PaddleOCR 3.x 当前结构及旧结构，统一为 words。"""

    payload = record.get("res", record) if hasattr(record, "get") else record
    if not isinstance(payload, dict):
        return []

    texts = payload.get("rec_texts", []) or []
    scores = payload.get("rec_scores", []) or []
    polygons = payload.get("rec_polys")
    if polygons is None:
        polygons = payload.get("rec_polygons", []) or []
    if not polygons:
        polygons = payload.get("dt_polys", []) or payload.get("det_polygons", []) or []

    words: list[dict[str, Any]] = []
    for index, text in enumerate(texts):
        text = str(text or "").strip()
        if not text:
            continue
        bbox = None
        polygon = polygons[index] if index < len(polygons) else None
        if polygon is not None:
            try:
                xs = [float(point[0]) for point in polygon]
                ys = [float(point[1]) for point in polygon]
                left, top = int(min(xs)), int(min(ys))
                right, bottom = int(max(xs)), int(max(ys))
                if left >= 0 and top >= 0 and right > left and bottom > top:
                    bbox = {
                        "left": left,
                        "top": top,
                        "width": right - left,
                        "height": bottom - top,
                    }
            except (TypeError, ValueError, IndexError):
                bbox = None
        score = scores[index] if index < len(scores) else 0.9
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0
        words.append({"text": text, "confidence": score, "bbox": bbox})
    return words


class PaddleLocalOCR:
    """任务级 PaddleOCR 处理器，实例内部懒加载模型。"""

    def __init__(self) -> None:
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
            from paddleocr import PaddleOCR

            # PaddleOCR 3.7 在 Windows 底层对含中文/空格的绝对模型路径兼容性较差。
            # bat 入口会把 cwd 固定为 engine，因此这里使用稳定的相对路径。
            det_dir = Path("models/PP-OCRv5_mobile_det")
            rec_dir = Path("models/PP-OCRv5_mobile_rec")
            options = {
                "lang": "ch",
                "text_detection_model_name": "PP-OCRv5_mobile_det",
                "text_recognition_model_name": "PP-OCRv5_mobile_rec",
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
                "enable_mkldnn": False,
            }
            if det_dir.exists() and rec_dir.exists():
                options.update({
                    "text_detection_model_dir": det_dir.as_posix(),
                    "text_recognition_model_dir": rec_dir.as_posix(),
                })
            self._ocr = PaddleOCR(
                **options,
            )
        return self._ocr

    @staticmethod
    def _save_pdf_page(page: fitz.Page, target: Path) -> tuple[int, int]:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(str(target))
        return pix.width, pix.height

    @staticmethod
    def _copy_image(source: Path, target: Path) -> tuple[int, int]:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.save(target, format="JPEG", quality=95)
            return image.width, image.height

    def recognize_file(
        self,
        file_path: str | Path,
        file_id: str,
        pages_dir: str | Path,
        progress: ProgressCallback | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """处理一个文件，返回 pages 元数据和 ocr 页面记录。"""

        source = Path(file_path).expanduser().resolve()
        pages_root = Path(pages_dir)
        pages_root.mkdir(parents=True, exist_ok=True)
        page_entries: list[dict[str, Any]] = []
        ocr_entries: list[dict[str, Any]] = []

        if source.suffix.lower() == ".pdf":
            document = fitz.open(str(source))
            try:
                page_sources = [(index + 1, page) for index, page in enumerate(document)]
                for source_page, page in page_sources:
                    page_id = f"{file_id}_p{source_page:03d}"
                    image_path = pages_root / f"{page_id}.jpg"
                    width, height = self._save_pdf_page(page, image_path)
                    page_entries.append({
                        "page_id": page_id,
                        "file_id": file_id,
                        "filename": source.name,
                        "source_page": source_page,
                        "image": f"pages/{image_path.name}",
                        "width": width,
                        "height": height,
                    })
                    ocr_entries.append(self._recognize_page(page_id, file_id, source.name, source_page, image_path))
                    if progress:
                        progress({"file": source.name, "page": source_page, "total_pages": len(page_sources)})
            finally:
                document.close()
        else:
            page_id = f"{file_id}_p001"
            image_path = pages_root / f"{page_id}.jpg"
            width, height = self._copy_image(source, image_path)
            page_entries.append({
                "page_id": page_id,
                "file_id": file_id,
                "filename": source.name,
                "source_page": 1,
                "image": f"pages/{image_path.name}",
                "width": width,
                "height": height,
            })
            ocr_entries.append(self._recognize_page(page_id, file_id, source.name, 1, image_path))
            if progress:
                progress({"file": source.name, "page": 1, "total_pages": 1})

        return page_entries, ocr_entries

    def _recognize_page(
        self,
        page_id: str,
        file_id: str,
        filename: str,
        source_page: int,
        image_path: Path,
    ) -> dict[str, Any]:
        result = self._get_ocr().predict(str(image_path))
        record = result[0] if result else {}
        words = _normalize_words(record)
        for index, word in enumerate(words, start=1):
            word["word_id"] = f"{page_id}_w{index:03d}"
        return {
            "page_id": page_id,
            "file_id": file_id,
            "filename": filename,
            "source_page": source_page,
            "text": "\n".join(word["text"] for word in words),
            "words": words,
        }
