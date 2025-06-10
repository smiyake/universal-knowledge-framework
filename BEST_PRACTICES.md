# Universal Knowledge Framework - ベストプラクティス

## 推奨ディレクトリ構造

### ❌ 避けるべき構造（既存Obsidianボルトに直接インストール）
```
既存のObsidianボルト/
├── .obsidian/          # 既存の設定
├── Daily Notes/        # 既存のノート
├── Projects/           # 既存のノート
├── .ukf/              # ⚠️ フレームワークファイルが混在
├── CLAUDE.md          # ⚠️ フレームワークファイルが混在
└── README.md          # ⚠️ どれが元のファイルか不明
```

### ✅ 推奨構造（プロジェクト専用ディレクトリ）
```
my-project/                    # プロジェクトルート
├── knowledge/                 # プロジェクト専用Obsidianボルト
│   ├── .obsidian/            # プロジェクト用設定
│   ├── 00_Overview/          # プロジェクト概要
│   ├── 01_Requirements/      # 要件定義
│   ├── 02_Design/           # 設計文書
│   ├── 03_Implementation/   # 実装メモ
│   └── CLAUDE.md            # Claude用ガイド
├── src/                      # ソースコード
├── tests/                    # テスト
├── .ukf/                     # フレームワーク管理
└── README.md                 # プロジェクトREADME
```

## セットアップ手順

### 1. 新規プロジェクトの作成（推奨）
```bash
# プロジェクトディレクトリを作成
mkdir my-awesome-project
cd my-awesome-project

# フレームワークでプロジェクト初期化
ukf create-project --name "My Awesome Project" --type web-development

# knowledge/ディレクトリがObsidianボルトとして作成される
```

### 2. 既存Obsidian設定の活用（オプション）
```bash
# 既存のObsidian設定をコピー（非破壊的）
ukf copy-obsidian-settings --from ~/ObsidianVault --to ./knowledge
```

### 3. Obsidianでの開き方
1. Obsidianを起動
2. 「別のボルトを開く」を選択
3. `my-awesome-project/knowledge/` を選択
4. プロジェクト専用のボルトとして管理

## 利点

### 1. 明確な分離
- 個人的なノートとプロジェクト文書が混在しない
- プロジェクトごとに独立した知識ベース
- Gitでの管理が容易

### 2. 柔軟な構成
- プロジェクトタイプに応じた最適な構造
- 必要に応じて既存設定を再利用
- チーム共有が簡単

### 3. 移植性
- プロジェクト全体を簡単に移動
- 他の開発者への引き継ぎが容易
- バックアップ・リストアが単純

## 既存プロジェクトへの導入

### 方法1: サブディレクトリとして追加
```bash
cd existing-project/
mkdir knowledge
cd knowledge
ukf init --type web-development
```

### 方法2: 並列ディレクトリとして管理
```
workspace/
├── existing-project/        # 既存のコード
└── existing-project-docs/   # ドキュメント専用
    └── knowledge/
```

## トラブルシューティング

### Q: 既存のObsidianボルトに誤ってインストールしてしまった
A: 以下のファイル/ディレクトリを削除してください：
- `.ukf/`
- `CLAUDE.md`
- フレームワークが生成したREADME.md等

### Q: 複数プロジェクトでObsidianプラグインを共有したい
A: コミュニティプラグインは各ボルトで個別管理が推奨ですが、シンボリックリンクで共有も可能です。

### Q: 既存のノートをプロジェクトに移行したい
A: 必要なノートのみを選択的にコピーすることを推奨します。
```bash
cp -r ~/ObsidianVault/Projects/MyProject/* ./knowledge/
```

## まとめ

Universal Knowledge Frameworkは、**プロジェクトごとに独立した知識ベース**を作成することを前提に設計されています。既存のObsidianボルトとは分離して使用することで、整理された効率的なナレッジ管理が可能になります。