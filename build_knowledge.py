import os
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def build_vector_database():
    pdf_path = "data/sample_report.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f" 找不到文件: {pdf_path}，请确保你已经放入了 PDF 文件！")
        return

    print(" 1. 正在加载 PDF 文档...")
    loader = PDFPlumberLoader(pdf_path)
    documents = loader.load()
    print(f" 加载完成，文档共 {len(documents)} 页。")

    print(" 2. 正在进行文本切分 (Chunking)...")
    # 每块 800 个字符，块之间重叠 150 个字符
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = text_splitter.split_documents(documents)
    print(f" 切分完成，共切分出 {len(chunks)} 个文本块。")

    print(" 3. 正在下载并加载开源词向量模型 (初次运行可能需要几分钟下载)...")
    # 使用 HuggingFace 的轻量级开源模型
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

    print(" 4. 正在向量化并存入 FAISS 数据库...")
    # 核心步骤：把文本块丢给模型变成向量，并存进 FAISS
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # 保存到本地
    vector_store.save_local("faiss_index")
    print(" 向量数据库已保存到当前目录下的 'faiss_index' 文件夹中。")

if __name__ == "__main__":
    build_vector_database()