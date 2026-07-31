# まもるバス

**まもるバス**は、保育園・幼稚園の送迎バスで、子どもの置き去りを防ぐための安全確認PWAです。

園にあるスマートフォンとQRコードを活用し、職員が毎日行う確認を、

**乗車 → 降車 → 人数照合 → 車内の目視確認と5〜30秒撮影 → 記録保存 → 送迎完了**

の順番で、迷わず進められる仕組みを目指しています。

画面は、ITに詳しくない職員でも使いやすいように、大きなボタンと分かりやすい日本語を中心にしています。AIは職員の確認を補助する役割とし、AIの判定だけで安全確認を完了させない設計方針です。

> [!IMPORTANT]
> 現在は開発途中の試作版です。公開ページは画面と基本操作を確認するためのデモであり、実際の送迎業務にはまだ使用できません。

![「まもるバス」LINE・メール通知連携の仕組み](docs/images/mamoru-bus-line-mail-notification-flow.png)

## 公開デモ

[まもるバスを開く](https://kazunyon.github.io/child_presence_detection/)


GitHub PagesはReact画面を配信し、Render上のFastAPI（サービス名の例：`mamoru-bus-api`）へ認証済みリクエストを送ります。データはAPI側のデータベースへ保存されます。GitHub Pages単体ではFastAPIやデータベースは動作しません。

## インストールガイド

利用目的に応じて、次のいずれかを選びます。

| 目的 | 必要な作業 |
|---|---|
| 公開デモを試す | インストール不要。上の「まもるバスを開く」から利用 |
| PCで開発・動作確認する | Git、Node.js、Pythonを準備し、フロントエンドとAPIを起動 |
| 新しい公開環境を作る | RenderへAPI・DBを配置し、GitHub Pagesから接続 |

> [!IMPORTANT]
> 公開デモを試すだけなら、PCへのインストールやRenderの設定は必要ありません。現在は開発途中の試作版のため、実際の送迎業務には使用しないでください。

### 1. 公開デモを使う

1. 上の [まもるバスを開く](https://kazunyon.github.io/child_presence_detection/) を押します。
2. ブラウザで画面が開いたら、ログインして基本操作を確認します。
3. iPhoneへ追加する場合は、Safariの **共有 → ホーム画面に追加 → 追加** を押します。
4. PC版Chromeでは、アドレスバー付近のインストールアイコンが表示された場合に、そこからPWAとして追加できます。

公開デモのログイン情報は、管理者から安全な方法で受け取ってください。PINやSecretはREADMEへ記載しません。

### 2. PCへ開発環境をインストールする

#### 必要なもの

- [Git](https://git-scm.com/downloads)
- [Node.js](https://nodejs.org/)（GitHub Pagesのビルド環境はNode.js 22）
- [Python](https://www.python.org/downloads/)
- Windows PowerShellまたはターミナル

#### ソースコードを取得する

PowerShellを開き、次を実行します。

```powershell
git clone https://github.com/kazunyon/child_presence_detection.git
cd child_presence_detection
```

Privateリポジトリを取得できない場合は、GitHubへログインし、このリポジトリの閲覧権限があることを確認してください。

#### バックエンド（FastAPI）を起動する

1つ目のPowerShellで実行します。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

起動後、ブラウザで [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) を開き、APIが応答することを確認します。

ローカル環境では、環境変数を指定しなければSQLiteの `backend/mamoru_bus.db` を使用します。開発用の動画は `backend/uploads` に保存されます。

> [!NOTE]
> PowerShellで仮想環境の有効化が制限された場合は、`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`、続けて `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000` を実行できます。

#### フロントエンド（React）を起動する

2つ目のPowerShellで、リポジトリ直下へ移動して実行します。

```powershell
npm install
npm run dev
```

画面に表示されたURL（通常は [http://localhost:5173](http://localhost:5173)）を開きます。ローカル起動時は、`VITE_API_BASE_URL` を指定しなければ `http://127.0.0.1:8000` のAPIへ接続します。

#### 起動を終了する

フロントエンドとバックエンドを起動した各PowerShellで、`Ctrl + C` を押します。

### 3. RenderとGitHub Pagesへインストールする

公開環境は、次の順番で準備します。

1. Renderで `render.yaml` を使い、FastAPIの **mamoru-bus-api**、PostgreSQLの **mamoru-bus-db**、動画保存用Persistent Diskを作成します。
2. Renderの `/health` が正常に応答することを確認します。
3. GitHubの **Settings → Secrets and variables → Actions → Variables** に、`VITE_API_BASE_URL` を登録します。
4. 値にはRender APIの公開URLを指定します。例：`https://mamoru-bus-api.onrender.com`
5. GitHubの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にします。
6. GitHub Actionsの `Deploy PWA to GitHub Pages` が成功したことを確認します。
7. 公開デモを開き、ログイン、記録保存、動画表示、API通信を確認します。

詳しい手順は、後述の [Renderへのインストール・環境変数設定](#renderへのインストール環境変数設定) と [LINE Developersのインストール・Messaging API設定](#line-developersのインストールmessaging-api設定) を参照してください。

> [!WARNING]
> `JWT_SECRET`、LINEのChannel access token／Channel secret、職員PINなどは、GitHubやフロントエンドへ登録しないでください。SecretはRenderのEnvironmentへ保存します。

### 4. インストール後の基本確認

| 確認項目 | 正常な状態 |
|---|---|
| FastAPI | `/health` が正常応答する |
| React画面 | ログイン画面が表示される |
| API接続 | ログイン後に園・車両・記録を取得できる |
| データ保存 | 再読み込み後も登録内容が残る |
| 動画 | 5〜30秒のテスト動画を保存し、記録詳細から開ける |
| 通知 | テスト用のLINE・メールだけで確認してから有効化する |

### 5. よくあるインストールエラー

| 症状 | 確認すること |
|---|---|
| `npm` が見つからない | Node.jsをインストール後、PowerShellを開き直す |
| `python` が見つからない | Pythonをインストールし、PATH設定を確認する |
| 画面がAPIエラーになる | FastAPIが8000番で起動しているか確認する |
| GitHub Pagesだけ接続できない | `VITE_API_BASE_URL`、Renderの公開URL、`CORS_ORIGINS` を確認する |
| RenderのBuildが失敗する | Root Directoryが `backend`、Build Commandが `pip install -r requirements.txt` であることを確認する |
| 動画が再デプロイ後に消える | Persistent Diskと `UPLOAD_DIR` の設定を確認する |

## 2026年7月29日現在の実装状況

| 機能 | 状況 | 内容 |
|---|---|---|
| 職員ログイン・権限 | 実装済み | JWT認証、管理者・運転担当・第三者確認のロール制御 |
| 園ごとのデータ分離 | 実装済み | 園児、職員、車両、バス、送迎、通知、監査ログを園単位で分離 |
| 園児・職員・車両・バス設定 | 実装済み | 管理者が設定画面から登録・更新。園児名とQR文字列は一覧から確認・編集可能。車両・便は過去記録を残したまま非表示化 |
| バスごとの通常名簿 | 実装済み | 送迎する園児をバスごとに登録 |
| 当日の園児変更 | 実装済み | 欠席・臨時乗車に合わせて運行中の名簿を変更 |
| QR・手動による乗車・降車 | 実装済み | 園児QR、手入力、園児ごとの手動操作で担当者と時刻を記録 |
| 乗車・降車の工程切替 | 実装済み | 行き便で全員の乗車確認後、自動的に降車確認へ切り替え |
| 人数照合 | 実装済み | 現在の工程に応じて確認済み、対象、未確認の人数を表示 |
| 送迎開始直後の選び直し | 実装済み | 乗降・車内撮影前の送迎だけ中止し、バス選択へ戻れる |
| 車内確認・GPS | 実装済み | 帰りの完了前チェックで車内確認記録を作成し、許可された場合の位置情報を保存 |
| 第三者確認 | 任意機能 | 別職員のID・PINで確認記録を残せる。送迎完了の必須条件ではない |
| 完了前チェックのACTIVE表示 | 実装済み | 全員の降車確認後にACTIVEとなり、車内撮影と送迎完了を有効化 |
| 送迎完了条件 | 実装済み | 全員降車、車内確認記録、5〜30秒の車内撮影1件がそろうまで完了不可。第三者確認は任意 |
| 進行中の送迎再開 | 実装済み | 記録画面からバス名・車両名を確認して再開 |
| 過去記録・監査ログ | 実装済み | 期間検索、乗降、担当者、安全確認、GPS等を閲覧 |
| オフライン乗降記録 | 一部実装 | 端末内に保留し、通信復帰後に重複防止付きで同期 |
| 管理者PINの緊急復旧 | 実装済み | 一時トークンを使い、固定初期PINへ戻さず安全に再設定 |
| 動画証跡 | 一部実装 | 5〜30秒の車内撮影、アップロード、動画ID・保存キー・保存先パスの記録、記録詳細からの動画表示に対応。Render Persistent Disk設定を追加済み |
| AI動画チェック | 土台のみ | AI補助要求と結果表示に対応。実際のAIプロバイダーは未接続のため、人による再確認を促す |
| LINE・メール通知 | 実装済み（実運用確認前） | 保護者・園児・同意管理、バナナ幼稚園（@785ntzvy）QR連携、署名付きWebhook、降車時のLINE／メール併送、履歴・個別再送UI、LINE連携解除 |
| PDF・CSV出力 | 未実装 | 記録帳票の出力は今後 |
| 未確認アラーム | 未実装 | 時間超過時の警告・管理者通知は今後 |

## 現在できること

### 1. 認証と園ごとのデータ分離

- APIログインでJWTを発行し、以降のAPI操作に認証トークンを必須とする
- 職員に `admin`、`operator`、`verifier` のロールを設定する
- 管理操作、通知送信、動画判定などをロールで制限する
- 全レコードに園（organization）IDを持たせ、別の園のデータを取得・操作できないようにする
- PINをPBKDF2-SHA256でハッシュ化して保存する

### 2. 園児・職員・車両・バス・通常名簿の管理

管理者は設定画面から、次の情報を登録・更新できます。

- 園の名称
- 園児と園児QR
- 職員と権限
- 車両
- バス・方向
- バスごとの通常名簿

一般職員による設定変更は、画面だけでなくAPIでも403エラーとして拒否します。

車両と便は、運行済みの過去記録を壊さないように削除扱いではなく非表示化します。非表示化した車両は今後の便選択から外れ、過去の送迎記録には当時の車両名・便名が残ります。同じ車両名を再登録した場合は、非表示化された車両を復元して利用します。

### 3. 当日の送迎名簿

送迎開始時に、選択したバスの通常名簿を当日の送迎へ引き継ぎます。

- 行き：通常名簿の園児を乗車確認の対象として準備し、全員の乗車確認後に画面を降車確認へ自動で切り替える
- 帰り：通常名簿の園児を乗車済みとして開始し、降車確認へ進む
- 欠席や臨時乗車：運行中に当日の園児名簿を変更する
- すでに乗車・降車を確認した園児：誤って名簿から外せない

通常名簿にいない園児をQRで読み取った場合は、そのまま記録せず、当日の園児変更を行うよう案内します。

乗車確認中の「未確認」は `対象人数 - 乗車確認済み人数`、降車確認中の「未確認」は `乗車確認済み人数 - 降車確認済み人数` を表します。これにより、画面上の人数と未降車警告が矛盾しないようにしています。

### 4. 運行記録と安全確認

- 送迎の開始
- 乗降や安全確認をまだ記録していない送迎の中止とバス選択のやり直し
- 園児QRによる乗車・降車
- カメラが使えない場合のQR文字列入力と、職員操作による手動乗降記録
- 乗車数、降車数、未降車数の照合
- 帰りの完了前チェックでの車内確認・GPS記録
- 任意の別職員による第三者確認
- 完了条件の確認
- 日時、担当者、操作内容の監査ログ保存
- 進行中の送迎の再表示・再開
- 期間を指定した過去記録の閲覧

#### 画面の工程遷移とACTIVE表示

1. 行き便は乗車確認から開始します。
2. 対象園児全員の乗車確認が終わると、画面は自動的に帰りの降車確認へ切り替わります。
3. 未降車の園児がいる間、「帰りの完了前チェック」は「降車確認待ち」となり、車内撮影と送迎完了は無効です。
4. 全員の降車確認が終わると、「帰りの完了前チェック」が `ACTIVE` になり、車内撮影を開始できます。
5. 「車内撮影して送迎を完了する」を押し、車内撮影（5〜30秒）を行います。
6. 動画が1件として保存されると、車内確認記録を作成し、そのまま送迎を完了します。

`ACTIVE` は「安全確認が完了した」という意味ではなく、「完了前チェックを開始できる」という意味です。未降車の園児がいる場合、車内確認記録がない場合、または5秒以上の車内撮影が1件もない場合は、送迎を完了できません。第三者確認は記録できますが、送迎完了の必須条件ではありません。

### 5. 通信不能時の乗降記録

通信不能時の乗降記録は端末内に一時保留し、通信復帰後に同期します。`client_event_id`を使い、同じ操作が二重登録されることを防ぎます。

ただし、オフライン状態ですべての機能を利用できるわけではありません。本番導入前に、長時間の圏外、端末再起動、複数端末利用を含む試験が必要です。

### 6. 通知・動画・AI連携の土台

- 保護者のメールアドレス、対象園児、通知同意、LINE希望を管理する
- 「バナナ幼稚園」（`@785ntzvy`）への期限付き・一回限りのQR連携案内をメール送信する
- 署名付きLINE Webhookで連携トークンを照合し、保護者とLINEユーザーIDを紐付ける
- LINE連携の解除、通知同意の撤回、QR案内の再発行を管理画面から行う
- 降車記録を保護者単位で冪等化し、LINEとメールへ別キューで併送する
- LINE／メールの送信結果、再送回数、失敗理由を記録し、管理画面から個別再送する
- 送迎ごとの車内動画を5〜30秒で撮影し、動画証跡として保存する
- 5秒経過後はSTOPでき、30秒で自動終了する
- アップロード時に動画ID、元ファイル名、`storage_key`、保存先パス、形式、AI補助状態を記録する
- 記録詳細の「動画・AI補助」から、認証済みの職員が動画を開ける
- 動画取得APIは同じ園 `organization_id` の動画だけを返す
- AI判定要求の状態を記録する
- AI未接続時は、人による目視確認が必要であることを表示する

#### 動画証跡の保存と表示

記録詳細の「動画・AI補助」には、次の情報を表示します。

- 動画ID
- 保存キー `storage_key`
- 保存先パス
- 形式 `content_type`
- AI補助状態とAI補助メッセージ

動画確認はRender Shellではなく、記録詳細画面の「動画を開く」ボタンから行います。ボタンを押すと、フロントエンドが認証トークン付きで `GET /api/videos/{video_id}/download` を呼び出し、バックエンドが権限確認後に動画ファイルを返します。

バックエンド側では、動画の `organization_id` がログイン職員の園と一致する場合だけ返却します。別の園の動画、存在しない動画、保存先ファイルが消えている動画は取得できません。

Render Free環境ではShellが使えない、または本番サーバー内のファイルを直接確認できない場合があります。そのため、動画確認はアプリの記録詳細画面から行う設計です。

## 目指す運用の流れ

1. 職員が担当するバスと方向を選び、送迎を開始します。
2. 欠席や臨時乗車がある場合は、当日の園児名簿を修正します。
3. 園児が乗車したら、園児QRを読み取ります。
4. 全員の乗車確認後、画面が自動的に降車確認へ切り替わります。
5. 到着後、園児が降車するたびにQRを読み取ります。
6. 乗車人数と降車人数が一致し、完了前チェックが `ACTIVE` になったことを確認します。
7. 職員が座席、足元、座席の下、荷物の陰を目視確認します。
8. 職員が車内を最後尾まで目視確認し、アプリで車内撮影を開始します。
9. 車内を5〜30秒撮影します。5秒経過後はSTOPでき、30秒で自動終了します。
10. 動画が1件として保存されると、車内確認記録と送迎完了を連続して保存します。
11. 必要に応じて、運転担当者とは別の職員が車内と記録を再確認し、第三者確認を任意で残します。
12. 必要に応じて、保護者へ降車完了を通知します。

> この流れは完成時の目標を含みます。5〜30秒撮影と動画証跡保存、動画1件を必須とする送迎完了は実装済みですが、実際のAI判定、通知の画面運用など一部は未完成です。

## 安全上の考え方

まもるバスは、職員による安全確認を支援するシステムです。

- アプリの表示だけで「安全」と判断しない
- 必ず職員が車内の最後尾まで移動して目視確認する
- 必要に応じて、運転担当者とは別の職員が再確認する
- 人数が一致しない場合は完了扱いにしない
- 園児の所在が分からない場合は、園の緊急対応手順に従う
- AIの判定だけで安全確認を完了しない

スマートフォン、QRコード、動画、AIのいずれか一つに頼るのではなく、複数の確認を重ねて見落としを減らすことを目的としています。

## システム構成

```text
職員のスマートフォン
  └─ GitHub Pages（React PWA）
       └─ Render（FastAPI / mamoru-bus-api）
            ├─ データベース
            ├─ 動画証跡（Render Persistent Disk / ローカルファイル保存）
            ├─ 通知Webhook
            └─ LINE Messaging API
```

- フロントエンド：React、TypeScript、Vite、Tailwind CSS、vite-plugin-pwa
- バックエンド：FastAPI、Python、SQLAlchemy
- 開発用データベース：SQLite
- 公開画面：GitHub Pages
- 公開API：Render

## 開発環境

### フロントエンド

```powershell
npm install
npm run dev
```

ビルド確認:

```powershell
npm run build
```

### バックエンド

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

フロントエンドは環境変数 `VITE_API_BASE_URL` でFastAPIのURLを指定します。未指定時は `http://127.0.0.1:8000` を使用します。

バックエンドの単体テスト:

```powershell
cd backend
python -m unittest test_main.py
```
### 生成物の扱い

`outputs/*` は設計書レンダリングなどのローカル生成物です。GitHubへ上げないため、`.gitignore` で除外しています。共有が必要な成果物は、内容を確認したうえで別途管理してください。

## 主な環境変数

| 環境変数 | 用途 |
|---|---|
| `VITE_API_BASE_URL` | フロントエンドが接続するFastAPIのURL |
| `ADMIN_PIN_RECOVERY_TOKEN` | 管理者PINを緊急復旧するための一時トークン |
| `NOTIFICATION_WEBHOOK_URL` | 通知先Webhook |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging APIのアクセストークン |
| `LINE_CHANNEL_SECRET` | LINE Webhook署名検証用Secret |
| `LINE_ORGANIZATION_ID` | LINE連携の対象となる園ID |
| `LINE_BASIC_ID` | 採用するLINE公式アカウントのBasic ID。バナナ幼稚園は `@785ntzvy` |
| `LINE_OFFICIAL_ACCOUNT_NAME` | 画面・メールへ表示する公式アカウント名 |
| `LINE_LINK_TOKEN_PEPPER` | QR連携トークンのハッシュを強化するSecret |
| `LINE_LINK_EXPIRE_HOURS` | QR連携案内の有効時間。既定は24時間 |
| `EMAIL_WEBHOOK_URL` | メール配信アダプターのWebhook URL |
| `EMAIL_FROM_ADDRESS` | メール送信元 |
| `NOTIFICATION_FEATURE_ENABLED` | 降車時の自動配信を有効化するフラグ |
| `UPLOAD_DIR` | 動画ファイルの保存先。未指定時はバックエンドの `./uploads` |

`render.yaml` では、Render Persistent Diskを `/var/data` にマウントし、`UPLOAD_DIR=/var/data/mamoru-bus-uploads` を指定しています。Renderの通常ファイル領域やローカル保存だけにすると、再デプロイやインスタンス再作成で動画ファイルが消える可能性があります。本番運用ではPersistent Diskの容量、保存期限、削除手順、バックアップ、またはS3/R2等のオブジェクトストレージ連携を別途決めてください。

> [!WARNING]
> 本番用のトークン、Secret、PINは、Git、README、画面キャプチャ、ブラウザの保存領域へ記録しないでください。動作確認用の認証情報も公開リポジトリには記載しないでください。

## Renderへのインストール・環境変数設定

Renderでは、FastAPI、PostgreSQL、動画保存用Persistent Diskを管理します。ここでいう「インストール」は、PCへソフトを入れる作業ではなく、GitHubのソースからRender上にAPIとDBを作成して接続する作業です。

- 既存環境: [まもるバス Render Environment](https://dashboard.render.com/project/prj-d9gumscvikkc73a61qpg/environment/evm-d9gumscvikkc73a61qq0)
- 構成定義: [render.yaml](render.yaml)
- 公式資料: [Render Blueprint](https://render.com/docs/infrastructure-as-code)、[環境変数とSecret](https://render.com/docs/configure-environment-variables)

> [!IMPORTANT]
> `render.yaml` にはPostgreSQLのplan `starter` と1GBのPersistent Diskが定義されています。新規作成やプラン変更の前に、Render画面に表示される月額料金を必ず確認してください。Free Web ServiceではPersistent Diskを使用できず、通常ファイル領域へ保存した動画は再デプロイ等で失われます。

### 0. 事前準備

次を準備します。

- Renderへログインできるアカウント
- GitHubの `kazunyon/child_presence_detection` をRenderから読み取れる権限
- LINE Developersから取得するChannel access tokenとChannel secret
- 本番で使用する園のDB上のorganization ID
- メール配信アダプターのWebhook URLと送信元アドレス
- Secretを保管するパスワードマネージャー

> [!WARNING]
> Channel access token、Channel secret、JWT Secret、PIN、復旧トークンは、GitHub、README、Issue、画面キャプチャへ貼り付けないでください。RenderではSecretとして保存します。

### 1. 既存環境を確認する場合

1. [まもるバス Render Environment](https://dashboard.render.com/project/prj-d9gumscvikkc73a61qpg/environment/evm-d9gumscvikkc73a61qq0)を開きます。
2. Environment内にWeb Serviceの **mamoru-bus-api** とPostgreSQLの **mamoru-bus-db** があることを確認します。
3. **mamoru-bus-api → Settings** で、Repositoryが `kazunyon/child_presence_detection`、Branchが `main`、Root Directoryが `backend` であることを確認します。
4. Build Commandが `pip install -r requirements.txt`、Start Commandが `uvicorn main:app --host 0.0.0.0 --port $PORT` であることを確認します。
5. Health Check Pathが `/health` であることを確認します。
6. **mamoru-bus-api → Disks** で、Persistent Diskが `/var/data` にマウントされていることを確認します。
7. **mamoru-bus-api → Environment** で、後述の環境変数が存在することを確認します。Secretの値は表示・共有しません。

### 2. 新しいRender環境を作る場合（Blueprint）

1. Render Dashboardで **New → Blueprint** を選びます。
2. GitHubを接続し、リポジトリ **kazunyon/child_presence_detection** を選びます。Privateリポジトリが一覧に出ない場合は、RenderのGitHub Appへ対象リポジトリの読取権限を追加します。
3. Blueprint Pathはリポジトリ直下の `render.yaml` を指定します。
4. 作成予定の **mamoru-bus-api**、**mamoru-bus-db**、Persistent Disk、料金プランを確認します。
5. `sync: false` の環境変数を入力します。まだ通知試験を始めない場合も、`NOTIFICATION_FEATURE_ENABLED` は `false` のままにします。
6. **Apply / Deploy Blueprint** を実行し、作成完了まで待ちます。
7. Blueprint作成後、Environment画面で各サービスの状態が **Live / Available** になったことを確認します。

`render.yaml` により、次が自動設定されます。

| 対象 | 自動設定される内容 | 導入者が確認すること |
|---|---|---|
| Web Service | Python、Root Directory、Build／Start Command、Health Check | RepositoryとBranchが正しい |
| PostgreSQL | `mamoru-bus-db` を作成 | plan、容量、接続状態 |
| DB接続 | `DATABASE_URL` をDBから連携 | 手入力で上書きしていない |
| CORS | `https://kazunyon.github.io` を許可 | 別ドメインを使う場合は追加 |
| 動画保存 | `/var/data` をマウントし、`UPLOAD_DIR` を設定 | Diskが付いている、容量に余裕がある |
| Secret | `JWT_SECRET` と `LINE_LINK_TOKEN_PEPPER` を生成 | 再作成・上書きを安易に行わない |

### 3. Renderへ登録する環境変数

登録場所は **mamoru-bus-api → Environment** です。値を変更した場合は、Save後の再デプロイ完了まで待ちます。

| 環境変数 | 値の取得元・設定値 | Secret扱い | 確認内容 |
|---|---|---:|---|
| `DATABASE_URL` | `mamoru-bus-db` から自動連携 | はい | PostgreSQL接続文字列。手入力しない |
| `JWT_SECRET` | Render自動生成、または32文字以上のランダム値 | はい | 変更すると既存ログインが無効になる |
| `CORS_ORIGINS` | `https://kazunyon.github.io` | いいえ | 末尾の不要な `/` を付けない |
| `ENVIRONMENT` | `production` | いいえ | 本番動作になっている |
| `UPLOAD_DIR` | `/var/data/mamoru-bus-uploads` | いいえ | Diskのマウント先配下である |
| `TOKEN_EXPIRE_MINUTES` | `480` | いいえ | JWTの有効時間（分） |
| `ADMIN_PIN_RECOVERY_TOKEN` | 緊急復旧時だけ作るランダム値 | はい | 復旧後は削除する |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE DevelopersのMessaging APIタブ | はい | 対象チャネルのトークンである |
| `LINE_CHANNEL_SECRET` | LINE DevelopersのBasic settings | はい | 対象チャネルのSecretである |
| `LINE_BASIC_ID` | `@785ntzvy` | いいえ | バナナ幼稚園のBasic IDと一致 |
| `LINE_OFFICIAL_ACCOUNT_NAME` | `バナナ幼稚園` | いいえ | 案内メール・画面の表示名 |
| `LINE_LINK_TOKEN_PEPPER` | Render自動生成、または32文字以上のランダム値 | はい | DBへ保存する連携トークンの保護用 |
| `LINE_LINK_EXPIRE_HOURS` | `24` | いいえ | QR／連携リンクの有効時間 |
| `LINE_ORGANIZATION_ID` | 本番DBで確認した園ID | いいえ | 推測で `1` と決めない |
| `EMAIL_WEBHOOK_URL` | 採用したメール配信アダプター | はい | HTTPSの送信先URL |
| `EMAIL_FROM_ADDRESS` | 園または検証用の送信元 | いいえ | 配信事業者で使用可能なアドレス |
| `NOTIFICATION_FEATURE_ENABLED` | 初期は `false` | いいえ | 結合試験・園責任者承認後だけ `true` |

### 4. GitHub PagesからRender APIへ接続する

1. **mamoru-bus-api → Settings** で公開URL（例: `https://mamoru-bus-api.onrender.com`）を確認します。
2. ブラウザで `https://<Render API URL>/health` を開き、正常応答を確認します。
3. GitHubリポジトリで **Settings → Secrets and variables → Actions → Variables** を開きます。
4. Repository variable `VITE_API_BASE_URL` を作成し、値をRender API URLにします。末尾の `/` は付けません。
5. GitHub PagesのWorkflowを再実行するか、`main` の次回更新で再デプロイします。
6. 公開画面を再読み込みし、ログインとAPI通信を確認します。

`VITE_API_BASE_URL` はブラウザへ埋め込まれる公開URLなのでGitHub Actionsの **Variable** に登録します。LINEのTokenやSecretは、GitHub Actionsにもフロントエンドにも登録しません。

### 5. Renderデプロイ後の確認

1. **Events / Deploys** で最新デプロイが成功していることを確認します。
2. **Logs** でPython依存関係、DB接続、マイグレーション、Uvicorn起動のエラーがないことを確認します。
3. `/health` が応答することを確認します。
4. アプリからログインし、設定画面と過去記録を開けることを確認します。
5. 5〜30秒のテスト動画を保存し、記録詳細の「動画を開く」から再生できることを確認します。
6. LINE設定後は、LINE DevelopersのVerifyとテストアカウントの連携確認を行います。

### 6. Renderで失敗した場合

| 症状 | 主な確認箇所 |
|---|---|
| Repositoryが選べない | Render GitHub AppのRepository access |
| Build Failed | Deploy Log、`backend/requirements.txt`、Root Directory |
| `/health` が404 | API URL、Start Command、Health Check Path |
| DB接続エラー | `mamoru-bus-db` の状態、`DATABASE_URL` の自動連携 |
| 公開画面だけAPIエラー | `VITE_API_BASE_URL`、`CORS_ORIGINS`、GitHub Pages再デプロイ |
| 動画が再デプロイ後に消える | Persistent Disk、マウント先、`UPLOAD_DIR` |
| 環境変数を直しても変わらない | Save後の再デプロイ完了、変数名の綴り |

## 管理者PINの安全な復旧

管理者がログインできず、ほかの管理者もいない場合だけ使う緊急復旧手順です。既知の初期PINへ戻す機能ではありません。

1. パスワードマネージャー等で32文字以上の十分に長いランダム文字列を作成します。
2. Renderの環境変数に `ADMIN_PIN_RECOVERY_TOKEN` として登録し、再デプロイを待ちます。
3. ログイン画面の「管理者PINを復旧する」を開き、復旧トークンと新しい8文字以上のPINを入力します。
4. 職員ID `3` と新しいPINでログインできることを確認します。
5. **Renderから `ADMIN_PIN_RECOVERY_TOKEN` を削除し、再デプロイします。**

同じ復旧トークンはデータベース上でも一度しか使用できません。復旧操作は監査ログに `auth.admin_pin_recovery` として残ります。

## LINE Developersのインストール・Messaging API設定

採用するLINE公式アカウントは **バナナ幼稚園（`@785ntzvy`）** です。ここでいう「インストール」は、LINE公式アカウントでMessaging APIを有効化し、LINE DevelopersとRenderをWebhookで接続する作業です。

- LINE Developers Console: [https://developers.line.biz/console/](https://developers.line.biz/console/)
- LINE Official Account Manager: [https://manager.line.biz/](https://manager.line.biz/)
- 公式手順: [Messaging APIを始める](https://developers.line.biz/en/docs/messaging-api/getting-started/)、[Botを構築する](https://developers.line.biz/en/docs/messaging-api/building-bot/)

> [!IMPORTANT]
> 現在は、LINE Developers ConsoleからMessaging APIチャネルを直接新規作成できません。先にLINE公式アカウントを作成し、LINE Official Account ManagerでMessaging APIを有効化すると、LINE Developers側にチャネルが作成されます。

### 0. 既存の「バナナ幼稚園」を使うか確認する

新しい公式アカウントを作る前に、既存の `@785ntzvy` を使えるか確認します。

1. [LINE Official Account Manager](https://manager.line.biz/)へログインし、**バナナ幼稚園** が表示されることを確認します。
2. [LINE Developers Console](https://developers.line.biz/console/)へ同じBusiness IDでログインします。
3. 対象Providerを開き、バナナ幼稚園のMessaging APIチャネルが表示されることを確認します。
4. **Basic settings** の権限で自分がAdminであることを確認します。
5. **Messaging API** タブのBasic IDが `@785ntzvy` であることを確認します。

既存チャネルが確認できた場合は、新規作成せず「2. チャネル情報をRenderへ登録する」へ進みます。見つからない場合、別のBusiness IDでログインしていないか、Providerまたは公式アカウントの管理権限が付いているかを確認します。

### 1. LINE公式アカウントを新規作成する場合

既存の `@785ntzvy` を利用する場合、この手順は不要です。

1. LINE Business IDを準備し、[LINE Official Account Manager](https://manager.line.biz/)でLINE公式アカウントを作成します。
2. 作成した公式アカウントを開き、**設定 → Messaging API** からMessaging APIの利用を有効にします。
3. 管理するProviderを選択します。Providerは園または運営会社を表す単位として、将来の担当者管理も考えて選びます。
4. Provider確定後、[LINE Developers Console](https://developers.line.biz/console/)へ同じBusiness IDでログインします。
5. 選択したProviderの中にMessaging APIチャネルが作成されたことを確認します。

> [!CAUTION]
> LINE公式アカウントへ割り当てたProviderは、後から変更・解除できません。個人用Providerを安易に選ばず、園または運営会社の管理方針を決めてから確定してください。

### 2. チャネル情報をRenderへ登録する

LINE Developers Consoleで **Provider → バナナ幼稚園のMessaging APIチャネル** を開きます。

| LINE Developersの場所 | 取得する値 | Render環境変数 | 注意 |
|---|---|---|---|
| **Basic settings** | Channel secret | `LINE_CHANNEL_SECRET` | Secretとして保存。再発行すると旧Secretは無効 |
| **Messaging API** | Channel access token | `LINE_CHANNEL_ACCESS_TOKEN` | Secretとして保存。READMEへ貼らない |
| **Messaging API** | Basic ID | `LINE_BASIC_ID` | バナナ幼稚園は `@785ntzvy` |
| 運用で決定 | 表示名 | `LINE_OFFICIAL_ACCOUNT_NAME` | `バナナ幼稚園` |
| Renderで生成 | ランダム値 | `LINE_LINK_TOKEN_PEPPER` | LINE側には登録しない |
| 本番DBで確認 | 園ID | `LINE_ORGANIZATION_ID` | 推測値を使わない |

Channel access tokenが未発行の場合は、Messaging APIタブのChannel access token欄から発行します。現在の実装・検証で使用するトークン方式を決め、失効・再発行時の交換手順も記録してください。再発行した場合はRenderの値を更新し、再デプロイします。

### 3. Webhook URLを接続する

1. Renderで **mamoru-bus-api** の公開URLを確認します。
2. LINE Developersで **Messaging API → Webhook settings → Webhook URL** を開きます。
3. 次のURLを登録します: `https://<Render API URL>/api/integrations/line/webhook`
4. **Update** で保存します。
5. **Verify** を押し、成功することを確認します。
6. **Use webhook** を有効にします。
7. RenderのLogsで404、500、署名検証エラーがないことを確認します。

> [!NOTE]
> Webhook URLはGitHub PagesのURLではありません。LINEからのPOSTを受けるFastAPIのRender URLを指定します。URLはHTTPSで、外部から到達できる必要があります。

このAPIは `x-line-signature` と `LINE_CHANNEL_SECRET` を使って署名を検証します。署名検証を外したり、LINEの送信元IPだけで安全性を判断したりしないでください。

### 4. LINE Official Account Manager側を確認する

1. [LINE Official Account Manager](https://manager.line.biz/)でバナナ幼稚園を開きます。
2. **設定 → 応答設定** で、Messaging APIを利用する運用になっていることを確認します。
3. あいさつメッセージや応答メッセージを使用する場合は、アプリの案内と重複・矛盾しない文章にします。
4. テスト担当者が公式アカウントを友だち追加できることを確認します。

### 5. メール配信アダプターを設定する

LINE希望者にもメールを必須とし、降車完了はLINEとメールへ別々に併送します。

1. メール配信アダプターのHTTPS URLをRenderの `EMAIL_WEBHOOK_URL` に登録します。
2. 使用可能な送信元を `EMAIL_FROM_ADDRESS` に登録します。
3. テスト用メールへ、件名、本文、連携URL、QR画像が届くことを確認します。
4. メール失敗時に同じ期限付きリンクを使い回さず、管理画面から新しいQR案内を再発行します。

### 6. LINE連携の結合テスト

実在する保護者へ送信する前に、園のテスト用メールアドレスとLINEアカウントで確認します。

1. Renderの `NOTIFICATION_FEATURE_ENABLED=false` を維持します。
2. 管理画面でテスト保護者、メール、園児、通知同意、LINE希望を登録します。
3. 「QR案内を発行」を押し、メールを受信します。
4. テスト用LINEアカウントでバナナ幼稚園を友だち追加します。
5. メールのQRまたはリンクを使い、LINEトークで表示された `連携 <token>` を送信します。
6. 管理画面で対象保護者がLINE連携済みになったことを確認します。
7. テスト送迎で降車記録を作成し、LINEとメールがそれぞれ1通届くことを確認します。
8. 通知履歴で各経路の `sent`、失敗理由、再送回数を確認します。
9. LINEだけ失敗、メールだけ失敗、個別再送、連携解除、同意撤回を確認します。
10. 園責任者が結果を確認した後、Renderの `NOTIFICATION_FEATURE_ENABLED=true` を保存し、再デプロイします。
11. 有効化後もテスト保護者で最終確認してから実在する保護者を登録します。

### 7. LINEで失敗した場合

| 症状 | 主な確認箇所 |
|---|---|
| Provider／チャネルが見つからない | 同じBusiness ID、ProviderのAdmin権限、公式アカウント側のMessaging API有効化 |
| Verifyが失敗する | Render APIがLive、Webhook URLの綴り、HTTPS、末尾パス |
| 署名エラー | 対象チャネルのChannel secret、再発行の有無、Render再デプロイ |
| 401／403で送信失敗 | Channel access tokenの対象・失効・再発行 |
| 友だち追加しても連携されない | Use webhook、Render Logs、`連携 <token>` の期限 |
| 別の園へ紐付く | `LINE_ORGANIZATION_ID` と本番DBの園ID |
| LINEは届くがメールが届かない | `EMAIL_WEBHOOK_URL`、`EMAIL_FROM_ADDRESS`、メール側ログ |
| 設定後も自動通知されない | `NOTIFICATION_FEATURE_ENABLED`、再デプロイ、通知同意 |

連携トークンの平文はDBへ保存しません。QR／連携リンクは期限付き・一回限りです。LINEとメールの片方が成功しても、もう片方の結果は別に記録します。

## 現在できないこと・導入前の必須対応

本アプリは開発途中です。園児の安否確認、事故防止の最終確認、法令上必要な記録にはまだ使用しないでください。必ず職員による目視確認と園の緊急対応手順を優先してください。

- 第三者確認は任意記録であり、職員IDとPINによる確認に留まる。運転者本人との厳密な分離や強い本人確認は未完成
- 車内撮影は5〜30秒で保存できるが、スマホ・ブラウザ・通信状態によってアップロード失敗や再撮影が必要になる場合がある
- AIプロバイダー未接続のため、実際の子ども検出・動画判定は未実施
- LINE・メール通知のコードと管理画面は実装済みだが、LINE Developersの本番チャネル照合、メール配信事業者設定、実機・実回線・実運用試験は未実施
- 動画は現在ファイル保存。Render Persistent Disk設定は追加済みだが、本番では暗号化、保存期限、削除手順、アクセス記録、バックアップ設計が必要
- 多要素認証、トークン失効、通常のPIN変更、PDF・CSV出力、バックアップ・障害復旧は未実装
- 本格的なDBマイグレーション、負荷試験、脆弱性診断、実園での運用評価は未実施

## GitHub Pagesへの公開

`main`ブランチへ変更を反映すると、GitHub Actionsがフロントエンドをビルドし、GitHub Pagesへ公開します。

初回だけ、GitHubリポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に設定してください。

## 今後の優先開発

1. 動画保存の本番運用設計（容量、保存期限、削除手順、バックアップ、暗号化、S3/R2等の検討）
2. 任意の第三者確認を運用に組み込む場合の本人確認強化
3. 未確認アラームと管理者通知
4. LINE／メール通知のテストアカウントによる結合・実機試験と園運用承認
5. AI動画チェックの実プロバイダー接続
6. PDF・CSV出力とバックアップ
7. 動画の暗号化保存とアクセス記録
8. 権限・監査・暗号化を含む本番セキュリティ対応
9. 実際の園での操作確認と安全性評価

## 注意事項

本システムは開発中であり、現時点では送迎バスの安全装置や法令上必要な装置を置き換えるものではありません。実証・本番導入前に、園の安全管理責任者、関係機関、専門家と運用方法を確認してください。

