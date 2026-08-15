# マスタ項目選択・詳細表示・新規登録GUI 設計仕様

## 1. 目的

データベースに登録された既存のマスタ項目から1件を選択し、その項目に紐づく詳細設定を表示する。

また、既存項目に存在しない新しい項目を追加する場合は、項目本体と、それに紐づく詳細設定を同一操作で登録できるようにする。

本GUIでは、以下の2つの操作を明確に分離する。

- 既存項目：選択・詳細確認
- 新規項目：項目作成・詳細設定入力・登録

---

## 2. 基本画面

### 2.1 項目選択画面

```text
┌──────────────────────────────────────────┐
│ Robot Model                              │
│                                          │
│ [ RS600                         ▼ ] [＋] │
│                                          │
│ ───────── 詳細設定 ─────────────────── │
│                                          │
│ Payload          20 kg                   │
│ Arm Length       1200 mm                 │
│ Gear Ratio       100                     │
│ Controller       RC700                   │
│                                          │
└──────────────────────────────────────────┘
```

### 2.2 画面要素

| 要素 | 種類 | 動作 |
|---|---|---|
| 項目選択 | ComboBox | DBに存在する項目を選択 |
| 新規追加 | Button | 新規登録画面を開く |
| 詳細設定 | ReadOnly表示 | 選択された項目の詳細設定を表示 |

詳細設定表示は原則として編集不可とする。

---

## 3. 既存項目選択

### 3.1 初期表示

画面起動時にDBから項目一覧を取得する。

```text
SELECT id, name
FROM RobotModel
ORDER BY name
```

取得した一覧をComboBoxに表示する。

### 3.2 項目変更時

ユーザーがComboBoxで項目を選択した場合、

1. 選択された項目のIDを取得
2. IDを使用して詳細設定を取得
3. 詳細設定表示領域を更新

する。

```text
ComboBox選択
    ↓
RobotModel ID
    ↓
RobotModelSetting取得
    ↓
詳細設定表示
```

---

# 4. 新規追加

## 4.1 起動

「＋新規追加」ボタンを押すと、新規登録画面を表示する。

既存項目の詳細表示画面とは別画面、またはモーダルダイアログとする。

```text
┌─────────────────────────────────────┐
│ 新しいRobot Model                   │
│                                     │
│ Model Name                          │
│ [                              ]    │
│                                     │
│ ─────── 詳細設定 ─────────────── │
│                                     │
│ Payload          [            ] kg   │
│ Arm Length       [            ] mm   │
│ Gear Ratio       [            ]     │
│ Controller       [         ▼  ]     │
│                                     │
│          [キャンセル] [登録]        │
└─────────────────────────────────────┘
```

---

## 5. 新規登録画面の入力項目

### 5.1 項目本体

例：

| 項目 | 入力 | 必須 |
|---|---|---|
| Model Name | TextBox | ○ |

### 5.2 詳細設定

例：

| 項目 | 入力 | 必須 |
|---|---|---|
| Payload | 数値入力 | ○ |
| Arm Length | 数値入力 | ○ |
| Gear Ratio | 数値入力 | ○ |
| Controller | ComboBox | ○ |

実際の項目は対象となるマスタに応じて定義する。

---

# 6. 登録処理

「登録」ボタン押下時には以下を実行する。

```text
入力値検証
    ↓
RobotModel INSERT
    ↓
生成された RobotModel ID を取得
    ↓
RobotModelSetting INSERT
    ↓
Transaction Commit
    ↓
登録完了
```

### 6.1 トランザクション

RobotModelとRobotModelSettingは同一トランザクションで登録する。

どちらか一方の登録に失敗した場合、両方をロールバックする。

```text
BEGIN TRANSACTION

INSERT RobotModel
INSERT RobotModelSetting

COMMIT
```

エラー発生時：

```text
ROLLBACK
```

---

# 7. 登録後の動作

登録成功後は新規登録画面を閉じ、元の項目選択画面を更新する。

新規登録した項目を自動的に選択状態にする。

```text
新規登録
   ↓
RobotModel一覧再取得
   ↓
新規項目を選択
   ↓
詳細設定を表示
```

例えば `RS1000` を追加した場合、

```text
Robot Model
[ RS1000 ▼ ]

詳細設定

Payload       20 kg
Arm Length    1200 mm
Gear Ratio    100
Controller    RC700
```

となる。

---

# 8. バリデーション

登録前に入力値を検証する。

### 8.1 必須チェック

未入力の場合は登録不可とする。

```text
Model Name is required.
```

### 8.2 重複チェック

Model Nameが既に存在する場合は登録不可とする。

```text
「RS600」は既に登録されています。
```

### 8.3 数値チェック

数値項目には数値以外を入力できないようにする。

また、必要に応じて最小値・最大値を設定する。

例：

```text
Payload > 0
Arm Length > 0
Gear Ratio > 0
```

---

# 9. 詳細表示と編集の分離

詳細設定表示画面は参照専用とする。

将来的に既存項目の詳細設定を変更する必要がある場合は、「編集」機能を追加する。

```text
┌─────────────────────────────┐
│ Robot Model                  │
│ [ RS600 ▼ ]                  │
│                              │
│ 詳細設定                     │
│ Payload       20 kg          │
│ Arm Length    1200 mm        │
│ Gear Ratio    100            │
│                              │
│ [編集]        [＋新規追加]   │
└─────────────────────────────┘
```

編集時は新規登録画面と同様の入力UIを使用できるが、処理はUPDATEとなる。

---

# 10. DB構成

基本構成は以下とする。

```text
RobotModel
----------------
id             PK
name           UNIQUE
created_at
updated_at


RobotModelSetting
----------------
id             PK
robot_model_id FK
payload
arm_length
gear_ratio
controller_id
created_at
updated_at
```

リレーション：

```text
RobotModel
    │
    │ 1 : 1
    ↓
RobotModelSetting
```

※詳細設定が将来的に複数存在する可能性がある場合は1:Nも検討する。

---

# 11. GUIとDBの責務

GUI側ではDBのIDを内部的に保持し、表示にはnameを使用する。

```text
ComboBox
    DisplayMember = name
    ValueMember   = id
```

例えば、

```text
表示値：RS600
内部値：15
```

とする。

他のテーブルからRobotModelを参照するときは、文字列ではなくIDを使用する。

```text
Measurement
----------------
id
robot_model_id
...
```

---

# 12. 推奨する画面構成

最終的には以下の構成を推奨する。

```text
┌──────────────────────────────────────────┐
│ Robot Model                              │
│                                          │
│ [ RS600                         ▼ ] [＋] │
│                                          │
│ ───────── 詳細設定 ─────────────────── │
│                                          │
│ Payload          20 kg                   │
│ Arm Length       1200 mm                 │
│ Gear Ratio       100                     │
│ Controller       RC700                   │
│                                          │
│ [編集]                                   │
└──────────────────────────────────────────┘
                     │
                     │ ＋
                     ↓
┌──────────────────────────────────────────┐
│ 新しいRobot Model                        │
│                                          │
│ Model Name       [ RS1000             ]  │
│                                          │
│ ───────── 詳細設定 ─────────────────── │
│                                          │
│ Payload          [ 20               ] kg │
│ Arm Length       [ 1200             ] mm │
│ Gear Ratio       [ 100                  ]│
│ Controller       [ RC700          ▼ ]    │
│                                          │
│              [キャンセル] [登録]        │
└──────────────────────────────────────────┘
```

---

# 13. 実装上の重要事項

### 13.1 「新規追加画面」と「詳細表示画面」を別Viewにする

WPF/MVVMの場合は、例えば以下の構成とする。

```text
RobotModelView
    └── RobotModelViewModel

RobotModelCreateDialog
    └── RobotModelCreateViewModel
```

詳細表示用ViewModelと新規登録用ViewModelを分離する。

### 13.2 DBアクセスをGUIから直接呼ばない

```text
View
 ↓
ViewModel
 ↓
Service
 ↓
Repository
 ↓
Database
```

のように分離する。

### 13.3 登録処理はServiceに集約

新規登録は、

```text
RobotModelService.Create(...)
```

のような1つの処理として扱う。

Service内部で、

```text
RobotModel INSERT
+
RobotModelSetting INSERT
```

を同一トランザクションで実行する。

これにより、GUI側は「新しいRobot Modelを作成する」という操作だけを意識すればよい。

---

# 14. 設計方針

本GUIでは以下を基本方針とする。

1. **既存項目の選択と詳細確認はメイン画面**
2. **新規追加は別画面**
3. **新規追加画面では項目本体と詳細設定を同時に入力**
4. **登録処理は1トランザクション**
5. **登録成功後は元画面に戻り、新規項目を自動選択**
6. **詳細表示はReadOnly**
7. **既存項目の編集機能は新規登録とは別操作**
8. **DBでは名前ではなくIDで関連付ける**
9. **GUI・ビジネスロジック・DBアクセスを分離する**

この構成を基本形として、`Robot Model` 以外の各種マスタにも同じパターンを適用できるようにする。