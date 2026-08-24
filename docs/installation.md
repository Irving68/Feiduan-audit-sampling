# 安装说明

## 普通用户

1. 在项目主页点击“下载 Windows 最新版”。
2. 下载 `WangEr-Audit-Sampling-Windows.zip`。
3. 将 ZIP 完整解压到具有读写权限的本地文件夹。
4. 不要只复制 `SKILL.md`；`engine`、`agents` 和其他根目录文件需要保持相对位置不变。
5. 将解压后的文件夹导入支持 Skill、本地文件和本地命令调用的 Agent。
6. 首次使用时，Agent 会自动运行本地环境检查。

便携包已经包含 Python、必要依赖和 PP-OCR 模型，不需要另行安装 Python。

## 开发者

源码仓库不提交生成后的 `runtime/python` 和 `models`。在 Windows PowerShell 中运行：

```powershell
windows\build-portable.ps1
windows\build-package.ps1 -Output releases
```

第一条命令准备便携 Python、依赖和 OCR 模型；第二条命令生成 `WangEr-Audit-Sampling-Windows.zip`。

发布前必须运行测试、安全扫描，并在干净的 Windows 10/11 x64 环境执行一次 `engine\audit-sampling.bat doctor`。
