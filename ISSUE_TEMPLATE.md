# [Bug] v1.1.0でのインポートエラー - DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR

## バグの説明
v1.1.0へのアップデート後、`ukf`コマンド実行時にインポートエラーが発生します。

## エラー内容
```
ImportError: cannot import name 'DEFAULT_INPUT_DIR' from 'universal_knowledge.utils' (/mnt/d/Projects/00_CGZ/ai-trading-system/universal-knowledge-framework/src/universal_knowledge/utils/__init__.py)
```

## 再現手順
1. UKF v1.1.0をインストール
2. `ukf --version`コマンドを実行
3. 上記のインポートエラーが発生

## 原因
- `cli.py`が`utils`モジュールから直接`DEFAULT_INPUT_DIR`と`DEFAULT_OUTPUT_DIR`をインポートしようとしている
- 実際にはこれらの定数は`utils.claude2md`モジュールに定義されている

## 修正内容
1. `pyproject.toml`のバージョンを1.1.0に更新（`__init__.py`と一致させる）
2. `cli.py`のインポート文を以下のように修正：
```python
# 修正前
from .utils import process_logs, DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR

# 修正後
from .utils import process_logs
from .utils.claude2md import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
```

## 関連ブランチ
- fix/import-error-v1.1.0

## Pull Request URL
https://github.com/smiyake/universal-knowledge-framework/pull/new/fix/import-error-v1.1.0

## 環境
- Python: 3.10
- OS: WSL2 (Ubuntu)
- UKF Version: 1.1.0