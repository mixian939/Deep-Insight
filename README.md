# 🚀 Deep-Insight: 多智能体商业尽调系统

Deep-Insight 是一个基于 **LangGraph** 构建的企业级多智能体自动化分析引擎。系统旨在解决金融尽职调查、破产风险预警及商业情报收集中数据孤岛与分析效率低下的问题。

通过引入 RAG（检索增强生成）与 Agent-based 工作流，本系统能够并行处理非结构化研报、结构化财务指标以及全网实时情报，最终由协同智能体输出深度交叉验证的专业分析报告。

## ✨ 核心架构与特性

系统采用 **“三核扇出-扇入 (Fan-out / Fan-in)”** 并发架构，包含四个核心节点：

- **🕵️ 研报检索员 (RAG Researcher):** 基于 FAISS 向量库与 BGE 中文模型，精准召回数十万字的 PDF 深度研报片段。
- **📊 数据分析师 (Text-to-SQL Analyst):** 自动将自然语言转化为 SQL，直连企业财务数据库，精准提取负债率、现金流等核心风控指标。
- **🌐 联网情报员 (Web Search Agent):** 实时感知宏观经济政策与行业黑天鹅事件，打破大模型知识截止日期的局限。
- **✍️ 尽调主笔 (Reviewer & Writer):** 汇总上述三维数据，进行逻辑交叉验证，识别财务异常点，生成 Markdown 格式的最终报告。

*注：系统底层集成了 LangGraph Checkpointer，支持跨多轮对话的上下文状态短期记忆。*

## 🛠️ 技术栈 (Tech Stack)

- **应用编排:** LangChain, LangGraph
- **大语言模型:** 智谱 GLM-4 (完美兼容 OpenAI API 规范)
- **向量检索:** FAISS, Sentence-Transformers (BAAI/bge-small-zh-v1.5)
- **网络接入:** DuckDuckGo Search (模拟 MCP 轻量级挂载)
- **后端服务:** FastAPI, Redis, SQLite

## 📂 项目目录结构

克隆本项目后，你的核心目录结构应如下所示：

```text
deep-insight-agent/
├── data/                    # 存放待分析的 PDF 财报或研报文件
├── build_knowledge.py       # RAG 知识库构建脚本（将 PDF 转化为 FAISS 向量库）
├── core_agent.py            # 多智能体核心逻辑（包含 LangGraph 工作流定义）
├── main.py                  # FastAPI 后端服务接口
├── requirements.txt         # 项目依赖包清单
└── .gitignore               # Git 忽略文件配置
```
## 📦 快速开始 (Quick Start)

### 1. 环境准备
克隆本项目并安装依赖：
```Bash
git clone [https://github.com/你的用户名/deep-insight-agent.git](https://github.com/你的用户名/deep-insight-agent.git)
cd deep-insight-agent
python -m venv venv

# Windows 激活: venv\Scripts\activate
# Mac/Linux 激活: source venv/bin/activate

pip install -r requirements.txt
```

### 2：配置大模型 API Key
系统默认使用智谱 GLM-4 模型。请在 core_agent.py 和 main.py 的顶部配置您的 API Key：

```Python
my_api_key = "your_api_key_here"  # 替换为你的真实 Key
```

### 3：构建本地向量知识库 (RAG 初始化)
将目标企业的财报 PDF 放入 data/ 文件夹（重命名为 sample_report.pdf），并在终端运行数据处理脚本：

```Bash
python build_knowledge.py
#注：脚本运行完毕后，项目根目录下会自动生成 faiss_index 文件夹，此时本地知识库构建完成。
```

### 4：启动系统与测试
本项目提供两种运行方式：

方式一：后端 API 模式（推荐）
启动 FastAPI 服务器，对外提供 RESTful 接口：

```Bash
（venv）uvicorn main:app --reload
服务启动后，打开浏览器访问 http://127.0.0.1:8000/docs，即可在 Swagger UI 可视化界面中提交尽调任务并获取 JSON 报告。
```

方式二：终端调试模式
如果你只想在命令行中查看多智能体的内部思考过程（并行检索、SQL 打印等）：

```Bash
（venv）python -X utf8 core_agent.py
```
#### 本README文档由Gemini生成内容，人工编写补全
