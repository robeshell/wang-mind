# Wang-Mind - 智能思维导图生成器

Wang-Mind 是一个基于人工智能的思维导图生成工具，能够将文本内容智能转换为结构化的思维导图。

## 功能特点

- 🤖 基于 AI 的文本理解和结构化
- 📊 生成清晰的思维导图结构
- 🎨 支持 Markdown 格式输出
- 🚀 前后端分离架构
- ⚡ 高效的文本处理能力

## 技术栈

### 前端

- TypeScript + React
- Vite 构建工具
- Tailwind CSS 样式框架
- Markdown 渲染支持

### 后端

- Python + FastAPI
- OpenAI API 集成
- 异步处理支持
- 日志管理系统

## 快速开始

### 环境要求

- Node.js 16+
- Python 3.8+
- OpenAI API Key

### 后端设置

1. 进入后端目录

```bash
cd backend
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

- 复制 `.env.example` 到 `.env`
- 设置必要的环境变量（如 OpenAI API Key）

4. 启动服务

```bash
python run.py
```

### 前端设置

1. 进入前端目录

```bash
cd frontend
```

2. 安装依赖

```bash
npm install
```

3. 启动开发服务器

```bash
npm run dev
```

## 使用说明

1. 访问前端页面（默认为 http://localhost:5173）
2. 在输入框中粘贴或输入要处理的文本
3. 点击生成按钮，等待 AI 处理
4. 查看生成的思维导图结果

## 项目结构

```
wang-mind/
├── frontend/           # 前端项目目录
│   ├── src/           # 源代码
│   ├── public/        # 静态资源
│   └── package.json   # 依赖配置
└── backend/           # 后端项目目录
    ├── app/          # 应用代码
    ├── logs/         # 日志文件
    └── requirements.txt # Python依赖
```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License
