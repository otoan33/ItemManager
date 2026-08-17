"""Scene Item / マスタテーブル共通のSQLite永続化。

app.py はこのモジュール経由でのみDBにアクセスする。
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db/scene_manager.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# CSVで初期投入するマスタテーブルとCSVファイルの対応。
SEED_CSV_TABLES = {
    "hand_models": ASSETS_DIR / "hand_models.csv",
    "input_parameters": ASSETS_DIR / "input_parameters.csv",
    "input_commands": ASSETS_DIR / "input_commands.csv",
    "fit_modes": ASSETS_DIR / "fit_modes.csv",
    "model_versions": ASSETS_DIR / "model_versions.csv",
    "analyze_modes": ASSETS_DIR / "analyze_modes.csv",
}

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 列名でアクセスできるようにする
    return conn


def _seed_from_csv(table: str, csv_path: Path) -> None:
    """CSVの内容をtableに投入する（登録済みの名前はスキップ）。

    CSVの列がそのままカラムになるため、列が増減しても対応不要。
    """
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = [tuple(row[c] for c in columns) for row in reader]
    if not rows:
        return
    placeholders = ", ".join("?" for _ in columns)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            rows,
        )
        conn.commit()


def init_db() -> None:
    """schema.sql でテーブルを作成し、CSVで初期データを投入する。"""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema)
    for table, csv_path in SEED_CSV_TABLES.items():
        _seed_from_csv(table, csv_path)


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


def update(table: str, item_id: int, **fields) -> None:
    """指定テーブルのidの行を更新する。

    キーワード引数のキーがそのままカラム名になるため、
    テーブルのカラム構成が変わっても呼び出し側との対応を保ったまま使える。
    """
    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"UPDATE {table} SET {set_clause} WHERE id = ?",
            (*fields.values(), item_id),
        )
        conn.commit()


def delete(table: str, item_id: int) -> None:
    """指定テーブルからidで1件削除する。"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        conn.commit()


# --- シーン子テーブル専用 -------------------------------------------
# run_tasks / fit_models / review_resultsは (scene_id, <id_column>) の
# 組み合わせが主キーのため、id単一カラムを前提とする上記の汎用関数は使えない。


def fetch_scene_child(table: str, id_column: str, scene_id: int) -> list[dict]:
    """指定シーンに属する行を全件取得する（id_column昇順）。"""
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE scene_id = ? ORDER BY {id_column}", (scene_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def insert_scene_child(table: str, id_column: str, scene_id: int, **fields) -> int:
    """指定シーンに1件追加し、採番されたid_columnの値を返す。

    id_columnはシーンごとに1から始まる連番として、既存の最大値+1を採番する。
    """
    columns = ", ".join(["scene_id", id_column, *fields.keys()])
    placeholders = ", ".join("?" for _ in range(len(fields) + 2))
    with sqlite3.connect(DB_PATH) as conn:
        new_id = conn.execute(
            f"SELECT COALESCE(MAX({id_column}), 0) + 1 FROM {table} WHERE scene_id = ?", (scene_id,)
        ).fetchone()[0]
        conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            (scene_id, new_id, *fields.values()),
        )
        conn.commit()
        return new_id


def update_scene_child(table: str, id_column: str, scene_id: int, item_id: int, **fields) -> None:
    """指定シーン・idの行を更新する。"""
    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"UPDATE {table} SET {set_clause} WHERE scene_id = ? AND {id_column} = ?",
            (*fields.values(), scene_id, item_id),
        )
        conn.commit()


def fetch_run_tasks(scene_id: int) -> list[dict]:
    """指定シーンのRunTaskを全件取得する。"""
    return fetch_scene_child("run_tasks", "run_id", scene_id)


def insert_run_task(scene_id: int, **fields) -> int:
    """指定シーンにRunTaskを1件追加し、採番されたrun_idを返す。"""
    return insert_scene_child("run_tasks", "run_id", scene_id, **fields)


def update_run_task(scene_id: int, run_id: int, **fields) -> None:
    """指定シーン・run_idのRunTaskを更新する。"""
    update_scene_child("run_tasks", "run_id", scene_id, run_id, **fields)
