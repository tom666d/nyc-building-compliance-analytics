# Step 2：認識 NYC Open Data 與原始資料

## 這一步要完成什麼

這一步不急著把資料放進 Snowflake。我們先直接閱讀 New York City Open Data（紐約市開放資料平台，以下簡稱 NYC Open Data）的真實資料，回答：

1. 三個資料集各有多少資料？
2. 每一列大致代表什麼？
3. 有哪些可以識別紀錄的欄位？
4. 日期、狀態和建築識別碼是否一致？
5. 原先的資料模型假設是否能被真實資料支持？

這個過程叫做 source profiling（來源資料剖析）。先理解資料再建模，可以避免把錯誤假設寫進整條資料管線。

## 我實際做了什麼

我直接呼叫三個官方資料集的 Application Programming Interface（應用程式介面，以下簡稱 API），取得：

- metadata；
- 欄位名稱與資料型態；
- 即時資料筆數；
- 少量真實樣本；
- Building Identification Number 的涵蓋情況；
- 主要狀態的分布；
- 自然鍵是否重複。

只下載少量樣本做人工檢查，再用伺服器端聚合查詢計算全體筆數。這樣不用先下載超過六百萬列資料，也能有效驗證重要假設。

## 三個資料集

Profile date：2026-09-19，America/Chicago 時區。這些資料每日更新，所以筆數不是永久不變的常數。

| 資料集 | Dataset ID | 當時筆數 | 欄位數 | 每列大致代表 |
|---|---:|---:|---:|---|
| DOB NOW: Build – Approved Permits | `rbx6-tga4` | 1,002,770 | 46 | 一筆 permit 與 work type 的來源紀錄，但實際 grain 尚待釐清 |
| DOB Complaints Received | `eabe-havv` | 3,133,744 | 15 | 一筆 complaint 來源紀錄 |
| DOB Violations | `3h2n-5cm9` | 2,476,860 | 18 | 一筆舊系統 violation 紀錄 |

三個來源合計 6,613,374 列。

## Application Programming Interface 是什麼

Application Programming Interface（應用程式介面）是讓一個程式依照約定向另一個系統要求資料或功能的介面。

人在瀏覽器中看 NYC Open Data 網頁；Python 程式則可以向 API endpoint 發出 request，取得機器容易處理的資料。

例如 complaints 的 endpoint：

```text
https://data.cityofnewyork.us/resource/eabe-havv.json
```

- `data.cityofnewyork.us` 是資料平台的 domain；
- `/resource/` 表示要存取資料資源；
- `eabe-havv` 是穩定的 dataset identifier；
- `.json` 表示希望取得 JavaScript Object Notation 格式的結果。

## 新名詞解釋

### Open data

Open data（開放資料）是政府或組織以可公開取得、使用和分析的方式發布的資料。公開不代表完美，也不代表所有欄位都有相同品質。

### Dataset

Dataset（資料集）是一組相關的資料。表格式資料通常由 rows 和 columns 組成。

### Row 與 column

- Row（列）通常代表一筆紀錄或一個業務事件。
- Column（欄）代表每筆紀錄的一項屬性，例如 complaint number、status 或 date entered。

不能只看到一列就假設它代表一個 permit。必須用文件和資料剖析確認 grain。

### Endpoint

Endpoint（端點）是 API 中可以接收 request 的特定網址。不同 endpoint 可以回傳 metadata、資料紀錄或其他資源。

### Request 與 response

- Request（請求）是我們送給 API 的要求，例如「請回傳五列資料」。
- Response（回應）是 API 傳回的結果與狀態。

### JavaScript Object Notation

JavaScript Object Notation 是常見的文字資料交換格式，通常簡寫為 JSON。它使用 key-value pairs（鍵值配對）表示資料，例如：

```json
{
  "complaint_number": "1000006",
  "status": "CLOSED",
  "bin": "1006289"
}
```

### Metadata

Metadata（詮釋資料）是「描述資料的資料」，例如資料集名稱、更新時間、欄位名稱和欄位型態。

### Schema

Schema（結構定義）描述資料有哪些欄位、欄位型態和關係。來源 schema 可能改變，因此資料管線需要偵測重要變更。

### Data type

Data type（資料型態）說明一個值應如何解讀，例如 text、number 或 date。看起來像日期的文字不一定已經是 date type。

### Natural key

Natural key（自然鍵）是來源業務中原本就存在、可用來識別一筆紀錄的欄位或欄位組合，例如 complaint number。

### Null

Null 表示沒有值或未知。它和數字 0、空字串、字串 `UNKNOWN` 不相同。

### Cardinality

Cardinality（基數）在這裡表示欄位有多少不同值，或兩類資料之間的數量關係。例如一個 permit 是否對應一個或多個 work types。

### Data profiling

Data profiling（資料剖析）是使用統計、分布、唯一性、缺值和樣本檢查來理解資料實際特性的過程。

### Deduplication

Deduplication（去除重複）是辨識並處理重複紀錄的過程。完全相同的 payload 和相同業務事件的不同版本，是兩種不同問題，不能使用同一條規則隨意刪除。

### Socrata 與 Socrata Query Language

Socrata 是 NYC Open Data 使用的開放資料平台技術。Socrata Query Language 是它提供的查詢語言，語法概念類似 Structured Query Language（結構化查詢語言）。它讓我們在伺服器端選欄位、篩選、分組和計數。

## 發現一：日期不能用同一種方式解析

三個來源中的日期看起來相似，實際格式不同：

| 來源 | Metadata 型態 | 樣本格式 |
|---|---|---|
| Permits | calendar date | `2016-12-07T08:23:00.000` |
| Complaints | text | `12/30/1988` |
| Violations | text | `19880713` |

如果直接使用同一條轉換規則，部分日期會變成 null 或被錯誤解讀。因此 staging model 必須依來源明確指定解析格式，並測試解析失敗數量。

## 發現二：Building Identification Number 並非永遠存在

Building Identification Number 是紐約市用來識別特定建築物的編號，通常簡稱 BIN。

| 來源 | 有 BIN 的列數 | 缺少 BIN 的列數 |
|---|---:|---:|
| Permits | 1,002,770 | 0 |
| Complaints | 3,133,744 | 0 |
| Violations | 2,473,646 | 3,214 |

Violations 中約 0.1298% 的列缺少 BIN。比例雖小，但不能直接丟掉：

- event-level fact 應保留它們；
- building-level summary 不能假裝已涵蓋它們；
- dashboard 應顯示 matched 與 unmatched coverage。

## 發現三：狀態詞彙不一致

Complaints 使用：

- `CLOSED`
- `ACTIVE`

Permits 使用：

- `Signed-off`
- `Permit Issued`

Legacy violations 有多種 category，例如：

- `V-DOB VIOLATION - ACTIVE`
- `V*-DOB VIOLATION - Resolved`
- `V*-DOB VIOLATION - DISMISSED`

這表示我們不能對所有資料集使用同一個 `status != CLOSED` 規則。每個來源都需要明確的 status mapping（狀態對照規則）。

## 發現四：Complaint number 幾乎唯一，但仍有來源重複

- 總列數：3,133,744
- 不同 complaint number：3,133,738
- 有 6 個 complaint number 各出現兩次

抽查 complaint `2124643` 時，兩列的 API payload 完全相同。這支持以下處理方式：

1. 以 complaint number 作為業務識別碼；
2. 移除完全相同的 payload；
3. 保留唯一性測試，若未來出現不同內容的相同 complaint number，就讓測試提醒我們。

## 發現五：原本的 Permit grain 假設錯了

原始設計假設以下三個欄位能識別一筆 permit：

```text
job filing number
+ work permit
+ sequence number
```

真實資料否定了這個假設。某個實際案例中，同一組欄位出現 12 列，原因包括：

- 三個 tracking numbers；
- 每個 tracking number 對應四個 work types；
- renewal with changes 與 renewal without changes；
- 不同 issued date、expired date 和 applicant。

加入 tracking number 和 work type 以後，來源仍有少量完全相同的重複 payload。另一方面，tracking number 本身也不是全域唯一。

這代表：

- 目前不能建立或宣稱一張以 unique permit 為 grain 的 `fct_permits`；
- 不能用 `row_number()` 隨意保留其中一列，因為可能丟掉真的 work type；
- 下一步需要評估「permit issuance fact + permit-to-work-type bridge」設計；
- 在確認以前，只能安全移除完全相同的 payload。

這是一個非常好的面試故事：不是先寫模型再找證據，而是用資料剖析推翻自己的假設，留下決策紀錄，再修改設計。

## 發現六：看起來像錯誤的字串可能代表真實狀態

Permit 資料中有：

```text
job_filing_number = Permit is no
work_permit = Permit is not yet issued
```

這看起來像表頭或髒資料，但抽查後發現其他欄位含有真實地址、BIN、tracking number 和工作說明。因此不能只因字串奇怪就刪除；它可能表示 permit 尚未取得正式號碼。

## 為什麼不把完整樣本提交到 Git

本次下載的 metadata 和樣本只放在被 `.gitignore` 排除的 `work/` 目錄。正式 repository 只提交：

- 可重現的查詢；
- 統計結果；
- 設計結論；
- 必要的測試。

這可避免 repository 因原始匯出檔變得龐大，也避免把每天會變動的資料當成程式碼版本管理。

## 知識點總結

- Dataset ID 比網頁標題更適合作為穩定的程式識別。
- Metadata 告訴我們來源宣告的 schema，但實際值仍需 profiling。
- 日期看起來相同，不代表 data type 或格式相同。
- 自然鍵是需要用資料驗證的假設，不是看欄位名稱猜出來的答案。
- Exact duplicate、同一事件的不同版本和一對多關係必須分開處理。
- 缺少 BIN 的事件應保留，building-level 報表則要公開涵蓋率。
- 真實資料推翻原設計時，應修改設計並留下紀錄，而不是隱藏例外。

## 官方文件

- [NYC Open Data：DOB NOW Build Approved Permits](https://data.cityofnewyork.us/d/rbx6-tga4)
- [NYC Open Data：DOB Complaints Received](https://data.cityofnewyork.us/d/eabe-havv)
- [NYC Open Data：DOB Violations](https://data.cityofnewyork.us/d/3h2n-5cm9)
- [Socrata：Getting started with the SODA Consumer API](https://dev.socrata.com/consumers/getting-started.html)
- [Socrata：Socrata Query Language](https://dev.socrata.com/docs/queries/)
- [NYC Open Data：API documentation](https://opendata.cityofnewyork.us/how-to/#api)

## 面試題與參考答案

### 1. How did you evaluate the source data before modeling it?

I queried the official metadata and API endpoints, inspected real samples, measured row and column counts, profiled status distributions and BIN coverage, and tested candidate natural keys for uniqueness. This exposed different date formats, missing building identifiers, exact duplicates, and a false permit-grain assumption before warehouse implementation.

### 2. What surprised you about the permit dataset?

The documented row description was not sufficient to define a stable analytical grain. A job filing, work permit, and sequence combination could contain multiple tracking numbers and work types. Tracking number was not globally unique either, and some refined key combinations still contained exact duplicate payloads.

### 3. How would you handle duplicate records?

I separate exact technical duplicates from business-level versions and legitimate one-to-many relationships. Exact payload duplicates can be removed using a deterministic row hash. Business versions require a validated identity and ordering rule, while multiple work types should be modeled rather than discarded.

### 4. Why keep records without BIN?

They are still valid source events and removing them would make event totals impossible to reconcile. I retain them in event-level facts, exclude them from building-level aggregation only when necessary, and publish the unmatched coverage.

### 5. Why not trust the source data dictionary alone?

The data dictionary describes intended fields and types, but it cannot prove current uniqueness, completeness, status distributions, or actual value formats. Profiling tests whether the live data supports the assumptions required by the analytical model.

### 6. How do you make the profiling reproducible?

I record the stable dataset identifiers, profile date, query logic, point-in-time results, and resulting architecture decision. Raw samples remain outside version control because they change daily, while the reasoning and queries stay in the repository.

### 7. What would you monitor when the pipeline runs daily?

I would monitor source freshness, row-count changes, schema changes, null rates for critical identifiers, duplicate key rates, date parsing failures, accepted status values, and the percentage of records that can be linked to a building.

### 8. Tell me about a time your data changed your design.

My initial permit model assumed that job filing number, work permit, and sequence number formed a unique grain. Source profiling showed multiple tracking numbers and work types under the same combination. I documented the failed assumption, stopped treating the fact as production-ready, and proposed separating permit issuance from its work-type relationship rather than arbitrarily keeping one row.

## 自我檢查

進入下一步前，應該能回答：

- API、endpoint、JSON 和 metadata 分別是什麼？
- 為什麼只看五筆 sample 不足以證明 key 是唯一的？
- 三個來源的日期格式有何不同？
- 哪個來源有缺少 BIN 的問題？
- exact duplicate 和一對多關係有何不同？
- 為什麼目前的 permit grain 必須重新設計？
