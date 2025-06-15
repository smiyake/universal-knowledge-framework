"""
Claude Code同期機能の使用例
"""

import json
from pathlib import Path
from universal_knowledge.ai.claude_code_sync import ClaudeCodeSync, TaskStatus, TaskPriority

def main():
    """Claude Code同期のデモンストレーション"""
    
    # 1. 同期マネージャーの初期化
    print("=== Claude Code同期デモ ===\n")
    
    sync = ClaudeCodeSync(
        vault_path=Path("./demo_knowledge"),
        auto_commit=False  # デモなのでGit自動コミットは無効
    )
    
    # 2. サンプルタスクの作成
    sample_tasks = [
        {
            "id": "demo-001",
            "content": "UKF統合機能の実装",
            "status": "in_progress",
            "priority": "high"
        },
        {
            "id": "demo-002",
            "content": "ドキュメント作成",
            "status": "pending",
            "priority": "medium"
        },
        {
            "id": "demo-003",
            "content": "初期設定完了",
            "status": "completed",
            "priority": "low"
        }
    ]
    
    print("1. サンプルタスクを同期...")
    print(f"   タスク数: {len(sample_tasks)}")
    print()
    
    # 3. Claude → Knowledge Base同期
    sync.sync_from_claude(sample_tasks)
    print("✅ Claude → Knowledge Base 同期完了")
    print(f"   タスクファイル: {sync.vault_path / sync.task_file_name}")
    print()
    
    # 4. 同期状態確認
    status = sync.get_sync_status()
    print("2. 同期状態:")
    print(f"   最終同期: {status['last_sync']}")
    print(f"   タスク数: {status['total_tasks']}")
    print(f"   キャッシュ: {status['cache_file']}")
    print()
    
    # 5. Knowledge Base → Claude同期
    print("3. Knowledge Baseからタスクを取得...")
    exported_tasks = sync.sync_to_claude()
    print(f"✅ {len(exported_tasks)}タスクをエクスポート")
    print()
    
    # 6. エクスポートされたタスクの表示
    print("4. エクスポートされたタスク (TodoWrite形式):")
    print(json.dumps(exported_tasks, ensure_ascii=False, indent=2))
    print()
    
    # 7. コールバック機能のデモ
    print("5. コールバック機能のデモ...")
    
    def on_sync_complete(tasks):
        print(f"   [コールバック] 同期完了: {len(tasks)}タスク処理")
        for task in tasks[:3]:  # 最初の3つを表示
            print(f"   - {task.content} ({task.status.value})")
    
    sync.set_on_sync_complete(on_sync_complete)
    
    # 新しいタスクで再同期
    new_task = {
        "id": "demo-004",
        "content": "コールバックテスト",
        "status": "pending",
        "priority": "high"
    }
    sample_tasks.append(new_task)
    
    print("   新しいタスクを追加して再同期...")
    sync.sync_from_claude(sample_tasks)
    print()
    
    # 8. 生成されたファイルの内容を表示
    print("6. 生成されたタスクファイルの内容:")
    print("-" * 50)
    task_file = sync.vault_path / sync.task_file_name
    if task_file.exists():
        content = task_file.read_text(encoding='utf-8')
        # 最初の20行を表示
        lines = content.split('\n')[:20]
        for line in lines:
            print(line)
        if len(content.split('\n')) > 20:
            print("... (以下省略)")
    print("-" * 50)
    
    print("\n✅ デモ完了!")
    print("\n💡 実際の使用では:")
    print("   1. Claude CodeでTodoReadを実行")
    print("   2. 取得したJSONを ukf claude sync --tasks-json に渡す")
    print("   3. 必要に応じて ukf claude export でタスクを取得")
    print("   4. TodoWriteで Claude Code に反映")


if __name__ == "__main__":
    main()