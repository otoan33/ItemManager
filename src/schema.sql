-- Hand Model マスタテーブル。scene_items.hand_model から参照される。
CREATE TABLE IF NOT EXISTS hand_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 初期データ（無ければ追加。何度initを実行しても増殖しない）。
INSERT OR IGNORE INTO hand_models (name) VALUES ('Hand A'), ('Hand B'), ('Hand C');

-- Scene Item テーブル定義。db.py の init_db() から読み込まれる。
CREATE TABLE IF NOT EXISTS scene_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    robot_model TEXT NOT NULL DEFAULT '',
    hand_model INTEGER NOT NULL REFERENCES hand_models(id),
    surrounding_model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
