# Windows 构建说明

普通用户不需要执行这些命令，请直接下载 GitHub Release 中的 `WangEr-Audit-Sampling-Windows.zip`。

## 构建便携环境

在 Windows 10/11 x64 PowerShell 中，从仓库根目录运行：

```powershell
windows\build-portable.ps1
```

该脚本准备嵌入式 Python、依赖和 PP-OCRv5 模型，并运行环境检查。生成的 `runtime/` 和 `models/` 被 `.gitignore` 排除，不应提交到源码仓库。

## 构建发布包

```powershell
windows\build-package.ps1 -Output releases
```

生成文件：

```text
releases\WangEr-Audit-Sampling-Windows.zip
```

发布包根目录包含 Skill、说明和许可证，`engine/` 包含源码、便携 Python、依赖和 OCR 模型。

正式发布前必须在干净 Windows 环境运行：

```text
engine\audit-sampling.bat doctor
```
