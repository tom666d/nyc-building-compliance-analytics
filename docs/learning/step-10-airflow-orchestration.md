# Step 10：使用 Apache Airflow 自動執行資料管線

## 這一步完成了什麼

前九步已經有可以個別執行的工作：

```text
取得真實資料
  -> 寫入 Snowflake
  -> 檢查來源新鮮度
  -> 建立 dbt models
  -> 執行資料測試
  -> 產生文件與 lineage
  -> 檢查文件完整性
```

但在 Step 9 結束時，仍然需要人按照正確順序逐一輸入指令。Step 10 使用
Apache Airflow 將它們組成一條可排程、可重試、可觀察、失敗會停止的完整流程。

這一步實際完成：

1. 安裝 Apache Airflow 3.3.2，不需要申請另一個線上帳號；
2. 建立一個名為 `nyc_dob_daily` 的 Dag；
3. 定義 9 個 tasks 與它們的先後依賴；
4. 設定每天紐約時間早上 6 點的 schedule；
5. 設定 retries、timeouts、catchup 與 concurrency；
6. 讓三個資料來源在一般 scheduler 下可以平行執行；
7. 新增 retry-safe raw ingestion，避免同一次執行因重試而重複寫入；
8. 新增 Airflow Dag 結構自動檢查；
9. 使用真實 NYC Open Data 與 Snowflake 完成端到端測試；
10. 保留實際遇到的效能問題與修正理由，作為非照抄的開發證據。

## 為什麼需要 orchestration

假設每天都由人執行：

```text
1. load permits
2. load complaints
3. load violations
4. dbt source freshness
5. dbt build
6. dbt docs generate
7. documentation check
```

可能出現：

- 忘記其中一個步驟；
- 上游失敗，卻繼續發布舊資料；
- 不知道昨天究竟在哪一步失敗；
- 網路短暫中斷後，需要人半夜重跑；
- 同一份工作重跑後，raw table 多出重複資料；
- 兩次流程同時修改同一組 tables；
- 無法證明資料每天按照相同規則產生。

Orchestration 解決的不是 SQL 計算本身，而是「什麼時間、依什麼順序、在什麼條件下，可靠地執行所有工作」。

## 新名詞解釋

### Orchestration

Orchestration 中文可理解為「編排」。它負責協調多個工作之間的順序、依賴、排程、重試、狀態與失敗處理。

它像樂團指揮：指揮不代替每一位樂手演奏，但決定誰先開始、誰必須等待、失敗時如何處理。

### Apache Airflow

Apache Airflow 是開放原始碼的 workflow orchestration platform，也就是工作流程編排平台。本專案在自己的電腦安裝並執行，因此不需要再申請 Airflow 線上帳號。

Apache 是維護這個開放原始碼專案的基金會名稱，不代表要購買 Apache 的服務。

### Workflow 與 data pipeline

- Workflow：一組有先後關係的工作流程。
- Data pipeline：把資料從來源移動、轉換、測試並交付給使用者的流程。

本專案的 data pipeline 是一種 workflow。

### Dag：Directed Acyclic Graph

Dag 是 Directed Acyclic Graph，中文常譯為「有向無環圖」。

- Directed：箭頭有方向，例如 ingestion 指向 dbt build。
- Acyclic：不能繞一圈回到自己，否則工作永遠無法完成。
- Graph：由 nodes 與 edges 組成。

Airflow 現行文件使用 `Dag` 的寫法；程式類別仍是 `DAG`。本專案的 Dag ID 是 `nyc_dob_daily`。

### Task

Task 是 Dag 裡的一個可執行工作，例如：

```text
verify_loader_access
ingest_sources.permits
build_and_test
```

Dag 是整條流程，task 是其中一個步驟。

### Task instance

Task 是定義；task instance 是某次 Dag run 裡真正執行的那一份工作。

例如 `ingest_sources.permits` 每天都是同一個 task，但 9 月 20 日與 9 月 21 日的執行是不同 task instances，各自有開始時間、結束時間、狀態與 logs。

### Operator

Operator 是描述 task 如何執行的模板。本專案使用 `BashOperator`，讓 Airflow 執行已存在的 command-line commands。

雖然名稱含有 Bash，但重點不是把邏輯塞進 shell script，而是讓 Airflow 呼叫已經可獨立測試的 Python 與 dbt commands。

### Command-line interface

Command-line interface 是可以在 terminal 用文字指令操作程式的介面，常簡寫為 CLI。例如：

```text
nyc-dob-ingest permits
dbt build
```

Airflow 重複使用這些 CLI，所以同一份功能可以手動執行、在測試中執行，也可以被 scheduler 執行。

### TaskGroup

TaskGroup 是把相關 tasks 在 Airflow 圖上整理成一組的方式。本專案把 permits、complaints、violations 放進 `ingest_sources` 群組。

TaskGroup 主要改善可讀性，不會把三個 tasks 合併成一個 task。

### Dependency

Dependency 是相依關係。例如：

```text
ingest_sources >> check_source_freshness
```

意思是三個來源載入成功後，才能執行 freshness check。

### Upstream 與 downstream

- Upstream：目前 task 之前必須完成的工作。
- Downstream：目前 task 成功後才能開始的工作。

若 ingestion 失敗，所有 downstream publication tasks 都不應執行。

### Scheduler

Scheduler 是 Airflow 中判斷「現在有哪些 tasks 已達到執行條件」的元件。它會讀取 schedule、dependency 與目前狀態，再把可執行工作交給 executor。

### Executor

Executor 決定 tasks 實際用什麼方式執行。這個本機學習環境使用 Airflow standalone 提供的本機執行方式。正式環境可以使用適合多台機器或容器的 executor，但本專案沒有假裝已部署那種基礎設施。

### API server 與 web interface

API server 提供程式化介面，也支援瀏覽器中的 Airflow web interface。介面可以看到 Dag、tasks、run history、logs 與失敗位置。

### Dag processor

Dag processor 讀取 Python Dag files，把它們解析成 Airflow 可以排程的結構。如果 Dag file import 失敗，流程根本不會被正確註冊。

### Triggerer

Triggerer 負責等待非同步事件的 tasks，例如等待外部條件但不持續占用 worker。本專案目前沒有 deferrable tasks，但 `airflow standalone` 仍可能啟動這個元件。

### Metadata database

Metadata database 儲存 Airflow 自己的運行資料，例如 Dag runs、task states、timestamps 與設定。它不存放本專案的 NYC building business data。

本機使用 SQLite。SQLite 是一個輕量、單檔案資料庫，適合學習與本機測試；正式多人環境通常會選擇 PostgreSQL 等受支援的獨立資料庫。

### Dag run

Dag run 是整個 Dag 的一次執行。每個 run 有自己的 `run_id`、logical date 與總體狀態。

### Run ID

Run ID 是一次 Dag run 的唯一識別碼。本專案把它傳給三個 ingestion tasks，作為一致的 `load_id`。

### Logical date

Logical date 代表 Airflow 認為這次執行對應的資料時間，不一定等於程式真正開始執行的時鐘時間。這個差異對補跑、排程與資料分區很重要。

### Data interval

Data interval 是一次排程所代表的資料時間範圍。真正的 production incremental pipeline 常依 data interval 查詢某段時間內新增或更新的資料。

目前專案仍使用 bounded first slice，還沒有把 data interval 轉成來源 watermark。這被明確記為限制。

### Schedule

Schedule 是 Airflow 應在什麼時間建立新的 Dag run。本專案是紐約時間每天早上 6 點。

### Cron expression

Cron expression 是用五個欄位描述重複時間的格式：

```text
minute hour day-of-month month day-of-week
0      6    *            *     *
```

`0 6 * * *` 的意思是每天 06:00。

### Time zone 與 Daylight Saving Time

Time zone 是時區。本專案使用 `America/New_York`，而不是固定的協調世界時偏移，因此 Airflow 能依紐約的 Daylight Saving Time（夏令時間）規則調整。

### Catchup

Catchup 是 Airflow 是否自動補建 start date 到現在之間所有過去排程。若專案 start date 在幾個月前，開啟 catchup 可能突然建立幾百次執行。

本專案設定 `catchup=False`，避免第一次啟用就大量讀取 API 與使用 Snowflake credits。

### Backfill

Backfill 是刻意重新執行一段過去期間。Catchup 是 scheduler 自動補過去的 schedule；backfill 通常是操作人員明確要求補資料。兩者相關，但不是同一件事。

### Retry 與 retry delay

Retry 是 task 失敗後自動再試。Retry delay 是兩次嘗試之間等待多久。

本專案每個 task 最多重試兩次，間隔五分鐘。短暫的網路或 Snowflake 問題不一定要立刻變成人工事故。

### Timeout

Timeout 是允許工作執行的最長時間。它避免某個卡住的 process 永遠占用資源。

- 權限檢查：5 分鐘；
- ingestion：20 分鐘；
- freshness：10 分鐘；
- dbt build：45 分鐘；
- docs generation：15 分鐘；
- 整個 Dag run：2 小時。

### Concurrency 與 `max_active_runs`

Concurrency 是同時執行工作的能力。三個來源彼此沒有 dependency，因此正常 scheduler 可以同時執行。

`max_active_runs=1` 表示整條 Dag 同一時間只允許一個 active run，避免兩天的流程同時重建同一組 development tables。

### Parallelism

Parallelism 是實際能同時執行多少工作。Dag graph 允許平行，不代表任何測試工具一定平行。`airflow dags test` 為了本機整合驗證可能依序執行，但真正 scheduler 看到三個 source tasks 是可以同時執行的。

### Preflight check

Preflight check 是正式改資料前的前置檢查。本專案先確認 loader 與 transformer roles 可以看到必要 Snowflake objects，失敗就不進行 ingestion。

### Quality gate

Quality gate 是必須通過才能進入下一階段的檢查。本專案有三層：

```text
source freshness
  -> dbt data tests
  -> documentation contract
```

任何一層失敗，都不能把這次流程視為成功發布。

### Fail fast

Fail fast 是在已知不可能安全繼續時盡早失敗。例如 credentials 或 roles 不正確，就不需要先呼叫三個來源 API。

### Idempotency

Idempotency 中文常譯為「冪等性」。意思是同一個操作重複執行，最終結果與執行一次相同。

例如同一個 `load_id` 載入同樣 5 筆：

```text
第一次：inserted 5
第二次：inserted 0
```

若沒有 idempotency，Airflow retry 可能把暫時性失敗變成資料重複問題。

### Canonical JSON

Canonical JSON 是用固定 key 順序與固定格式序列化的 JavaScript Object Notation。相同內容即使原始 key 順序不同，也會得到相同文字，進而得到相同 hash。

### SHA-256 hash

SHA-256 是一種雜湊演算法，會把任意內容轉成固定長度的 fingerprint。本專案用它產生 `source_row_hash`，用於判斷兩個完整 raw payload 是否相同。

Hash 不是原始 business key，也不是用來還原原文的加密。

### Merge

Merge 是資料庫中可以依條件決定更新或插入的 statement。本專案只使用它的「not matched then insert」部分：當同一個 row hash 與 load ID 尚不存在時才新增。

### Batch

Batch 是一次處理一批資料。本步第一次完整測試發現，對 1,000 筆逐筆執行 merge 雖然正確，卻太慢。修正後每 250 筆組成一批，因此 1,000 筆只需要 4 次 merge。

這是一個重要工程證據：單元測試只能證明邏輯，真實整合測試才暴露遠端資料庫 round trip 的效能成本。

### DagBag

DagBag 是 Airflow 用來載入與收集 Dag definitions 的元件。本專案的 `check_airflow_dag.py` 使用它確認 Dag 可以 import，而且沒有 import errors。

### Structural contract

Structural contract 是對 Dag 結構的自動規則。本專案檢查：

- 必須正好有預期的 9 個 tasks；
- dependencies 正確；
- schedule 與 time zone 正確；
- catchup 關閉；
- 最多一個 active run；
- 初次註冊時 paused；
- retries 與 timeouts 存在；
- ingestion command 有穩定的 templated load ID。

這個檢查不連外，適合在 Step 11 的 continuous integration 使用。

### Jinja template

Jinja 是 Airflow 用來把執行時內容放入 task fields 的 template 語法。本專案的 `{{ run_id }}` 會在每次 run 被替換成該次真正的 run ID。

### Environment variable

Environment variable 是 process 執行時讀取的設定值。本專案用它提供：

- 專案位置；
- 每個來源的 records 上限；
- Snowflake connection settings；
- 這次執行的 load ID。

Credentials 不寫在 Dag file，也不進 Git。

### Virtual environment

Virtual environment 是隔離的 Python dependencies 空間。本專案有兩個：

- `.venv`：ingestion、dbt、tests；
- `.airflow-venv`：Apache Airflow 與 provider。

Airflow 依賴很多 packages，分開可以避免版本要求互相干擾。

### Constraints file

Constraints file 是固定一整組相容 package versions 的清單。Airflow 官方安裝方式搭配對應版本與 Python 版本的 constraints，降低 dependency conflict。

### Provider

Provider 是 Airflow 對特定服務或常用 operator 的獨立套件。Airflow 3 的 `BashOperator` 來自 standard provider，而不是核心 package。

### Integration test

Integration test 驗證多個真實元件真的能一起工作。本步的完整測試連接：

```text
Airflow + NYC Open Data + Python loader + Snowflake + dbt + documentation checker
```

它與 unit test 不同：unit test 快速驗證單一函式，不需要外部 API 或 Snowflake credentials。

### Observability

Observability 是能從 logs、states、timestamps 與 metrics 理解系統發生什麼事。Airflow 為每個 task instance 留下狀態與 logs，使失敗不再只是一個模糊的「今天資料沒更新」。

## Step 10.1：先保留既有責任邊界

我們沒有把 extraction 或 SQL business logic 搬進 Dag file。Airflow 只協調：

```text
Python ingestion owns extraction and raw loading
dbt owns transformations, tests, and documentation metadata
Airflow owns order, schedule, retries, and run state
```

這叫 separation of concerns，也就是「關注點分離」。每個工具只負責自己擅長的部分。

## Step 10.2：先驗證權限，再改資料

兩個 preflight tasks 分別使用：

- loader role：只能處理 raw ingestion 所需物件；
- transformer role：讀 raw 並建立 dbt schemas。

它們都成功後，三個 source tasks 才能開始。這同時展示 least privilege 與 fail fast。

## Step 10.3：讓來源獨立，但讓品質檢查等待全部完成

Permits、complaints、violations 不互相依賴，因此圖上是三條平行分支。Freshness task 則必須等待三條分支都成功。

這避免：

- 不必要地把三個來源串成慢速直線；
- 其中一個來源失敗時仍建立不完整的 building snapshot。

## Step 10.4：設計安全的 retries

若 API response 已取得、Snowflake 已寫入，但 task 在回報成功前中斷，Airflow 會重試。為此：

```text
Airflow run_id
  -> ingestion --load-id
  -> Snowflake MERGE ON source_row_hash + load_id
```

同一個 run 的 retry 使用同一個 key；下一天的新 run 則有新的 load ID，保留新的 extraction snapshot。

## Step 10.5：把品質與文件放進發布路徑

流程不是 `load -> build -> success`，而是：

```text
load
  -> freshness gate
  -> build + 115 data tests
  -> generate docs
  -> validate 118 mart columns + 15 source columns
  -> success
```

也就是說，品質與 documentation 不是開發者有空才做的附加工作，而是 publication contract。

## Step 10.6：控制成本與錯誤範圍

本專案使用 Snowflake trial account，所以：

- Dag 第一次出現時是 paused；
- `catchup=False`；
- 每個來源預設只讀 1,000 筆；
- 同時間只允許一個 Dag run；
- task 與整體都有 timeout；
- warehouse 仍保留前面步驟設定的 auto-suspend。

`paused` 表示不自動排程，不代表不能使用 `dags test` 做一次受控驗證。

## Step 10.7：第一次端到端測試學到什麼

第一次測試不是直接成功，這反而留下真正的工程決策證據。

### 問題一：CLI 還是舊版本

Airflow 呼叫的 package 是之前安裝時複製進 virtual environment 的版本，因此不認得新加入的 `--load-id`。

修正：把專案安裝改為 editable mode。Editable mode 讓 environment 指向目前 source code，開發時修改後不必每次重新封裝。

### 問題二：逐筆 merge 太慢

原始實作對 1,000 筆執行 1,000 次遠端 database statement。Unit tests 通過，但真實 Snowflake run 顯示 round trips 太多。

修正：先在記憶體移除相同 payload，再每 250 筆做一次 parameterized merge。受控驗證顯示：

```text
same load ID, first run: inserted 5
same load ID, second run: inserted 0
```

之後完整流程的每個 1,000-row source task 約在數秒內完成，而不是數分鐘仍未完成。

### 為什麼這對面試重要

這能說明你不是只把範例 Dag 貼進 repository。你：

- 遇到 packaging boundary；
- 用端到端測試重現；
- 找到 remote round-trip bottleneck；
- 保留 idempotency；
- 增加 unit test 與 dbt test；
- 再次用真實服務驗證。

## 實際驗證結果

2026-09-20 的受控 Dag run：

```text
Dag state: success
Task instances: 9/9 success
Permits ingested: 1,000
Complaints ingested: 1,000
Violations ingested: 1,000
Source freshness: 3/3 pass
dbt: PASS=128, WARN=0, ERROR=0, NO-OP=2, TOTAL=130
Published mart documentation: 118/118 columns
Source documentation: 15/15 columns
```

20 個 Python tests 也全部通過，其中包含 batch merge 與 stable load ID 行為。

## 我們沒有假裝完成的部分

1. 目前 local Airflow 使用 SQLite，不是高可用 production deployment。
2. 還沒有 notification recipient，所以沒有捏造 email 或 Slack alerts。
3. 每天讀取的是有上限的 ordered first slice，還沒有 source watermark。
4. 新 run 會保存新的 raw extraction snapshot，長期 retention policy 尚未定義。
5. Dag 預設 paused，不會在未經同意時每天使用 Snowflake credits。
6. 真正 Business Intelligence dashboard 仍在 Step 12。

這些限制不會讓作品變差。能明確區分「已驗證」與「下一階段」反而更可信。

## 本步知識點總結

完成 Step 10 後，你應該能用自己的話解釋：

1. Airflow 負責 orchestration，不負責 business transformation logic。
2. Dag 是整條 workflow，task 是其中一個工作，task instance 是某次真正執行。
3. Dependency 決定安全順序，沒有相依的 tasks 才能平行。
4. Schedule、time zone、catchup、backfill 與 logical date 是不同概念。
5. Retry 只有搭配 idempotent task 才安全。
6. `run_id + source_row_hash` 讓同一次 ingestion retry 不重複。
7. Source freshness、data tests 與 documentation contract 都是 quality gates。
8. `max_active_runs=1`、paused start 與 bounded loads 是成本和併發控制。
9. Airflow 與專案使用不同 virtual environments，是 dependency isolation。
10. Unit tests 與 live integration tests 找到的問題不同，兩種都需要。

## 官方文件

- [Apache Airflow Quick Start](https://airflow.apache.org/docs/apache-airflow/stable/start.html)
- [Apache Airflow Dags](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)
- [Apache Airflow Tasks](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html)
- [Apache Airflow Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html)
- [Cron and Time Intervals](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/cron.html)
- [BashOperator](https://airflow.apache.org/docs/apache-airflow-providers-standard/stable/operators/bash.html)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Airflow Command Line Interface](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [Snowflake MERGE](https://docs.snowflake.com/en/sql-reference/sql/merge)
- [dbt source freshness](https://docs.getdbt.com/reference/commands/source)

## 面試題與參考答案

### 1. 為什麼這個專案需要 Airflow？

**參考答案：**

> The individual ingestion and dbt commands already worked, but the data product still needed reliable ordering, scheduling, retries, run history, and blocking quality gates. I used Airflow to coordinate those existing commands. It gives the project one observable workflow from source access checks through ingestion, freshness, dbt tests, and documentation validation without moving transformation logic into the Dag.

### 2. 為什麼不用 cron？

**參考答案：**

> Cron can start a command at a time, but it does not naturally represent task-level dependencies, retry state, parallel source branches, or a visible run graph. Airflow made each failure stage explicit and allowed downstream publication to stop when freshness, data quality, or documentation failed.

### 3. Airflow Dag 裡為什麼使用 BashOperator？

**參考答案：**

> I already had tested command-line interfaces for ingestion, Snowflake access checks, and dbt. BashOperator let Airflow orchestrate those stable interfaces while keeping business logic outside the orchestration layer. That preserves portability: every command can still run locally or in continuous integration without importing Airflow.

### 4. 你的 task 如何做到 idempotent？

**參考答案：**

> Airflow passes the stable Dag run identifier into each ingestion task as a load ID. The loader hashes a canonical representation of each raw payload and merges on the combination of source row hash and load ID. If the same task retries, already committed rows do not insert again. A new Dag run uses a new load ID so it still preserves a new extraction snapshot.

### 5. 為什麼只用 source row hash 不夠？

**參考答案：**

> Using only the payload hash would remove the same unchanged record across different extraction runs and destroy snapshot-level audit history. Combining the hash with load ID prevents duplicates within one run while preserving evidence that the source record was observed again on a later run.

### 6. 如何證明 retry safety，不只是說它應該有效？

**參考答案：**

> I tested the merge behavior at three levels. Unit tests verify stable load IDs, page deduplication, and merge keys. A live controlled check loaded five records twice with the same load ID and observed five inserts followed by zero. A dbt singular test then checks every raw table for duplicate source-row-hash and load-ID combinations.

### 7. 為什麼 `catchup=False`？

**參考答案：**

> This is a bounded portfolio pipeline without a validated historical watermark design. Enabling catch-up could create many old runs and unnecessary API and Snowflake usage. I disabled it until historical intervals and late-arriving data have explicit semantics.

### 8. 為什麼 `max_active_runs=1`？

**參考答案：**

> The current development pipeline rebuilds shared dbt relations. Allowing two Dag runs to overlap could create write contention or publish inconsistent artifacts. Limiting the Dag to one active run is a simple safety control until the models and schemas are designed for concurrent runs.

### 9. 三個 ingestion tasks 是真的平行嗎？

**參考答案：**

> The dependency graph allows them to run in parallel because none depends on another. Actual parallel execution depends on the executor and available worker capacity. The local `dags test` integration command may execute them sequentially, while a running scheduler can dispatch them concurrently.

### 10. 為什麼 Airflow 要獨立 virtual environment？

**參考答案：**

> Airflow has a large, tightly constrained dependency set. I installed it with the official version-specific constraints in a separate environment so those dependencies do not force changes to the ingestion and dbt environment. The Dag then calls the project commands through absolute paths.

### 11. 你如何控制 portfolio project 的 Snowflake 成本？

**參考答案：**

> The Dag starts paused, catch-up is disabled, only one run can be active, and each source defaults to 1,000 rows. Tasks and the full run have timeouts, and Snowflake warehouse auto-suspend remains enabled. A cheap structural Dag test is separate from the live end-to-end test so routine validation does not consume warehouse credits.

### 12. 為什麼 build 前要做 source freshness？

**參考答案：**

> A successful transformation of stale inputs is still a bad publication. The freshness task acts as a gate after all three ingestions. If the declared source-age policy fails, Airflow stops before rebuilding and documenting marts as if they were current.

### 13. 第一次端到端測試找到什麼？

**參考答案：**

> It found two integration issues that unit tests could not expose. First, the installed command-line package was a stale non-editable copy, so Airflow could not see the new load-ID option. Second, executing one merge per row caused excessive Snowflake round trips. I changed development installation to editable mode and replaced row-by-row merges with parameterized batches of 250 while preserving the same idempotency key.

### 14. 這可以稱為 production-ready 嗎？

**參考答案：**

> It is production-minded and end-to-end verified, but I would not claim it is a production deployment. The local metadata database is SQLite, alerts are not connected to a real incident channel, and extraction still uses bounded slices instead of validated watermarks. The repository makes those limitations explicit and identifies them as the next operational design work.

### 15. Airflow 與 dbt 的責任如何區分？

**參考答案：**

> Airflow owns when work runs, task dependencies, retries, timeouts, and execution state. dbt owns SQL transformations, model dependencies, tests, documentation, and warehouse lineage. Keeping that boundary prevents business rules from being duplicated in an orchestration file.

## Step 10 完成標準

- [x] Airflow 使用官方 constraints 安裝在獨立 environment。
- [x] Dag 可以被解析，沒有 import error。
- [x] 9 個 tasks、dependencies、schedule 與 safety settings 有自動檢查。
- [x] 每個 task 有 retry 與 timeout。
- [x] 同一次 run 的 ingestion retry 不會重複寫入。
- [x] 三個 sources、freshness、dbt build、docs 與 contract 完整串接。
- [x] 真實端到端 Dag run 為 success。
- [x] 128 個可執行 dbt nodes 通過，0 warnings，0 errors。
- [x] 正式英文文件與 Architecture Decision Record 已保留。
- [x] 本步的知識點、官方文件、面試題與答案已整理。

下一步是 Step 11：建立 GitHub continuous integration，讓每次 proposed change 自動執行 Python tests、style checks、dbt parse 與 Airflow structural contract。
