"""Utilities for converting Claude chat logs to Markdown."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Union

# 設定定数
IGNORE_PHRASES = {"了解です", "はい", "OK", "ok", "承知しました"}
DEFAULT_INPUT_DIR = "claude_logs"
DEFAULT_OUTPUT_DIR = "knowledge/Claude"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CHUNK_SIZE = 1000  # 大容量ファイル処理時のチャンクサイズ

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeLogValidationError(Exception):
    """Claude ログファイルの検証エラー"""
    pass


def validate_claude_log(log_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
    """
    Claude ログデータの構造を検証
    
    Args:
        log_data: ログデータ（辞書またはメッセージリスト）
        
    Returns:
        bool: 検証結果
        
    Raises:
        ClaudeLogValidationError: 検証に失敗した場合
    """
    logger.debug("ログデータの構造検証を開始")
    
    if isinstance(log_data, list):
        # メッセージリスト形式
        messages = log_data
    elif isinstance(log_data, dict):
        # 辞書形式 - messagesキーをチェック
        if 'messages' not in log_data:
            raise ClaudeLogValidationError("必須フィールド 'messages' が見つかりません")
        messages = log_data['messages']
        
        # 任意フィールドの検証
        if 'conversation_id' in log_data and not isinstance(log_data['conversation_id'], str):
            raise ClaudeLogValidationError("conversation_id は文字列である必要があります")
            
        if 'timestamp' in log_data:
            # タイムスタンプの基本チェック
            timestamp = log_data['timestamp']
            if not isinstance(timestamp, (str, int, float)):
                raise ClaudeLogValidationError("timestamp は文字列または数値である必要があります")
    else:
        raise ClaudeLogValidationError(f"不正なデータ形式: {type(log_data)}")
    
    # メッセージの検証
    if not isinstance(messages, list):
        raise ClaudeLogValidationError("messages は配列である必要があります")
    
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise ClaudeLogValidationError(f"メッセージ {i} は辞書である必要があります")
        
        # roleフィールドの検証（任意）
        if 'role' in msg and msg['role'] not in ['user', 'assistant', 'system']:
            logger.warning(f"メッセージ {i}: 不明なロール '{msg['role']}'")
        
        # contentフィールドの存在チェック
        if 'content' not in msg:
            logger.warning(f"メッセージ {i}: 'content' フィールドがありません")
    
    logger.debug(f"検証完了: {len(messages)}件のメッセージを確認")
    return True


def check_file_size(file_path: Path) -> bool:
    """
    ファイルサイズをチェック
    
    Args:
        file_path: チェック対象ファイル
        
    Returns:
        bool: サイズ制限内かどうか
    """
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"大容量ファイル検出: {file_path.name} "
            f"({file_size / (1024*1024):.1f}MB > {MAX_FILE_SIZE / (1024*1024):.1f}MB)"
        )
        return False
    return True


def convert_log_to_markdown(json_path: Path, exclude_short: bool = True) -> str:
    """
    単一のClaude チャットログJSONファイルをMarkdownに変換
    
    Parameters
    ----------
    json_path:
        JSONファイルのパス
    exclude_short:
        短いメッセージを除外するかどうか
        
    Returns:
        str: 変換されたMarkdownテキスト
        
    Raises:
        ClaudeLogValidationError: ログ検証エラー
        json.JSONDecodeError: JSON解析エラー
        FileNotFoundError: ファイルが見つからない
        UnicodeDecodeError: 文字エンコーディングエラー
    """
    logger.info(f"ログ変換開始: {json_path}")
    
    # ファイル存在チェック
    if not json_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {json_path}")
    
    # ファイルサイズチェック
    if not check_file_size(json_path):
        logger.warning(f"大容量ファイルを処理中: {json_path}")
    
    try:
        # JSON読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 構造検証
        validate_claude_log(data)
        
        # メッセージ抽出
        messages = []
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get('messages', [])
        
        logger.debug(f"メッセージ数: {len(messages)}")
        
        # Markdown変換
        lines = [f"# {json_path.stem}"]
        processed_count = 0
        skipped_count = 0
        
        for msg in messages:
            role = msg.get('role', 'assistant').capitalize()
            content = msg.get('content', '')
            text = str(content).strip()
            
            if exclude_short and (not text or len(text) < 2 or text in IGNORE_PHRASES):
                skipped_count += 1
                continue
                
            lines.append(f"\n## {role}\n{text}")
            processed_count += 1
        
        logger.info(
            f"変換完了: {json_path.name} - "
            f"処理済み: {processed_count}件, スキップ: {skipped_count}件"
        )
        
        return "\n".join(lines) + "\n"
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析エラー: {json_path} - {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"文字エンコーディングエラー: {json_path} - {e}")
        raise
    except ClaudeLogValidationError as e:
        logger.error(f"ログ検証エラー: {json_path} - {e}")
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: {json_path} - {e}")
        raise


def process_logs(input_dir: Path, output_dir: Path, exclude_short: bool = True) -> None:
    """
    入力ディレクトリ内の全JSONログをMarkdownファイルに変換
    
    Args:
        input_dir: JSONログファイルがあるディレクトリ
        output_dir: Markdownファイルの出力先ディレクトリ
        exclude_short: 短いメッセージを除外するかどうか
    """
    logger.info(f"ログ処理開始: {input_dir} -> {output_dir}")
    
    # 入力ディレクトリの存在チェック
    if not input_dir.exists():
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"入力パスはディレクトリではありません: {input_dir}")
    
    # 出力ディレクトリ作成
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"出力ディレクトリ作成: {output_dir}")
    except PermissionError as e:
        logger.error(f"出力ディレクトリ作成権限エラー: {output_dir} - {e}")
        raise
    
    # JSONファイル検索
    json_files = list(sorted(input_dir.glob('*.json')))
    if not json_files:
        logger.warning(f"JSONファイルが見つかりません: {input_dir}")
        return
    
    logger.info(f"処理対象: {len(json_files)}個のJSONファイル")
    
    # 統計情報
    success_count = 0
    error_count = 0
    total_processed_messages = 0
    total_skipped_messages = 0
    
    for json_file in json_files:
        try:
            logger.debug(f"処理中: {json_file.name}")
            
            # ファイルサイズ事前チェック
            file_size = json_file.stat().st_size
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"大容量ファイルをスキップ: {json_file.name} ({file_size / (1024*1024):.1f}MB)")
                error_count += 1
                continue
            
            # Markdown変換
            md_file = output_dir / (json_file.stem + '.md')
            markdown = convert_log_to_markdown(json_file, exclude_short)
            
            # ファイル書き込み
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            success_count += 1
            logger.debug(f"変換完了: {json_file.name} -> {md_file.name}")
            
        except (json.JSONDecodeError, ClaudeLogValidationError) as e:
            logger.error(f"ファイル処理エラー: {json_file.name} - {e}")
            error_count += 1
            continue
        except Exception as e:
            logger.error(f"予期しないエラー: {json_file.name} - {e}")
            error_count += 1
            continue
    
    # 処理結果サマリー
    logger.info(
        f"処理完了 - 成功: {success_count}件, エラー: {error_count}件, "
        f"合計: {len(json_files)}件"
    )
    
    if error_count > 0:
        logger.warning(f"{error_count}件のファイルでエラーが発生しました。ログを確認してください。")


def validate_all_logs(input_dir: Path) -> Dict[str, Any]:
    """
    ディレクトリ内の全ログファイルを検証
    
    Args:
        input_dir: 検証対象ディレクトリ
        
    Returns:
        Dict: 検証結果サマリー
    """
    logger.info(f"ログ検証開始: {input_dir}")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"ディレクトリが見つかりません: {input_dir}")
    
    json_files = list(input_dir.glob('*.json'))
    if not json_files:
        logger.warning(f"JSONファイルが見つかりません: {input_dir}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": []}
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            validate_claude_log(data)
            valid_count += 1
            logger.debug(f"✅ {json_file.name}")
        except Exception as e:
            invalid_count += 1
            error_info = {"file": json_file.name, "error": str(e)}
            errors.append(error_info)
            logger.error(f"❌ {json_file.name}: {e}")
    
    result = {
        "total": len(json_files),
        "valid": valid_count,
        "invalid": invalid_count,
        "errors": errors
    }
    
    logger.info(f"検証完了: {valid_count}/{len(json_files)}件が有効")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Claude chat logs to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s -i ./claude_logs -o ./knowledge/Claude
  %(prog)s --include-short --verbose
  %(prog)s --validate-only
        """
    )
    parser.add_argument(
        '-i', '--input', 
        default=DEFAULT_INPUT_DIR, 
        help=f'Directory containing Claude JSON logs (default: {DEFAULT_INPUT_DIR})'
    )
    parser.add_argument(
        '-o', '--output', 
        default=DEFAULT_OUTPUT_DIR, 
        help=f'Output directory for Markdown files (default: {DEFAULT_OUTPUT_DIR})'
    )
    parser.add_argument(
        '--include-short', 
        action='store_true', 
        help='Include very short messages and acknowledgements'
    )
    parser.add_argument(
        '--validate-only', 
        action='store_true', 
        help='Only validate JSON structure without conversion'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true', 
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    try:
        if args.validate_only:
            # 検証のみモード
            result = validate_all_logs(input_dir)
            print(f"検証結果: {result['valid']}/{result['total']}件が有効")
            
            if result['errors']:
                print("\nエラー詳細:")
                for error in result['errors']:
                    print(f"  {error['file']}: {error['error']}")
            
            sys.exit(0 if result['invalid'] == 0 else 1)
        else:
            # 通常の変換モード
            process_logs(input_dir, output_dir, exclude_short=not args.include_short)
            print(f"✅ Claude ログの変換が完了しました: {output_dir}")
            
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


