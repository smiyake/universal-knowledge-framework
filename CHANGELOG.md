# Changelog

All notable changes to the Universal Knowledge Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Claude Code連携機能 (`ukf claude` コマンド群)
  - TodoRead/TodoWrite APIとの双方向同期
  - タスクキャッシュ管理
  - Git自動コミット機能
  - CLI統合 (`sync`, `init`, `status`, `export`)
- `claude_code_sync.py` モジュール
  - `ClaudeCodeSync` クラス
  - `ClaudeTask` データモデル
  - タスクステータス・優先度のEnum定義
- Claude Code連携ドキュメント
- テストケース追加

## [1.1.0] - 2025-01-15

### Added
- プロジェクト統計情報API
- AI開発ワークフロー統合
- 動的テンプレートエンジン
- ツール間連携アーキテクチャ (Bridge Adapter)
- Git統合強化

### Changed
- CLIコマンド構造の改善
- ドキュメント構造の整理

### Fixed
- Obsidian連携の安定性向上
- パフォーマンスの改善

## [1.0.0] - 2025-01-01

### Added
- 初回リリース
- 基本的なナレッジ管理機能
- Obsidian連携
- タスク管理
- プロジェクトテンプレート

[Unreleased]: https://github.com/cginzai/universal-knowledge-framework/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/cginzai/universal-knowledge-framework/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/cginzai/universal-knowledge-framework/releases/tag/v1.0.0