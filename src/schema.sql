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

-- Fit Mode マスタテーブル。fit_models.fit_mode から参照される。
CREATE TABLE IF NOT EXISTS fit_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Model Version マスタテーブル。fit_models.model_version から参照される。
CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Analyze Mode マスタテーブル。review_results.analyze_mode から参照される。
CREATE TABLE IF NOT EXISTS analyze_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
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
-- run_idはシーンごとに1から連番で採番する（db.pyのinsert_scene_child参照）。
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

-- Fit Model テーブル定義。scene_id + fit_id の組み合わせを主キーとする。
-- fit_idはシーンごとに1から連番で採番する（db.pyのinsert_scene_child参照）。
-- run_sourceは参照するRunTask.run_idのリストをJSON配列文字列として保持する。
CREATE TABLE IF NOT EXISTS fit_models (
    scene_id INTEGER NOT NULL REFERENCES scene_items(id),
    fit_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    run_source TEXT NOT NULL DEFAULT '[]',
    initial_parameter_path TEXT NOT NULL DEFAULT '',
    fit_mode INTEGER NOT NULL REFERENCES fit_modes(id),
    model_version INTEGER NOT NULL REFERENCES model_versions(id),
    output_parameter_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (scene_id, fit_id)
);

-- Review Result テーブル定義。scene_id + result_id の組み合わせを主キーとする。
-- result_idはシーンごとに1から連番で採番する（db.pyのinsert_scene_child参照）。
-- run_sourceは参照するRunTask.run_idのリストをJSON配列文字列として保持する。
CREATE TABLE IF NOT EXISTS review_results (
    scene_id INTEGER NOT NULL REFERENCES scene_items(id),
    result_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    run_source TEXT NOT NULL DEFAULT '[]',
    analyze_mode INTEGER NOT NULL REFERENCES analyze_modes(id),
    output_result_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (scene_id, result_id)
);
