"""
Run Task ページ

説明：
 タスク実行用のページ（未実装）。
 Scene Settingページで「確定」した際に選択されていたシーン名を表示する。
"""

from __future__ import annotations
import streamlit as st

st.markdown("#### Run Task")

scene_name = st.session_state.get("confirmed_scene_name")
if scene_name:
    st.markdown(f"選択中のシーン: **{scene_name}**")
else:
    st.info("Scene Settingでシーンを選択し、「確定」を押してください。")
