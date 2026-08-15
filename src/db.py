"""Scene Item データのSQLite永続化。

app2.py はこのモジュール経由でのみDBにアクセスする。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db/scene_manager.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 列名でアクセスできるようにする
    return conn


def init_db() -> None:
    """schema.sql を読み込み、テーブルが無ければ作成する。"""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema)


def fetch_all() -> list[dict]:
    """登録済みシーンアイテムを全件取得する（id昇順）。カラム構成はテーブル定義に追従する。"""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM scene_items ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def insert(**fields) -> int:
    """1件登録し、採番されたidを返す。

    キーワード引数のキーがそのままカラム名になるため、
    テーブルのカラム構成が変わっても呼び出し側との対応を保ったまま使える。
    """
    columns = ", ".join(fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            f"INSERT INTO scene_items ({columns}) VALUES ({placeholders})",
            tuple(fields.values()),
        )
        conn.commit()
        return cur.lastrowid


def delete(item_id: int) -> None:
    """指定idの1件を削除する。"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM scene_items WHERE id = ?", (item_id,))
        conn.commit()
