# 汎用ナレッジ管理フレームワーク
# Universal Knowledge Framework

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/smiyake/universal-knowledge-framework)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

あらゆるプロジェクトで利用可能な汎用的な文書管理・知識蓄積システムです。Claude-Obsidian連携により、効率的なナレッジベース構築を支援します。

## ✨ 新機能 (v1.1.0)

- 🔍 **プロジェクト統計情報API** - ファイル分析・アクティビティ追跡
- 🤖 **AI開発ワークフロー統合** - Claude Code連携・セッション管理
- 📄 **動的テンプレートエンジン** - コンテキスト認識テンプレート
- 🌉 **ツール間連携アーキテクチャ** - Bridge Adapter・拡張基盤
- 📊 **Git統合強化** - コミット履歴分析・自動バックアップ

## 特徴

- **汎用性**: あらゆる業界・プロジェクトタイプに対応
- **AI統合**: Claude Codeとの最適化された連携・開発支援
- **Claude Code連携**: TodoRead/TodoWrite APIとの双方向同期 🆕
- **Obsidian連携**: 強力な文書管理・可視化機能
- **動的テンプレート**: プロジェクト状況に応じた最適なテンプレート
- **統計分析**: プロジェクト進捗・アクティビティの詳細分析
- **自動化**: タスク管理・文書同期・開発支援の自動化

## 対応プロジェクトタイプ

- **Webアプリケーション開発**
- **データサイエンス・機械学習**
- **ビジネス・企画プロジェクト**
- **学術研究・論文作成**
- **個人学習・スキル向上**

## インストール

### PyPI経由（準備中）

```bash
# 将来対応予定
pip install universal-knowledge-framework
```

### GitHub経由（現在推奨）

```bash
pip install git+https://github.com/cginzai/universal-knowledge-framework.git
```

### ソースから

```bash
git clone https://github.com/cginzai/universal-knowledge-framework.git
cd universal-knowledge-framework
pip install -e .
```

### Template Repositoryとして利用

1. GitHubで **"Use this template"** ボタンをクリック
2. 新しいリポジトリを作成
3. カスタマイズして利用

## 基本的な使用方法

### 新規プロジェクト作成（推奨）

```bash
# プロジェクト専用ディレクトリを作成
mkdir my-project
cd my-project

# フレームワークでプロジェクト初期化
ukf create-project --name "マイプロジェクト" --type web-development
```

⚠️ **重要**: 既存のObsidianボルトに直接インストールしないでください。詳細は[ベストプラクティス](BEST_PRACTICES.md)を参照。

### 文書同期開始

```bash
ukf sync start
```

### タスク管理

```bash
ukf task add "新機能の実装"
ukf task list
ukf task complete 1
```

### 新機能の使用例

#### プロジェクト統計分析
```bash
# プロジェクト概要表示
ukf stats summary

# ファイル統計詳細
ukf stats files

# アクティビティ分析
ukf stats activity --days 30

# 統計レポート出力
ukf stats export --format markdown
```

#### AI開発ワークフロー
```bash
# 開発セッション開始
ukf ai session start --type implementation

# マイルストーン記録
ukf ai milestone add "機能実装完了"

# セッション終了・レポート生成
ukf ai session end --summary "新機能実装完了"
```

#### 動的テンプレート
```bash
# プロジェクトに最適なテンプレート生成
ukf template generate session --context auto

# テンプレート推奨
ukf template recommend

# カスタムテンプレート作成
ukf template create my-template --file template.md
```

#### ツール間連携
```bash
# Obsidian連携設定
ukf bridge setup obsidian

# データ同期
ukf bridge sync --target obsidian
```

#### Claude Code連携 🆕
```bash
# Claude Code連携初期化
ukf claude init

# TodoReadタスクを同期
ukf claude sync --tasks-json '[{"id":"1","content":"タスク","status":"pending","priority":"high"}]'

# 同期状態確認
ukf claude status

# タスクをClaude Code形式でエクスポート
ukf claude export
```

#### ClaudeログのMarkdown変換
```bash
# JSONログをMarkdownに変換
ukf claude2md -i claude_logs -o knowledge/Claude
```

## 📋 更新・アップグレード

### 既存環境の更新

```bash
# 自動更新（推奨）
ukf update

# 手動更新
cd /path/to/universal-knowledge-framework
git pull origin main
pip install -e .
```

詳細な更新手順については [UPDATE_GUIDE.md](UPDATE_GUIDE.md) を参照してください。

### バージョン確認

```bash
# 現在のバージョン確認
ukf version

# 利用可能な新機能確認
ukf --help
```

## テンプレート一覧

- **basic-project**: 基本的なプロジェクト構造
- **web-development**: Webアプリケーション開発用
- **data-science**: データ分析・機械学習用
- **business**: ビジネス・企画書作成用
- **research**: 学術研究・論文作成用
- **personal**: 個人学習・スキル向上用

## 📚 ドキュメント

- [UPDATE_GUIDE.md](UPDATE_GUIDE.md) - 更新・アップグレード手順
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - ベストプラクティス
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - セットアップガイド

## ライセンス

MIT License

## 貢献

プルリクエストや課題報告を歓迎します。

### バグ報告・機能要求
- [GitHub Issues](https://github.com/smiyake/universal-knowledge-framework/issues)

### 開発への参加
- [CONTRIBUTING.md](CONTRIBUTING.md) - 貢献ガイドライン