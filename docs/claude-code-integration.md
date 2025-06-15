# Claude Code Integration Guide

Universal Knowledge Framework (UKF) のClaude Code連携機能についての詳細ガイドです。

## 概要

Claude Code連携機能は、Claude CodeのTodoRead/TodoWrite APIと連携して、タスク管理を自動化する機能です。

### 主な機能

- **双方向同期**: Claude Code ↔ ナレッジベース間でタスクを同期
- **自動コミット**: 変更を自動的にGitにコミット
- **キャッシュ管理**: タスクの永続化とオフライン対応
- **CLI統合**: `ukf claude`コマンドで簡単操作

## クイックスタート

### 1. 初期設定

```bash
# Claude Code連携を初期化
ukf claude init
```

### 2. タスクの同期

```bash
# Claude CodeのTodoReadで取得したタスクを同期
ukf claude sync --tasks-json '[
  {
    "id": "1",
    "content": "機能実装",
    "status": "in_progress",
    "priority": "high"
  }
]'
```

### 3. 状態確認

```bash
# 同期状態を確認
ukf claude status
```

### 4. エクスポート

```bash
# ナレッジベースのタスクをClaude Code形式でエクスポート
ukf claude export > tasks.json
```

## 詳細な使用方法

### タスク同期の仕組み

1. **Claude → Knowledge Base**
   - TodoReadでタスクを取得
   - `ukf claude sync`でナレッジベースに反映
   - マークダウン形式でタスクを管理

2. **Knowledge Base → Claude**
   - マークダウンファイルからタスクを読み取り
   - `ukf claude export`でJSON形式に変換
   - TodoWriteで使用可能

### タスクファイル形式

同期されたタスクは以下の形式で保存されます：

```markdown
# タスク管理

最終更新: 2025-06-15 12:00:00 (Claude Code 自動同期)

## 🔄 進行中タスク

- [>] #task-001 **UKF統合機能の実装**

## 📋 未完了タスク

- [ ] #task-002 **テストケースの作成** 🟡 medium

## ✅ 完了タスク

- [x] #task-003 **ドキュメント更新**

---

## 📊 サマリー

- **総タスク数**: 3
- **完了**: 1
- **進行中**: 1
- **未完了**: 1
- **完了率**: 33.3%
```

### プログラムからの使用

```python
from universal_knowledge.ai.claude_code_sync import ClaudeCodeSync

# 初期化
sync = ClaudeCodeSync(
    vault_path="./knowledge",
    auto_commit=True
)

# Claude Codeからタスクを同期
tasks = [
    {
        "id": "1",
        "content": "新機能の実装",
        "status": "pending",
        "priority": "high"
    }
]
sync.sync_from_claude(tasks)

# ナレッジベースからタスクを取得
claude_tasks = sync.sync_to_claude()
print(f"エクスポート: {len(claude_tasks)}タスク")
```

## 設定オプション

### 環境変数

```bash
# ナレッジベースのパス（デフォルト: ./knowledge）
export UKF_VAULT_PATH="/path/to/knowledge"

# キャッシュファイルのパス（デフォルト: ./.claude-task-cache.json）
export UKF_CLAUDE_CACHE="/path/to/cache.json"

# Git自動コミット（デフォルト: true）
export UKF_AUTO_COMMIT="false"
```

### CLIオプション

```bash
# カスタムナレッジベースパスを指定
ukf claude sync --vault-path /custom/path --tasks-json '...'

# Git自動コミットを無効化
ukf claude sync --no-auto-commit --tasks-json '...'
```

## ベストプラクティス

### 1. 定期的な同期

```bash
# cronで定期実行
*/30 * * * * ukf claude sync
```

### 2. タスクの構造化

```python
# 明確なタスクIDとコンテンツ
task = {
    "id": "feature-auth-001",
    "content": "JWT認証機能の実装",
    "status": "in_progress",
    "priority": "high"
}
```

### 3. エラーハンドリング

```python
try:
    sync.sync_from_claude(tasks)
except Exception as e:
    print(f"同期エラー: {e}")
    # キャッシュから復元
    cached_tasks = sync._load_cache()
```

## トラブルシューティング

### 同期が失敗する場合

1. **権限エラー**
   ```bash
   # ディレクトリ権限を確認
   ls -la ./knowledge
   chmod 755 ./knowledge
   ```

2. **Git関連エラー**
   ```bash
   # Git初期化
   git init
   # リモート設定
   git remote add origin <repository-url>
   ```

3. **キャッシュ破損**
   ```bash
   # キャッシュをクリア
   rm ./.claude-task-cache.json
   # 再同期
   ukf claude sync --tasks-json '...'
   ```

### デバッグモード

```python
import logging

# ログレベルを設定
sync = ClaudeCodeSync(log_level="DEBUG")

# 詳細なログを確認
logging.basicConfig(level=logging.DEBUG)
```

## 高度な使用方法

### カスタムコールバック

```python
# 同期完了時の処理
def on_sync_complete(tasks):
    print(f"同期完了: {len(tasks)}タスク")
    # 通知送信など

sync.set_on_sync_complete(on_sync_complete)
sync.sync_from_claude(tasks)
```

### バッチ処理

```python
# 複数プロジェクトの一括同期
projects = ["project1", "project2", "project3"]

for project in projects:
    sync = ClaudeCodeSync(vault_path=f"./{project}/knowledge")
    tasks = get_tasks_for_project(project)
    sync.sync_from_claude(tasks)
```

### カスタムフォーマット

```python
# タスクファイル名をカスタマイズ
sync.task_file_name = "プロジェクトタスク.md"
sync.sync_log_dir = "ログ"
sync.sync_log_file = "同期履歴.md"
```

## リリースノート

### v1.0.0 (2025-06-15)

- 初回リリース
- Claude Code TodoRead/TodoWrite対応
- 双方向同期機能
- CLI統合
- Git自動コミット
- キャッシュ管理

## 今後の機能追加予定

- リアルタイム同期（ファイル監視）
- WebSocket/SSE対応
- 複数プロジェクト管理
- タスクフィルタリング
- カスタムテンプレート
- 統計・レポート機能

## 貢献方法

1. フォークしてクローン
2. フィーチャーブランチ作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエスト作成

## ライセンス

MIT License - 詳細は[LICENSE](../LICENSE)を参照してください。