"""
Review Result ページ

説明：
 ReviewResultテーブル（レビュー結果履歴）の一覧表示・新規追加・実行を行うページ。
 Scene Settingページで「確定」した際に選択されていたシーンに紐づく結果のみを扱う。
 ReviewResultは (scene_id, result_id) の組み合わせが主キーで、result_idはシーンごとに採番される。
 RunSourceは参照するRunTask(run_id)のリストをJSON配列文字列として保持する。
"""

from __future__ import annotations
import streamlit as st
import time
import json
from dataclasses import dataclass, field, fields

from db import fetch_all, fetch_run_tasks, fetch_scene_child, insert_scene_child, update_scene_child

TABLE = "review_results"
ID_COLUMN = "result_id"

# --- データ定義 ---------------------------------------------------

@dataclass
class ReviewResult:
    scene_id: int = field(default=0, metadata={"input": False, "label": "SceneID"})
    result_id: int = field(default=0, metadata={"input": False, "label": "ResultID"})
    created_at: str = field(default="", metadata={"input": False, "label": "CreatedAt"})
    run_source: str = field(default="[]", metadata={"input": True, "label": "RunSource"})
    analyze_mode: int = field(default=0, metadata={"input": True, "label": "AnalyzeMode", "ref_table": "analyze_modes"})
    output_result_path: str = field(default="", metadata={"input": False, "label": "OutputResultPath"})
    status: str = field(default="", metadata={"input": False, "label": "Status"})

def get_input_fields(cls):
    return [f for f in fields(cls) if f.metadata.get("input", False)]

def get_ref_options(cls) -> dict[str, dict[int, dict]]:
    """metadataでref_tableが指定されたフィールド用に、参照先テーブルの{id: 行dict}を集める。"""
    ref_tables = {f.metadata["ref_table"] for f in fields(cls) if f.metadata.get("ref_table")}
    return {table: {row["id"]: row for row in fetch_all(table)} for table in ref_tables}

COLUMN_ORDER = [f.name for f in fields(ReviewResult)]
COLUMN_LABELS = {f.name: f.metadata["label"] for f in fields(ReviewResult)}

def format_run_source(run_ids: list[int], run_tasks: list[dict]) -> str:
    names = {t["run_id"]: t["name"] for t in run_tasks}
    return ", ".join(f"Run{rid}:{names.get(rid, '?')}" for rid in run_ids)

# --- 新規登録ダイアログ  ----------------------------------------

@st.dialog("New Review Result")
def show_create_dialog(scene_id: int) -> None:
    run_tasks = fetch_run_tasks(scene_id)
    ref_options = get_ref_options(ReviewResult)

    for f in get_input_fields(ReviewResult):
        ref_table = f.metadata.get("ref_table")
        if f.name == "run_source":
            if run_tasks:
                st.multiselect(
                    COLUMN_LABELS[f.name],
                    options=[t["run_id"] for t in run_tasks],
                    format_func=lambda rid, ts=run_tasks: f"Run{rid}: {next((t['name'] for t in ts if t['run_id'] == rid), '')}",
                    key=f"create_{f.name}",
                )
            else:
                st.warning("参照可能なRunTaskがありません。先にRun Taskを登録してください。")
        elif ref_table:
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
                values = {}
                for f in get_input_fields(ReviewResult):
                    if f.name == "run_source":
                        values[f.name] = json.dumps(st.session_state.get(f"create_{f.name}", []))
                    else:
                        values[f.name] = st.session_state.get(f"create_{f.name}", "")
                values["status"] = "Pending"
                values["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                insert_scene_child(TABLE, ID_COLUMN, scene_id, **values)
            except Exception as e:
                st.error(str(e))
            else:
                st.rerun()


# --- メイン画面 -------------------------------------------------

st.markdown("#### Review Result")

confirmed_scene_id = st.session_state.get("confirmed_scene_id")
confirmed_scene_name = st.session_state.get("confirmed_scene_name")

if confirmed_scene_name:
    st.markdown(f"選択中のシーン: **{confirmed_scene_name}**")
else:
    st.info("Scene Settingでシーンを選択し、「確定」を押してください。")

# ReviewResult一覧と新規追加ボタンを横並びで表示
col_title, col_add = st.columns([5, 1])
with col_title:
    st.markdown("##### ReviewResult")
with col_add:
    if st.button("＋", width='stretch', help="新規追加", disabled=confirmed_scene_id is None):
        show_create_dialog(confirmed_scene_id)

ref_options = get_ref_options(ReviewResult)
review_results = fetch_scene_child(TABLE, ID_COLUMN, confirmed_scene_id) if confirmed_scene_id is not None else []

if review_results:
    run_tasks = fetch_run_tasks(confirmed_scene_id)

    df_data = []
    for item in review_results:
        row = {}
        for f in fields(ReviewResult):
            value = item[f.name]
            ref_table = f.metadata.get("ref_table")
            if f.name == "run_source":
                run_ids = json.loads(value) if value else []
                value = format_run_source(run_ids, run_tasks)
            elif ref_table:
                ref_row = ref_options[ref_table].get(value)
                value = ref_row["name"] if ref_row else value
            row[COLUMN_LABELS[f.name]] = value
        df_data.append(row)

    event = st.dataframe(df_data, width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row", key="review_result_table")
    selected_rows = event.selection.rows if event.selection else []
    selected_result_id = review_results[selected_rows[0]]["result_id"] if selected_rows else None
elif confirmed_scene_id is not None:
    st.info("登録されているReviewResultがありません。「＋」から新規追加してください。")
    selected_result_id = None
else:
    selected_result_id = None

# 選択中のReviewResultを実行する。OutputResultPathはここで自動生成する（実行エンジン未実装のプレースホルダー）。
def execute_selected_result() -> None:
    update_scene_child(
        TABLE, ID_COLUMN, confirmed_scene_id, selected_result_id,
        status="Completed",
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        output_result_path=f"output/review_results/scene{confirmed_scene_id}_result{selected_result_id}.json",
    )

st.button("実行", disabled=selected_result_id is None, on_click=execute_selected_result)
