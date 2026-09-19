# Step 4：用 Python 取得第一批真實資料

## 這一步要完成什麼

這一步讓專案第一次透過自己的 Python 程式取得真實 NYC Open Data，而不依賴瀏覽器手動下載，也不需要 Snowflake 帳號。

完成後，我們有一個 command 可以：

1. 選擇 permits、complaints 或 violations；
2. 指定最多下載幾列；
3. 把大型結果分成多個 pages 取得；
4. 遇到暫時性網路問題時自動 retry；
5. 將每筆來源紀錄寫成 JSON Lines；
6. 產生記錄來源、時間、列數和檔案指紋的 manifest；
7. 不完整下載時不覆蓋原本成功的輸出。

## 為什麼先做本機小型 extraction

如果一開始就同時連接 NYC Open Data 和 Snowflake，出錯時很難判斷問題來自：

- 網路；
- 來源 Application Programming Interface；
- Python 程式；
- Snowflake credentials；
- database permissions；
- table definition。

先完成 bounded local extraction（有上限的本機擷取），可以隔離前半段問題。我們先證明「Python 能可靠取得來源資料」，下一步才處理 warehouse loading。

## 實際 command

```text
nyc-dob-extract complaints --limit 25
```

這個 command 表示：

- 執行 `nyc-dob-extract` 程式；
- 選擇 `complaints` dataset；
- 最多取得 25 rows；
- 使用預設輸出 `work/samples/complaints.jsonl`。

測試分頁時使用：

```text
nyc-dob-extract complaints --limit 5 --page-size 2
```

五筆資料、每頁最多兩筆，因此總共需要三頁：2 + 2 + 1。

## 新名詞解釋

### Python module 與 package

- Module（模組）通常是一個 `.py` Python 檔案。
- Package（套件）是一組有共同用途、可以一起 import 的 modules。

本專案的 `nyc_dob_ingestion` 是 package，`socrata.py` 和 `extract.py` 是其中的 modules。

### Hypertext Transfer Protocol

Hypertext Transfer Protocol 是網路上 client 和 server 溝通的協定，通常簡寫為 HTTP。HTTPS 是加密版本，能保護傳輸內容並驗證伺服器身分。

本專案向以下 HTTPS endpoint 發出 request：

```text
https://data.cityofnewyork.us/resource/eabe-havv.json
```

### Client 與 server

- Client（客戶端）是主動發出 request 的程式；這裡是我們的 Python 程式。
- Server（伺服器）接收 request 並傳回 response；這裡是 NYC Open Data。

### GET request

GET 是 Hypertext Transfer Protocol method，用來要求讀取資源。這個 extraction 只讀取公開資料，不會修改 NYC Open Data。

### Query parameter

Query parameter（查詢參數）是附加在網址上的控制條件。本程式傳送：

- `$limit`：本頁最多回傳幾列；
- `$offset`：從前面略過幾列；
- `$order`：用什麼順序回傳。

### Pagination

Pagination（分頁）是把大量結果拆成多次 request。

假設要取得五筆、page size 是二：

| Request | Limit | Offset | 取得位置 |
|---|---:|---:|---|
| Page 1 | 2 | 0 | 第 1–2 筆 |
| Page 2 | 2 | 2 | 第 3–4 筆 |
| Page 3 | 1 | 4 | 第 5 筆 |

Socrata 官方提醒，分頁必須指定穩定排序，否則不同 pages 可能重複或遺漏。本專案改用平台建議的 `:id` 排序。

### Offset pagination 的限制

即使排序穩定，如果來源在長時間下載期間新增或刪除資料，後續 offset 仍可能移動。因此 Step 4 只用於 bounded samples。完整 production extract 還需要評估 snapshot export、watermark 或 checkpoint strategy。

### Timeout

Timeout（逾時）限制程式等待伺服器回應的時間。如果沒有 timeout，網路異常時程式可能一直等待。

### Status code

HTTP status code 是伺服器回報 request 結果的數字：

- `200` 通常表示成功；
- `400` 表示 request 不符合要求；
- `404` 表示資源不存在；
- `429` 表示 request 太頻繁；
- `500` 系列通常表示伺服器暫時發生問題。

程式使用 `raise_for_status()`，讓不成功的 HTTP response 明確失敗，而不是把錯誤訊息當成資料。

### Retry 與 backoff

Retry（重試）是在可能是暫時性問題時重新發出 request。Backoff（退避）是在每次重試前等待一段時間，避免立刻持續攻擊仍忙碌的 server。

本程式對 `429`、`500`、`502`、`503` 和 `504` 最多自動 retry 三次。

### Session

Requests Session 是可重複使用連線和共用 headers 的 client object。它能提供 connection pooling，避免每一頁都重新建立完整連線。

### Header、User-Agent 與 application token

Header 是 HTTP request 的附加資訊。

- `User-Agent` 說明是哪個 client 發出 request；
- `X-App-Token` 可提供 NYC Open Data application token。

Application token 不是 Snowflake password，也不是用來修改公開資料。它能讓資料平台辨識應用程式，通常有助於 request 管理。程式從 environment variable 讀取，沒有寫死在原始碼。

### JavaScript Object Notation Lines

JavaScript Object Notation Lines 通常寫成 JSON Lines 或 JSONL。檔案中的每一行都是一個獨立 JSON object：

```text
{"bin":"1006289","complaint_number":"1000006","status":"CLOSED"}
{"bin":"1006289","complaint_number":"1000008","status":"CLOSED"}
```

與一個巨大 JSON array 相比，JSON Lines 比較容易逐行寫入、逐行讀取和處理大型資料。

### Manifest

Manifest（清單／執行摘要）描述 extraction 結果，而不是存放主要資料。它記錄：

- dataset name 和 ID；
- source URL；
- extraction timestamp；
- requested limit；
- row count 和 page count；
- SHA-256；
- output path。

### Hash 與 SHA-256

Hash（雜湊）把任意內容轉換成固定長度指紋。SHA-256 是 Secure Hash Algorithm 256-bit 的簡稱。

如果檔案任何一個字元改變，SHA-256 通常也會改變。它可以驗證檔案內容是否和 manifest 記錄一致，但不是用來加密或隱藏資料。

### Atomic write

Atomic write（原子寫入）表示先把資料寫進 temporary file，全部成功後再一次替換正式輸出。如果下載到一半失敗，正式輸出不會只剩不完整的半份檔案。

### Command-line interface

Command-line interface（命令列介面，常簡寫為 CLI）讓使用者透過文字 command 執行程式。本專案用 Python `argparse` 驗證 dataset、limit、page size 和 output path。

### Dependency injection 與 fake object

Dependency injection（依賴注入）表示把程式依賴的物件從外部傳入，而不是在內部永遠建立固定物件。

`SocrataClient` 可以接收一個 session，因此 unit test 能傳入 FakeSession。Fake object（假物件）模擬外部系統，不需要真的連網，就能測試分頁參數和回應處理。

## 程式檔案責任

### `datasets.py`

保存三個 dataset 的穩定 ID、Snowflake target table 和排序規則。所有 dataset 使用 Socrata 建議的 `:id` 排序。

### `socrata.py`

負責：

- 建立 HTTP Session；
- 設定 User-Agent 與 application token；
- 設定 retry/backoff；
- 產生 `$limit`、`$offset`、`$order`；
- 檢查 HTTP status；
- 確認 response 是 JSON array；
- 一頁一頁回傳 rows。

### `extract.py`

負責：

- 建立輸出目錄；
- 將 rows 寫成 JSON Lines；
- 計算 SHA-256；
- 使用 atomic write；
- 建立 manifest。

### `extract_cli.py`

負責解析使用者 command，選擇 dataset，讀取 environment variable，並呼叫 extraction logic。

這樣拆分是 separation of concerns（關注點分離）：網路、檔案寫入和使用者介面各自負責不同事情，更容易測試。

## 本次真實執行結果

2026-09-19 成功下載：

| Dataset | Rows | JSON valid | SHA-256 verified |
|---|---:|---|---|
| Permits | 25 | Yes | Yes |
| Complaints | 25 | Yes | Yes |
| Violations | 25 | Yes | Yes |

另外執行五筆 complaints、每頁兩筆的測試：

- row count：5
- page count：3
- 證明多頁下載邏輯能正常工作

所有輸出都在 `work/samples/`，不會提交到 Git。

## 自動測試

測試數量由 3 個增加到 7 個，目前全部通過。

新增測試驗證：

- 多頁下載的 limit 與 offset；
- 使用穩定的 `:id` 排序；
- 拒絕 0 或超過 50,000 的 page size；
- JSON Lines 內容；
- manifest 的 dataset ID、row count、page count 和 SHA-256 格式。

## 目前刻意保留的限制

- 尚未執行完整六百多萬列下載；
- 尚未建立 incremental extraction；
- 尚未做 source schema drift detection；
- 尚未加入中斷後從 checkpoint 恢復；
- 尚未將資料載入 Snowflake；
- raw extraction 不改欄位名稱、不轉日期、不修正 status。

Incremental extraction 是只取得上次成功之後新增或變更的資料。Schema drift 是來源欄位被新增、刪除或改變型態。Checkpoint 是記錄進度，讓中斷後能從已完成位置繼續。

這些會在理解來源更新行為後逐步加入，不在 Step 4 一次塞進去。

## 知識點總結

- 先隔離 extraction，再處理 warehouse loading，較容易診斷問題。
- 大型 Application Programming Interface 結果需要 pagination。
- 分頁必須有穩定排序，但 offset 對持續變動的來源仍有限制。
- Production network code 應設定 timeout、status check 和有限 retry。
- JSON Lines 適合逐列處理與大型資料。
- Manifest 和 SHA-256 讓一次 extraction 可被驗證與追蹤。
- Atomic write 避免失敗時留下看似成功的不完整輸出。
- Dependency injection 讓網路程式可以不連網測試。
- Raw layer 應保存來源語意；資料清理屬於後續 transformation。

## 官方文件

- [Socrata：Paging through Data](https://dev.socrata.com/docs/paging.html)
- [Socrata：LIMIT clause](https://dev.socrata.com/docs/queries/limit.html)
- [Socrata：OFFSET clause](https://dev.socrata.com/docs/queries/offset)
- [Requests：Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
- [Requests：Advanced usage and timeouts](https://requests.readthedocs.io/en/latest/user/advanced/)
- [Python：json encoder and decoder](https://docs.python.org/3/library/json.html)
- [Python：argparse](https://docs.python.org/3/library/argparse.html)
- [Python：hashlib](https://docs.python.org/3/library/hashlib.html)

## 面試題與參考答案

### 1. How did you make the source extraction reliable?

I added explicit timeouts, HTTP status validation, bounded retries with backoff for rate limits and transient server errors, stable Socrata ordering, page-size validation, atomic file writes, and an extraction manifest containing row counts and a SHA-256 digest.

### 2. Why did you use JSON Lines instead of one JSON array?

JSON Lines allows records to be written and processed incrementally without holding the full dataset in memory. Each line is independently parseable, which is useful for large extracts and failure diagnosis.

### 3. How did you test pagination without repeatedly calling the live API?

I injected a fake HTTP session into the Socrata client. The test returns controlled pages and verifies the generated limit, offset, order, and timeout values without requiring network access.

### 4. Why use `:id` for ordering?

Socrata warns that paged results are not implicitly ordered and recommends an explicit order, at minimum `:id`. The previous business-field order was not unique, so it could not guarantee stable page boundaries.

### 5. Is offset pagination safe for the full production dataset?

Not completely. Stable ordering prevents arbitrary ordering, but a dataset that changes during a long extraction can still shift offsets. The bounded sample command is reliable for inspection; the production strategy still needs snapshot or incremental-watermark design.

### 6. What is the purpose of the manifest?

The manifest makes each extract auditable. It records the source dataset, extraction time, requested and actual counts, number of pages, output path, and file digest so the result can be verified later.

### 7. Why do you keep raw extraction separate from data cleaning?

The raw layer should preserve what the source delivered for auditability. Parsing dates, normalizing statuses, and applying business rules belong in tested transformation models where the logic is visible and reproducible.

### 8. Why is retrying every error dangerous?

Some failures are permanent, such as an invalid query or missing resource. Retrying those only creates more traffic and delays the real error. The client retries rate limits and transient server errors, while client errors fail immediately.

## 自我檢查

進入下一步以前，應能回答：

- 為什麼要使用 pagination？
- limit、offset 和 order 各自控制什麼？
- timeout、retry 和 backoff 有什麼不同？
- JSON Lines 與一般 JSON array 有什麼差異？
- manifest 和 SHA-256 解決什麼問題？
- 為什麼使用 atomic write？
- 為什麼 Step 4 還不能直接稱為 production full-load pipeline？
