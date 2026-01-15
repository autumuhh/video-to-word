# 🎬 Video2Word Agent (视频转文档智能体)

> **"别只是‘看’完视频，把它‘变成’你的知识库。"**

Video2Word 是一个基于 **AI 多模态大模型 (Gemini/GPT-4o)** 的智能工具，能够自动观看视频、提取关键帧（PPT/板书）、分析内容，并最终生成一份**排版精美、图文并茂的学术级 Word 笔记**。

## 🌟 核心亮点 (Key Features)

*   **👀 “看得见”的 AI**: 不仅仅是语音转文字，它能像人眼一样捕捉视频中的 PPT 翻页、板书变化，自动截图并插入文档。
*   **🎓 学术论文级排版**: 生成的 Word 文档采用标准学术格式（宋体/Times New Roman、居中题注、1.5倍行距），直接可用作正式报告或复习讲义。
*   **💪 全能平台支持**: 内置 **Playwright 浏览器模拟技术**，完美支持 **Bilibili (B站)**、**YouTube** 以及 **抖音/小红书** 等反爬虫严格的平台。
*   **🧠 灵活的模型配置**: 支持通过 OpenAI 兼容接口连接 **Gemini 2.0 Flash**、GPT-4o 等最新模型。
*   **🛡️ 隐私与安全**: 核心逻辑本地运行，API Key 本地存储，安全可控。

## 🛠️ 技术架构

本项目基于以下前沿技术构建：
*   **LangGraph**: 编排复杂的智能体工作流（分类 -> 下载 -> 处理 -> 分析 -> 生成）。
*   **Streamlit**: 构建极简、美观的对话式交互界面。
*   **Playwright**: 处理复杂的动态网页抓取（进程隔离模式，Windows 兼容）。
*   **OpenCV**: 智能视觉算法，精准识别场景变化，提取精华关键帧。
*   **python-docx**: 深度定制的 Word 文档生成引擎。

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
确保已安装 Python 3.8+。

```bash
# 克隆项目
git clone https://github.com/your-repo/video-to-word.git
cd video-to-word

# 安装依赖
pip install -r requirements.txt

# 安装浏览器内核 (用于抖音下载)
playwright install chromium
```

### 2. 配置 API
复制 `.env.example` 为 `.env`，并填入您的配置：

```ini
# .env 文件
GOOGLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx  # 您的 API Key
GOOGLE_API_BASE=https://cli.dearmer.xyz   # API 代理地址 (可选)
LLM_MODEL=gemini-3-flash-preview            # 指定模型 (推荐gemini-3-flash-preview 或 GPT-5)
```

### 3. 运行应用
```bash
streamlit run app.py
```
浏览器将自动打开 `http://localhost:8501`。

## 📖 使用指南

1.  **输入链接**: 在对话框中直接粘贴 B站、YouTube 或 抖音 的视频链接。
2.  **上传文件**: 点击侧边栏的“上传本地视频”，支持 mp4, mov, mkv 等格式。
3.  **等待生成**: 
    *   智能体首先会下载视频。
    *   然后进行视觉抽帧（根据视频长度，提取 10-50 张关键图）。
    *   AI 进行深度多模态分析（需 1-2 分钟）。
    *   最后生成 Word 文档供下载。

## 📂 项目结构
```text
video_to_word/
├── app.py                  # Streamlit 前端入口
├── graph/                  # LangGraph 智能体核心
│   ├── nodes/              # 各个功能节点 (下载、处理、分析等)
│   └── state.py            # 状态定义
├── tools/                  # 独立工具脚本 (如 Playwright 下载器)
├── word_mcp_server/        # Word 生成模块
├── requirements.txt        # 项目依赖
└── .env                    # 配置文件
```

## 🤝 贡献
欢迎提交 Issue 和 Pull Request！

## 📄 许可证
MIT License