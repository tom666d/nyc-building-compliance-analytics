# Step 9：建立文件與資料血緣

## 這一步完成了什麼

Step 8 已經證明資料通過品質規則，但一個 production-like data product 還必須讓別人回答：

- 這張表解決什麼問題？
- 每一列代表什麼？
- 每一個欄位的定義與限制是什麼？
- 數字從哪個官方來源而來？
- 哪些 models 會受到某次修改影響？
- 最後是哪個 dashboard 或 monitoring product 使用它？

本步完成：

```text
3 official raw sources
  -> 3 staging models
  -> 1 reusable intermediate model
  -> 1 building dimension + 3 event facts
  -> 1 daily snapshot + 4 quality views
  -> 2 downstream exposures
```

並且新增：

1. 9 個 published models 的完整 model descriptions；
2. 118/118 個 published physical columns 的 descriptions；
3. 3 個 sources 與 15/15 個 source columns 的 descriptions；
4. 可重複使用的 docs blocks；
5. 專案自己的 dbt documentation overview；
6. `building_compliance_360` 與 `data_quality_monitoring` exposures；
7. 把 model 與 column descriptions 寫入 Snowflake comments；
8. 自動比對 dbt definitions 與實體 Snowflake catalog 的 documentation contract；
9. recruiter 可以直接閱讀的英文 lineage 文件與設計決策紀錄。

## 為什麼這不是「補註解」而已

如果 analyst 看到：

```text
ACTIVE_PERMIT_RECORD_COUNT = 47
```

卻不知道它是：

- 47 張 unique permits；
- 47 個 approved source records；
- 還是 47 個目前未過期的 issued records；

那麼數字雖然可以查，卻不能安全使用。

本專案的定義是：

> Count of issued source records not expired on snapshot_date; not a unique permit count.

最後一句 `not a unique permit count` 很重要。它主動揭露 Step 2 profiling 發現的 grain 限制，而不是讓 dashboard 使用者誤以為那是 unique permit 數量。

Analytics Engineer 的工作不只讓 query 成功，也要讓 data product 可被正確發現、理解、信任與維護。

## 新名詞解釋

### Documentation

Documentation 是資料產品的說明文件。在 dbt 中，它可以包含 model、column、source、test、code、資料型別、相依關係與 downstream consumer。

### Metadata

Metadata 是「描述資料的資料」。例如：

- table 名稱；
- column 名稱與資料型別；
- model description；
- table owner；
- 上下游相依關係；
- 最近產生時間。

`1,000 complaints` 是 data；「這個 column 是 complaint number」是 metadata。

### Data catalog

Data catalog 是讓使用者搜尋與理解資料資產的目錄。它通常整合名稱、description、owner、schema、quality 與 lineage。

本專案使用 dbt 產生的 documentation site 作為基礎 catalog，而不是購買另一套商業產品。

### Data dictionary

Data dictionary 是欄位級定義清單，例如 column name、data type、business meaning 與允許值。它通常是 data catalog 的一部分。

### Data lineage

Data lineage 是資料從來源到最終產品的流向與相依關係。例如：

```text
raw complaints
  -> stg_dob_complaints
  -> fct_complaints
  -> fct_building_compliance_daily
  -> building_compliance_360
```

它回答「這個數字從哪來」以及「改這裡會影響哪裡」。

### Directed Acyclic Graph

Directed Acyclic Graph，中文可稱「有向無環圖」，常簡寫為 DAG。

- Directed：箭頭有方向；source 指向 downstream model。
- Acyclic：不能沿著箭頭走一圈回到原點。
- Graph：由 nodes 與 edges 組成。

dbt 根據 `source()` 與 `ref()` 自動建立 Directed Acyclic Graph，因此這不是人工猜測的流程圖。

### Node

Node 是圖中的一個節點，例如 source、model、test 或 exposure。

### Edge

Edge 是兩個 nodes 之間的有方向連線，表示相依關係。

### Upstream 與 downstream

- Upstream：產生目前資料的上游來源。
- Downstream：使用目前資料的下游 model 或產品。

例如 `fct_permit_records` 的 upstream 包含 staging permit model；downstream 包含 daily snapshot、quality views 與 dashboard exposure。

### Dependency

Dependency 是一個資產必須依賴另一個資產才能建立或使用的關係。dbt 的 `ref()` 不只替換 table name，也會建立 dependency 並決定執行順序。

### Impact analysis

Impact analysis 是修改前先檢查會影響哪些 downstream assets 與使用者。

例如修改 permit status mapping 之前，應看到它可能改變：

```text
permit fact
  -> daily building metrics
  -> business intelligence dashboard
  -> quality scorecard
```

### Discoverability

Discoverability 是使用者能否找到可用資料，並快速判斷它是否適合自己的問題。有 table 但找不到或看不懂，仍不是良好的 data product。

### Description

Description 是寫在 dbt YAML 設定檔中的人類可讀定義。YAML 是一種常用的結構化設定檔格式；本專案用它將 model 與 column metadata 放在程式碼版本控制中。

### Docs block

Docs block 是可以重複引用的 Markdown 長文字區塊。Markdown 是一種簡單的純文字排版語法。

本專案將 `building_key`、`source_dataset_id`、`ingested_at` 等共用定義放在 `models/_docs.md`，再用 `doc()` 引用，避免九個 models 各寫出不一致版本。

### Custom overview

Custom overview 是產生的 dbt documentation 首頁。本專案用名稱為 `__overview__` 的 docs block 說明用途、公開資料產品與限制，取代一般性的預設首頁。

### Exposure

Exposure 是 dbt graph 中代表 downstream 使用方式的節點，例如 dashboard、notebook、application 或 machine learning pipeline。

Exposure 不會建立資料表，所以 dbt build 中顯示 `NO-OP`，意思是「沒有資料庫操作」，不是失敗。

本專案有：

- `building_compliance_360`：未來的商業智慧 dashboard；
- `data_quality_monitoring`：品質 scorecard 與 exception investigation 使用情境。

### Business Intelligence

Business Intelligence，常簡寫為 BI，是把資料轉成 dashboard、report 與決策資訊的實務。真正的 BI layer 會在 Step 12 建立；Step 9 只先誠實宣告 planned exposure。

### Maturity

Exposure maturity 表達 downstream product 的穩定程度：low、medium 或 high。

- planned dashboard 目前是 low；
- 已有可查詢品質 views 的 monitoring exposure 是 medium；
- 沒有任何產品被誇大成 high。

### `persist_docs`

`persist_docs` 是 dbt 設定，會把 YAML descriptions 寫入支援的資料庫 relation comments 與 column comments。

Relation 是資料庫中可以被查詢的物件，例如 table 或 view。Comment 是附在 relation 或 column 上的 metadata。

### Manifest

Manifest 是 dbt 解析專案後產生的 JavaScript Object Notation file，檔名是 `manifest.json`。JavaScript Object Notation，常簡寫為 JSON，是一種結構化文字格式。

Manifest 記錄：

- models、sources、tests、exposures；
- descriptions；
- dependencies；
- compiled metadata。

它代表「專案宣告自己應該是什麼」。

### Catalog

本步的 `catalog.json` 是 dbt 查詢 Snowflake metadata 後產生的 catalog artifact，包含實體 relations、columns、types 與 comments。

它代表「Snowflake 實際存在什麼」。

### Artifact

Artifact 是工具執行後產生、可供其他工具讀取的結構化輸出。Manifest 與 catalog 都是 dbt artifacts。

它們放在 `target/`，不進 Git，因為：

- 可以重新產生；
- 內容與特定執行環境有關；
- 每次 build 可能造成大量無意義 diff。

### Documentation coverage

Documentation coverage 是已文件化資產占應文件化資產的比例。

本步開始時：

```text
published physical columns documented = 25 / 118
```

完成後：

```text
published physical columns documented = 118 / 118
source physical columns documented = 15 / 15
```

### Documentation drift

Documentation drift 是文件與實體資料結構逐漸不一致。兩種常見情況：

1. SQL 新增了 column，但 YAML 沒有 description；
2. SQL 移除了 column，但 YAML 留著舊 definition。

本步的自動檢查兩種都會失敗。

### Contract

Contract 是明確、可檢查的約定。Documentation contract 表示「發布資料前必須有完整且未漂移的 metadata」，不是靠 developer 記得做。

## Step 9.1：先量測，不先宣稱完成

dbt 會從 Snowflake introspect physical columns。Introspect 是工具主動讀取資料庫 metadata 的動作。

這代表：即使 column 沒有寫 description，它仍可能出現在 dbt docs 網頁上。因此：

```text
dbt docs generate succeeded
```

不等於：

```text
all columns are documented
```

我們先比較舊的 `manifest.json` 與 `catalog.json`，找到：

```text
published models: 9
published physical columns: 118
columns with authored descriptions: 25
```

這個 baseline 很重要，因為面試時可以說明具體改善，而不只是「我加了一些 docs」。

## Step 9.2：補齊 model 與 column business definitions

每個 published model description 必須至少說明：

- grain；
- data source 或 scope；
- 重要限制。

每個 column description 不是把 column name 換句話說，而是回答：

- 它代表什麼？
- 怎麼計算？
- 使用哪個時間點？
- 可以是 null 嗎，為什麼？
- 有什麼不能做的解讀？

例如：

```text
approval_to_issue_days
```

被定義為 approval 到 issuance 的 calendar days，任何一個日期缺少時是 null。這比只寫「days to issue」更精確。

## Step 9.3：用 docs blocks 管理共用定義

`building_key` 會出現在 dimension、三張 event facts、daily snapshot 與多個 quality views。

若每一處自己寫，長期可能變成：

```text
surrogate key
building id
hashed BIN
warehouse key
```

看似類似，實際上讓使用者懷疑是不是不同東西。

本專案用同一個 docs block 定義：它是由 validated Building Identification Number 決定性產生的 warehouse surrogate key，不是 NYC Open Data 原生欄位。

「決定性」表示相同輸入總是得到相同結果。

## Step 9.4：文件化 sources

三張 raw tables 每張都有五個 physical columns：

```text
raw_payload
source_dataset_id
source_row_hash
load_id
ingested_at
```

Source description 說明它來自哪一個官方 dataset；column descriptions 說明 lineage metadata 的用途。

要注意：dbt `persist_docs` 不會替 declared sources 寫 database comments，因為 sources 是 dbt 之外已存在的 objects。它們仍會出現在 dbt documentation 中。

## Step 9.5：建立真實 lineage，而不是手動畫好看的圖

SQL 中的：

```text
source('dob_raw', 'complaints')
ref('stg_dob_complaints')
```

讓 dbt 知道 upstream dependency。dbt 可以依此：

- 排定 build order；
- 產生 lineage graph；
- 依 exposure 選出所有 ancestors；
- 幫助 impact analysis。

英文文件中的 Mermaid diagram 是閱讀版摘要。Mermaid 是用純文字描述流程圖的語法。真正可執行的 lineage authority 仍是 dbt graph。

## Step 9.6：用 exposures 接到 business value

只有 models 的 graph 會在資料倉儲結束；加上 exposure 後，lineage 延伸到使用者產品。

本專案移除了原本的：

```text
https://example.invalid/replace-with-bi-url
replace-me@example.com
```

原因不是「placeholder 不好看」，而是它會假裝一個尚未存在的 dashboard 已部署，也會讓 reviewer 點到無效內容。

Exposure 的 `url` 是 optional，所以 Step 12 真正發布 dashboard 前，最誠實做法是先不填。

## Step 9.7：把 definitions 寫入 Snowflake

專案設定：

```text
persist_docs:
  relation: true
  columns: true
```

然後重新執行 dbt build。這讓 description 同時存在：

```text
Git-controlled YAML
  -> dbt generated documentation
  -> Snowflake relation and column comments
```

這很重要，因為不是每位 analyst 都會先開 GitHub。有人可能直接在 Snowflake worksheet 或另一個 catalog 工具中發現 table。

## Step 9.8：建立自動 documentation contract

新增指令：

```text
make dbt-docs-check
```

它會先產生最新 dbt documentation，再比較 `manifest.json` 與 `catalog.json`。

失敗條件包含：

1. published model 沒有 description；
2. 任一 physical published column 沒有 description；
3. YAML 描述了一個 Snowflake 不存在的 column；
4. raw source table 或 physical source column 沒有 description；
5. exposure 沒有 description 或 owner；
6. exposure 還有 placeholder URL 或 contact。

這個 script 也有 unit tests。Unit test 是針對一小段程式邏輯的自動測試；測試刻意建立缺 description、placeholder 與 stale column 的情況，確認 contract 真的會擋下來。

## Step 9.9：實際驗證結果

### dbt parse

先執行 parse，確認 YAML、docs block 引用與 graph dependency 都合法。

```text
13 models
114 data tests
3 sources
2 exposures
```

### dbt build

重新 build 後：

```text
PASS = 127
WARN = 0
ERROR = 0
NO-OP = 2 exposures
TOTAL = 129
```

兩個 exposure 是 metadata nodes，不建立 Snowflake object，所以 `NO-OP` 是預期行為。

### Documentation contract

```text
published models: 9
published columns: 118/118 documented
sources: 3
source columns: 15/15 documented
exposures: 2
Documentation contract passed.
```

### Snowflake comments

重新產生 catalog 後，9 張 published relations 全部有 relation comment，118 個 published columns 全部有 column comment。

這是三層證據：

```text
declaration: YAML has descriptions
generation: manifest and catalog agree
deployment: Snowflake exposes the comments
```

## 哪些檔案是 recruiter 應該看的

- `docs/lineage.md`：英文 end-to-end lineage 與驗證證據；
- `docs/decisions/0009-documentation-is-a-release-contract.md`：為何把 docs 當 release contract；
- `dbt/nyc_building_compliance/models/_docs.md`：overview 與 reusable definitions；
- marts YAML files：完整 published data dictionary；
- `models/marts/operations/bi_metrics.yml`：downstream exposures；
- `scripts/check_dbt_documentation.py`：自動 coverage enforcement。

這些 artifacts 顯示的不是「照 tutorial 產生一個 docs 網頁」，而是你先量測缺口、定義 contract、處理真實 grain 限制、避免假 dashboard link，再用 Snowflake catalog 驗證部署結果。

## 本步知識點總結

1. dbt documentation 同時結合 code metadata、warehouse metadata 與 dependency graph。
2. Lineage 的主要價值是 traceability 與 impact analysis，不只是視覺化。
3. Model description 應先說 grain，column description 應說 business meaning 與限制。
4. dbt docs 成功產生，不代表 documentation coverage 完整。
5. Manifest 表達 project declaration；catalog 表達 warehouse reality。
6. Docs blocks 可以集中共用定義，降低 wording drift。
7. Exposure 把 warehouse models 連到 downstream business product。
8. 尚未存在的 dashboard 不應填 fabricated URL。
9. `persist_docs` 讓 definition 在 Snowflake 中也可被發現。
10. Documentation coverage 應成為可失敗的 release contract。
11. Generated artifacts 可以重新產生，不應為了展示而全部提交 Git。
12. 100% coverage 只證明 definitions 存在；內容是否正確仍要 human review。

## 官方文件

- [dbt：About documentation](https://docs.getdbt.com/docs/build/documentation)
- [dbt：docs command](https://docs.getdbt.com/reference/commands/cmd-docs)
- [dbt：description property](https://docs.getdbt.com/reference/resource-properties/description)
- [dbt：docs blocks and custom overview](https://docs.getdbt.com/docs/build/documentation#using-docs-blocks)
- [dbt：persist_docs](https://docs.getdbt.com/reference/resource-configs/persist_docs)
- [dbt：Exposures](https://docs.getdbt.com/docs/build/exposures)
- [Snowflake：Information Schema](https://docs.snowflake.com/en/sql-reference/info-schema)
- [Snowflake：COLUMNS view](https://docs.snowflake.com/en/sql-reference/info-schema/columns)
- [Snowflake：TABLES view](https://docs.snowflake.com/en/sql-reference/info-schema/tables)

## 面試題與參考答案

### 1. What is data lineage, and why does it matter?

參考答案：

> Data lineage shows how data moves from source systems through transformations to downstream products. It supports traceability, impact analysis, incident investigation, and stakeholder communication. In my project, dbt derives model-level lineage from `source()` and `ref()` dependencies and extends it to two downstream exposures.

### 2. How did you validate documentation completeness?

參考答案：

> I did not treat successful docs generation as proof of completeness because dbt can introspect and display undocumented warehouse columns. I built a contract that compares the authored manifest with the physical Snowflake catalog. It requires descriptions for all published models, all 118 physical mart columns, all three source tables and their 15 physical columns, and meaningful exposure metadata. It also detects stale column declarations.

### 3. What is the difference between `manifest.json` and `catalog.json`?

參考答案：

> The manifest represents the parsed dbt project: resources, descriptions, tests, dependencies, and exposures. The catalog represents warehouse metadata such as physical relations, columns, data types, and comments. Comparing them helps detect documentation drift between declared intent and deployed reality.

### 4. What is an exposure in dbt?

參考答案：

> An exposure represents a downstream use of dbt data, such as a dashboard or application. It connects technical lineage to a business-facing consumer. I defined one exposure for the planned Building Compliance 360 dashboard and another for data quality monitoring.

### 5. Why did you remove the dashboard URL?

參考答案：

> The dashboard is planned for a later phase and the URL property is optional. Keeping a fake link would misrepresent the implementation state. I kept the exposure and its dependencies, but I will add the URL only when a real dashboard is deployed.

### 6. What does `persist_docs` do?

參考答案：

> It writes dbt model and column descriptions into supported warehouse relation and column comments. That improves discoverability for users working directly in Snowflake. I verified the deployment by regenerating the catalog and confirming comments on all nine published relations and all 118 published columns.

### 7. Why use docs blocks instead of repeating descriptions?

參考答案：

> Shared concepts such as the building key and ingestion metadata appear in multiple models. Reusable docs blocks create one governed definition and reduce inconsistent wording. Model-specific columns still receive local descriptions where the meaning depends on context.

### 8. Is 100% documentation coverage enough?

參考答案：

> No. Coverage proves that documentation exists and aligns structurally with the warehouse, but it cannot prove that the wording is accurate or useful. Human review, business validation, tests, and observed data behavior are still required.

### 9. How would lineage help during a change?

參考答案：

> If I change permit status mapping, lineage shows that the permit fact, daily building snapshot, business intelligence exposure, and quality monitoring exposure may be affected. I can select the appropriate downstream models and tests and communicate the potential metric change before release.

### 10. Why not commit the generated dbt site to Git?

參考答案：

> The generated target directory contains environment-specific, reproducible artifacts and creates noisy diffs. I commit the source definitions, the documentation contract, and design decisions instead. A reviewer with the configured warehouse can regenerate the same catalog using a documented command.

### 11. How is this different from commenting SQL?

參考答案：

> SQL comments mainly help developers reading transformation code. dbt descriptions become structured metadata that appears in the catalog, lineage site, manifest, and Snowflake comments. Exposures also connect definitions to downstream products, which ordinary SQL comments do not provide.

### 12. What was the measurable improvement in this step?

參考答案：

> The baseline had descriptions for only 25 of 118 published physical columns. After the change, all 118 mart columns and all 15 physical source columns were documented, two exposures were represented in lineage, all warehouse comments were persisted, and the full dbt build completed without warnings or errors.

## 你現在應該能用自己的話說明

完成 Step 9 後，你應該可以不看答案說明：

1. documentation、catalog 與 lineage 的差別；
2. Directed Acyclic Graph 如何由 nodes 與 edges 組成；
3. `source()`、`ref()` 與 exposure 如何形成 end-to-end lineage；
4. 為什麼 docs generation success 不等於 100% coverage；
5. manifest 與 catalog 各自代表什麼；
6. 為什麼要把 descriptions persist 到 Snowflake；
7. 如何用 documentation contract 防止 schema drift；
8. 為什麼 planned dashboard 不應放假 URL；
9. 這套文件系統如何讓 analyst、operator 與 recruiter 各自受益；
10. 100% coverage 的價值與限制。
