"""王二审计抽凭 v1.2.0-beta 环境检查。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .paths import JOBS_ROOT, MODELS_ROOT, PROJECT_ROOT, ensure_runtime_dirs


def _module_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_doctor() -> tuple[bool, list[dict[str, str]]]:
    """返回 (是否通过, 检查结果)。不自动联网安装依赖。"""

    ensure_runtime_dirs()
    checks: list[dict[str, str]] = []

    # 当前 Mac 开发环境仍允许使用 3.9；Windows 交付包会固定到经过验证的
    # 便携 Python 版本（目标为 3.10+）。因此 3.9 在开发机上提示 warning，
    # 不把基础协议和单元检查挡住；低于 3.9 才判定为不可用。
    if sys.version_info < (3, 9):
        python_status = "error"
    elif sys.version_info < (3, 10):
        python_status = "warning"
    else:
        python_status = "ok"
    checks.append({
        "name": "Python",
        "status": python_status,
        "detail": sys.version.split()[0],
    })

    if sys.platform.startswith("win"):
        portable_root = (PROJECT_ROOT / "runtime" / "python").resolve()
        executable = Path(sys.executable).resolve()
        portable_ok = portable_root == executable.parent or portable_root in executable.parents
        checks.append({
            "name": "便携运行环境",
            "status": "ok" if portable_ok else "error",
            "detail": str(executable),
        })

    for module, label in (
        ("paddleocr", "PaddleOCR"),
        ("paddle", "PaddlePaddle"),
        ("fitz", "PDF 处理组件"),
        ("openpyxl", "Excel 组件"),
        ("PIL", "图片组件"),
    ):
        checks.append({
            "name": label,
            "status": "ok" if _module_ok(module) else "error",
            "detail": "已安装" if _module_ok(module) else "未安装",
        })

    checks.append({
        "name": "任务目录",
        "status": "ok" if JOBS_ROOT.exists() and JOBS_ROOT.is_dir() else "error",
        "detail": str(JOBS_ROOT),
    })
    expected_models = [MODELS_ROOT / "PP-OCRv5_mobile_det", MODELS_ROOT / "PP-OCRv5_mobile_rec"]
    models_ready = all(path.exists() for path in expected_models)
    checks.append({
        "name": "模型目录",
        "status": "ok" if models_ready else ("error" if sys.platform.startswith("win") else "warning"),
        "detail": str(MODELS_ROOT) if models_ready else "缺少本地检测或识别模型",
    })

    passed = all(item["status"] in {"ok", "warning"} for item in checks)
    return passed, checks
