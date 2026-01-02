"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
### 2026/01/02 m.sonoki add start
import csv
### 2026/01/02 m.sonoki add end
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
### 2026/01/02 m.sonoki add start
from langchain.schema import Document
### 2026/01/02 m.sonoki add end
import constants as ct


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################

def get_source_icon(source):
    """
    メッセージと一緒に表示するアイコンの種類を取得

    Args:
        source: 参照元のありか

    Returns:
        メッセージと一緒に表示するアイコンの種類
    """
    # 参照元がWebページの場合とファイルの場合で、取得するアイコンの種類を変える
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON
    
    return icon


def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def query_employees_by_department(department_name):
    """
    ### 2026/01/02 m.sonoki add start
    部署名で従業員を直接フィルタリング
    
    Args:
        department_name: 部署名（例：「人事部」）
    
    Returns:
        該当部署の全従業員リスト、またはNone
    """
    import pandas as pd
    import os
    
    csv_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, "社員について", "社員名簿.csv")
    if not os.path.exists(csv_path):
        return None
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        # 部署列でフィルタリング
        filtered_df = df[df['部署'] == department_name]
        if len(filtered_df) > 0:
            return filtered_df
        return None
    except Exception:
        return None
    ### 2026/01/02 m.sonoki add end


def get_llm_response(chat_message):
    """
    LLMからの回答取得

    Args:
        chat_message: ユーザー入力値

    Returns:
        LLMからの回答
    """
    ### 2026/01/02 m.sonoki add start
    # 部署別従業員一覧クエリの検出と直接処理
    import re
    from langchain.schema import Document
    department_pattern = r'(人事部|営業部|総務部|経理部|IT部|マーケティング部).*(従業員|社員|メンバー).*(一覧|リスト|情報)'
    match = re.search(department_pattern, chat_message)
    
    if match and st.session_state.mode == ct.ANSWER_MODE_2:  # 社内問い合わせモードのみ
        department = match.group(1)
        employees_df = query_employees_by_department(department)
        
        if employees_df is not None and len(employees_df) > 0:
            ### 2026/01/02 m.sonoki mod start
            # CSVの全項目を表示するようにDataFrameをそのまま使用
            import pandas as pd
            # 列名を日本語のまま表示
            result_df = employees_df.copy()
            markdown_table = result_df.to_markdown(index=False)
            ### 2026/01/02 m.sonoki mod end
            
            answer = f"### {department}に所属している従業員情報\n\n{markdown_table}\n\n{department}には合計{len(employees_df)}名の従業員が所属しています。"
            
            # 会話履歴に追加
            st.session_state.chat_history.extend([
                HumanMessage(content=chat_message),
                answer
            ])
            
            # LangChainのDocument形式で返す
            return {
                "answer": answer,
                "context": [Document(page_content="", metadata={"source": "./data/社員について/社員名簿.csv"})]
            }
    ### 2026/01/02 m.sonoki add end
    
    # LLMのオブジェクトを用意
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのプロンプトテンプレートを作成
    question_generator_template = ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_generator_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # モードによってLLMから回答を取得する用のプロンプトを変更
    if st.session_state.mode == ct.ANSWER_MODE_1:
        # モードが「社内文書検索」の場合のプロンプト
        question_answer_template = ct.SYSTEM_PROMPT_DOC_SEARCH
    else:
        # モードが「社内問い合わせ」の場合のプロンプト
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY
    # LLMから回答を取得する用のプロンプトテンプレートを作成
    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのRetrieverを作成
    history_aware_retriever = create_history_aware_retriever(
        llm, st.session_state.retriever, question_generator_prompt
    )

    # LLMから回答を取得する用のChainを作成
    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)
    # 「RAG x 会話履歴の記憶機能」を実現するためのChainを作成
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # LLMへのリクエストとレスポンス取得
    llm_response = chain.invoke({"input": chat_message, "chat_history": st.session_state.chat_history})
    # LLMレスポンスを会話履歴に追加
    st.session_state.chat_history.extend([HumanMessage(content=chat_message), llm_response["answer"]])

    return llm_response

### 2026/01/02 m.sonoki add start
def load_csv_as_single_document(path):
    """
    CSVファイルを1つのドキュメントとして読み込み、検索精度を向上させる
    
    Args:
        path: CSVファイルのパス
    
    Returns:
        統合されたドキュメントのリスト（1要素）
    """
    import csv
    from langchain.schema import Document
    
    with open(path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    
    if not rows:
        return []
    
    # CSVファイル名から内容を推測
    file_name = os.path.basename(path)
    
    # ヘッダー（列名）を取得
    headers = list(rows[0].keys())
    
    # 統合テキストを作成
    content_parts = [f"=== {file_name} ==="]
    content_parts.append(f"総データ数: {len(rows)}件")
    content_parts.append(f"データ項目: {', '.join(headers)}\n")
    
    # 部署でグループ化
    if '部署' in headers:
        content_parts.append("【部署別データ】")
        
        # 部署ごとにグループ化
        dept_groups = {}
        for row in rows:
            dept = row.get('部署', '不明')
            if dept not in dept_groups:
                dept_groups[dept] = []
            dept_groups[dept].append(row)
        
        # 各部署ごとにデータを記述
        for dept, dept_rows in sorted(dept_groups.items()):
            # セクション間を明確に分離（チャンクオーバーラップで混ざらないように）
            content_parts.append("\n" + "="*60)
            
            # セクションヘッダーを記述
            section_header = f"\n■ {dept} ({len(dept_rows)}名)"
            content_parts.append(section_header)
            
            # 部署情報を複数行でまず追加（セクションが分割されても検索可能にする）
            content_parts.append(f"部署: {dept}, 従業員数: {len(dept_rows)}名")
            content_parts.append("")  # 空行でセクション開始を明確に
            
            for i, row in enumerate(dept_rows, 1):
                # 各従業員を明確に分離するため、複数行に分けて記述
                # 部署情報を明示的に含める（「所属部署」として別表記で混同を防ぐ）
                employee_lines = [f"  {i}. 社員ID: {row.get('社員ID', '')}, 氏名: {row.get('氏名（フルネーム）', '')}, 所属部署: {row.get('部署', '')}"]
                
                # 追加情報を別行に記述
                additional_info = []
                if row.get('役職'):
                    additional_info.append(f"役職: {row.get('役職')}")
                if row.get('従業員区分'):
                    additional_info.append(f"従業員区分: {row.get('従業員区分')}")
                if row.get('年齢'):
                    additional_info.append(f"年齢: {row.get('年齢')}")
                if row.get('性別'):
                    additional_info.append(f"性別: {row.get('性別')}")
                
                if additional_info:
                    employee_lines.append("      " + ", ".join(additional_info))
                
                # スキルと資格を別行に記述
                skills_certs = []
                if row.get('スキルセット'):
                    skills_certs.append(f"スキル: {row.get('スキルセット')}")
                if row.get('保有資格'):
                    skills_certs.append(f"資格: {row.get('保有資格')}")
                
                if skills_certs:
                    employee_lines.append("      " + " | ".join(skills_certs))
                
                # 従業員情報の最後に空行を追加（チャンク分割時の区切りとして機能）
                employee_lines.append("")
                
                content_parts.extend(employee_lines)
    else:
        # 部署列がない場合は通常の形式
        content_parts.append("【社員データ】")
        key_fields = ['社員ID', '氏名（フルネーム）', '部署', '役職', '従業員区分']
        
        for i, row in enumerate(rows, 1):
            main_info = []
            for key in key_fields:
                if key in row and row[key]:
                    main_info.append(f"{key}:{row[key]}")
            
            other_info = []
            for key, value in row.items():
                if key not in key_fields and value and key in ['年齢', '性別', 'スキルセット', '保有資格']:
                    if len(value) > 50:
                        other_info.append(f"{key}:{value[:47]}...")
                    else:
                        other_info.append(f"{key}:{value}")
            
            row_text = f"{i}. " + ", ".join(main_info)
            if other_info:
                row_text += " | " + ", ".join(other_info)
            content_parts.append(row_text)
    
    # 主要項目の一覧を最後に追加
    content_parts.append("\n【主要項目の一覧】")
    important_columns = ['部署', '役職', '従業員区分', '性別']
    for column in important_columns:
        if column in headers:
            unique_values = sorted(set(row.get(column, '') for row in rows if row.get(column, '')))
            if unique_values:
                content_parts.append(f"・{column}: {', '.join(unique_values)}")
    
    # 統合テキストを作成
    unified_content = "\n".join(content_parts)
    
    # Documentオブジェクトとして返す
    doc = Document(
        page_content=unified_content,
        metadata={"source": path}
    )
    
    return [doc]
### 2026/01/02 m.sonoki add end