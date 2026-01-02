import os
import sys
import unicodedata
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import WebBaseLoader

RAG_TOP_FOLDER_PATH = "./data"
SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": lambda path: CSVLoader(path, encoding="utf-8")
}

def recursive_file_check(path, docs_all, file_count):
    """
    RAGの参照先となるデータソースの読み込み
    """
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            recursive_file_check(full_path, docs_all, file_count)
    else:
        file_load(path, docs_all, file_count)


def file_load(path, docs_all, file_count):
    """
    ファイル内のデータ読み込み
    """
    file_extension = os.path.splitext(path)[1]
    file_name = os.path.basename(path)

    print(f"チェック中: {path}")
    print(f"  拡張子: {file_extension}")
    
    if file_extension in SUPPORTED_EXTENSIONS:
        try:
            loader = SUPPORTED_EXTENSIONS[file_extension](path)
            docs = loader.load()
            docs_all.extend(docs)
            file_count[file_extension] = file_count.get(file_extension, 0) + 1
            print(f"  OK 読み込み成功: {len(docs)} documents")
        except Exception as e:
            print(f"  NG エラー: {e}")
    else:
        print(f"  - スキップ（サポート外の拡張子）")


# テスト実行
docs_all = []
file_count = {}

print("=== データ読み込みテスト ===")
recursive_file_check(RAG_TOP_FOLDER_PATH, docs_all, file_count)

print("\n=== サマリー ===")
print(f"総ドキュメント数: {len(docs_all)}")
print(f"ファイルタイプ別:")
for ext, count in file_count.items():
    print(f"  {ext}: {count} files")

# いくつかの.docxドキュメントの内容を確認
print("\n=== .docxドキュメントサンプル ===")
docx_docs = [doc for doc in docs_all if doc.metadata.get('source', '').endswith('.docx')]
print(f".docx ドキュメント数: {len(docx_docs)}")
if docx_docs:
    print(f"最初の.docxファイル:")
    print(f"  ソース: {docx_docs[0].metadata.get('source')}")
    print(f"  内容 (最初の150文字): {docx_docs[0].page_content[:150]}")
