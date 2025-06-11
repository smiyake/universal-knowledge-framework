import json
import tempfile
import pytest
from pathlib import Path
from universal_knowledge.utils.claude2md import (
    convert_log_to_markdown, 
    process_logs, 
    validate_claude_log,
    validate_all_logs,
    ClaudeLogValidationError,
    MAX_FILE_SIZE
)


def test_convert_log_to_markdown():
    """基本的なログ変換テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "sample.json"
        data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "了解です"}
            ]
        }
        log.write_text(json.dumps(data), encoding='utf-8')
        md = convert_log_to_markdown(log)
        assert "## User" in md
        assert "Hello" in md
        assert "Hi" in md
        # short message should be excluded
        assert "了解です" not in md


def test_process_logs_creates_markdown_files():
    """ディレクトリ処理テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / "logs"
        out_dir = Path(tmpdir) / "out"
        logs_dir.mkdir()
        data = {"messages": [{"role": "user", "content": "Test"}]}
        (logs_dir / "a.json").write_text(json.dumps(data), encoding='utf-8')
        process_logs(logs_dir, out_dir)
        md_file = out_dir / "a.md"
        assert md_file.exists()
        content = md_file.read_text(encoding='utf-8')
        assert "Test" in content


def test_validate_claude_log_valid_dict():
    """有効な辞書形式ログの検証テスト"""
    valid_data = {
        "conversation_id": "test-123",
        "timestamp": "2024-01-01T00:00:00Z",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }
    assert validate_claude_log(valid_data) == True


def test_validate_claude_log_valid_list():
    """有効なリスト形式ログの検証テスト"""
    valid_data = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    assert validate_claude_log(valid_data) == True


def test_validate_claude_log_missing_messages():
    """messagesフィールド不足のエラーテスト"""
    invalid_data = {
        "conversation_id": "test-123",
        "timestamp": "2024-01-01T00:00:00Z"
        # messages field missing
    }
    with pytest.raises(ClaudeLogValidationError, match="必須フィールド 'messages' が見つかりません"):
        validate_claude_log(invalid_data)


def test_validate_claude_log_invalid_messages_type():
    """不正なmessagesタイプのエラーテスト"""
    invalid_data = {
        "messages": "not a list"  # should be list
    }
    with pytest.raises(ClaudeLogValidationError, match="messages は配列である必要があります"):
        validate_claude_log(invalid_data)


def test_validate_claude_log_invalid_message_format():
    """不正なメッセージ形式のエラーテスト"""
    invalid_data = {
        "messages": [
            "not a dict",  # should be dict
            {"role": "user", "content": "Hello"}
        ]
    }
    with pytest.raises(ClaudeLogValidationError, match="メッセージ 0 は辞書である必要があります"):
        validate_claude_log(invalid_data)


def test_validate_claude_log_invalid_data_type():
    """不正なデータタイプのエラーテスト"""
    invalid_data = "not a dict or list"
    with pytest.raises(ClaudeLogValidationError, match="不正なデータ形式"):
        validate_claude_log(invalid_data)


def test_malformed_json_handling():
    """不正なJSON形式の処理テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "malformed.json"
        log.write_text("{invalid json", encoding='utf-8')
        
        with pytest.raises(json.JSONDecodeError):
            convert_log_to_markdown(log)


def test_large_log_conversion():
    """大容量ログの処理テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "large.json"
        
        # 大量のメッセージを含むログデータ作成
        large_data = {
            "messages": [
                {"role": "user", "content": f"Message {i}"}
                for i in range(1000)
            ]
        }
        
        log.write_text(json.dumps(large_data), encoding='utf-8')
        md = convert_log_to_markdown(log)
        
        # 正常に変換されることを確認
        assert "Message 0" in md
        assert "Message 999" in md
        assert md.count("## User") == 1000


def test_empty_log_handling():
    """空ログファイルの処理テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "empty.json"
        
        # 空のメッセージリスト
        empty_data = {"messages": []}
        log.write_text(json.dumps(empty_data), encoding='utf-8')
        
        md = convert_log_to_markdown(log)
        # ヘッダーのみが含まれることを確認
        assert f"# {log.stem}" in md
        assert "## User" not in md
        assert "## Assistant" not in md


def test_file_not_found_error():
    """ファイルが見つからない場合のエラーテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "not_found.json"
        
        with pytest.raises(FileNotFoundError):
            convert_log_to_markdown(non_existent)


def test_unicode_decode_error():
    """文字エンコーディングエラーのテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "bad_encoding.json"
        
        # 不正なエンコーディングでファイル作成
        with open(log, 'wb') as f:
            f.write(b'\xff\xfe{"messages": []}')  # Invalid UTF-8
        
        with pytest.raises(UnicodeDecodeError):
            convert_log_to_markdown(log)


def test_validate_all_logs():
    """ディレクトリ内全ログ検証テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / "logs"
        logs_dir.mkdir()
        
        # 有効なログファイル
        valid_data = {"messages": [{"role": "user", "content": "Hello"}]}
        (logs_dir / "valid.json").write_text(json.dumps(valid_data), encoding='utf-8')
        
        # 無効なログファイル
        invalid_data = {"no_messages": "invalid"}
        (logs_dir / "invalid.json").write_text(json.dumps(invalid_data), encoding='utf-8')
        
        result = validate_all_logs(logs_dir)
        
        assert result["total"] == 2
        assert result["valid"] == 1
        assert result["invalid"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["file"] == "invalid.json"


def test_include_short_messages():
    """短いメッセージを含める設定のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "short.json"
        data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "了解です"}  # normally excluded
            ]
        }
        log.write_text(json.dumps(data), encoding='utf-8')
        
        # exclude_short=Falseで短いメッセージも含める
        md = convert_log_to_markdown(log, exclude_short=False)
        assert "Hello" in md
        assert "了解です" in md


def test_process_logs_with_mixed_files():
    """有効・無効ファイルが混在する場合のディレクトリ処理テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / "logs"
        out_dir = Path(tmpdir) / "out"
        logs_dir.mkdir()
        
        # 有効なファイル
        valid_data = {"messages": [{"role": "user", "content": "Valid"}]}
        (logs_dir / "valid.json").write_text(json.dumps(valid_data), encoding='utf-8')
        
        # 無効なJSONファイル
        (logs_dir / "invalid.json").write_text("{invalid", encoding='utf-8')
        
        # テキストファイル（無視される）
        (logs_dir / "ignore.txt").write_text("ignore me", encoding='utf-8')
        
        # process_logsは例外を投げずに続行する
        process_logs(logs_dir, out_dir)
        
        # 有効なファイルのみが変換される
        assert (out_dir / "valid.md").exists()
        assert not (out_dir / "invalid.md").exists()
        assert not (out_dir / "ignore.md").exists()


def test_directory_not_found_error():
    """存在しないディレクトリの処理エラーテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_dir = Path(tmpdir) / "not_found"
        out_dir = Path(tmpdir) / "out"
        
        with pytest.raises(FileNotFoundError):
            process_logs(non_existent_dir, out_dir)


def test_role_capitalization():
    """ロールの大文字化テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "roles.json"
        data = {
            "messages": [
                {"role": "user", "content": "User message"},
                {"role": "assistant", "content": "Assistant message"},
                {"role": "system", "content": "System message"}
            ]
        }
        log.write_text(json.dumps(data), encoding='utf-8')
        md = convert_log_to_markdown(log)
        
        assert "## User" in md
        assert "## Assistant" in md
        assert "## System" in md
