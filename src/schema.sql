-- Scene Item テーブル定義。db.py の init_db() から読み込まれる。
CREATE TABLE IF NOT EXISTS scene_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    robot_model TEXT NOT NULL DEFAULT '',
    hand_model TEXT NOT NULL DEFAULT '',
    surrounding_model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
