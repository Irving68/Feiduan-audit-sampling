"""王二审计抽凭 v1.2.0-beta 本地 CLI。"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .agent_protocol import AgentProtocolError, normalize_agent_text, validate_agent_fields
from .agent_prompt import build_agent_prompt
from .doctor import run_doctor
from .excel_export import export_excel
from .manifest import create_manifest, load_manifest, new_job_id, save_manifest
from .matcher import match_fields
from .ocr import PaddleLocalOCR
from .paths import collect_many_inputs, ensure_runtime_dirs, job_dir
from .preview import open_preview, render_preview


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _try_auto_open(job_id: str, preview: str) -> None:
    try:
        open_preview(preview)
        _emit({"type": "preview_opened", "job_id": job_id, "preview": preview})
    except Exception as exc:
        _emit({"type": "warning", "job_id": job_id, "message": f"结果已生成，但自动打开失败: {exc}"})


def command_doctor(_: argparse.Namespace) -> int:
    passed, checks = run_doctor()
    for check in checks:
        _emit({"type": "doctor", **check})
    _emit({"type": "doctor_summary", "status": "ok" if passed else "error"})
    return 0 if passed else 2


def _write_agent_request(job_id: str, manifest: dict) -> Path:
    target = job_dir(job_id) / "agent-input.json"
    pages = []
    for page in manifest.get("ocr", []):
        pages.append({
            "file": page.get("filename", ""),
            "file_id": page.get("file_id", ""),
            "page": page.get("source_page"),
            "page_id": page.get("page_id"),
            "text": page.get("text", ""),
            "words": [
                {
                    "word_id": word.get("word_id"),
                    "text": word.get("text", ""),
                    "confidence": word.get("confidence", 0),
                }
                for word in page.get("words", []) or []
            ],
        })
    request = {
        "tool": "王二审计抽凭 v1.2.0-beta",
        "job_id": job_id,
        "mode": manifest["job"].get("mode"),
        "keywords": manifest["job"].get("keywords"),
        "instructions": "只处理 pages.words 中的 OCR 文字，不要读取图片；每个字段必须返回准确的 file、file_id、page_hint 和 evidence_word_ids。value 可由 Agent 修正，但 raw_value、source_text 和 evidence_word_ids 必须保留原始 OCR 证据。",
        "pages": pages,
    }
    target.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt_path = job_dir(job_id) / "agent-prompt.txt"
    prompt_path.write_text(build_agent_prompt(request), encoding="utf-8")
    return target


def _write_agent_retry(job_id: str, manifest: dict, errors: list[str]) -> Path:
    manifest.setdefault("review", {})["validation_attempts"] = int(manifest.get("review", {}).get("validation_attempts", 0) or 0) + 1
    manifest["job"]["status"] = "awaiting_agent_correction"
    target = job_dir(job_id) / "agent-retry-prompt.txt"
    details = "\n".join(f"- {error}" for error in errors)
    target.write_text(
        "Agent 输出未通过本地协议校验。请只修正 agent-output.json，不要重新运行 OCR，也不要读取图片。\n\n"
        f"校验问题：\n{details}\n\n"
        "重新读取 agent-input.json 中的 pages.words，使用真实 word_id 修正 evidence_word_ids；"
        "保留准确的 file、file_id、page_hint、raw_value 和 source_text。修正后再次执行 render。\n",
        encoding="utf-8",
    )
    manifest.setdefault("review", {})["last_validation_errors"] = errors
    save_manifest(job_id, manifest)
    return target


def _run_ocr(job_id: str, manifest: dict, resume: bool = False) -> None:
    engine = PaddleLocalOCR()
    task_pages = job_dir(job_id) / "pages"
    all_pages = list(manifest.get("pages", []) if resume else [])
    all_ocr = list(manifest.get("ocr", []) if resume else [])
    files = manifest["files"]
    manifest["job"]["status"] = "ocr_running"
    save_manifest(job_id, manifest)
    for index, item in enumerate(files, start=1):
        file_id = item["file_id"]
        if resume and item.get("status") == "completed":
            continue
        _emit({"type": "file_started", "job_id": job_id, "file": item["name"], "index": index, "total": len(files)})
        try:
            pages, ocr = engine.recognize_file(item["source_path"], file_id, task_pages, lambda event: _emit({"type": "ocr_progress", "job_id": job_id, **event}))
            item["page_count"] = len(pages); item["status"] = "completed"
            all_pages.extend(pages); all_ocr.extend(ocr)
        except Exception as exc:
            item["status"] = "failed"; item["error"] = str(exc); item["page_count"] = 0
            manifest["summary"]["failed_count"] += 1
            _emit({"type": "file_failed", "job_id": job_id, "file": item["name"], "error": str(exc)})
        manifest["pages"] = all_pages; manifest["ocr"] = all_ocr
        manifest["summary"]["page_count"] = len(all_pages)
        save_manifest(job_id, manifest)
    if not all_ocr:
        manifest["job"]["status"] = "failed"; save_manifest(job_id, manifest)
        raise RuntimeError("所有输入文件 OCR 均失败")
    manifest["job"]["status"] = "awaiting_agent"
    request = _write_agent_request(job_id, manifest)
    save_manifest(job_id, manifest)
    _emit({"type": "agent_input_ready", "job_id": job_id, "path": str(request), "prompt": str(job_dir(job_id) / "agent-prompt.txt"), "message": "请让 Agent 读取 prompt 文件，并把返回 JSON 保存为 agent-output.json 后执行 render。"})


def _render_job(job_id: str, agent_json: str | None = None) -> dict:
    manifest = load_manifest(job_id)
    source = Path(agent_json) if agent_json else job_dir(job_id) / "agent-output.json"
    if not source.exists():
        raise FileNotFoundError(f"找不到 Agent 输出 JSON: {source}")
    fields = [field for field in normalize_agent_text(source.read_text(encoding="utf-8")) if field.get("importance") == "high"]
    if not fields:
        raise ValueError("Agent 输出中没有 high 重要性的关键字段")
    # 单文件任务中 Agent 未回填文件名时自动补齐；多文件任务仍保留空值，避免误归属。
    names = [item["name"] for item in manifest.get("files", [])]
    if len(names) == 1:
        for field in fields:
            field["file"] = names[0]
    else:
        aliases = {name: name for name in names}
        aliases.update({Path(name).stem: name for name in names})
        for field in fields:
            supplied = str(field.get("file", "") or "")
            if supplied not in aliases:
                raise ValueError(f"多文件任务的每个字段必须返回有效 file，当前值: {supplied or '<空>'}")
            field["file"] = aliases[supplied]
    files_by_name = {}
    for item in manifest.get("files", []):
        files_by_name.setdefault(item["name"], []).append(item)
    for field in fields:
        if not field.get("file_id") and len(files_by_name.get(field.get("file", ""), [])) == 1:
            field["file_id"] = files_by_name[field["file"]][0]["file_id"]
    validation_errors = validate_agent_fields(manifest, fields)
    if validation_errors:
        retry_path = _write_agent_retry(job_id, manifest, validation_errors)
        raise AgentProtocolError(f"Agent 输出校验失败，请按 {retry_path} 修正后重试")
    matched = match_fields(manifest, fields)
    manifest["fields"] = matched
    manifest.setdefault("review", {}).update({
        "stage": "completed",
        "agent_corrections": sum(1 for f in matched if f.get("correction")),
        "fields_using_raw_evidence": sum(1 for f in matched if f.get("evidence_source") in {"raw_value", "source_text"}),
        "fields_using_evidence_ids": sum(1 for f in matched if f.get("evidence_source") == "evidence_word_ids"),
    })
    manifest["summary"]["field_count"] = len(matched)
    manifest["summary"]["review_count"] = sum(1 for f in matched if f.get("review_reasons") or float(f.get("confidence", 0) or 0) < .9)
    manifest["job"]["status"] = "rendering"
    save_manifest(job_id, manifest)
    existing_excel = manifest.get("artifacts", {}).get("excel")
    if existing_excel:
        excel_target = Path(existing_excel)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        excel_target = job_dir(job_id) / (f"审计结果_整套模式_{timestamp}.xlsx" if manifest["job"].get("mode") == "whole-set" else f"审计结果_非整套模式_{timestamp}.xlsx")
    manifest.setdefault("artifacts", {})["preview_file"] = str(job_dir(job_id) / "preview.html")
    excel = export_excel(manifest, excel_target)
    preview = render_preview(manifest, job_dir(job_id))
    manifest["artifacts"].update({"excel": str(excel), "preview_file": str(preview), "preview_url": preview.as_uri()})
    manifest["job"]["status"] = "completed"
    manifest["job"]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    save_manifest(job_id, manifest)
    return {"excel": str(excel), "preview": str(preview), "review_count": manifest["summary"]["review_count"], "field_count": len(matched)}


def command_run(args: argparse.Namespace) -> int:
    files = collect_many_inputs(args.input)
    job_id = new_job_id(); ensure_runtime_dirs(); (job_dir(job_id) / "pages").mkdir(parents=True, exist_ok=True)
    manifest = create_manifest(job_id, args.mode, files)
    manifest["job"]["keywords"] = None
    save_manifest(job_id, manifest)
    _emit({"type": "started", "job_id": job_id, "input_count": len(files), "manifest": str(job_dir(job_id) / "manifest.json")})
    _run_ocr(job_id, manifest)
    if args.agent_json:
        result = _render_job(job_id, args.agent_json)
        _emit({"type": "completed", "job_id": job_id, **result})
        if not args.no_open:
            _try_auto_open(job_id, result["preview"])
    return 0


def command_resume(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.job_id)
    if manifest.get("job", {}).get("status") == "completed":
        _emit({"type": "already_completed", "job_id": args.job_id})
        return 0
    _run_ocr(args.job_id, manifest, resume=True)
    return 0


def command_render(args: argparse.Namespace) -> int:
    result = _render_job(args.job_id, args.agent_json)
    _emit({"type": "completed", "job_id": args.job_id, **result})
    if not args.no_open:
        _try_auto_open(args.job_id, result["preview"])
    return 0


def command_status(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.job_id)
    _emit({"type": "status", "job_id": args.job_id, "job": manifest.get("job"), "summary": manifest.get("summary"), "artifacts": manifest.get("artifacts")})
    return 0


def command_open(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.job_id)
    target = manifest.get("artifacts", {}).get("preview_file") or str(job_dir(args.job_id) / "preview.html")
    if not Path(target).exists():
        raise FileNotFoundError("该任务还没有生成高亮页面，请先执行 render")
    open_preview(target); _emit({"type": "opened", "job_id": args.job_id, "preview": str(Path(target).resolve())}); return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="audit-sampling", description="王二审计抽凭 v1.2.0-beta")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="检查本地运行环境"); doctor.set_defaults(func=command_doctor)
    run = sub.add_parser("run", help="OCR并生成Agent输入"); run.add_argument("--input", required=True, nargs="+", help="一个或多个 PDF、图片或文件夹"); run.add_argument("--mode", choices=("whole-set", "non-whole"), required=True); run.add_argument("--agent-json", default=None, help="可选：直接使用已有 Agent 输出 JSON"); run.add_argument("--no-open", action="store_true", help="完成后不自动打开高亮页面"); run.set_defaults(func=command_run)
    render = sub.add_parser("render", help="读取Agent JSON并生成Excel与高亮页"); render.add_argument("--job-id", required=True); render.add_argument("--agent-json", default=None); render.add_argument("--no-open", action="store_true", help="完成后不自动打开高亮页面"); render.set_defaults(func=command_render)
    resume = sub.add_parser("resume", help="恢复被中断的 OCR 任务"); resume.add_argument("--job-id", required=True); resume.set_defaults(func=command_resume)
    status = sub.add_parser("status", help="查看任务状态"); status.add_argument("--job-id", required=True); status.set_defaults(func=command_status)
    op = sub.add_parser("open", help="打开历史高亮结果"); op.add_argument("--job-id", required=True); op.set_defaults(func=command_open)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        job_id = getattr(args, "job_id", None)
        if job_id:
            try:
                manifest = load_manifest(job_id)
                manifest["job"]["status"] = "interrupted"
                save_manifest(job_id, manifest)
            except Exception:
                pass
        _emit({"type": "interrupted", "job_id": job_id, "message": "任务已保存，可使用 resume 继续"})
        return 130
    except Exception as exc:
        _emit({"type": "error", "error": str(exc)}); return 1


if __name__ == "__main__":
    raise SystemExit(main())
