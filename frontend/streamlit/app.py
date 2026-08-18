import streamlit as st
import requests
import os
from typing import List, Dict

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(
    page_title="FDE Template",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 FDE PoC Platform")
st.markdown("---")

def search_documents(query: str, limit: int = 10) -> tuple[str, List[Dict]]:
    """ドキュメント検索"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/search/",
            json={"query": query, "limit": limit},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        status = f"✓ {data['total']} 件の結果"
        return status, results
    except requests.ConnectionError:
        return "✗ Backend に接続できません", []
    except Exception as e:
        return f"✗ エラー: {str(e)}", []

def check_health() -> str:
    """ヘルスチェック"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            return "✓ Backend は稼働中です"
        else:
            return "✗ Backend エラー"
    except requests.ConnectionError:
        return "✗ Backend に接続できません"
    except Exception as e:
        return f"✗ エラー: {str(e)}"

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")

    tab_health, tab_info = st.tabs(["ステータス", "情報"])

    with tab_health:
        if st.button("ステータス確認", use_container_width=True):
            health = check_health()
            if "稼働中" in health:
                st.success(health)
            else:
                st.error(health)

    with tab_info:
        st.markdown("""
        **FDE Template Phase 1**

        - Backend API: http://backend:8000
        - Docs: http://backend:8000/docs
        - Frontend: Streamlit
        """)

# メインコンテンツ
tab_search, tab_about = st.tabs(["🔍 検索", "ℹ️ について"])

with tab_search:
    st.subheader("ドキュメント検索")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "検索クエリ",
            placeholder="検索キーワードを入力...",
            label_visibility="collapsed"
        )
    with col2:
        limit = st.number_input("件数", min_value=1, max_value=100, value=10)

    if st.button("🔍 検索", use_container_width=True, type="primary"):
        if query:
            with st.spinner("検索中..."):
                status, results = search_documents(query, limit)

            st.info(status)

            if results:
                st.subheader("検索結果")
                for i, doc in enumerate(results, 1):
                    with st.container(border=True):
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            st.caption(f"#{i} - {doc.get('id', 'N/A')}")
                        with col2:
                            st.write(f"**{doc.get('title', 'No title')}**")
                        st.markdown(f"```\n{doc.get('content', '')[:200]}...\n```")
            else:
                st.warning("検索結果がありません")
        else:
            st.warning("検索キーワードを入力してください")

with tab_about:
    st.markdown("""
    ### FDE Template について

    **Forward Deployed Engineer** 向けの再利用可能な AI PoC 基盤

    #### 特徴
    - ✓ ローカル（OSS）で低コスト開発
    - ✓ AWS Managed Service への置き換え可能
    - ✓ プロジェクトごとに機能 ON/OFF
    - ✓ ローカル ↔ AWS で同じコード

    #### Architecture
    ```
    Streamlit UI (8501) ← Backend (8000) ↔ PostgreSQL + MinIO
                                         ↔ OpenSearch (Phase 2+)
                                         ↔ Neo4j (Phase 3+)
    ```

    #### Frontend
    - **Gradio**: `frontend/gradio/` (推奨)
    - **Streamlit**: `frontend/streamlit/` (このアプリ)
    - **Custom**: `frontend/custom/`
    """)

st.markdown("---")
st.caption("FDE Template Phase 1 | Streamlit Frontend")
