# 文件共享器

一个简单易用的文件共享服务器,支持拖放上传、文件预览、文件夹导航等功能。

## 功能特性

- 📤 **拖放上传** - 支持拖拽文件到浏览器上传
- 🎨 **现代化界面** - 美观的渐变色设计和卡片式布局
- 🖼️ **图片预览** - 图片文件自动显示缩略图
- 📂 **文件夹导航** - 支持浏览子文件夹,面包屑导航
- 📊 **上传进度** - 实时显示上传进度条
- 📱 **响应式设计** - 自适应手机、平板、电脑
- 🎯 **文件图标** - 根据文件类型显示对应图标

## 安装依赖

```bash
pip install flask click
```

## 使用方法

### 基本用法

```bash
# 共享当前目录
python main.py

# 共享指定目录
python main.py /path/to/folder

# 使用自定义端口
python main.py . --port 8080

# 启用调试模式
python main.py . --debug
```

### 访问地址

启动后会显示访问地址,例如:
```
🚀 文件共享器启动成功!
📂 共享目录: /Users/username/projects
🌐 访问地址: http://192.168.1.100:32198
💡 提示: 在同一局域网的设备都可以访问此地址
```

在浏览器中打开显示的地址即可使用。同一局域网内的其他设备也可以访问。

### 命令行参数

- `dir` - 要共享的目录路径(默认:当前目录)
- `--port` - 指定端口号(默认:32198)
- `--debug` - 启用调试模式,方便开发

## 项目结构

```
file-server/
├── main.py              # 主程序文件
├── templates/
│   └── index.html       # 网页模板
├── favicon_32.png       # 网站图标
└── README.md            # 说明文档
```

## 技术栈

- **后端**: Flask (Python Web框架)
- **前端**: HTML5 + CSS3 + JavaScript
- **CLI**: Click (命令行界面)

## 支持的文件类型图标

- 📄 PDF文档
- 📝 Word文档 (doc, docx)
- 📊 Excel表格 (xls, xlsx)
- 📽 PPT演示文稿
- 📦 压缩文件 (zip, rar, 7z)
- 🎵 音频文件 (mp3, wav, flac)
- 🎬 视频文件 (mp4, avi, mkv, mov)
- 🐍 Python代码
- 📜 JavaScript代码
- 🌐 HTML文件
- 🎨 CSS样式

## 配置

默认配置:
- 最大文件大小: 16MB
- 默认端口: 32198
- 监听地址: 0.0.0.0 (所有网络接口)

如需修改,编辑 [main.py](main.py:17) 中的配置。

## 注意事项

- 确保已安装Flask和Click
- 在同一局域网内设备可访问
- 上传的文件会保存到指定目录
- 按 Ctrl+C 停止服务器

## 许可

MIT License
