"""
Scene Item Management App

説明：
 このアプリは、シーンアイテムの管理を行うための簡単なWebアプリケーションです。
 複数ページで構成されており、各ページの役割は以下の通りです。
   - Scene Setting: シーンアイテムの新規追加・選択・詳細表示・削除
   - Run Task: タスク実行（未実装）
使用技術：
 - Streamlit: Webアプリケーションのフレームワーク
 - SQLite: データの永続化（db.py経由）
"""

from __future__ import annotations
import streamlit as st

from db import init_db

# タイトルとアイコンを設定
st.set_page_config(page_title="Scene Manager", page_icon="🤖", layout="wide")

# layout="wide"だと画面幅いっぱいに広がりすぎるため、左右の余白を
# centeredより少し狭い程度に収まるようCSSで最大幅を制限する。
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1200px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

# --- ページ構成 ---------------------------------------------------

pages = [
    st.Page("pages/scene_setting.py", title="Scene Setting", icon="🗂️"),
    st.Page("pages/run_task.py", title="Run Task", icon="▶️"),
    st.Page("pages/fit_model.py", title="Fit Model", icon="🧩"),
    st.Page("pages/review_result.py", title="Review Result", icon="📊"),
]

pg = st.navigation(pages)
pg.run()
