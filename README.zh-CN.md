# 文件共享器

单文件 Flask 服务器，通过 HTTP 共享本地目录，配 Bauhaus 风格文件浏览器：
拖放上传、浏览器内预览、文件夹导航、类型过滤、子串搜索。

## 安装

```bash
pip install flask click
```

## 使用

```bash
# 默认端口（32198）共享当前目录
python main.py

# 共享指定目录
python main.py /path/to/folder

# 自定义端口 + 调试模式
python main.py . --port 8080 --debug
```

在浏览器打开打印的 URL（`http://<host>:<port>/`）即可。同一局域网内的
任何设备都能访问。

### 命令行参数

| 参数 | 默认值 | 用途 |
| --- | --- | --- |
| `dir`（位置参数） | 当前工作目录 | 要共享的目录 |
| `--port` | `32198` | HTTP 端口 |
| `--debug` | 关闭 | Flask 调试模式 |

## 功能

- **上传** — 拖放或点击；进度条；上限 100 MB。
- **预览** — PDF、Markdown、HTML、纯文本（`.txt/.json/.xml/.csv/...`）、
  图片（`.png/.jpg/.gif/.svg/...`）。
- **导航** — 面包屑、类型过滤标签、子串搜索。
- **类型编码** — folder / image / document / code / media / archive，
  每类用 Bauhaus 形状 + 颜色双编码（色盲友好）。

## 项目结构

```
file-server/
├── main.py              # Flask 应用 + 卡片生成 + CLI
└── assets/
    ├── index.html       # 内联 CSS/JS 的 Bauhaus 模板
    └── favicon_32.png
```

## 技术栈

Flask · Click · 原生 HTML/CSS/JS（无构建步骤）。

## 许可

MIT
