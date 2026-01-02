import os
from langchain_community.document_loaders import Docx2txtLoader

# .docxファイルのテスト読み込み
test_file = './data/サービスについて/Webサービス「EcoTee Creator」について.docx'

if os.path.exists(test_file):
    print(f"ファイル存在: {test_file}")
    try:
        loader = Docx2txtLoader(test_file)
        docs = loader.load()
        print(f"読み込み成功: {len(docs)} documents")
        if docs:
            print(f"最初の200文字: {docs[0].page_content[:200]}")
            print(f"メタデータ: {docs[0].metadata}")
    except Exception as e:
        print(f"エラー: {e}")
else:
    print(f"ファイルが見つかりません: {test_file}")

# データフォルダ内の全.docxファイルをチェック
print("\n=== 全.docxファイルの読み込みテスト ===")
for root, dirs, files in os.walk('./data'):
    for file in files:
        if file.endswith('.docx'):
            file_path = os.path.join(root, file)
            try:
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
                print(f"✓ {file_path}: {len(docs)} docs")
            except Exception as e:
                print(f"✗ {file_path}: {e}")
