import json
import tempfile
from pathlib import Path
from universal_knowledge.utils.claude2md import convert_log_to_markdown, process_logs


def test_convert_log_to_markdown():
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
