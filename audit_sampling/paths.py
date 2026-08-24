"""跨平台路径和任务目录约定。"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = PROJECT_ROOT / "runtime"
JOBS_ROOT = RUNTIME_ROOT / "jobs"
MODELS_ROOT = PROJECT_ROOT / "models"

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def ensure_runtime_dirs() -> None:
    """创建运行时目录；不触碰上层现有项目目录。"""

    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)


def job_dir(job_id: str) -> Path:
    """返回任务目录。任务 ID 由现有工具的 8 位规则生成。"""

    return JOBS_ROOT / job_id


def collect_inputs(input_path: str | Path) -> list[Path]:
    """收集单文件、多个文件或文件夹第一层的支持文件。

    MVP 默认不递归子文件夹，避免误处理项目目录中的无关资料。
    """

    path = Path(input_path).expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {path.suffix}")
        return [path]

    if not path.exists():
        raise FileNotFoundError(f"输入路径不存在: {path}")
    if not path.is_dir():
        raise ValueError(f"输入路径不是文件或文件夹: {path}")

    files = sorted(
        (item for item in path.iterdir() if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda item: item.name.casefold(),
    )
    if not files:
        raise ValueError(f"文件夹中没有支持的 PDF 或图片: {path}")
    return files


def collect_many_inputs(input_paths: list[str | Path]) -> list[Path]:
    """合并多个文件/文件夹参数并按首次出现顺序去重。"""
    result: list[Path] = []
    seen: set[Path] = set()
    for input_path in input_paths:
        for path in collect_inputs(input_path):
            if path not in seen:
                result.append(path)
                seen.add(path)
    return result
