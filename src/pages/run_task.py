"""
Run Task ページ

説明：
 RunTaskテーブル（タスク実行履歴）の一覧表示・新規追加・実行を行うページ。
 Scene Settingページで「確定」した際に選択されていたシーンに紐づくタスクのみを扱う。
 RunTaskは (scene_id, run_id) の組み合わせが主キーで、run_idはシーンごとに採番される。
"""

from __future__ import annotations
import streamlit as st
import time
from dataclasses import dataclass, field, fields

from db import fetch_all, fetch_run_tasks, insert_run_task, update_run_task

# --- データ定義 ---------------------------------------------------

@dataclass
class RunTask:
    scene_id: int = field(default=0, metadata={"input": False, "label": "SceneID"})
    run_id: int = field(default=0, metadata={"input": False, "label": "RunID"})
    name: str = field(default="", metadata={"input": True, "label": "Name"})
    input_parameter_path: int = field(default=0, metadata={"input": True, "label": "InputParameterPath", "ref_table": "input_parameters"})
    input_command_path: int = field(default=0, metadata={"input": True, "label": "InputCommandPath", "ref_table": "input_commands"})
    output_data_path: str = field(default="", metadata={"input": True, "label": "OutputDataPath"})
    status: str = field(default="", metadata={"input": False, "label": "Status"})
    created_at: str = field(default="", metadata={"input": False, "label": "CreatedAt"})

def get_input_fields(cls):
    return [f for f in fields(cls) if f.metadata.get("input", False)]

def get_ref_options(cls) -> dict[str, dict[int, dict]]:
    """metadataでref_tableが指定されたフィールド用に、参照先テーブルの{id: 行dict}を集める。"""
    ref_tables = {f.metadata["ref_table"] for f in fields(cls) if f.metadata.get("ref_table")}
    return {table: {row["id"]: row for row in fetch_all(table)} for table in ref_tables}

COLUMN_ORDER = [f.name for f in fields(RunTask)]
COLUMN_LABELS = {f.name: f.metadata["label"] for f in fields(RunTask)}

# --- 新規登録ダイアログ  ----------------------------------------

@st.dialog("New Run Task")
def show_create_dialog(scene_id: int) -> None:
    ref_options = get_ref_options(RunTask)

    for f in get_input_fields(RunTask):
        ref_table = f.metadata.get("ref_table")
        if ref_table:
            options = ref_options[ref_table]
            if options:
                st.selectbox(COLUMN_LABELS[f.name], options=list(options.keys()), format_func=lambda i, o=options: o[i]["name"], key=f"create_{f.name}")
            else:
                st.warning(f"{COLUMN_LABELS[f.name]}が登録されていません。")
        else:
            st.text_input(COLUMN_LABELS[f.name], key=f"create_{f.name}")

    btn_cancel, btn_register = st.columns(2)
    with btn_cancel:
        if st.button("キャンセル", width='stretch'):
            st.rerun()
    with btn_register:
        if st.button("登録", type="primary", width='stretch'):
            try:
                values = {
                    f.name: st.session_state.get(f"create_{f.name}", "")
                    for f in get_input_fields(RunTask)
                }
                values["status"] = "Pending"
                values["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                insert_run_task(scene_id, **values)
            except Exception as e:
                st.error(str(e))
            else:
                st.rerun()


# --- メイン画面 -------------------------------------------------

st.markdown("#### Run Task")

confirmed_scene_id = st.session_state.get("confirmed_scene_id")
confirmed_scene_name = st.session_state.get("confirmed_scene_name")

if confirmed_scene_name:
    st.markdown(f"選択中のシーン: **{confirmed_scene_name}**")
else:
    st.info("Scene Settingでシーンを選択し、「確定」を押してください。")

# RunTask一覧と新規追加ボタンを横並びで表示
col_title, col_add = st.columns([5, 1])
with col_title:
    st.markdown("##### RunTask")
with col_add:
    if st.button("＋", width='stretch', help="新規追加", disabled=confirmed_scene_id is None):
        show_create_dialog(confirmed_scene_id)

ref_options = get_ref_options(RunTask)
run_tasks = fetch_run_tasks(confirmed_scene_id) if confirmed_scene_id is not None else []

if run_tasks:
    # ref_table付きの列（InputParameterPath / InputCommandPath）はidではなく
    # マスタテーブルのpathを表示する。
    df_data = []
    for task in run_tasks:
        row = {}
        for f in fields(RunTask):
            value = task[f.name]
            ref_table = f.metadata.get("ref_table")
            if ref_table:
                ref_row = ref_options[ref_table].get(value)
                value = ref_row["path"] if ref_row else value
            row[COLUMN_LABELS[f.name]] = value
        df_data.append(row)

    event = st.dataframe(df_data, width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row", key="run_task_table")
    selected_rows = event.selection.rows if event.selection else []
    selected_run_id = run_tasks[selected_rows[0]]["run_id"] if selected_rows else None
elif confirmed_scene_id is not None:
    st.info("登録されているRunTaskがありません。「＋」から新規追加してください。")
    selected_run_id = None
else:
    selected_run_id = None

# 選択中のRunTaskを実行する（現時点ではStatus/Timestampの更新のみ）。
def execute_selected_task() -> None:
    update_run_task(
        confirmed_scene_id,
        selected_run_id,
        status="Completed",
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

st.button("実行", disabled=selected_run_id is None, on_click=execute_selected_task)
