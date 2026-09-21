# Step 8：建立資料品質測試與可觀測性

## 這一步完成了什麼

Step 7 已經有 primary key、foreign key、accepted values 與 row-count tests。Step 8 將它們擴充成一個可以回答下列問題的品質系統：

- 原始資料是不是最近有成功載入？
- 每張 fact 有多少 records 可以對應到 building？
- 新的 source status 是否超出目前的 business definition？
- 每日 snapshot 的 totals 是否真的與 event facts 相同？
- 哪些問題必須停止 pipeline？
- 哪些是來源本身的已知限制，應保留並監控？
- 發生問題時，analyst 能不能直接查到 affected records？

已建立：

```text
Reusable generic test
└── not_null_proportion_at_least

Cross-model singular tests
├── assert_current_snapshot_reconciles
├── assert_status_flags_consistent
├── assert_no_reversed_event_dates
├── assert_no_unmapped_statuses
└── assert_quality_summary_complete

Quality audit views
├── audit_data_quality_summary
├── audit_unresolved_building_records
├── audit_date_anomalies
└── audit_status_mapping_exceptions
```

三個 raw sources 也加入 ingestion metadata tests 與 freshness checks。

## 為什麼「測試越多」不一定越好

一個沒有理解 source meaning 的 test，可能只是製造 noise。

例如真實 sample 有兩筆 violations 沒有有效 Building Identification Number。如果設定：

```text
every violation building_key must be not null
```

pipeline 每次都會失敗。但這兩筆 records：

- 是官方來源的一部分；
- 不是 transformation 創造的；
- 沒有足夠證據可以自動配對到某棟 building；
- 應該保留供 record-level investigation。

正確做法不是刪掉 records，也不是讓 pipeline 永遠紅燈，而是：

1. 設定可量測的 coverage threshold；
2. 在 audit view 保存 affected records；
3. 在 scorecard 顯示 `WARN`；
4. 如果 coverage 真的跌破可接受標準，再停止 pipeline。

## 新名詞解釋

### Data quality

Data quality 是資料是否適合預定用途。它不只是「有沒有 null」，還包含正確 grain、合法 values、relationships、一致的 business rules 與及時更新。

### Data quality dimension

Data quality dimension 是評估資料品質的一個面向。本專案使用：

- completeness：必要資料是否存在；
- uniqueness：應唯一的 key 是否重複；
- validity：value 是否符合合法格式或 domain；
- referential integrity：foreign key 是否能找到對應 dimension；
- consistency：不同欄位與不同 models 是否表達相同規則；
- reconciliation：上游與下游 totals 是否對得起來；
- timeliness：資料是否在可接受時間內更新。

### Completeness

Completeness 是資料是否足夠完整。例如 1,000 筆 violations 中有 998 筆有 building key，building-key completeness 是 99.8%。

### Uniqueness

Uniqueness 是應該唯一的 key 是否只出現一次。例如 complaint key 或 building/date compound key。

### Validity

Validity 是 value 是否符合定義。例如 Building Identification Number 必須是七位數；status group 必須屬於批准的 value list。

### Referential integrity

Referential integrity 是非空的 foreign key 必須在被指向的 table 中存在。例如 fact 的 `building_key` 必須能在 `dim_buildings` 找到。

### Consistency

Consistency 是不同欄位或 models 不互相矛盾。例如：

```text
complaint_status_group = ACTIVE
is_open = FALSE
```

這就是 inconsistency，應讓 test 失敗。

### Reconciliation

Reconciliation 是用獨立方式重新計算結果，確認上下游數字一致。例如從 event facts 算出的 open violation count，必須等於 current daily snapshot 的加總。

### Timeliness 與 freshness

Timeliness 是資料是否及時。Freshness check 會比較 raw table 最新 ingestion timestamp 與現在時間。

本專案設定：

```text
source age > 36 hours -> WARN
source age > 72 hours -> ERROR
```

### Data test

dbt data test 是一個 assertion。Test query 會回傳違反規則的 rows：

- 回傳 0 rows：通過；
- 回傳 1 row 或更多：失敗或警告，依設定決定。

### Generic data test

Generic data test 是可以套用在不同 models 與 columns 的 reusable test。本專案建立 `not_null_proportion_at_least`，讓三張 facts 共用相同 coverage 邏輯。

### Singular data test

Singular data test 是一個專門驗證特定 business rule 的 Structured Query Language file。例如 daily snapshot reconciliation。

### Assertion

Assertion 是對資料應該符合什麼條件的明確聲明。例如：「任何 source status 都必須有 governed mapping。」

### Threshold

Threshold 是允許範圍的界線。本專案 building-key coverage threshold 是 99%，不是要求不切實際的 100%。

### Severity

Severity 是問題的嚴重度。Blocking error 應阻止不可靠資料繼續發布；warning 表示結果仍可使用，但有需要被看見的限制。

### False positive

False positive 是 test 報錯，但實際資料沒有違反真正的 business rule。例如把「active complaint 已有 disposition date」一律當成錯誤，可能就是 false positive，因為 disposition 可能只代表一次處理動作，不代表案件已關閉。

### Audit model

Audit model 是專門讓人查詢品質問題的 model。Test 告訴你「規則是否通過」；audit model 告訴你「哪些 records 需要調查」。

### Data observability

Data observability 是讓團隊可以持續知道 data pipeline 與 data products 的健康狀態。本步用 freshness、coverage、quality status 與 detail views 建立基礎 observability。

### Data contract

Data contract 是 producer 與 consumer 對資料結構和行為的明確約定。例如 fact grain、合法 status values、building-key coverage 與更新頻率。

## Step 8.1：先 profile，而不是直接寫 tests

在建立規則前，先查詢真實 marts：

### Permit records

```text
total records: 1,000
missing BIN: 0
missing building key: 0
unmapped statuses: 0
issued before approved: 0
missing approved date: 1
missing issued date: 1
missing expired date: 2
```

Missing dates 沒有直接設成 blocking error，因為 source lifecycle 可能允許某些 dates 不存在。沒有 domain confirmation 前，不應擅自宣稱所有 dates 都 mandatory。

### Complaints

```text
total records: 1,000
missing building key: 0
unmapped statuses: 0
disposition before entered: 0
active with disposition date: 9
```

9 筆 active complaints 已有 disposition date，但這不一定矛盾。Status 是官方 current state；disposition date 可能是一次處理紀錄。因為沒有證據說這一定錯，所以只記錄 profiling 結果，不建立 blocking test。

### Violations

```text
total records: 1,000
missing or invalid BIN: 2
missing building key: 2
unmapped statuses: 0
issue-date parse failures: 2
resolved or dismissed without disposition date: 1
```

Open/closed definition使用 official category，不使用 disposition date，因此 resolved row 缺 date 不會被錯算成 open。

### Building dimension

```text
total buildings: 2,383
missing BBL: 1,423
missing borough: 0
missing display address: 1
observed in one source: 2,359
observed in two sources: 24
observed in all three sources: 0
```

大多數 buildings 只有一個 source observation，主要原因是每個來源只載入 1,000-row bounded sample，而且三個 samples 不是同一組 buildings。這不是 dimension failure。

## Step 8.2：定義 blocking contracts

下列問題會直接影響 published metrics，所以 test 必須失敗：

1. primary key duplicate 或 null；
2. non-null foreign key 找不到 dimension；
3. event fact row count 與 staging 不一致；
4. status flag 和 status group 矛盾；
5. 出現沒有 governed mapping 的新 status；
6. permit issued date 早於 approved date；
7. complaint disposition date 早於 entered date；
8. current snapshot totals 與 facts 不一致；
9. building-key coverage 低於 99%；
10. source 超過 72 小時沒有 ingestion。

這些問題可能改變 dashboard 數字，不能只放一個 warning 後繼續發布。

## Step 8.3：建立 reusable coverage test

`not_null_proportion_at_least` 的邏輯是：

```text
populated proportion = non-null rows / total rows

if table is empty -> fail
if populated proportion < required minimum -> fail
otherwise -> pass
```

Step 8 當時三個 fact models 都設定：

```text
building_key coverage >= 0.99
```

實際結果：

| Fact | Coverage | Result |
|---|---:|---|
| Permit records | 100.00% | PASS |
| Complaints | 100.00% | PASS |
| Violations | 99.80% | PASS |

為什麼 threshold 不是 100%？因為真實官方資料確實可能沒有 Building Identification Number。要求 100% 會讓已知且無法由 pipeline 修正的 source issue 永久阻止工作。

為什麼不是 90%？因為 building-level product 若有 10% records 無法對應 building，會嚴重低估某些 properties 的 workload。

99% 是 Phase 1 hypothesis，完整資料 baseline 建立後仍需要重新評估。

Step 12 建立 dashboard 時，進一步發現 legacy violations 有 11 筆使用 `0000000`，
原本的七位數 syntax test 錯把它當成 building。修正後 permits 與 complaints 仍使用
99% blocking threshold；legacy violations 使用 98% blocking floor，但 audit scorecard
仍以 99% 作為 desired threshold，低於 99% 會顯示 `ERROR`。這不是偷偷降低品質標準，
而是把「是否允許保留來源缺陷」與「是否對使用者顯示品質不足」分成兩個控制。

## Step 8.4：建立 cross-model singular tests

### Snapshot reconciliation

`assert_current_snapshot_reconciles` 會獨立計算：

- building count；
- open complaint count；
- open violation count；
- active permit record count；
- complaints in the last 30 days。

任何 expected value 與 current snapshot aggregate 不相同，test 就回傳 failing row。

實際驗證：

```text
open complaints: fact 12 = snapshot 12
open violations: fact with building key 26 = snapshot 26
```

### Status flag consistency

例如：

```text
is_open must equal (status_group = ACTIVE)
is_status_unmapped must equal (status_group = UNKNOWN)
```

這能避免 developer 修改 status group，卻忘記同步 boolean flag。

### Unmapped status assertion

若 New York City Department of Buildings 新增 status，staging 不會刪掉它，但 `assert_no_unmapped_statuses` 會阻止 downstream publication，要求先決定這個 status 應如何影響 metrics。

目前 mapping exceptions 是 0 rows。

### Reversed lifecycle dates

Permits 與 complaints 的先後順序是明確 business rule，所以 reversed dates 會失敗。

Violation malformed issue dates 已經被 staging 轉成 null 並留下 flag。它們是已知 source exceptions，因此進入 audit model，而不是讓每次 pipeline 永久失敗。

## Step 8.5：建立四張 audit views

### `audit_data_quality_summary`

每個 domain 一列，包含：

- total records；
- matched 與 missing building keys；
- coverage percentage；
- unmapped statuses；
- date anomalies；
- last ingestion timestamp；
- source age；
- minimum threshold；
- quality status。

### `audit_unresolved_building_records`

保存所有 `building_key is null` 的 fact records，並區分：

- `MISSING_OR_INVALID_BIN`
- `UNMATCHED_VALID_BIN`

目前有兩筆 violations，兩筆都是 missing or invalid Building Identification Number。

### `audit_date_anomalies`

保存：

- permit issued before approved；
- complaint disposition before entered；
- violation issue-date parse failure。

目前有兩筆 violation issue-date parse failures。

### `audit_status_mapping_exceptions`

保存所有 `UNKNOWN` status records。目前是 0 rows。

這張空 view 仍有價值：未來 source schema 或 status 改變時，它會自動開始出現 records。

## Step 8.6：建立 source metadata tests

三張 raw tables 的下列欄位不可為 null：

- `source_row_hash`
- `load_id`
- `ingested_at`

這些不是 business fields，而是 pipeline lineage metadata：

- hash 支援 exact-payload deduplication；
- load identifier 追蹤哪一次 ingestion；
- ingestion timestamp 支援 freshness 與 incident investigation。

## Step 8.7：執行 source freshness

新增 command：

```text
make dbt-freshness
```

實際結果：

```text
dob_raw.permits     PASS
dob_raw.complaints  PASS
dob_raw.violations  PASS
```

建置當時三個 sources 的 age 都是約 5 小時，低於 36-hour warning threshold。

Freshness 不等於 source event date 很新。它只證明我們最近成功把資料載入 raw table。如果來源本身停止更新但 ingestion 仍重複下載舊資料，還需要額外的 source watermark monitoring。

## Step 8.8：實際 quality scorecard

| Domain | Total | Matched building | Coverage | Unmapped | Date anomalies | Source age | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Complaints | 1,000 | 1,000 | 100.00% | 0 | 0 | 5 hours | `PASS` |
| Permit records | 1,000 | 1,000 | 100.00% | 0 | 0 | 5 hours | `PASS` |
| Violations | 1,000 | 998 | 99.80% | 0 | 2 | 5 hours | `WARN` |

注意兩種 warning 的差別：

- dbt command result：`WARN=0`，代表沒有 test 以 warning 結束；
- quality scorecard：violations 為 `WARN`，代表資料仍可發布，但存在透明的 source exceptions。

## 完整驗證結果

```text
13 models
114 data tests
3 sources
1 exposure

PASS = 127
WARN = 0
ERROR = 0
NO-OP = 1 exposure
TOTAL = 128
```

相比 Step 7：

```text
models:     9 -> 13
data tests: 67 -> 114
```

Quality-only build 也先獨立執行：

```text
4 audit views + 31 related tests = 35 PASS
```

Reader role 可以查詢 quality summary，表示 Snowflake future grants 對新建立的 views 正常生效。

## 為什麼不使用 test failure table 取代 audit views

dbt 可以使用 `store_failures` 保存 test failures，但本專案目前沒有用它作為主要 product，原因是：

1. test failure table 主要用於 developer debugging；
2. test 失敗資料通常只有某一次 test run 的 failing rows；
3. business 與 operations users 需要穩定命名、文件化的 quality views；
4. 已知 source exceptions 不一定應讓 test 失敗。

未來仍可在 development 或 continuous integration 中啟用 stored failures，兩者不是互斥的。

## 目前限制

- 所有 thresholds 都來自 bounded sample，而不是完整歷史 baseline；
- scorecard 是 current-state view，尚未保存每日品質趨勢；
- freshness 只量測 ingestion timestamp；
- quality status 尚未透過 email、Slack 或 incident system 發通知；
- 沒有自動修正 malformed source records；
- 沒有 valid Building Identification Number 的 records 仍不能進入 building snapshot；
- 完整 production service-level agreement 需要 stakeholder 確認。

## 知識點總結

- Data quality test 必須對應真正的 business risk。
- Known source exceptions 與 transformation bugs 應分開處理。
- Blocking tests 保護 data contract；audit views 提供調查細節。
- Threshold 應根據 baseline 與 consumer impact 設定。
- Generic tests 適合重複規則；singular tests 適合跨模型 business logic。
- Reconciliation 能抓到單一欄位 tests 看不到的 aggregation 錯誤。
- Freshness 應獨立執行並設定 warning/error windows。
- 新 status 不應默默進入 `UNKNOWN` 後繼續發布。
- Null foreign key coverage 比強迫每列 not null 更符合真實公開資料。
- Quality scorecard 與 command execution status 是不同層次的訊號。

## 官方文件

- [dbt：Data tests](https://docs.getdbt.com/docs/build/data-tests)
- [dbt：Singular and generic data tests](https://docs.getdbt.com/docs/build/data-tests#singular-data-tests)
- [dbt：Store data test failures](https://docs.getdbt.com/docs/build/data-tests#storing-data-test-failures)
- [dbt：Sources](https://docs.getdbt.com/docs/build/sources)
- [dbt：Source freshness](https://docs.getdbt.com/docs/build/sources#source-data-freshness)
- [dbt：Source command](https://docs.getdbt.com/reference/commands/source)
- [dbt：Severity, error_if, and warn_if](https://docs.getdbt.com/reference/resource-configs/severity)
- [dbt-utils package](https://hub.getdbt.com/dbt-labs/dbt_utils/latest/)
- [Snowflake：COUNT_IF](https://docs.snowflake.com/en/sql-reference/functions/count_if)
- [Snowflake：DATEDIFF](https://docs.snowflake.com/en/sql-reference/functions/datediff)

## 面試題與參考答案

### 1. How do you decide whether a data-quality issue should fail the pipeline?

I evaluate whether the issue can materially corrupt a published metric or violate a declared data contract. Duplicate grains, unmapped statuses, reconciliation failures, reversed lifecycle dates, and coverage below the service threshold are blocking. Known source defects that cannot be safely corrected remain visible in audit views and quality scorecards without making every run unusable.

### 2. Why did you not require every fact to have a non-null building key?

The official source contains legitimate records without a usable Building Identification Number. Requiring 100 percent completeness would create a permanent false alarm or encourage unsafe fuzzy matching. I retained those records, exposed them in an audit view, and enforced a measurable 99 percent coverage threshold instead.

### 3. What is the difference between a generic and a singular dbt data test?

A generic test is parameterized and reusable across resources, such as my `not_null_proportion_at_least` coverage test. A singular test is a project-specific SQL query that returns violations of one business rule, such as reconciling the current snapshot to several event facts.

### 4. How does a dbt data test work?

A dbt data test selects failing records. Zero returned rows means the assertion passes. One or more returned rows produce a failure or warning depending on the test configuration.

### 5. What does your reconciliation test protect against?

It independently calculates building count and key metrics from the dimensions and event facts, then compares them with the current daily snapshot. It can catch incorrect filters, join fan-out, status logic changes, or an incomplete incremental merge even when every individual column passes its own tests.

### 6. Why should a new unmapped status block publication?

The pipeline cannot know whether the new status should count as active, resolved, dismissed, or something else. Continuing would silently publish a business definition that has not been approved. The record remains preserved, but the test forces an explicit mapping decision before downstream metrics are trusted.

### 7. What is the difference between freshness and event recency?

Freshness measures how recently the warehouse received data, using the ingestion timestamp. Event recency describes the dates inside the business records. A pipeline can ingest an unchanged or stale upstream dataset today, so ingestion freshness alone does not prove that the source system produced new events.

### 8. Why did the violation quality score show `WARN` while dbt reported zero warnings?

The scorecard warning is a data-product status indicating known retained source exceptions: two unresolved building identities and two malformed dates. The dbt command had zero warnings because all blocking contracts and configured tests passed.

### 9. How would you choose a production coverage threshold?

I would profile the full historical distribution, segment it by source and time, measure the consumer impact of unmatched records, and agree on a service-level objective with stakeholders. I would then monitor both the absolute failure count and the percentage so small and large loads behave sensibly.

### 10. What would you add next for production observability?

I would persist daily quality metrics, compare them with historical baselines, monitor source watermarks and volume changes, store selected failing rows for incident debugging, connect the checks to orchestration, and route actionable failures to an owned notification channel.
