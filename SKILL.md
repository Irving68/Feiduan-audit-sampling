---
name: wanger-audit-sampling
description: Process audit sampling materials on Windows with the bundled local PaddleOCR engine, structured Agent field extraction, Excel output, and local yellow-highlight evidence preview. Use for PDF files, scanned images, or folders of vouchers. OCR and rendering stay local; OCR text may be sent to the user's selected Agent.
---

# 王二审计抽凭 v1.2.0-beta

Use the bundled Windows engine for OCR, evidence coordinates, matching, Excel output, and the local preview. The Agent handles the short user conversation and extracts audit-relevant fields from OCR text.

## Privacy boundary

- Source PDF and image files are processed by the bundled local engine and must not be uploaded by this workflow.
- The engine writes OCR text to the local job directory. Reading that text with a networked Agent may transmit it to the Agent provider.
- Before continuing with a networked Agent, make sure the user understands that OCR text can contain sensitive information and must follow their organization's data rules.
- Do not print full OCR text, internal JSON, or absolute source paths unless the user explicitly requests them.
- Do not ask users to submit client material in public bug reports. Request a synthetic or fully redacted reproduction instead.

## Required conversation

1. If the user has not provided PDF/image files or a folder, ask them to provide the local input paths.
2. Before processing, ask exactly one required choice:

   `请选择处理模式：`

   `整套资料：每一个文件仅对应一笔凭证，输出结果将按 PDF 文件为单位输出。`

   `非整套资料：每一个文件对应多笔凭证，输出结果将按资料类型为单位分组输出。`

   Map “整套资料” to `whole-set` and “非整套资料” to `non-whole`.
3. Do not ask for keywords. Determine high-importance audit fields from the OCR text.
4. After the mode is chosen, continue automatically without confirmation at every stage.

## Workflow

The package root contains `engine\audit-sampling.bat`. Use the bundled engine, not a system Python installation.

1. On first use, run `engine\audit-sampling.bat doctor` silently.
   - Continue when it passes.
   - If the bundled runtime or models are unavailable, stop before OCR and explain the missing local component.
2. Run `engine\audit-sampling.bat run --input <paths> --mode whole-set|non-whole --no-open`.
3. When the engine emits `agent_input_ready`, read that job's `agent-prompt.txt` and `agent-input.json`.
4. Extract only high-importance audit fields. Every field must include:
   - `document_type`, exact `file`, `file_id`, and a stable `group_id`;
   - `name`, `value`, `page_hint`, `source_text`, `confidence`, and `importance: "high"`;
   - exact `evidence_word_ids` copied from supporting OCR word blocks;
   - when correcting OCR, preserve the OCR evidence in `raw_value` and `source_text`, place the corrected result in `value`, and explain it in `correction`.
5. Save strict JSON matching `engine\agent-output.schema.json` to `engine\runtime\jobs\<job_id>\agent-output.json`.
6. Run `engine\audit-sampling.bat render --job-id <job_id>`.
   - If validation fails, read `agent-retry-prompt.txt`, correct only `agent-output.json`, and retry at most twice.
   - Do not rerun OCR for an Agent JSON validation problem.
7. Return file count, page count, extracted field count, review count, Excel path, and preview path.

## Recovery and output invariants

- Resume interrupted OCR with `engine\audit-sampling.bat resume --job-id <job_id>`.
- Historical results are read-only; open the existing `preview.html` instead of rerunning OCR.
- Preserve the established Excel columns, labels, merged cells, naming logic, and accuracy row.
- Evidence highlighting prefers `evidence_word_ids`; text matching is only a compatibility fallback.
- Excel value cells link to local field entry files that forward to the matching field in `preview.html`.
- Do not replace the local OCR engine with a cloud OCR API.
