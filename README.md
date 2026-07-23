# まもるバス

保育園・幼稚園向けの送迎バス置き去り防止・安全確認PWAです。

## 開発

```powershell
npm install
npm run dev
```

API は別ターミナルで起動します。

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

`DATABASE_URL` を PostgreSQL の接続URLに設定すれば、本番DBへ移行できます。

## GitHub Pages

`main` ブランチへのpush時に、GitHub Actions が `dist` を GitHub Pages へデプロイします。
