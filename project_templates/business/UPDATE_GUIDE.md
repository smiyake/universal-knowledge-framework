# UKF更新ガイド - プロジェクト用
# Universal Knowledge Framework Update Guide - For Projects

このファイルは、UKF (Universal Knowledge Framework) を使用しているプロジェクト用の更新ガイドです。

## 🔄 定期的な更新チェック

### 簡単更新（推奨）
```bash
# 自動更新 - 最も簡単
ukf update run

# 更新チェックのみ
ukf update check
```

### 手動更新
```bash
# UKFプロジェクトディレクトリで
cd /path/to/universal-knowledge-framework
git pull origin main
pip install -e .
```

## 📊 プロジェクト固有の活用方法

### このプロジェクトでの新機能活用

#### 統計情報分析
```bash
# プロジェクト統計表示
ukf stats summary

# 最近のアクティビティ確認
ukf stats activity --days 7

# レポート出力
ukf stats export --format markdown --output weekly-report.md
```

#### AI開発セッション
```bash
# 作業開始時
ukf ai session start --type implementation --description "週次開発作業"

# 重要な進捗時
ukf ai milestone add "機能実装完了"

# 作業終了時
ukf ai session end --summary "今週の成果まとめ"
```

#### 動的テンプレート
```bash
# プロジェクトに最適化されたテンプレート生成
ukf template generate session --context auto

# 会議録テンプレート
ukf template generate meeting --language ja
```

## 🔧 トラブルシューティング

### よくある問題

#### コマンドが見つからない
```bash
# UKFの再インストール
pip install -e /path/to/universal-knowledge-framework
```

#### 新機能が使えない
```bash
# 最新版確認
ukf version

# 強制更新
ukf update run --force
```

## 📋 更新履歴の記録

このプロジェクトでの更新履歴：

- [ ] v1.1.0 統計機能導入済み
- [ ] AI開発ワークフロー導入済み  
- [ ] 動的テンプレート導入済み
- [ ] Bridge連携設定済み

## 🎯 推奨ワークフロー

### 週次ルーチン
1. `ukf update check` - 更新確認
2. `ukf stats activity --days 7` - 週次活動確認
3. 必要に応じて `ukf update run` - 更新実行

### 月次ルーチン
1. `ukf stats export --format markdown` - 月次レポート
2. `ukf update backups` - バックアップ確認
3. `ukf update cleanup` - 古いバックアップ削除

---

**このファイルはプロジェクト作成時に自動生成されました。**
最新の更新情報は [UKF UPDATE_GUIDE.md](https://github.com/smiyake/universal-knowledge-framework/blob/main/UPDATE_GUIDE.md) を参照してください。