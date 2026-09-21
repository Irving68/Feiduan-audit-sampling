# 飞段抽凭工具｜Windows v1.3.1

这是飞段抽凭工具的公开下载入口。仓库地址保持不变：<https://github.com/Irving68/Feiduan-audit-sampling>。

> 当前公开版本：Windows v1.3.1。它是免费本地内部使用的二进制发行版，不是开源源码仓库。

## 下载 Windows 最新版

[下载 Windows v1.3.1](../../releases/latest/download/Feiduan-sampling-Windows-v1.3.1.zip)

下载后请同时取得 Release 中的 `checksums.txt`，核验 ZIP 的 SHA-256。不要使用 GitHub 的 `Code → Download ZIP`；它只包含本说明材料，不包含可运行程序、Python 运行环境或 OCR 模型。

## 安装与使用

1. 解压 `Feiduan-sampling-Windows-v1.3.1.zip` 到一个具有读写权限的本地文件夹。
2. 在解压目录运行 `Install-Windows.ps1`，完成后重启 WorkBuddy。
3. 按压缩包内的 Skill 说明，让 Agent 开始抽凭。

详细步骤、数据边界与限制见 [安装说明](docs/installation.md)、[隐私说明](docs/privacy.md) 和 [已知限制](docs/limitations.md)。

## 授权边界

飞段自有代码、可执行程序、脚本、Skill、配置及随包文档按 [免费使用许可](LICENSE) 提供：个人和企业可以免费在自己控制的设备上作合法的内部业务、学习或测试使用。

未经权利人书面许可，不得再分发、转售、出租、托管、作为面向第三方的服务提供、冒充官方、逆向工程或规避保护；适用法律强制允许的范围除外。第三方组件继续按其各自许可证提供，见 [第三方组件与许可证通知](THIRD_PARTY_NOTICES.md)。

## 版本与历史

- v1.3.1 是当前公开的 Windows 二进制发行版。自有材料不适用旧版 AGPL-3.0。
- 仓库历史中的 v1.2.0-beta 曾以 AGPL-3.0 公开发布；该历史版本及其已获得副本仍受其原有许可证约束。本页与 v1.3.1 发行包不会将 AGPL-3.0 延伸至新版自有材料。
- 旧版不再作为官方下载渠道维护。历史记录不会因本页更新而被改写或撤销。

## 数据与审计提示

PDF、图片、OCR、证据坐标、Excel 和高亮预览由本地 Engine 处理。如果用户选择联网的 Agent 或模型，字段判断所需的 OCR 候选文字可能由相应服务提供商处理。请先确认符合单位的数据安全制度，并由审计人员复核全部结果；本工具不替代专业判断，也不对审计结论提供保证。

请勿在公开 Issue、截图或日志中上传客户资料、OCR 全文、凭证、工作底稿、个人信息或未脱敏图像。安全问题请参阅 [安全政策](SECURITY.md)。
