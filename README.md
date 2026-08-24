# 王二审计抽凭｜WangEr Audit Sampling

Windows 本地优先的审计抽凭工具：本地 OCR、坐标级证据绑定、Excel 结果和黄色高亮预览。

> 当前版本：v1.2.0-beta。Beta 版本仅用于测试和反馈，不能替代审计人员的专业判断与复核。

## 下载 Windows 最新版

[下载 Windows 便携版（无需安装 Python）](../../releases/latest/download/WangEr-Audit-Sampling-Windows.zip)

普通用户请使用上面的 Release 安装包。不要使用 GitHub 页面中 `Code → Download ZIP` 自动生成的源码包；源码包不包含便携 Python 和 OCR 模型。

下载后：

1. 解压到本地普通文件夹；
2. 将整个文件夹作为 Skill 导入支持本地文件和命令调用的 Agent；
3. 在 Agent 中提出“使用王二审计抽凭处理这些资料”；
4. 选择“整套资料”或“非整套资料”；
5. 获取 Excel 和本地高亮预览。

详细步骤见 [安装说明](docs/installation.md)。

## 功能

- Windows 10/11 x64 便携运行环境；
- PDF、JPG、JPEG、PNG 和文件夹输入；
- PaddleOCR 本地文字识别；
- OCR 词级坐标和证据 ID；
- Agent 复核与结构化字段协议；
- Excel 输出及本地高亮预览；
- 任务中断恢复和历史结果重新打开。

## 隐私边界

- PDF、图片、OCR、坐标、高亮和 Excel 处理由本地引擎完成；
- OCR 文本会写入本地任务目录；
- 如果使用联网 Agent，Agent 读取 OCR 文本时可能将文本发送给其服务提供商；
- 使用前请确认符合所在单位的数据安全、保密和跨境传输要求；
- 不要在 GitHub Issues 中上传客户资料、OCR 全文、底稿或未脱敏截图。

完整说明见 [隐私说明](docs/privacy.md)。

## 仓库与安装包

- 本仓库保存 Skill、引擎源码、构建脚本、协议和测试；
- Windows 便携 Python、第三方依赖和 OCR 模型放在 GitHub Releases；
- 普通用户无需自行安装 Python；
- 开发者可使用 `windows/build-portable.ps1` 构建便携环境，再使用 `windows/build-package.ps1` 生成发布包。

## 当前限制

这是参赛版本的公开 Beta：

- 仅支持 Windows x64；
- 字段结果必须由审计人员复核；
- 凭证版式、扫描质量和 Agent 能力会影响结果；
- 暂不提供自动更新、团队权限、项目归档或 Excel 插件；
- 不保证适配所有 Agent 和企业电脑安全策略。

更多内容见 [已知限制](docs/limitations.md)。

## 反馈

欢迎提交 Bug 和功能建议，但请只使用虚构或彻底脱敏的复现材料。安全问题请参阅 [SECURITY.md](SECURITY.md)。

## 许可证

本项目自有代码采用 AGPL-3.0 许可证。打包的 Python、PaddleOCR、PP-OCR 模型及其他依赖保留各自许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。项目名称“王二审计抽凭”及相关标识不因代码许可证而授权他人冒充官方版本。
