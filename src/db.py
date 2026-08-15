"""Scene Item / マスタテーブル共通のSQLite永続化。

app.py はこのモジュール経由でのみDBにアクセスする。
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db/scene_manager.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
HAND_MODELS_CSV_PATH = Path(__file__).resolve().parent.parent / "assets/hand_models.csv"

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 列名でアクセスできるようにする
    return conn


def _seed_hand_models() -> None:
    """hand_models.csv の内容をhand_modelsテーブルに投入する（登録済みの名前はスキップ）。

    CSVの列がそのままカラムになるため、image_path等の列を増減しても対応不要。
    """
    with HAND_MODELS_CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = [tuple(row[c] for c in columns) for row in reader]
    if not rows:
        return
    placeholders = ", ".join("?" for _ in columns)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            f"INSERT OR IGNORE INTO hand_models ({', '.join(columns)}) VALUES ({placeholders})",
            rows,
        )
        conn.commit()


def init_db() -> None:
    """schema.sql でテーブルを作成し、hand_models.csv で初期データを投入する。"""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema)
    _seed_hand_models()


def fetch_all(table: str) -> list[dict]:
    """指定テーブルを全件取得する（id昇順）。カラム構成はテーブル定義に追従する。"""
    with _connect() as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def insert(table: str, **fields) -> int:
    """指定テーブルに1件登録し、採番されたidを返す。

    キーワード引数のキーがそのままカラム名になるため、
    テーブルのカラム構成が変わっても呼び出し側との対応を保ったまま使える。
    """
    columns = ", ".join(fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(fields.values()),
        )
        conn.commit()
        return cur.lastrowid


def delete(table: str, item_id: int) -> None:
    """指定テーブルからidで1件削除する。"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        conn.commit()
