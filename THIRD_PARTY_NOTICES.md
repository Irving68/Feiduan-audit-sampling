# 第三方组件与许可证通知

飞段抽凭工具 v1.3.1 的 Windows 包随包分发第三方开源组件。具体版本由锁定依赖、`build-manifest.json` 和包内对应的许可证文件共同记录。

## 直接运行和构建依赖

- Python 3.12：PSF License。
- PaddlePaddle 3.3.0、PaddleOCR 3.4.1 及其运行依赖：本地 OCR；以各组件随包许可证为准。
- pypdfium2 5.7.0 / PDFium：本地 PDF 渲染；包内保留 pypdfium2、PDFium 及其构建依赖的许可证文件。
- MCP Python SDK 2.2.0：本地 MCP 协议服务。
- openpyxl 3.1.5：Excel 生成。
- Pillow 12.1.0：图像处理。
- PyInstaller 6.22.3：Windows 可执行程序封装。

## LGPL 组件

- `python-bidi 0.6.11`：GNU Lesser General Public License（LGPL）；上游源码与版本历史：<https://github.com/MeirKriheli/python-bidi>。
- `crc32c 2.9.post0`：GNU Lesser General Public License v2.1 or later；上游源码与版本历史：<https://github.com/ICRAR/crc32c>。

上述组件以可分离的第三方库形式位于安装包 `bin/_internal/` 下。用户依其各自许可证享有的运行、研究、修改、替换和重新链接权利，不受飞段自有代码许可的限制。安装包保留这些组件随包的许可证原文、元数据和 SBOM（如上游包提供）。

发布包不包含 PyMuPDF/fitz。各第三方组件仍保留其原始版权、署名、源码获取和许可证权利；本文件不替代包内许可证原文，也不构成法律意见。飞段自有代码的免费使用许可见 `LICENSE`，该许可不替代或改变第三方组件许可证；如有冲突，就相应第三方组件以其自身许可证为准。
