# Step 6：使用 dbt 建立 staging models

## 這一步要完成什麼

Raw tables 保存的是 JSON payload。Step 6 使用 dbt 把這些資料轉成三個可以分析、測試和閱讀的 staging views：

```text
RAW.RAW_DOB_NOW_PERMITS  → DEV_STAGING.STG_DOB_NOW_PERMITS
RAW.RAW_DOB_COMPLAINTS   → DEV_STAGING.STG_DOB_COMPLAINTS
RAW.RAW_DOB_VIOLATIONS   → DEV_STAGING.STG_DOB_VIOLATIONS
```

本步已在真實 Snowflake account 建置完成。

## 為什麼不直接從 raw table 做 dashboard

Raw payload 有幾個問題：

- 欄位藏在 JSON 內；
- 日期格式依 source 不同；
- borough 有完整名稱、縮寫或數字代碼；
- BIN 可能不合法；
- 同一筆來源 payload 可能在不同 load 重複出現；
- raw field names 不一定適合商業使用者。

如果每個 dashboard 都自己解析 JSON，business logic 會重複而且容易不一致。Staging layer 把「來源格式」轉成「一致、可重用的欄位」。

## 新名詞解釋

### dbt

dbt 是 data build tool。它讓 analytics engineer 使用 Structured Query Language 定義 transformations，並負責依 dependencies 建置 models、執行 tests、產生 documentation 和 lineage。

### Model

dbt model 通常是一個 `.sql` file。檔案內的 query 會被 dbt materialize 成 database object，例如 table 或 view。

### Materialization

Materialization 是 model 在 warehouse 中如何存在。本步使用 `view`：它保存 query definition，不另外保存一份完整資料。

### Source

Source 是 dbt 對外部或上游 table 的正式宣告。`source('dob_raw', 'complaints')` 告訴 dbt 這是 raw input，不是另一個 dbt model。

### Common Table Expression

Common Table Expression 通常簡寫為 CTE，是 `WITH name AS (...)` 定義的暫時查詢區塊。它讓 deduplication、ranking 和最後 selection 分段閱讀。

### Type casting

Type casting 是把 value 從一種 data type 轉成另一種。例如把 JSON string `10/26/2022` 轉成真正的 `DATE`。

### TRY function

Snowflake 的 `TRY_TO_DATE`、`TRY_TO_TIMESTAMP_NTZ` 在轉換失敗時回傳 `NULL`，而不是讓整個 model 中止。但 `TRY` 不等於資料正確，因此仍要加 format rules 和 quality flags。

### Window function 與 ROW_NUMBER

Window function 在不合併 rows 的情況下，對一組 rows 計算排名。`ROW_NUMBER()` 可以讓我們在每個 business key 內選最新 source state。

### Natural key 與 technical key

- Natural key：source 或 business 本身具有意義的識別欄位，例如 complaint number；
- Technical key：由系統建立，用來支援工程處理的 key，例如 canonical payload 的 SHA-256 hash。

Permit source 沒有通過 profiling 的 natural key，所以 staging 使用 source-row hash 當 technical content key，不假裝它是 business permit ID。

### Exact-payload deduplication

Exact-payload deduplication 只合併內容完全一樣的 source rows。它不會因為幾個欄位看起來相同，就刪除可能代表不同 work type 或 tracking number 的 permit rows。

### Data test

Data test 是針對 warehouse data 執行的 assertion。例如：

- key 不可以是 `NULL`；
- key 必須 unique；
- borough 必須屬於五個合法值；
- BIN 若存在，必須是七位數。

### Compiled SQL

dbt 會把 Jinja、macros、`source()` 和 tests 編譯成 Snowflake 真正執行的 SQL。除錯時閱讀 compiled SQL，能看到 database 收到的實際內容。

## 三個來源為什麼不能使用同一個日期規則

真實 samples 顯示：

| Source | 原始日期範例 | 解析方式 |
|---|---|---|
| Permit | `2023-06-05T00:00:00.000` | timestamp → date |
| Complaint | `10/26/2022` | `MM/DD/YYYY` |
| Violation | `19881031` | `YYYYMMDD` |

若只使用自動判斷，資料可能被錯誤但「成功」地解析。

## 真實資料發現：西元 223 年

第一次 staging build 後，quality query 發現 violation 最小日期是西元 223 年。追查 raw payload 得到：

```text
02230913
```

Snowflake 可以把它解析成 `0223-09-13`，但這顯然不是合理的 NYC DOB violation issue date。另一筆 `0306` 也無法形成完整日期。

最後規則是：

1. 必須符合八位數 `YYYYMMDD`；
2. 年份只能是 1900–2099；
3. 無效值不猜測修正；
4. `source_issue_date` 保留原字串；
5. `issue_date` 設為 `NULL`；
6. `issue_date_parse_failed` 設為 `TRUE`。

這兩筆 rows 仍存在 staging model，沒有被刪除。

## Borough standardization

不同來源使用不同表示方式：

```text
1 / MN / MANHATTAN
2 / BX / BRONX
3 / BK / BROOKLYN
4 / QN / QUEENS
5 / SI / STATEN ISLAND
```

`normalize_borough` macro 將它們轉成五個 canonical names。Complaints 沒有 borough field，因此暫時由有效 BIN 的第一碼推導。這是公開規則，不是隱藏推測。

## 實際建置與測試結果

第一次 build：

- 3 個 views 建立成功；
- 11 個 tests 通過；
- 1 個 test 發生 SQL syntax error。

原因是 column-level `dbt_utils.expression_is_true` 會自動將 column name 放在 expression 前面，原本的 expression 重複寫了 `bin`。閱讀 compiled SQL 後，改成 Snowflake 的 `REGEXP` operator。

最終 build：

```text
3 staging views + 13 data tests = 16 PASS
0 WARN
0 ERROR
```

Row counts：

| Staging model | Rows |
|---|---:|
| `STG_DOB_NOW_PERMITS` | 1,000 |
| `STG_DOB_COMPLAINTS` | 1,000 |
| `STG_DOB_VIOLATIONS` | 1,000 |

Violation quality result：

```text
parse failures: 2
null parsed issue dates: 2
minimum valid issue date: 1970-04-23
maximum valid issue date: 1988-12-30
```

## 目前限制

- 只驗證每個 source 的 1,000-row bounded sample；
- permit key 仍是 technical content key，不是驗證過的 natural key；
- date quality flags 尚未彙總成完整 quality mart；
- facts、dimensions 和 dashboard models 是下一個步驟。

## 知識點總結

- Raw layer 保存來源；staging layer 統一結構與型別。
- 每個來源的日期格式必須明確處理。
- `TRY` conversion 能避免整個 pipeline 中止，但不能取代品質規則。
- Exact duplicates 和 business-key versions 是兩種不同問題。
- Permit grain 不確定時，寧可保留 rows，也不要錯誤合併。
- Data quality exception 應保留原值並建立 flag。
- dbt test 失敗時，要查看 compiled SQL 和 failing rows。

## 官方文件

- [dbt：Models](https://docs.getdbt.com/docs/build/sql-models)
- [dbt：Sources](https://docs.getdbt.com/docs/build/sources)
- [dbt：Data tests](https://docs.getdbt.com/docs/build/data-tests)
- [dbt：Jinja and macros](https://docs.getdbt.com/docs/build/jinja-macros)
- [dbt-utils package](https://hub.getdbt.com/dbt-labs/dbt_utils/latest/)
- [Snowflake：Semi-structured data](https://docs.snowflake.com/en/user-guide/semistructured-concepts)
- [Snowflake：Date and time conversion](https://docs.snowflake.com/en/sql-reference/functions-conversion)
- [Snowflake：Window functions](https://docs.snowflake.com/en/user-guide/functions-window-using)

## 面試題與參考答案

### 1. What is the purpose of your staging layer?

The staging layer converts raw JSON payloads into consistently named and typed columns while preserving source lineage. It standardizes BIN, borough, and source-specific dates, removes exact duplicate payloads, and exposes quality exceptions without applying final business metrics.

### 2. Why did you use views for staging models?

The learning sample is small and the rules are still evolving, so views avoid storing another physical copy and make iteration inexpensive. I can change the materialization later if full-volume query performance justifies it.

### 3. How did you deduplicate permits without a reliable natural key?

I only removed exact payload duplicates using a canonical source-row hash. I retained distinct rows because profiling showed that the apparent permit key could represent several tracking numbers and work types. The hash is documented as a technical content key, not a business permit identifier.

### 4. What did your tests catch?

The automated tests verified key completeness and uniqueness, borough domains, BIN format, and non-null quality flags. A separate profile query found that automatic date parsing had interpreted `02230913` as the year 223, so I added an explicit format and year rule while preserving the raw value and exposing a parse-failure flag.

### 5. How do you debug a dbt test failure?

I identify whether the failure is a compilation error, database error, or returned failing rows. I then inspect the compiled SQL under dbt's target directory, run the relevant query against the warehouse when needed, correct the model or test definition, and rerun only the affected selection before the broader build.
