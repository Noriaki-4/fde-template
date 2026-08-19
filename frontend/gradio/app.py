import os
from typing import List, Tuple

import gradio as gr
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def search_documents(query: str, limit: int = 10) -> Tuple[str, List[List[str]]]:
    """ドキュメント検索"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/search/", json={"query": query, "limit": limit}, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # 結果をテーブル形式に変換
        results = []
        for doc in data.get("results", []):
            results.append(
                [
                    doc["id"],
                    doc["title"],
                    doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"],
                ]
            )

        status = f"✓ {data['total']} 件の結果"
        return status, results

    except requests.ConnectionError:
        return "✗ Backend に接続できません", [["エラー", "Backend 接続失敗", ""]]
    except Exception as e:
        return f"✗ エラー: {str(e)}", [["エラー", "検索エラー", str(e)]]


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


# Gradio インターフェース
with gr.Blocks(title="FDE Template") as demo:
    gr.Markdown("# FDE PoC Platform")

    with gr.Tab("検索"):
        gr.Markdown("### ドキュメント検索")

        with gr.Row():
            query_input = gr.Textbox(
                label="検索クエリ", placeholder="検索キーワードを入力...", lines=2
            )
            limit_input = gr.Number(label="件数上限", value=10, precision=0)

        search_btn = gr.Button("検索", variant="primary")
        status_output = gr.Textbox(label="ステータス", interactive=False)
        results_table = gr.Dataframe(
            label="検索結果", headers=["ID", "タイトル", "プレビュー"], interactive=False
        )

        search_btn.click(
            search_documents,
            inputs=[query_input, limit_input],
            outputs=[status_output, results_table],
        )

    with gr.Tab("システム"):
        gr.Markdown("### システムステータス")
        health_btn = gr.Button("ステータス確認", variant="secondary")
        health_output = gr.Textbox(label="Backend", interactive=False)

        health_btn.click(check_health, outputs=health_output)

    gr.Markdown(
        """
    ---
    **FDE Template Phase 1**
    - Backend API: http://backend:8000
    - Docs: http://backend:8000/docs
    """
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
