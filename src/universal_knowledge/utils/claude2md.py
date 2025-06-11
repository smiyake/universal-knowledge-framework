import json
from pathlib import Path
import argparse

IGNORE_PHRASES = {"了解です", "はい", "OK", "ok", "承知しました"}


def convert_log_to_markdown(json_path: Path, exclude_short: bool = True) -> str:
    """Convert a single Claude chat log JSON file to Markdown."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = []
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        messages = data.get('messages', [])

    lines = [f"# {json_path.stem}"]
    for msg in messages:
        role = msg.get('role', 'assistant').capitalize()
        content = msg.get('content', '')
        text = str(content).strip()
        if exclude_short and (not text or len(text) < 2 or text in IGNORE_PHRASES):
            continue
        lines.append(f"\n## {role}\n{text}")

    return "\n".join(lines) + "\n"


def process_logs(input_dir: Path, output_dir: Path, exclude_short: bool = True) -> None:
    """Process all JSON logs in the input directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for json_file in sorted(input_dir.glob('*.json')):
        md_file = output_dir / (json_file.stem + '.md')
        markdown = convert_log_to_markdown(json_file, exclude_short)
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Claude chat logs to Markdown")
    parser.add_argument('-i', '--input', default='claude_logs', help='Directory containing Claude JSON logs')
    parser.add_argument('-o', '--output', default='knowledge/Claude', help='Output directory for Markdown files')
    parser.add_argument('--include-short', action='store_true', help='Include very short messages')
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    process_logs(input_dir, output_dir, exclude_short=not args.include_short)


if __name__ == '__main__':
    main()
