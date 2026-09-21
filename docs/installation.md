# Windows v1.3.1 安装说明

1. 在项目主页下载 `Feiduan-sampling-Windows-v1.3.1.zip`，并同时下载 Release 中的 `checksums.txt`。
2. 使用 SHA-256 核验 ZIP，确认文件完整后，将 ZIP 完整解压到具有读写权限的本地文件夹。
3. 在解压目录运行 `Install-Windows.ps1`。安装完成后重启 WorkBuddy。
4. 使用压缩包内的 Skill 按实际工作资料启动抽凭流程。

不要只复制单个 `feiduan.exe`、Skill 或模型文件；它们需要保持安装包中的相对位置。Windows 包已经包含其所需运行环境和 OCR 模型，通常无需另行安装系统 Python。

本公开仓库只提供下载和使用说明，不提供 v1.3.1 的 Engine 源码或构建脚本。安装器与包内说明是具体版本的准确信息来源。

升级前请保留已有任务结果目录。若安装、启动或任务处理失败，请使用无敏感信息的最小复现描述，并避免公开客户资料、OCR 文本或日志。
