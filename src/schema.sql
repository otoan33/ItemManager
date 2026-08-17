-- Hand Model マスタテーブル。scene_items.hand_model から参照される。
CREATE TABLE IF NOT EXISTS hand_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    image_path TEXT NOT NULL DEFAULT ''
);

-- Input Parameter マスタテーブル。run_tasks.input_parameter_path から参照される。
CREATE TABLE IF NOT EXISTS input_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL DEFAULT ''
);

-- Input Command マスタテーブル。run_tasks.input_command_path から参照される。
CREATE TABLE IF NOT EXISTS input_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL DEFAULT ''
);

-- Scene Item テーブル定義。db.py の init_db() から読み込まれる。
CREATE TABLE IF NOT EXISTS scene_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    robot_model TEXT NOT NULL DEFAULT '',
    hand_model INTEGER NOT NULL REFERENCES hand_models(id),
    surrounding_model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

-- Run Task テーブル定義。scene_id + run_id の組み合わせを主キーとする。
-- run_idはシーンごとに1から連番で採番する（db.pyのinsert_run_task参照）。
CREATE TABLE IF NOT EXISTS run_tasks (
    scene_id INTEGER NOT NULL REFERENCES scene_items(id),
    run_id INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    input_parameter_path INTEGER NOT NULL REFERENCES input_parameters(id),
    input_command_path INTEGER NOT NULL REFERENCES input_commands(id),
    output_data_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    PRIMARY KEY (scene_id, run_id)
);
