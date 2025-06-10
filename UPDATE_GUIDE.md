# UKF更新ガイド
# Universal Knowledge Framework Update Guide

このガイドでは、Universal Knowledge Framework (UKF) の更新方法について説明します。

## 目次
- [現在のバージョン確認](#現在のバージョン確認)
- [更新方法](#更新方法)
- [新機能の使用方法](#新機能の使用方法)
- [既存プロジェクトでの利用](#既存プロジェクトでの利用)
- [トラブルシューティング](#トラブルシューティング)
- [バージョン履歴](#バージョン履歴)

## 現在のバージョン確認

```bash
# バージョン確認
ukf version

# 利用可能なコマンド確認
ukf --help
```

## 更新方法

### 開発版を使用している場合

```bash
# UKFプロジェクトディレクトリに移動
cd /path/to/universal-knowledge-framework

# 最新版を取得
git pull origin main

# 依存関係を更新
pip install -e .

# 更新確認
ukf version
```

### リリース版を使用している場合（将来対応）

```bash
# PyPIからの更新（将来リリース後）
pip install --upgrade universal-knowledge-framework

# 更新確認
ukf version
```

### 自動更新コマンド（推奨）

```bash
# 自動更新コマンド使用
ukf update

# 特定バージョンへの更新
ukf update --version 1.1.0

# 開発版への更新
ukf update --dev
```

## 新機能の使用方法

### v1.1.0の新機能

#### 1. プロジェクト統計情報API
```bash
# プロジェクト統計表示
ukf stats summary
ukf stats files
ukf stats activity

# 統計情報エクスポート
ukf stats export --format markdown --output stats.md
ukf stats export --format json --output stats.json
ukf stats export --format csv --output stats.csv

# 特定ファイルの分析
ukf stats analyze src/main.py
```

#### 2. AI開発ワークフロー統合
```bash
# AI開発セッション開始
ukf ai session start --type implementation --description "新機能実装"

# マイルストーン追加
ukf ai milestone add "データベース設計完了"

# ノート追加
ukf ai note add "パフォーマンス改善が必要" --type issue

# セッション終了
ukf ai session end --summary "新機能実装完了"

# セッション一覧表示
ukf ai session list

# セッションレポート生成
ukf ai report generate <session_id>
```

#### 3. 動的テンプレートエンジン
```bash
# コンテキスト認識テンプレート生成
ukf template generate session --context auto
ukf template generate planning --language ja --format markdown

# カスタムテンプレート作成
ukf template create my-template --file template.md --type custom

# テンプレート一覧表示
ukf template list

# プロジェクト推奨テンプレート
ukf template recommend

# テンプレート検証
ukf template validate template.md
```

#### 4. ツール間連携 (Bridge Adapter)
```bash
# Obsidian連携設定
ukf bridge setup obsidian

# データ同期
ukf bridge sync --target obsidian --mode bidirectional

# 連携状態確認
ukf bridge status

# 外部ツール設定
ukf bridge config obsidian --vault-path ~/Documents/MyVault
```

#### 5. Git統合強化
```bash
# Git履歴分析
ukf git analyze --since "2024-01-01"

# 自動バックアップ設定
ukf git backup setup --remote origin --branch backup

# コミット統計
ukf git stats --author "Your Name" --period month
```

## 既存プロジェクトでの利用

### 段階的導入パターン

#### 保守的アプローチ
```bash
# 1. まず統計機能を試用
ukf stats summary

# 2. テンプレート機能を段階的に導入
ukf template recommend

# 3. AI機能を試験的に使用
ukf ai session start --type exploration

# 4. Bridge機能で他ツール連携
ukf bridge setup obsidian
```

#### 積極的アプローチ
```bash
# 全機能を一括で試用
ukf ai session start --type migration --description "UKF最新版移行"
ukf stats export --format json --output migration-stats.json
ukf template generate migration --context auto
ukf bridge setup obsidian
ukf ai session end --summary "UKF最新版移行完了"
```

### 既存設定の互換性

- **既存の`.ukf/`ディレクトリ**: 後方互換性があります
- **同期設定**: 既存設定は保持されます
- **タスク管理**: 既存タスクは継続利用可能
- **プロジェクト構造**: 変更不要

## トラブルシューティング

### よくある問題と解決方法

#### 1. 更新後にコマンドが認識されない
```bash
# パッケージの再インストール
pip uninstall universal-knowledge-framework
pip install -e /path/to/universal-knowledge-framework
```

#### 2. 既存設定でエラーが発生
```bash
# 設定のバックアップと再作成
cp -r .ukf .ukf.backup
ukf sync stop
ukf sync start
```

#### 3. 新機能が利用できない
```bash
# 最新版の確認
ukf version
git log --oneline -5

# 強制更新
ukf update --force
```

#### 4. 依存関係のエラー
```bash
# 依存関係の再インストール
cd /path/to/universal-knowledge-framework
pip install -r requirements.txt
pip install -e .
```

### ログ確認
```bash
# UKFログ確認
cat .ukf/logs/ukf.log

# エラーログ確認
ukf debug info
```

## バージョン履歴

### v1.1.0 (最新)
- ✨ プロジェクト統計情報API実装
- ✨ AI開発ワークフロー統合
- ✨ 動的テンプレートエンジン
- ✨ ツール間連携アーキテクチャ
- ✨ Git統合強化
- 🐛 Git設定エラーの改善
- 📚 包括的なドキュメント整備

### v1.0.0
- 🚀 初期リリース
- 📁 基本的なプロジェクト管理
- 🔄 Obsidian同期機能
- 📝 タスク管理
- 🎯 プロジェクトテンプレート

## サポート

### ヘルプとドキュメント
```bash
# 詳細ヘルプ
ukf --help
ukf <command> --help

# オンラインドキュメント
ukf docs open
```

### 問題報告
- GitHub Issues: https://github.com/smiyake/universal-knowledge-framework/issues
- バグ報告やfeatute要求はこちらまで

### 貢献
- プルリクエスト歓迎
- 詳細は CONTRIBUTING.md を参照

---

**注意**: このガイドは開発版 (v1.1.0-dev) に基づいています。公式リリース時に一部手順が変更される場合があります。