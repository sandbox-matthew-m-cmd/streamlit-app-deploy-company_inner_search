"""
CSVファイルの読み込みとチャンク分割をテスト
"""
import sys
import unicodedata
from utils import load_csv_as_single_document
from langchain.text_splitter import CharacterTextSplitter

# CSVファイルを読み込み
csv_path = "./data/社員について/社員名簿.csv"
docs = load_csv_as_single_document(csv_path)

print("=== CSVドキュメントの読み込み結果 ===")
print(f"ドキュメント数: {len(docs)}")
print(f"総文字数: {len(docs[0].page_content)}")
print(f"\n最初の1000文字:\n{docs[0].page_content[:1000]}")
print(f"\n最後の500文字:\n{docs[0].page_content[-500:]}")

# チャンク分割
print("\n\n=== チャンク分割テスト ===")
text_splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separator="\n"
)

# Windows対応の文字列調整
for doc in docs:
    if sys.platform.startswith("win"):
        doc.page_content = unicodedata.normalize('NFC', doc.page_content)
        doc.page_content = doc.page_content.encode("cp932", "ignore").decode("cp932")

splitted_docs = text_splitter.split_documents(docs)
print(f"チャンク数: {len(splitted_docs)}")

# 各チャンクの内容をサンプル表示
print("\n=== 各チャンクのサンプル（最初の5チャンク） ===")
for i, chunk in enumerate(splitted_docs[:5]):
    print(f"\n--- チャンク {i+1} ---")
    print(f"文字数: {len(chunk.page_content)}")
    print(f"内容: {chunk.page_content[:200]}...")

# 「人事部」が含まれるチャンクを確認
print("\n\n=== 「人事部」が含まれるチャンク ===")
hr_chunks = [chunk for chunk in splitted_docs if "人事部" in chunk.page_content]
print(f"「人事部」を含むチャンク数: {len(hr_chunks)}")
for i, chunk in enumerate(hr_chunks[:3]):
    print(f"\n--- チャンク {i+1} ---")
    print(chunk.page_content[:300])
