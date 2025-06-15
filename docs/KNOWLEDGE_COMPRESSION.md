# 知識圧縮機能 - Claude Codeトークン最適化

## 概要

知識圧縮機能は、Claude Codeが効率的にプロジェクトを理解し開発を進めるための機能です。プロジェクトの重要情報を自動的に分析・圧縮し、トークン使用量を大幅に削減します。

## 🎯 目的

### 問題の背景

Claude Codeはプロジェクトの現状を把握するために多くのファイルを読み込み、大量のトークンを消費します。これにより：

- コンテキストウィンドウがすぐに一杯になる
- 開発効率が低下する
- コストが増大する

### 解決策

知識圧縮機能は、プロジェクトの全体像を「人間のマインドマップ」のように構造化し、必要な情報に素早くアクセスできるようにします。

## 🚀 基本的な使い方

### 1. プロジェクト知識の圧縮

```bash
# 基本的な使用方法
ukf knowledge compress

# 出力ファイルを指定
ukf knowledge compress --output MY_PROJECT_MAP.md

# 最大トークン数を指定
ukf knowledge compress --max-tokens 3000

# 特定の情報にフォーカス
ukf knowledge compress --focus "errors,tasks,architecture"
```

### 2. 自動更新モード

```bash
# ファイル変更を監視して自動更新
ukf knowledge watch

# 更新間隔を指定（秒）
ukf knowledge watch --interval 600  # 10分ごと
```

### 3. 状態確認

```bash
# 知識マップの状態を確認
ukf knowledge status
```

## 📦 出力内容

`PROJECT_KNOWLEDGE_MAP.md` には以下の情報が含まれます：

### 1. 現在地（プロジェクト概要）
- プロジェクト名、タイプ、説明
- 現在のエラーや問題
- 動作状態

### 2. アーキテクチャ
- 重要なディレクトリ構造
- 主要ファイルとその役割
- サービスやAPIの一覧
- 使用データベース

### 3. 開発コマンド
- 頻繁に使用するコマンド
- テスト、ビルド、デプロイ方法

### 4. 現在のタスク
- 優先度別のタスク一覧
- 進行中の作業

### 5. 解決パターン
- 頻出エラーとその解決方法
- コードスニペット

### 6. 最近の変更
- 最新コミット
- 更新されたファイル

## ⚙️ 設定

### 設定ファイルの作成

`.ukf/config.yaml` または `ukf.config.yaml` を作成：

```yaml
knowledge_compression:
  output_file: "PROJECT_KNOWLEDGE_MAP.md"
  max_tokens: 5000
  update_frequency: "on_commit"
  
  sections:
    - name: "current_state"
      sources: ["logs", "test_results", "docker_status"]
    - name: "architecture"
      sources: ["src/", "docs/"]
    - name: "tasks"
      sources: [".claude-task-cache.json", "TODO.md"]
      
  claude_code_optimization:
    enabled: true
    priority_order:
      - "errors_and_issues"      # エラー情報を最優先
      - "current_tasks"          # 現在のタスク
      - "recent_changes"         # 最近の変更
      - "architecture_summary"   # アーキテクチャ
```

### Gitフックでの自動更新

`.git/hooks/post-commit` を作成：

```bash
#!/bin/bash
# Claude Code向け知識マップを自動更新
ukf knowledge compress --silent
```

## 💡 Claude Codeでの活用方法

### 推奨ワークフロー

1. **セッション開始時**
   ```
   1. PROJECT_KNOWLEDGE_MAP.md を最初に読む
   2. 現在のエラーやタスクを確認
   3. 必要に応じて詳細ファイルを読む
   ```

2. **問題解決時**
   ```
   1. 知識マップの「解決パターン」を確認
   2. 類似エラーがないか確認
   3. 新しい解決策を実装後、マップを更新
   ```

3. **セッション終了時**
   ```bash
   # 知識マップを更新
   ukf knowledge compress
   
   # 変更をコミット
   git add PROJECT_KNOWLEDGE_MAP.md
   git commit -m "chore: 知識マップ更新"
   ```

### トークン削減効果

| 状況 | 従来の方法 | 知識圧縮使用 | 削減率 |
|------|------------|--------------|--------|
| 初回セッション | 15,000-20,000 | 3,000-5,000 | 75% |
| エラー調査 | 10,000-15,000 | 2,000-3,000 | 80% |
| 機能実装 | 8,000-12,000 | 2,500-4,000 | 70% |

## 🔧 高度な使用方法

### プロジェクトタイプ別最適化

#### Webアプリケーション
```yaml
knowledge_compression:
  claude_code_optimization:
    priority_order:
      - "api_endpoints"          # APIエンドポイント
      - "frontend_components"    # フロントエンド
      - "database_schema"        # DBスキーマ
      - "recent_changes"
```

#### データサイエンス
```yaml
knowledge_compression:
  claude_code_optimization:
    priority_order:
      - "data_pipeline"          # データパイプライン
      - "model_architecture"     # モデル構造
      - "experiment_results"     # 実験結果
      - "hyperparameters"
```

### CI/CD統合

#### GitHub Actions例
```yaml
name: Update Knowledge Map

on:
  push:
    branches: [main, develop]

jobs:
  update-knowledge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install UKF
        run: pip install universal-knowledge-framework
      - name: Compress Knowledge
        run: ukf knowledge compress
      - name: Commit Changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add PROJECT_KNOWLEDGE_MAP.md
          git commit -m "auto: Update knowledge map"
          git push
```

## 🎯 ベストプラクティス

### 1. 定期的な更新
- 毎日の作業開始時に更新
- 大きな変更後に更新
- CI/CDで自動更新

### 2. チームでの活用
- PROJECT_KNOWLEDGE_MAP.md をチームで共有
- 新メンバーのオンボーディングに活用
- コードレビュー時の参考資料

### 3. 情報の鮮度維持
- 古いエラー情報は定期的に削除
- 完了タスクはアーカイブ
- 重要度に応じた情報の更新

## 🔍 トラブルシューティング

### 知識マップが大きすぎる
```bash
# トークン数を減らす
ukf knowledge compress --max-tokens 2000

# 特定の情報に絞る
ukf knowledge compress --focus "errors,tasks"
```

### 自動更新が動かない
```bash
# watchdogをインストール
pip install watchdog

# デバッグモードで実行
ukf knowledge watch --debug
```

### 特定の情報が含まれない
設定ファイルの `sections` を調整：
```yaml
sections:
  - name: "custom_errors"
    sources: ["logs/custom.log", "errors/"]
```

## 📡 今後の拡張予定

- 🤖 AIによる重要度判定
- 🌐 多言語対応
- 📊 視覚的なマインドマップ生成
- 🔗 他のAIツールとの連携

## 💬 フィードバック

機能の改善やバグ報告は以下まで：
- [GitHub Issues](https://github.com/smiyake/universal-knowledge-framework/issues)
