"""
ベクトル検索で.docxファイルが検索結果に含まれるかテスト
"""
import os
import sys
import unicodedata
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, WebBaseLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 環境変数読み込み
load_dotenv()

RAG_TOP_FOLDER_PATH = "./data"
SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": lambda path: CSVLoader(path, encoding="utf-8")
}

def recursive_file_check(path, docs_all):
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            recursive_file_check(full_path, docs_all)
    else:
        file_load(path, docs_all)

def file_load(path, docs_all):
    file_extension = os.path.splitext(path)[1]
    if file_extension in SUPPORTED_EXTENSIONS:
        try:
            loader = SUPPORTED_EXTENSIONS[file_extension](path)
            docs = loader.load()
            docs_all.extend(docs)
        except Exception as e:
            print(f"Error loading {path}: {e}")

def adjust_string(s):
    if type(s) is not str:
        return s
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    return s

print("=== データ読み込み中... ===")
docs_all = []
recursive_file_check(RAG_TOP_FOLDER_PATH, docs_all)

# Windows対応の文字列調整
for doc in docs_all:
    doc.page_content = adjust_string(doc.page_content)
    for key in doc.metadata:
        doc.metadata[key] = adjust_string(doc.metadata[key])

print(f"総ドキュメント数: {len(docs_all)}")

# チャンク分割
print("\n=== チャンク分割中... ===")
text_splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separator="\n"
)
splitted_docs = text_splitter.split_documents(docs_all)
print(f"チャンク数: {len(splitted_docs)}")

# .docxチャンクの数を確認
docx_chunks = [doc for doc in splitted_docs if doc.metadata.get('source', '').endswith('.docx')]
pdf_chunks = [doc for doc in splitted_docs if doc.metadata.get('source', '').endswith('.pdf')]
print(f".docx チャンク数: {len(docx_chunks)}")
print(f".pdf チャンク数: {len(pdf_chunks)}")

# ベクトルストア作成
print("\n=== ベクトルストア作成中... ===")
embeddings = OpenAIEmbeddings()
db = Chroma.from_documents(splitted_docs, embedding=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 10})  # 10件取得

# テストクエリ
test_queries = [
    "EcoTee Creatorについて教えて",
    "Webサービスの利用方法",
    "代行出荷サービスについて",
    "マーケティングミーティングの議事録",
    "社員の育成方針"
]

print("\n=== 検索テスト ===")
for query in test_queries:
    print(f"\n【クエリ】: {query}")
    results = retriever.invoke(query)
    
    docx_count = 0
    pdf_count = 0
    
    for i, doc in enumerate(results[:5]):  # 上位5件のみ表示
        source = doc.metadata.get('source', 'Unknown')
        ext = os.path.splitext(source)[1]
        
        if ext == '.docx':
            docx_count += 1
        elif ext == '.pdf':
            pdf_count += 1
            
        # ファイル名のみを表示
        filename = os.path.basename(source)
        print(f"  {i+1}. [{ext}] {filename}")
        print(f"     内容: {doc.page_content[:80]}...")
    
    print(f"  .docx: {docx_count}件, .pdf: {pdf_count}件")

print("\n=== 完了 ===")
