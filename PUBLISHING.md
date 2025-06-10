# PyPI公開手順

## 準備

### 1. アカウント設定

```bash
# PyPI アカウント作成
# https://pypi.org/account/register/

# twine インストール
pip install twine build
```

### 2. 認証設定

```bash
# ~/.pypirc ファイル作成
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-your-api-token-here
```

## 公開手順

### 1. パッケージビルド

```bash
# パッケージビルド
python -m build

# 生成されるファイル確認
ls dist/
# universal_knowledge_framework-1.0.0-py3-none-any.whl
# universal_knowledge_framework-1.0.0.tar.gz
```

### 2. テスト（TestPyPI）

```bash
# TestPyPI にアップロード
twine upload --repository testpypi dist/*

# TestPyPI からインストールテスト
pip install --index-url https://test.pypi.org/simple/ universal-knowledge-framework
```

### 3. 本番公開

```bash
# PyPI にアップロード
twine upload dist/*

# インストール確認
pip install universal-knowledge-framework
```

## バージョン管理

### バージョンアップ手順

1. `pyproject.toml` のバージョン更新
2. `src/universal_knowledge/__init__.py` のバージョン更新
3. CHANGELOG.md 更新
4. Git tag 作成

```bash
git tag v1.0.1
git push origin v1.0.1
```

## 注意事項

- バージョンは一度公開すると変更不可
- ファイル内容の確認を十分に行う
- 機密情報が含まれていないことを確認
- ライセンス条項の確認

## 自動化（GitHub Actions）

`.github/workflows/publish.yml` で自動公開設定可能（将来対応）