"""
Fit Model ページ

説明：
 FitModelテーブル（モデルフィッティング履歴）の一覧表示・新規追加・実行を行うページ。
 Scene Settingページで「確定」した際に選択されていたシーンに紐づくFitのみを扱う。
 FitModelは (scene_id, fit_id) の組み合わせが主キーで、fit_idはシーンごとに採番される。
 RunSourceは参照するRunTask(run_id)のリストをJSON配列文字列として保持する。
"""

from __future__ import annotations
import streamlit as st
import time
import json
from dataclasses import dataclass, field, fields

from db import fetch_all, fetch_run_tasks, fetch_scene_child, insert_scene_child, update_scene_child

TABLE = "fit_models"
ID_COLUMN = "fit_id"

# --- データ定義 ---------------------------------------------------

@dataclass
class FitModel:
    scene_id: int = field(default=0, metadata={"input": False, "label": "SceneID"})
    fit_id: int = field(default=0, metadata={"input": False, "label": "FitID"})
    created_at: str = field(default="", metadata={"input": False, "label": "CreatedAt"})
    run_source: str = field(default="[]", metadata={"input": True, "label": "RunSource"})
    initial_parameter_path: str = field(default="", metadata={"input": True, "label": "InitialParameterPath"})
    fit_mode: int = field(default=0, metadata={"input": True, "label": "FitMode", "ref_table": "fit_modes"})
    model_version: int = field(default=0, metadata={"input": True, "label": "ModelVersion", "ref_table": "model_versions"})
    output_parameter_path: str = field(default="", metadata={"input": False, "label": "OutputParameterPath"})
    status: str = field(default="", metadata={"input": False, "label": "Status"})

def get_input_fields(cls):
    return [f for f in fields(cls) if f.metadata.get("input", False)]

def get_ref_options(cls) -> dict[str, dict[int, dict]]:
    """metadataでref_tableが指定されたフィールド用に、参照先テーブルの{id: 行dict}を集める。"""
    ref_tables = {f.metadata["ref_table"] for f in fields(cls) if f.metadata.get("ref_table")}
    return {table: {row["id"]: row for row in fetch_all(table)} for table in ref_tables}

COLUMN_ORDER = [f.name for f in fields(FitModel)]
COLUMN_LABELS = {f.name: f.metadata["label"] for f in fields(FitModel)}

def format_run_source(run_ids: list[int], run_tasks: list[dict]) -> str:
    names = {t["run_id"]: t["name"] for t in run_tasks}
    return ", ".join(f"Run{rid}:{names.get(rid, '?')}" for rid in run_ids)

# --- 新規登録ダイアログ  ----------------------------------------

@st.dialog("New Fit Model")
def show_create_dialog(scene_id: int) -> None:
    run_tasks = fetch_run_tasks(scene_id)
    ref_options = get_ref_options(FitModel)

    for f in get_input_fields(FitModel):
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
                for f in get_input_fields(FitModel):
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

st.markdown("#### Fit Model")

confirmed_scene_id = st.session_state.get("confirmed_scene_id")
confirmed_scene_name = st.session_state.get("confirmed_scene_name")

if confirmed_scene_name:
    st.markdown(f"選択中のシーン: **{confirmed_scene_name}**")
else:
    st.info("Scene Settingでシーンを選択し、「確定」を押してください。")

# FitModel一覧と新規追加ボタンを横並びで表示
col_title, col_add = st.columns([5, 1])
with col_title:
    st.markdown("##### FitModel")
with col_add:
    if st.button("＋", width='stretch', help="新規追加", disabled=confirmed_scene_id is None):
        show_create_dialog(confirmed_scene_id)

ref_options = get_ref_options(FitModel)
fit_models = fetch_scene_child(TABLE, ID_COLUMN, confirmed_scene_id) if confirmed_scene_id is not None else []

if fit_models:
    run_tasks = fetch_run_tasks(confirmed_scene_id)

    df_data = []
    for item in fit_models:
        row = {}
        for f in fields(FitModel):
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

    event = st.dataframe(df_data, width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row", key="fit_model_table")
    selected_rows = event.selection.rows if event.selection else []
    selected_fit_id = fit_models[selected_rows[0]]["fit_id"] if selected_rows else None
elif confirmed_scene_id is not None:
    st.info("登録されているFitModelがありません。「＋」から新規追加してください。")
    selected_fit_id = None
else:
    selected_fit_id = None

# 選択中のFitModelを実行する。OutputParameterPathはここで自動生成する（実行エンジン未実装のプレースホルダー）。
def execute_selected_fit() -> None:
    update_scene_child(
        TABLE, ID_COLUMN, confirmed_scene_id, selected_fit_id,
        status="Completed",
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        output_parameter_path=f"output/fit_models/scene{confirmed_scene_id}_fit{selected_fit_id}.yaml",
    )

st.button("実行", disabled=selected_fit_id is None, on_click=execute_selected_fit)
