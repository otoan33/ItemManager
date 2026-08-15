"""
Scene Setting ページ

説明：
 シーンアイテムの新規追加・選択・詳細表示・削除を行うページ。
"""

from __future__ import annotations
import streamlit as st
import time
from dataclasses import dataclass, field, fields
from pathlib import Path

from db import fetch_all, insert, delete

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

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

def get_ref_options(cls) -> dict[str, dict[int, dict]]:
    """metadataでref_tableが指定されたフィールド用に、参照先テーブルの{id: 行dict}を集める。

    行dict全体を持たせておくことで、name以外の属性（image_path等）も
    列が増減した場合にコード変更無しで参照できる。
    """
    ref_tables = {f.metadata["ref_table"] for f in fields(cls) if f.metadata.get("ref_table")}
    return {table: {row["id"]: row for row in fetch_all(table)} for table in ref_tables}

# --- 新規登録ダイアログ  ----------------------------------------

@st.dialog("New Scene Item")
def show_create_dialog() -> None:
    ref_options = get_ref_options(SceneItem)

    for field in get_input_fields(SceneItem):
        ref_table = field.metadata.get("ref_table")
        if ref_table:
            options = ref_options[ref_table]
            if options:
                st.selectbox(field.name, options=list(options.keys()), format_func=lambda i, o=options: o[i]["name"], key=f"create_{field.name}")
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
                st.session_state["selected_scene_id"] = new_id
                st.rerun()


# --- メイン画面 -------------------------------------------------

scene_items = [SceneItem(**row) for row in fetch_all("scene_items")]
ref_options = get_ref_options(SceneItem)

# シーンアイテム選択コンボボックスと新規追加ボタンを横並びで表示
st.markdown("#### Scene Setting")

col_select, col_add = st.columns([5, 1])
with col_select:
    if scene_items:
        options = [m.id for m in scene_items]
        # ページ遷移するとウィジェットのkey（item_select）は破棄されてしまうため、
        # 別のsession_stateキーに選択idを保持しておき、indexとして復元する。
        stored_id = st.session_state.get("selected_scene_id")
        default_index = options.index(stored_id) if stored_id in options else None
        selected_id = st.selectbox("Scene Item",index=default_index,options=options,
            format_func=lambda mid: next(m.name for m in scene_items if m.id == mid),
            key="item_select",label_visibility="collapsed",
        )
        st.session_state["selected_scene_id"] = selected_id
    else:
        selected_id = None
        st.info("登録されている項目がありません。「＋」から新規追加してください。")
with col_add:
    if st.button("＋", use_container_width=True, help="新規追加"):
        show_create_dialog()

# 確定ボタン。押下で選択中のシーンをRun Taskページに渡して遷移する。
if st.button("確定", disabled=selected_id is None, use_container_width=True):
    selected_name = next(m.name for m in scene_items if m.id == selected_id)
    st.session_state["confirmed_scene_name"] = selected_name
    st.switch_page("pages/run_task.py")

# シーンアイテムの詳細設定を表示する領域
st.markdown("##### Details")

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
                image_path = None
                if ref_table:
                    ref_row = ref_options[ref_table].get(raw)
                    value = ref_row["name"] if ref_row else raw
                    if ref_row:
                        image_path = ref_row.get("image_path") or None
                else:
                    value = raw
                rows.append((vfield.name, f"{value}", image_path))
            for label, value, image_path in rows:
                c1, c2 = st.columns([1, 2])
                c1.markdown(f"**{label}**")
                c2.markdown(value)
                if image_path:
                    full_path = PROJECT_ROOT / image_path
                    if full_path.exists():
                        c2.image(str(full_path), width=150)
                    else:
                        c2.caption(f"画像が見つかりません: {image_path}")
    else:
        st.markdown("(項目を選択してください)")

# 詳細設定領域の下に削除ボタンを表示。押下でリストから削除する。
def delete_selected_item() -> None:
    # ウィジェット生成前のコールバック内でのみ scene_item_select を更新できる。
    delete("scene_items", selected_id)
    st.session_state["item_select"] = None
    st.session_state["selected_scene_id"] = None

st.button("削除", disabled=selected_id is None, on_click=delete_selected_item)
