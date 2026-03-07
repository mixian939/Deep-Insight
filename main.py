from fastapi import FastAPI
from pydantic import BaseModel
import redis
import sqlite3
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. 核心大模型与组件初始化
# ==========================================
# 记得把这里换成你真实的 API Key！
my_api_key = "YOUR_API_KEY"

llm = ChatOpenAI(
    temperature=0.1,  
    model="glm-4",
    openai_api_key=my_api_key,
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)
print("正在加载词向量模型...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# ==========================================
# 2. 组装 LangGraph 多智能体工作流
# ==========================================
class AgentState(TypedDict):
    question: str
    documents: List[str]
    draft: str

def researcher_node(state: AgentState):
    print(f"[后台执行] 检索员正在搜索: {state['question']}")
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(state['question'])
    return {"documents": [doc.page_content for doc in docs]}

def writer_node(state: AgentState):
    print("[后台执行] 主笔正在撰写报告...")
    context = "\n\n".join(state['documents'])
    template = """你是一个专业的商业分析师。请严格根据以下提供的参考资料来回答问题。
    如果资料中没有相关信息，请明确指出。
    参考资料：\n{context}\n\n用户问题：\n{question}\n\n请输出专业、结构清晰的报告："""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": state['question']})
    return {"draft": response.content}

workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_edge(START, "researcher")      
workflow.add_edge("researcher", "writer")   
workflow.add_edge("writer", END)          

# 编译成可被调用的 Agent 应用
agent_app = workflow.compile()

# ==========================================
# 3. FastAPI 后端服务搭建
# ==========================================
app = FastAPI(title="Deep-Insight 企业级尽调系统 API")

# 连接 Redis (确保你的 Redis 软件在后台运行着)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 定义前端传过来的数据格式
class ResearchRequest(BaseModel):
    query: str

# 基础测试接口
@app.get("/")
def read_root():
    return {"status": "系统运行正常，API 准备就绪"}

# 核心工作流接口 (POST请求)
@app.post("/api/research"
    "/api/research", 
    summary=" 生成尽调报告", 
    description="传入具体的商业问题，系统将调度 LangGraph 多智能体工作流，结合 FAISS 向量库与智谱大模型，自动生成结构化分析报告。"
)
def do_research(request: ResearchRequest):
    print(f" 收到前端请求，任务目标: {request.query}")
    
    # 1. 初始化状态本
    initial_state = {
        "question": request.query, 
        "documents": [], 
        "draft": ""
    }
    
    # 2. 触发 LangGraph 工作流干活
    final_state = agent_app.invoke(initial_state)
    
    # 3. (可选进阶) 把这次的提问记录到 Redis 短期记忆里，保留 1 小时
    try:
        redis_client.set(f"last_query:{request.query}", final_state["draft"], ex=3600)
    except:
        print(" Redis 记录失败，但不影响核心流程。")
    
    # 4. 把写好的报告组装成 JSON 返回给前端
    return {
        "code": 200,
        "message": "报告生成成功",
        "data": {
            "query": request.query,
            "report": final_state["draft"]
        }
    }