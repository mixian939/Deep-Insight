import sys
import io
# 强制让终端输出使用 UTF-8 编码，防止 Windows 控制台中文报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import sqlite3
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun 

# ==========================================
# 0. 保持原本的数据库初始化 (略过细节，假装它存在)
# ==========================================
def init_financial_db():
    conn = sqlite3.connect('company_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS financial_metrics 
                      (company_name TEXT, year INTEGER, total_assets REAL, total_liabilities REAL, net_income REAL)''')
    cursor.execute("INSERT OR IGNORE INTO financial_metrics VALUES ('江苏海鸥', 2025, 5500000, 3200000, 600000)")
    conn.commit()
    conn.close()

init_financial_db()

# ==========================================
# 1. 核心大模型与组件初始化
# ==========================================
# 🔑 替换成你的真实 API Key
my_api_key = "YOUR_API_KEY"

llm = ChatOpenAI(temperature=0.1, model="glm-4", openai_api_key=my_api_key, openai_api_base="https://open.bigmodel.cn/api/paas/v4/")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
search_tool = DuckDuckGoSearchRun() # 初始化搜索工具

# ==========================================
# 2. 定义状态本 (新增 web_data 字段)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    documents: List[str]
    sql_data: str
    web_data: str  # 用来装全网搜索回来的最新情报

# ==========================================
# 3. 定义智能体 (Nodes) - 新增联网情报员
# ==========================================
def researcher_node(state: AgentState):
    user_query = state["messages"][-1].content
    print(f"\n [研报检索员] 正在查本地 PDF...")
    try:
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
        docs = retriever.invoke(user_query)
        return {"documents": [doc.page_content for doc in docs]}
    except:
        return {"documents": ["暂无本地 PDF 资料"]}

def sql_analyst_node(state: AgentState):
    user_query = state["messages"][-1].content
    print(f" [数据分析师] 正在查本地 SQLite 数据库...")
    sql_prompt = ChatPromptTemplate.from_template("""
    数据库名为 company_data.db，表名为 financial_metrics (company_name, year, total_assets, total_liabilities, net_income)。
    根据问题只输出一行 SQL 查询语句，不要任何解释。问题：{query}
    """)
    sql_query = (sql_prompt | llm).invoke({"query": user_query}).content.strip().replace("```sql", "").replace("```", "").strip()
    try:
        conn = sqlite3.connect('company_data.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return {"sql_data": f"数据库查询结果: {results}"}
    except Exception as e:
        return {"sql_data": f"数据库查询失败"}

# 联网情报员
def web_searcher_node(state: AgentState):
    user_query = state["messages"][-1].content
    print(f" [联网情报员] 正在全网搜索最新动态...")
    try:
        # 让大模型提炼一下搜索关键词
        search_result = search_tool.invoke(user_query)
        # 截取前 1000 个字符，防止搜索结果太长撑爆大模型的上下文
        return {"web_data": search_result[:1000]}
    except Exception as e:
        return {"web_data": "网络搜索失败或超时"}

def writer_node(state: AgentState):
    print(" [主笔] 正在汇总 PDF、SQL 和 全网情报，撰写报告...")
    user_query = state["messages"][-1].content
    context = "\n".join(state.get('documents', []))
    sql_context = state.get('sql_data', '无结构化数据')
    web_context = state.get('web_data', '无网络数据')
    
    # 告诉大模型它现在拥有三种维度的信息
    template = """你是一个顶级的商业尽调分析师。请结合以下【三个维度】的信息回答用户问题。
    如果各个维度的信息有冲突，请以【全网最新情报】为准进行说明。
    
    【1. 内部研报资料(PDF)】: \n{context}\n
    【2. 内部核心财务数据(SQL)】: \n{sql_context}\n
    【3. 全网最新情报(Web Search)】: \n{web_context}\n
    
    用户问题：\n{question}\n
    请输出极其专业、结构清晰的报告："""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({
        "context": context, 
        "sql_context": sql_context, 
        "web_context": web_context,
        "question": user_query
    })
    
    return {"messages": [AIMessage(content=response.content)]}

# ==========================================
# 4. 组装图：三核并行处理
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("sql_analyst", sql_analyst_node)
workflow.add_node("web_searcher", web_searcher_node) # 加入网络节点
workflow.add_node("writer", writer_node)

# 同时去查 PDF、查 SQL、查互联网
workflow.add_edge(START, "researcher")
workflow.add_edge(START, "sql_analyst")
workflow.add_edge(START, "web_searcher")

# 资料统一交给主笔
workflow.add_edge(["researcher", "sql_analyst", "web_searcher"], "writer")
workflow.add_edge("writer", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ==========================================
# 5.  运行测试
# ==========================================
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user_pro_001"}}
    
    print("\n--- 最终尽调 ---")

    question = "查一下江苏海鸥2025年上半年的净利润数字，然后去网上搜一下最近几天这家公司或者它所处的冷却塔行业有没有什么最新的大新闻或政策？最后结合PDF资料给我个综合评价。"
    print(f" 用户提问: {question}")
    
    initial_state = {"messages": [HumanMessage(content=question)]}
    final_state = app.invoke(initial_state, config=config)
    
    print("\n" + "="*60)
    print(" 报告:\n", final_state["messages"][-1].content)
    print("="*60)