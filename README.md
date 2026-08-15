# ItemManager

「マスタ項目選択・詳細表示・新規登録GUI 設計仕様」に基づく Streamlit実装（Robot Model マスタ）。

## 構成

```
app.py                          View（Streamlit）
service/robot_model_service.py  Service（バリデーション・トランザクション制御）
repository/                     Repository（SQLアクセス）
db/database.py, db/schema.sql   DB接続・スキーマ
models.py                       データクラス
errors.py                       業務例外
```

`View → Service → Repository → Database` の順に責務を分離（設計仕様13.2）。
DBはSQLite（`item_manager.db`、初回起動時に自動作成・サンプルデータ投入）。

## 実行方法

conda環境 `datamanager` を使用します（Streamlitはインストール済み）。

```bash
conda activate datamanager
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。

## 実装済み機能

- 起動時にDBからRobot Model一覧を取得しComboBoxに表示（3.1）
- ComboBox選択時に詳細設定（Payload / Arm Length / Gear Ratio / Controller）を読み取り専用表示（3.2, 2.2）
- 「＋」ボタンで新規登録ダイアログを表示（4.1）
- 新規登録：Model Name + 詳細設定を同一操作で入力し登録（5章）
- 登録時のバリデーション：必須チェック・重複チェック・数値チェック（8章）
- RobotModel / RobotModelSetting を同一トランザクションでINSERT、失敗時はロールバック（6章）
- 登録成功後は一覧を再取得し、新規項目を自動選択（7章）
- 詳細表示はReadOnly。「編集」ボタンは配置のみ（将来実装、9章）

## 他マスタへの展開

`Robot Model` と同じパターン（RobotModel / RobotModelSetting 相当のテーブル + Repository + Service）を
他マスタにも複製することで、同一のGUI構成を適用できます（設計仕様14章）。
