"""
Scene Item Management App

説明：
 このアプリは、シーンアイテムの管理を行うための簡単なWebアプリケーションです。
 ユーザーは新しいシーンアイテムを追加し、既存のアイテムを選択して詳細情報を表示したり、削除することができます。
機能：
 - 新規シーンアイテムの追加
 - シーンアイテムの選択と詳細表示
 - シーンアイテムの削除
使用技術：
 - Streamlit: Webアプリケーションのフレームワーク
 - SQLite: データの永続化（db.py経由）
"""

from __future__ import annotations
import streamlit as st
import time
from dataclasses import dataclass, field, fields

from db import init_db, fetch_all, insert, delete

# タイトルとアイコンを設定
st.set_page_config(page_title="Scene Manager", page_icon="🤖", layout="centered")

# sample data class for scene items
@dataclass
class SceneItem:
    id: int = field(default=0,metadata={"input": False, "view": False})
    name: str = field(default="",metadata={"input": True, "view": True})
    robot_model: str = field(default="",metadata={"input": True, "view": True})
    hand_model: int = field(default=0,metadata={"input": True, "view": True, "ref_table": "hand_models"})
    surrounding_model: str = field(default="",metadata={"input": True, "view": True})
    created_at: str = field(default="",metadata={"input": False, "view": True})

def get_input_fields(cls):
    return [f for f in fields(cls) if f.metadata.get("input", False)]

def get_view_fields(cls):
    return [f for f in fields(cls) if f.metadata.get("view", False)]

def get_ref_options(cls) -> dict[str, dict[int, str]]:
    """metadataでref_tableが指定されたフィールド用に、参照先テーブルの{id: name}を集める。"""
    ref_tables = {f.metadata["ref_table"] for f in fields(cls) if f.metadata.get("ref_table")}
    return {table: {row["id"]: row["name"] for row in fetch_all(table)} for table in ref_tables}

init_db()

# --- 新規登録ダイアログ  ----------------------------------------

@st.dialog("New Scene Item")
def show_create_dialog() -> None:
    ref_options = get_ref_options(SceneItem)

    for field in get_input_fields(SceneItem):
        ref_table = field.metadata.get("ref_table")
        if ref_table:
            options = ref_options[ref_table]
            if options:
                st.selectbox(field.name, options=list(options.keys()), format_func=lambda i, o=options: o[i], key=f"create_{field.name}")
            else:
                st.warning(f"{field.name}が登録されていません。")
        elif field.type == "str":
            st.text_input(field.name, key=f"create_{field.name}")
        else:
            st.number_input(field.name, key=f"create_{field.name}", step=1.0 if field.type == "int" else 0.1)

    btn_cancel, btn_register = st.columns(2)
    with btn_cancel:
        if st.button("キャンセル", use_container_width=True):
            st.rerun()
    with btn_register:
        if st.button("登録", type="primary", use_container_width=True):
            try:
                values = {
                    f.name: st.session_state.get(f"create_{f.name}", "")
                    for f in get_input_fields(SceneItem)
                }
                values["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                new_id = insert("scene_items", **values)
            except Exception as e:
                st.error(str(e))
            else:
                st.session_state["item_select"] = new_id  # Select the newly created item
                st.rerun()


# --- メイン画面 -------------------------------------------------

scene_items = [SceneItem(**row) for row in fetch_all("scene_items")]
ref_options = get_ref_options(SceneItem)

# シーンアイテム選択コンボボックスと新規追加ボタンを横並びで表示
st.markdown("#### Scene Item")

col_select, col_add = st.columns([5, 1])
with col_select:
    if scene_items:
        selected_id = st.selectbox("Scene Item",index=None,options=[m.id for m in scene_items],
            format_func=lambda mid: next(m.name for m in scene_items if m.id == mid),
            key="item_select",label_visibility="collapsed",
        )
    else:
        selected_id = None
        st.info("登録されている項目がありません。「＋」から新規追加してください。")
with col_add:
    if st.button("＋", use_container_width=True, help="新規追加"):
        show_create_dialog()

# シーンアイテムの詳細設定を表示する領域
st.markdown("###### 詳細設定")

with st.container(border=True):
    if selected_id is not None:

        detail = next((item for item in scene_items if item.id == selected_id), None)
        if detail is None:
            st.error("詳細設定が見つかりませんでした。")
        else:
            rows = []
            for vfield in get_view_fields(SceneItem):
                raw = getattr(detail, vfield.name)
                ref_table = vfield.metadata.get("ref_table")
                value = ref_options[ref_table].get(raw, raw) if ref_table else raw
                rows.append((vfield.name, f"{value}"))
            for label, value in rows:
                c1, c2 = st.columns([1, 2])
                c1.markdown(f"**{label}**")
                c2.markdown(value)
    else:
        st.markdown("(項目を選択してください)")

# 詳細設定領域の下に削除ボタンを表示。押下でリストから削除する。
def delete_selected_item() -> None:
    # ウィジェット生成前のコールバック内でのみ scene_item_select を更新できる。
    delete("scene_items", selected_id)
    st.session_state["item_select"] = None

st.button("削除", disabled=selected_id is None, on_click=delete_selected_item)
