# Step 7：建立事實表、維度表與每日快照

## 這一步完成了什麼

Step 6 把三個原始來源整理成可閱讀的 staging models。Step 7 再把 staging data 轉成真正供分析與 Business Intelligence 使用的 dimensional models：

```text
三個 staging models
        |
        v
int_building_observations
        |
        v
dim_buildings
   |        |        |
   v        v        v
permit   complaint  violation
records    facts      facts
   \        |        /
    \       |       /
     v      v      v
fct_building_compliance_daily
```

已在真實 Snowflake account 建立：

- `DIM_BUILDINGS`
- `FCT_PERMIT_RECORDS`
- `FCT_COMPLAINTS`
- `FCT_VIOLATIONS`
- `FCT_BUILDING_COMPLIANCE_DAILY`

這不是只有建立空架構。所有 models 都使用先前載入的 3,000 筆真實 New York City Department of Buildings 資料完成建置與測試。

## 為什麼需要 dimensional modeling

如果直接把 permits、complaints 和 violations 三張明細表互相 join，同一棟 building 可能有：

- 3 筆 permit records；
- 4 筆 complaints；
- 5 筆 violations。

直接 join 後可能產生 `3 × 4 × 5 = 60` 列。原本只有 4 筆 complaints，卻會被重複計算很多次。這叫做 measure multiplication，也就是衡量值因多對多關係而被放大。

本專案採用的做法是：

1. 各事件保留在自己的 fact table；
2. 共用同一張 building dimension；
3. 先在各 fact table 內依 building 聚合；
4. 最後才把已聚合的結果組成每日 snapshot。

## 新名詞解釋

### Dimensional modeling

Dimensional modeling 是為分析查詢設計資料的方式。它把資料分為描述「發生了什麼」的 facts，以及描述「與誰、在哪裡、何時有關」的 dimensions。

### Fact table

Fact table，中文常稱事實表，保存事件或可衡量的活動。例如一筆 complaint、一筆 violation source record，或某天某棟 building 的 open complaint count。

Fact table 最重要的問題不是欄位名稱，而是：每一列究竟代表什麼？這就是 grain。

### Dimension table

Dimension table，中文常稱維度表，保存用來描述、分類或篩選 facts 的資訊。本專案的 `dim_buildings` 提供 building key、Building Identification Number、borough 與 address。

### Grain

Grain 是一張表「每一列代表什麼」的精確聲明。例如：

- `fct_complaints`：每列是一個 complaint 的最新來源狀態；
- `fct_violations`：每列是一個 legacy violation 的最新來源狀態；
- `fct_building_compliance_daily`：每列是某一天的某一棟 building。

必須先定義 grain，才能正確選 key、join 和 metric。

### Business key、natural key 與 technical key

- Business key：業務上可辨認一個實體的 key；
- Natural key：來源資料本來就有的識別欄位，例如 complaint number；
- Technical key：系統為工程需要建立的 key，例如 source payload 的 hash。

本專案沒有假裝 permit source row hash 是真實 permit number。它只是 technical content key。

### Surrogate key

Surrogate key 是 data warehouse 產生的替代識別值。`building_key` 由 Building Identification Number 穩定產生，讓所有 fact tables 使用一致的 foreign key。

### Foreign key

Foreign key 是一張表指向另一張表 key 的欄位。例如 facts 的 `building_key` 指向 `dim_buildings.building_key`。

### Conformed dimension

Conformed dimension 是多個 facts 共用、定義一致的 dimension。Permits、complaints 與 violations 都使用同一張 `dim_buildings`，所以 borough 與 building identity 不會各自定義。

### Type 1 dimension

Type 1 dimension 只保存目前選定的描述值，不保存每次屬性變更的歷史版本。本專案 Phase 1 的 `dim_buildings` 是 Type 1：如果未來選到更好的 address，舊值會被新值取代。

### Snapshot fact

Snapshot fact 在固定時間點記錄一組狀態。本專案每日記錄每棟 building 的 open complaints、open violations、active permit source records 與資料涵蓋標記。

### Incremental model

Incremental model 第一次建立完整 table，之後只插入或更新需要的 grain，而不是每次刪掉所有歷史再重建。

### MERGE

`MERGE` 是 Snowflake 的一種 Structured Query Language 操作。它會依 key 判斷：已有的 row 要更新，新的 row 要插入。

### Idempotent

Idempotent 表示同一個工作重跑後，不會因重複執行而不斷增加錯誤結果。本專案同一天重跑 snapshot，仍只有一個 building/date row。

### Business Intelligence

Business Intelligence 常縮寫為 BI，指 dashboard、reporting 與支援商業決策的分析消費層。

## Step 7.1：先升級 dbt

舊環境是：

```text
dbt Core 1.9.11
dbt Snowflake adapter 1.9.4
```

執行時已出現版本棄用警告。因為本專案要作為面試作品，繼續使用已棄用版本會帶來兩個問題：

1. 新建立的專案看起來沒有處理 dependency lifecycle；
2. 舊設定方式可能在之後停止支援。

升級後是：

```text
dbt Core 1.12.5
dbt Snowflake adapter 1.12.1
Snowflake Python connector 4.7.4
```

沒有使用仍在 release candidate 階段的 dbt 2.0，因為 portfolio 應優先使用穩定版本。

升級也發現一個 dependency conflict：新版 adapter 要求 Snowflake connector 4.x，但專案原本限制 `<4`。最後同步修改 dependency range，並使用 `pip check` 確認沒有 broken requirements。

dbt 1.12 也要求 source freshness 設定移入 `config`。設定更新後，`dbt parse --no-partial-parse` 沒有任何 deprecation warning。

## Step 7.2：先看真實 status，再寫規則

我們沒有直接猜測 status。先查詢 warehouse 中的真實 sample：

| Source | 真實值 | Rows |
|---|---|---:|
| permit | `SIGNED-OFF` | 776 |
| permit | `PERMIT ISSUED` | 224 |
| complaint | `CLOSED` | 988 |
| complaint | `ACTIVE` | 12 |
| violation | `V*-DOB VIOLATION - Resolved` | 860 |
| violation | `V*-DOB VIOLATION - DISMISSED` | 112 |
| violation | `V-DOB VIOLATION - ACTIVE` | 28 |

再查完整官方 violation dataset，發現 category 還包含：

- work without permit active/dismissed；
- unserved Environmental Control Board active/dismissed；
- hazardous active/dismissed；
- 沒有清楚 lifecycle label 的其他 category。

因此 violation mapping 使用 category 內明確的 `ACTIVE`、`RESOLVED` 或 `DISMISSED` label。無法對應的資料標為 `UNKNOWN`，不刪除、也不猜成 open。

## Step 7.3：誠實處理 permit grain

先前 profiling 已經證明：

- job filing number + work permit + sequence number 不唯一；
- 加上 tracking number 和 work type 後仍可能有 exact duplicates；
- tracking number 也不一定只屬於一個 job filing。

所以本步沒有建立一張聲稱「每列是一張唯一 permit」的 `fct_permits`。真正建立的是：

```text
fct_permit_records
grain = one distinct DOB NOW approved-permit source payload
key   = canonical source-row hash
```

這個名稱是重要的 data contract。使用者看到 `active_permit_record_count`，就不會誤解成 unique permit count。

## Step 7.4：建立 building observations

`int_building_observations` 將三個 staging models 看到的 valid Building Identification Number、address、borough 與 Borough-Block-Lot 合併。

`int_` 表示 intermediate model，也就是 staging 與 final marts 之間的中間轉換層。它不是最終給 dashboard 使用的 table。

這一層保留重複 observations，因為同一棟 building 可能在很多事件中出現。下一層才選出一個 building row。

## Step 7.5：建立 `dim_buildings`

`dim_buildings` 每個 valid Building Identification Number 只有一列。選擇 descriptive attributes 的順序是：

1. 優先有合法十位數 Borough-Block-Lot 的 observation；
2. 再優先有 borough；
3. 再優先同時有 house number 與 street name；
4. 若仍相同，使用 source priority 與 ingestion time 決定。

為什麼不直接用 address fuzzy matching？因為兩個相似地址不一定是同一棟 building。Phase 1 寧可讓沒有 valid Building Identification Number 的 fact 留下 null building key，也不做無法辯護的自動合併。

## Step 7.6：建立三張 event facts

### `fct_permit_records`

保存：

- source record technical key；
- building foreign key；
- job、tracking、work type 和 permit status；
- approved、issued、expired dates；
- approval-to-issue days；
- source lineage fields。

Status group：

```text
PERMIT ISSUED -> ISSUED
SIGNED-OFF    -> SIGNED_OFF
其他值         -> UNKNOWN
```

Fact 內不使用今天日期永久計算 active flag，因為一筆 record 今天 active，過了 expiration date 就可能不 active。是否 active 應依 snapshot date 計算。

### `fct_complaints`

Status group：

```text
ACTIVE -> ACTIVE
CLOSED -> RESOLVED
其他值  -> UNKNOWN
```

只有 `ACTIVE` 的 row 會得到 `is_open = TRUE`。

### `fct_violations`

Status group：

```text
category contains ACTIVE    -> ACTIVE
category contains RESOLVED  -> RESOLVED
category contains DISMISSED -> DISMISSED
其他值                       -> UNKNOWN
```

不能使用 `disposition_date is null` 代表 open。真實 sample 中有一筆 category 為 resolved，但 disposition date 仍是 null。只看 date 會錯誤增加 open count。

## Step 7.7：建立每日 incremental snapshot

`fct_building_compliance_daily` 的 compound unique key 是：

```text
snapshot_date + building_key
```

Compound key 表示需要兩個欄位合在一起才唯一。

每日 snapshot 的建立順序：

1. complaints 先依 building 聚合；
2. violations 先依 building 聚合；
3. permit records 先依 building 聚合；
4. 三個聚合結果再 left join 到 `dim_buildings`。

這能避免明細互相 join 造成重複計算。

主要 measures：

- `open_complaint_count`
- `open_violation_count`
- `active_permit_record_count`
- `complaints_last_30_days`
- `oldest_open_complaint_date`
- `oldest_open_violation_date`
- `latest_permit_issued_date`
- 三個 unmapped status counts
- 三個 source-history flags

同一天重跑時，Snowflake `MERGE` 更新相同 key；下一天執行時則插入新的 date partition。

## Step 7.8：加入哪些 tests

本步加入：

- primary key 的 `not_null` 與 `unique`；
- fact foreign key 到 building dimension 的 `relationships`；
- status groups 的 `accepted_values`；
- dimension key 與 identifier format tests；
- source fact 與 staging 的 `equal_rowcount`；
- snapshot building/date compound uniqueness；
- counts 不得小於零；
- critical flags 不得是 null。

`equal_rowcount` 很重要，因為 fact join 後若 building dimension 不小心有 duplicate Building Identification Number，1,000 筆 source rows 可能變成 1,005 筆。這個 test 會讓 build 失敗，而不是讓 dashboard 悄悄重複計算。

## 真實 Snowflake 建置結果

第一次 dimensional build：

```text
1 intermediate view
1 building dimension
3 event fact tables
1 incremental daily snapshot
54 selected data tests
1 documented dashboard exposure

PASS = 60
WARN = 0
ERROR = 0
NO-OP = 1 exposure
```

`NO-OP` 不是錯誤。Exposure 是 dbt 對下游 dashboard 的文件描述，不需要在 Snowflake 建立 table。

最後從 staging 開始執行整個 project 的完整驗收結果是：

```text
9 models
67 data tests
1 exposure

PASS = 76
WARN = 0
ERROR = 0
NO-OP = 1 exposure
TOTAL = 77
```

Row counts：

| Model | Rows |
|---|---:|
| `DIM_BUILDINGS` | 2,383 |
| `FCT_PERMIT_RECORDS` | 1,000 |
| `FCT_COMPLAINTS` | 1,000 |
| `FCT_VIOLATIONS` | 1,000 |
| `FCT_BUILDING_COMPLIANCE_DAILY` | 2,383 |

## 為什麼 fact 有 28 個 open violations，snapshot 只有 26 個

這是本步最值得面試說明的結果之一。

```text
FCT_VIOLATIONS active rows       = 28
missing valid Building ID rows   = 2
daily snapshot open violations   = 26
```

兩筆 active violations 沒有 valid Building Identification Number：

- 它們仍完整保留在 `fct_violations`；
- `building_key` 是 null；
- 它們不會被錯誤指派到某個 building；
- building-level snapshot 無法安全納入它們。

這不是 transformation 遺失資料，而是 identity coverage 的透明限制。

Building-key coverage：

| Fact | Matched | Total |
|---|---:|---:|
| Permit records | 1,000 | 1,000 |
| Complaints | 1,000 | 1,000 |
| Violations | 998 | 1,000 |

## Incremental rerun 驗證

同一天再次執行 daily snapshot 後：

```text
snapshot date: 2026-09-20
row count: 2,383
distinct building keys: 2,383
```

Row count 沒有變成 4,766，證明同日 retry 會 merge，而不是重複 append。

Reader role 也成功看到五個 marts，表示先前設定的 future grants 對後來建立的 tables 生效。

## 目前限制

- Snowflake 目前只有每個 source 的 1,000-row bounded sample；
- `fct_permit_records` 不是 unique permit fact；
- building dimension 是 Type 1，沒有保存 address change history；
- 沒有 valid Building Identification Number 的 facts 不進入 building rollup；
- daily history 從第一次 scheduled run 才開始；
- late-arriving data 不會自動重寫過去所有 snapshot partitions；
- status mappings 是可解釋的 analytical definitions，不是官方法律判定。

## 知識點總結

- Grain 必須在寫 join 與 metric 前先定義。
- Fact table 記錄事件；dimension table 提供一致的分析描述。
- Conformed dimension 讓不同 facts 共用同一套 building identity。
- 多張 event facts 不能直接在明細層互相 join 後計數。
- Permit natural key 不確定時，要誠實發布 source-record fact。
- Open/active status 要使用明確 mapping，不能用缺少 date 當作唯一判斷。
- `UNKNOWN` 與 unmapped count 能讓新 source values 可見。
- Incremental `MERGE` 加 compound unique key，可以讓每日 retry 保持 idempotent。
- Null foreign key 不代表刪除資料；它可以誠實表示 identity 無法解析。
- Row-count reconciliation 能偵測 join 導致的資料增加或遺失。

## 官方文件與延伸閱讀

- [dbt：SQL models](https://docs.getdbt.com/docs/build/sql-models)
- [dbt：Incremental models](https://docs.getdbt.com/docs/build/incremental-models)
- [dbt：Configure incremental models](https://docs.getdbt.com/docs/build/incremental-models-overview)
- [dbt：Data tests](https://docs.getdbt.com/docs/build/data-tests)
- [dbt：The `ref` function](https://docs.getdbt.com/reference/dbt-jinja-functions/ref)
- [dbt Core releases on Python Package Index](https://pypi.org/project/dbt-core/)
- [dbt Snowflake releases on Python Package Index](https://pypi.org/project/dbt-snowflake/)
- [Snowflake：MERGE](https://docs.snowflake.com/en/sql-reference/sql/merge)
- [Snowflake：COUNT_IF](https://docs.snowflake.com/en/sql-reference/functions/count_if)
- [Kimball Group：Fact tables](https://www.kimballgroup.com/2008/11/fact-tables/)
- [Kimball Group：Four-step dimensional design process](https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/)

## 面試題與參考答案

### 1. What is the grain of each fact table?

`fct_complaints` has one row per latest-state complaint, and `fct_violations` has one row per latest-state legacy violation identifier. `fct_permit_records` has one row per distinct source payload because profiling did not identify a trustworthy permit business key. The daily snapshot has one row per building and snapshot date.

### 2. Why did you rename the permit fact to `fct_permit_records`?

The apparent permit key failed uniqueness tests across tracking numbers and work types. Calling each row a unique permit would overstate what the data proves, so I published a source-record fact keyed by the canonical payload hash and named its metrics accordingly. I documented a future permit-issuance fact and work-type bridge as a hypothesis rather than implementing an unvalidated grain.

### 3. Why do you need a conformed building dimension?

It gives permits, complaints, and violations the same building identity and descriptive attributes. That supports consistent filtering and aggregation while keeping the event facts separate at their own grains.

### 4. How did you prevent measure multiplication?

I did not join the three event facts at row level. I aggregated each fact independently by building and then joined those aggregates to the one-row-per-building dimension. I also added row-count and key tests to detect accidental fan-out.

### 5. How did you define an open violation?

I used the official violation category label. Categories containing `ACTIVE` map to active, while explicit resolved and dismissed labels map separately. Unknown categories remain visible and are not counted as open. I rejected the simpler rule based on a null disposition date because the real sample contained a resolved record with no disposition date.

### 6. Why is `building_key` nullable in event facts?

The source record can be valid even when its Building Identification Number is missing or malformed. I preserve that event with a null foreign key rather than dropping it or assigning it through an unvalidated fuzzy match. The building-level snapshot includes only records with a resolved building identity.

### 7. What makes your daily model incremental and idempotent?

It uses dbt's incremental materialization with Snowflake `MERGE` and the compound unique key of snapshot date and building key. A retry on the same date updates the same rows, while a later run inserts a new date partition. I verified a same-day rerun stayed at 2,383 rows.

### 8. What tests protect the dimensional model?

I test primary-key uniqueness and completeness, foreign-key relationships, accepted status groups, identifier formats, nonnegative metrics, compound snapshot uniqueness, and equal row counts between each staging model and its event fact. Together they protect both structure and business logic.

### 9. Why did the snapshot show 26 open violations when the fact showed 28?

Two active violation records had no valid Building Identification Number. They remain in the event fact with null building keys, but they cannot be safely assigned to a building-level snapshot. I expose that as an identity-coverage limitation instead of silently dropping or guessing the records.

### 10. What would you improve before production use?

I would load and profile the full history, validate permit issuance and work-type keys with a domain expert, measure late-arriving updates, decide whether historical snapshots need restatement, add a calendar dimension, and monitor unknown status rates and building-key coverage over time.
