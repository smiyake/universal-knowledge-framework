# セットアップガイド

## 概要

汎用ナレッジ管理フレームワークの設定・インストール方法です。

## インストール

### pip経由でのインストール（将来対応予定）

```bash
pip install universal-knowledge-framework
```

### ソースからのインストール

```bash
git clone https://github.com/USERNAME/universal-knowledge-framework.git
cd universal-knowledge-framework
pip install -e .
```

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

## 設定

### プロジェクトタイプ一覧

- `basic`: 基本的なプロジェクト構造
- `web-development`: Webアプリケーション開発用
- `data-science`: データ分析・機械学習用
- `business`: ビジネス・企画書作成用
- `research`: 学術研究・論文作成用
- `personal`: 個人学習・スキル向上用

## トラブルシューティング

### インストールエラー
- Python 3.8以上が必要です
- 依存関係の問題がある場合は、仮想環境での実行を推奨します

### Git関連エラー
- プロジェクト作成時のGit初期化に失敗した場合は、手動でgit initを実行してください

## 免責事項

このソフトウェアはAS ISで提供されます。
株式会社CGin財は使用に関する一切の責任を負いません。

## ライセンス

MIT License - 詳細はLICENSEファイルを参照してください。