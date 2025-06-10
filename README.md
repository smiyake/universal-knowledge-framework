# 汎用ナレッジ管理フレームワーク

## 概要

あらゆるプロジェクトで利用可能な汎用的な文書管理・知識蓄積システムです。Claude-Obsidian連携により、効率的なナレッジベース構築を支援します。

## 特徴

- **汎用性**: あらゆる業界・プロジェクトタイプに対応
- **Claude統合**: Claude Codeとの最適化された連携
- **Obsidian連携**: 強力な文書管理・可視化機能
- **テンプレート**: プロジェクトタイプ別のすぐ使えるテンプレート
- **自動化**: タスク管理・文書同期の自動化

## 対応プロジェクトタイプ

- **Webアプリケーション開発**
- **データサイエンス・機械学習**
- **ビジネス・企画プロジェクト**
- **学術研究・論文作成**
- **個人学習・スキル向上**

## インストール

### PyPI経由（推奨）

```bash
pip install universal-knowledge-framework
```

### ソースから

```bash
git clone https://github.com/smiyake/universal-knowledge-framework.git
cd universal-knowledge-framework
pip install -e .
```

### Template Repositoryとして利用

1. GitHubで **"Use this template"** ボタンをクリック
2. 新しいリポジトリを作成
3. カスタマイズして利用

## 基本的な使用方法

### 新規プロジェクト作成

```bash
ukf create-project --name "マイプロジェクト" --type web-development
```

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

## テンプレート一覧

- **basic-project**: 基本的なプロジェクト構造
- **web-development**: Webアプリケーション開発用
- **data-science**: データ分析・機械学習用
- **business**: ビジネス・企画書作成用
- **research**: 学術研究・論文作成用
- **personal**: 個人学習・スキル向上用

## ライセンス

MIT License

## 貢献

プルリクエストや課題報告を歓迎します。