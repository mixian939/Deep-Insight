from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

# 1. 定义状态本 (State)
class AgentState(TypedDict):
    question: str
    documents: List[str]
    draft: str
    review_passed: bool

# 2. 定义三个员工 (Nodes)
def researcher_node(state: AgentState):
    print(f"🕵️ 检索员：收到问题 '{state['question']}'，正在去知识库捞资料...")
    return {"documents": ["资料A：2023年财报", "资料B：高管变更公告"]}

def writer_node(state: AgentState):
    print("✍️ 主笔：拿到检索员找的资料了，正在奋笔疾书写初稿...")
    return {"draft": "这是一份基于资料A和B写出的深度分析初稿。"}

def reviewer_node(state: AgentState):
    print("🧑‍🏫 审查员：正在严格审查初稿质量...")
    print(f"   [审查内容]: {state['draft']}")
    return {"review_passed": True}

# 3. 组建流水线 (Graph)
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)

workflow.add_edge(START, "researcher")      
workflow.add_edge("researcher", "writer")   
workflow.add_edge("writer", "reviewer")     
workflow.add_edge("reviewer", END)          

app = workflow.compile()

# 4. 运行
if __name__ == "__main__":
    print("🚀 启动流水线测试...\n")
    initial_state = {
        "question": "请总结这家公司的最新财报", 
        "documents": [], 
        "draft": "", 
        "review_passed": False
    }
    final_state = app.invoke(initial_state)
    print("\n✅ 工作流执行完毕！最终状态：", final_state)