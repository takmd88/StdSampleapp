# Engineer Portfolio

Flask と SQLite で作った、1ページ構成のITエンジニア向けポートフォリオサイトです。

## セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

ブラウザで `http://127.0.0.1:5000` を開いてください。問い合わせ内容は `instance/portfolio.db` の `inquiries` テーブルへ保存されます。

## テスト

```powershell
python -m unittest discover -s tests -v
```

本番運用時は環境変数 `SECRET_KEY` に十分長いランダム値を設定してください。
