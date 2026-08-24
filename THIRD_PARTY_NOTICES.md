# 第三方软件声明

Windows 便携版包含未由本项目作者开发的运行环境、库和模型。它们保留各自的版权和许可证；本项目的 AGPL-3.0 许可证不改变第三方组件的许可证。

主要直接依赖包括：

| 组件 | 用途 | 上游许可证 |
|---|---|---|
| Python 3.10 Embedded | Windows 运行环境 | Python Software Foundation License |
| PaddlePaddle | OCR 推理框架 | Apache License 2.0 |
| PaddleOCR / PaddleX | OCR 工具链 | Apache License 2.0 |
| PP-OCRv5 mobile detection/recognition models | 本地文字检测与识别 | 上游模型随附条款 |
| PyMuPDF 1.24.13 | PDF 页面处理 | GNU Affero General Public License 3.0 |
| openpyxl | Excel 文件生成 | MIT License |
| Pillow | 图像处理 | HPND License |

便携包还包含上述组件的传递依赖。相应 `LICENSE`、`NOTICE`、`COPYING` 和包元数据会随运行环境保留。PyMuPDF 的 AGPL-3.0 条款是本项目选择 AGPL-3.0 的重要原因。正式对外发布前，仍应再次核对完整依赖清单及 OCR 模型的再分发条件。
