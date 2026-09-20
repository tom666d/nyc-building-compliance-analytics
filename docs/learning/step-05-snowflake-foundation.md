# Step 5：建立 Snowflake 資料倉儲基礎

## 這一步要完成什麼

Step 4 已證明 Python 能從 NYC Open Data 取得真實資料。Step 5 的工作，是準備一個安全、低成本、可重複建立的 Snowflake 環境，讓下一步可以把資料送入雲端資料倉儲。

本步建立的設計包括：

1. 一個專案 database；
2. 一個最小規模、會自動停止的 compute warehouse；
3. raw、staging、intermediate、marts 等 schemas；
4. 三個職責分離的 roles；
5. 三張保存原始 JSON 的 raw tables；
6. 一個每月用量安全上限；
7. 一個不修改資料的連線檢查工具；
8. 自動測試與英文正式文件。

## 先說清楚目前完成狀態

2026-09-20 已在真實 Snowflake trial account 完成雲端部署與唯讀驗證：

- 已完成：可執行的 Structured Query Language 腳本、角色與權限、warehouse、database、五個 schemas、三張 raw tables、resource monitor、自動測試、dbt schema 驗證與文件；
- 已驗證：46 個 bootstrap statements 全部成功，三個專案 roles 均能切換並通過預期的 object access checks；
- 後續已完成：key-pair Python/dbt 登入、三個 1,000-row 真實資料 samples，以及三個 staging views；
- 尚未完成：完整來源載入、dimensional marts、orchestration 與 business intelligence layer；
- 安全界線：account identifier、username、password 等本機設定不提交到 Git；
- 證據界線：目前可以說「Snowflake foundation 已部署」，但不能說「pipeline 已載入資料」或「dbt marts 已建好」。

這也是 data engineering 很重要的誠信原則：local validation 和 deployed validation 是兩種不同證據。

## 為什麼需要資料倉儲

Step 4 的 JSON Lines 適合保留與檢查小型 extraction，但不適合讓分析師反覆回答：

- 每棟建築有多少 open complaints？
- 哪些 borough 的 complaints 增加？
- permits、complaints、violations 如何依 Building Identification Number 關聯？
- 某個 metric 的定義是否一致？

Data warehouse（資料倉儲）是為分析查詢整理的集中式資料系統。它讓多個來源能經過一致的 transformation，成為可重複查詢、測試與文件化的 tables 或 views。

我們使用 Snowflake，是因為它能把 storage 與 compute 分開：資料可以留在 storage，只有執行載入或查詢時才啟動 compute warehouse。

## 核心結構

```text
Snowflake account
├── virtual warehouse: NYC_DOB_WH       ← 執行查詢的運算資源
└── database: NYC_DOB_ANALYTICS         ← 專案資料容器
    ├── RAW                              ← 原始來源 payload
    ├── DEV                              ← dbt 預設連線位置
    ├── DEV_STAGING                      ← 欄位重新命名與型別轉換
    ├── DEV_INTERMEDIATE                 ← 可重用中間邏輯
    └── DEV_MARTS                        ← 事實表、維度表與 BI tables
```

## 新名詞解釋

### Cloud data warehouse

Cloud data warehouse（雲端資料倉儲）是由雲端服務管理、主要支援分析型查詢的資料平台。它與一般應用程式的 transactional database 不完全相同：前者偏向掃描、彙總大量資料，後者偏向快速新增或更新單筆交易。

### Snowflake account

Account 是一個組織使用 Snowflake 的獨立管理範圍。Users、roles、warehouses、databases 與資源監控都存在某個 account 內。

### Database

Database 是 schemas 的上層容器。本專案使用：

```text
NYC_DOB_ANALYTICS
```

它代表整個 NYC DOB analytics 專案，而不是某一張表。

### Schema

Schema 是 database 內用來組織 tables、views 等 objects 的 namespace（命名空間）。

例如這兩個 object 可以同名，因為 schema 不同：

```text
NYC_DOB_ANALYTICS.RAW.BUILDINGS
NYC_DOB_ANALYTICS.DEV_MARTS.BUILDINGS
```

### Table 與 view

- Table 實際保存資料；
- View 保存一段查詢定義，每次讀取時依定義取得結果。

本專案 raw layer 使用 tables，dbt staging 預計使用 views，marts 預計使用 tables。

### Virtual warehouse

Snowflake virtual warehouse 是執行 loading、transformation 和 query 的 compute cluster。雖然名稱有 warehouse，但它不是資料存放位置。

可以用簡單比喻理解：

- database/table 是倉庫裡保存的貨物；
- virtual warehouse 是搬運與整理貨物的工作人員和機器。

停止 compute warehouse 不會刪除 database 裡的資料。

### Storage 與 compute 分離

Storage 是保存資料的容量；compute 是執行查詢需要的處理能力。兩者分開後，可以在不用查詢時停止 compute，仍保留資料。

### Credit

Credit 是 Snowflake 衡量資源使用量的計費單位。它不是固定美元價格；實際價格受版本、合約與地區影響。因此本專案的 one-credit monitor 是安全上限，不是費用預測。

### Auto-suspend 與 auto-resume

- Auto-suspend：warehouse 閒置一段時間後自動停止；
- Auto-resume：有查詢時自動重新啟動。

本專案閒置 60 秒後停止，降低忘記關閉 compute 的風險。

### Resource monitor

Resource monitor 追蹤 warehouse 使用的 credits，並能在指定百分比通知或停止 warehouse。

本專案設定：

- monthly quota：1 credit；
- 50%：通知；
- 75%：再次通知；
- 100%：立即停止 warehouse。

Resource monitor 不是萬無一失的預算系統，而且只涵蓋它監控的資源；仍需查看 account usage。

使用者還必須在 Snowflake preferences 啟用 resource-monitor notifications，email 也需要已驗證的地址。即使通知沒有設定好，100% 的 suspension trigger 仍是本專案真正的 enforcement control。

### User、role、privilege 與 grant

- User 是登入 Snowflake 的人或服務身分；
- Role 是一組工作權限；
- Privilege 是某個 object 上的特定操作權，例如 `SELECT` 或 `INSERT`；
- Grant 是把 privilege 給 role，或把 role 給 user 的動作。

關係可寫成：

```text
privilege → role → user
```

我們不把每個 privilege 零散地直接給 user，而是先依工作建立 roles，再把適合的 role 指派給 user。

### Role-based Access Control

Role-based Access Control 是「以角色管理權限」的方式，通常簡寫為 RBAC。本專案建立：

| Role | 可以做什麼 | 不應做什麼 |
|---|---|---|
| `NYC_DOB_LOADER` | 將 rows 寫入 raw tables、讀取驗證 | 建立或修改 dbt marts |
| `NYC_DOB_TRANSFORMER` | 讀 raw、在開發 schemas 建立 dbt objects | 寫入 raw source records |
| `NYC_DOB_READER` | 讀取 marts 供 BI 使用 | 讀 raw、修改 models |

### Least privilege

Least privilege（最小權限）表示一個人或程式只取得完成工作所需的最低權限。

如果 ingestion 程式被誤用，loader role 不應有權刪除 mart；如果 BI tool 被入侵，reader role 不應能改 raw data。這就是把角色拆開的實際價值。

### System role 與 custom role

Snowflake 內建 system roles，例如：

- `USERADMIN`：管理 users 和 roles；
- `SECURITYADMIN`：管理 grants；
- `SYSADMIN`：管理 warehouses、databases 與其他 objects；
- `ACCOUNTADMIN`：最高階 account 管理角色，應嚴格限制。

`NYC_DOB_LOADER` 等則是本專案建立的 custom roles。Snowflake 建議讓 custom-role hierarchy 最終接到 `SYSADMIN`，所以 bootstrap 有以下 grants：

```text
NYC_DOB_LOADER      ─┐
NYC_DOB_TRANSFORMER ─┼→ SYSADMIN
NYC_DOB_READER      ─┘
```

### Role hierarchy 與 privilege inheritance

Role hierarchy 是 role 可以被 grant 給另一個 role。上層 role 會繼承下層 role 的 privileges，稱為 privilege inheritance。

將 custom roles 接到 `SYSADMIN`，讓 system administrator 能管理它們所能存取的 project objects。

### Current grant 與 future grant

- `ON ALL TABLES` 對現在已存在的所有 tables 授權；
- `ON FUTURE TABLES` 對未來在 schema 內建立的 tables 自動授權。

只寫 future grant 不會補上既有 tables，所以兩者都需要。舊版 bootstrap 只給 transformer future raw-table access，這是本步修正的重要權限缺口。

### Structured Query Language

Structured Query Language 是操作 relational database 的語言，通常簡寫為 SQL。

常見分類：

- Data Definition Language：建立或修改結構，例如 `CREATE TABLE`；
- Data Manipulation Language：讀寫資料，例如 `SELECT`、`INSERT`；
- Data Control Language：管理權限，例如 `GRANT`、`REVOKE`。

### Raw layer

Raw layer 保存來源交付的資料與 ingestion metadata，不急著改成商業定義。這讓我們可以回頭回答：「來源當時到底給了什麼？」

### Semi-structured data 與 VARIANT

JSON 不一定每一列都有完全相同欄位，因此稱為 semi-structured data（半結構化資料）。Snowflake 的 `VARIANT` type 可以保存 JSON object。

三張 raw tables 都把來源 row 放在 `raw_payload VARIANT`，之後再由 dbt 將需要的欄位取出並轉型。

### Ingestion metadata

Metadata 是描述資料的資料。Raw table 除了 `raw_payload`，也保存：

- `source_dataset_id`：來源 dataset；
- `source_row_hash`：來源 row 的內容指紋；
- `load_id`：這次 load 的識別碼；
- `ingested_at`：收到資料的時間。

這些欄位支援 lineage、deduplication 與問題追查。

### Timestamp with time zone

`TIMESTAMP_TZ` 表示 timestamp 同時保存時區相關資訊。跨地區或比較不同執行環境時，比沒有時區的時間更不容易混淆。

### Environment variable 與 credentials

Environment variable 是由執行環境提供給程式的設定值。Credentials 是用來驗證身分的資訊，例如 username、private key 或 password。

程式從 `.env` 讀取 credentials，但 Git 只保存不含秘密的 `.env.example`。這避免把秘密寫死在 source code。

### Authentication 與 authorization

- Authentication 回答「你是誰？」；
- Authorization 回答「你能做什麼？」。

Key pair 或 username/password 屬於 authentication；roles 和 privileges 屬於 authorization。成功登入不代表有權存取每一張 table。

### Key-pair authentication

Key-pair authentication 使用 private key 證明程式身分，避免自動化長期保存一般使用者 password。Private key 必須放在安全的 secret manager，不能提交到 repository。

Step 5.5 已建立加密的 PKCS#8 private key 與專用 service user。本機 Python 和 dbt 都已透過 key-pair authentication 驗證；password 只保留為程式相容性 fallback，沒有用於本專案的雲端載入。

### Idempotent

Idempotent（冪等）表示同一個 setup 重複執行，不會每次都不受控制地建立重複 objects。

Bootstrap 使用 `IF NOT EXISTS` 與可重複的 `GRANT`。Warehouse 的 size、auto-suspend 和 auto-resume 也會重新套用。它不是完整 infrastructure-as-code state manager，但比只能執行一次的手動指令容易重現。

### Smoke test

Smoke test 是快速確認最重要功能是否可用的檢查。本專案的 `nyc-dob-snowflake-check` 不寫資料，只檢查：

- 是否能連線；
- active role 是否正確；
- 預期 schemas 是否可見；
- loader 與 transformer 是否看得到三張 raw tables；
- 是否有缺少 objects。

## 為什麼 dbt schema 不是只有 DEV

dbt project 設定了：

```text
target schema = DEV
custom schema = staging / intermediate / marts
```

dbt 的預設命名方式會把兩者組合：

| dbt model group | 實際 schema |
|---|---|
| staging | `DEV_STAGING` |
| intermediate | `DEV_INTERMEDIATE` |
| marts | `DEV_MARTS` |

本步實際執行 `dbt parse` 並讀取產生的 manifest，確認所有 models 的 resolved schema。這不是靠猜測，而是用 dbt 編譯結果驗證。

## 本步修正了哪些真實問題

舊 bootstrap 有四個會在真實執行時出現的缺口：

1. Raw tables 由 administrator 建立，但 loader 沒有既有 tables 的 `INSERT` privilege；
2. Transformer 只有 future-table grant，看不到已經建立的 raw tables；
3. dbt 實際需要 `DEV_STAGING`、`DEV_INTERMEDIATE`、`DEV_MARTS`，舊腳本只有 `DEV`；
4. Ingestion 原本預設使用 transformer role，違反職責分離。

新設計補上 existing 與 future grants、建立實際 dbt schemas，並讓 ingestion 明確使用 loader role。

## 實際操作順序

### 1. 在 Snowflake 執行 bootstrap

開啟 Snowsight worksheet，執行：

```text
infrastructure/snowflake/bootstrap.sql
```

執行者必須能切換到腳本使用的 system roles。最高權限只用於 account-level resource monitor。

### 2. 將 roles 指派給開發 user

複製並修改：

```text
infrastructure/snowflake/grant_roles.example.sql
```

把範例 username 換成自己的 Snowflake username，再由 `SECURITYADMIN` 執行。

### 3. 建立本機 `.env`

將 `.env.example` 複製為 `.env`，只在本機填入值。不要把 `.env` 加入 Git。

### 4. 執行 read-only check

```text
make snowflake-check
```

它會依序檢查 loader、transformer、reader 三個 roles。

### 5. 判讀結果

成功結果應包含：

```text
"ready": true
```

若 credentials 未設定，程式會明確列出缺少的 environment variable 名稱，但不會顯示任何 secret value。

## 自動測試與驗證結果

本步新增的 unit tests 驗證：

- loader 預設使用 `NYC_DOB_LOADER` 與 `RAW`；
- transformer 預設使用 `NYC_DOB_TRANSFORMER`，並尊重 dbt schema 設定；
- reader 預設使用 `NYC_DOB_READER` 與 `DEV_MARTS`；
- role 可以透過 environment variable 明確覆寫；
- credentials 缺少時只顯示 variable names，不洩漏 values。

此外，dbt manifest 已確認：

- 3 個 staging models → `DEV_STAGING`；
- 1 個 intermediate model → `DEV_INTERMEDIATE`；
- 5 個 mart models → `DEV_MARTS`。

2026-09-20 的雲端 worksheet 驗證結果：

- 46 個 bootstrap statements 全部成功；
- 三個 custom roles 已建立、接入 role hierarchy，並指派給開發 user；
- database 與 `RAW`、`DEV`、`DEV_STAGING`、`DEV_INTERMEDIATE`、`DEV_MARTS` 全部存在；
- `RAW` schema 內的預期 table 數量為 3；
- loader、transformer、reader 三個 roles 均能成功執行對應的唯讀 checks；
- warehouse 為 extra-small，auto-suspend 是 60 秒，auto-resume 已開啟；
- monthly resource monitor 已連接至 warehouse。

`DEV_MARTS` 目前仍有 0 張 table，因為 dimensional models 尚未執行。Step 5.5 後，三張 raw tables 已各載入 1,000 筆真實資料；Step 6 也已建立三個 staging views。

本機 `make snowflake-check` 已透過 service-user key pair 驗證 loader、transformer、reader，三個結果都是 `ready: true`。

## 知識點總結

- Snowflake 的 storage 和 compute 是不同概念；停止 warehouse 不會刪除資料。
- Database 包含 schemas；schema 包含 tables 和 views。
- Raw layer 保存 source payload 與 ingestion metadata，商業規則留給 dbt。
- Authentication 決定身分，authorization 決定權限。
- Role-based Access Control 比直接把零散 privileges 給 users 更容易管理。
- Least privilege 能限制誤操作或 credentials 外洩的影響範圍。
- Existing grants 和 future grants 解決不同時間點的 objects，通常兩者都需要。
- dbt custom schema 會影響實際 object 名稱，必須用 manifest 驗證。
- Auto-suspend、最小 warehouse size 與 resource monitor 是作品集環境的重要成本保護。
- Credentials 不應存在 Git；cloud object verification、local connector verification 與資料載入是三種不同證據。

## 官方文件

- [Snowflake：Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Snowflake：Configuring access control](https://docs.snowflake.com/en/user-guide/security-access-control-configure)
- [Snowflake：Virtual warehouses](https://docs.snowflake.com/en/user-guide/warehouses-overview)
- [Snowflake：Cost controls for warehouses](https://docs.snowflake.com/en/user-guide/cost-controlling-controls)
- [Snowflake：CREATE RESOURCE MONITOR](https://docs.snowflake.com/en/sql-reference/sql/create-resource-monitor)
- [Snowflake：Python Connector connection and authentication](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect)
- [dbt：Custom schemas](https://docs.getdbt.com/docs/build/custom-schemas)
- [dbt：Snowflake setup](https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup)

## 面試題與參考答案

### 1. Why did you create separate loader, transformer, and reader roles?

I applied least privilege and separated workloads. The loader can append raw source records, the transformer can read raw data and build dbt models in development schemas, and the reader can only query curated marts. This limits the impact of mistakes or compromised credentials and makes each access path easier to audit.

### 2. What is the difference between a Snowflake database and a warehouse?

A database is a logical container for persistent data objects such as schemas and tables. A virtual warehouse is compute used to load, transform, and query those objects. Suspending the warehouse stops compute consumption but does not remove the stored data.

### 3. Why do you store the source row as VARIANT?

The NYC Open Data responses are JSON and can contain optional fields. Keeping the complete source row in a VARIANT column preserves the delivered payload for auditability and replay. Typed fields and business rules are then made explicit and tested in dbt staging models.

### 4. Why are both current and future grants necessary?

Future grants apply to objects created after the grant is defined; they do not retroactively cover existing tables. Current grants cover objects already present. Using both avoids a gap during bootstrap and keeps access consistent as dbt creates new models.

### 5. How did you control Snowflake cost?

I selected an extra-small warehouse, enabled auto-resume, set auto-suspend to 60 seconds, started the warehouse suspended, and attached a monthly resource monitor that suspends it at a one-credit threshold. I also treat the threshold as a guardrail rather than a dollar forecast because credit pricing depends on the account agreement.

### 6. Why do the dbt schemas have names such as DEV_STAGING?

dbt's default schema naming combines the target schema with each configured custom schema. The target is DEV and the custom schema is staging, so the resolved schema is DEV_STAGING. I verified the names from the generated dbt manifest and provisioned grants for those actual destinations.

### 7. How do you know the setup is reproducible?

The database, schemas, tables, roles, grants, warehouse settings, and resource monitor are defined in version-controlled SQL. Object creation uses IF NOT EXISTS, mutable warehouse settings are reapplied, role checks are executable, and the Python configuration behavior is covered by unit tests.

### 8. Did you deploy this to Snowflake?

Yes. I executed the version-controlled bootstrap in a Snowflake trial account and verified the database, five schemas, three raw tables, three least-privilege roles, warehouse settings, and resource monitor. I later authenticated through a dedicated key-pair service identity, loaded 1,000 real rows per source, and built the three staging views. Dimensional marts remain a separate milestone.

### 9. Why not use ACCOUNTADMIN for the pipeline?

ACCOUNTADMIN has account-wide power and should be restricted. The pipeline only needs narrow data-loading privileges, so it uses a custom loader role. The bootstrap temporarily uses ACCOUNTADMIN only for the resource monitor operation that requires account-level authority.

### 10. How would you improve authentication before production automation?

I already replaced human-password authentication with an encrypted private key and a dedicated service identity for local automation. For production, I would put the key and passphrase in the orchestration or continuous-integration secret manager, use a separate identity per workload where practical, and rotate named key pairs according to policy.

## 自我檢查

進入 Step 6 前，應能用自己的話回答：

1. 為什麼 warehouse 不是保存資料的地方？
2. Database、schema、table 的包含關係是什麼？
3. Loader、transformer、reader 為什麼不能共用一個高權限 role？
4. Existing grant 和 future grant 有什麼差別？
5. 為什麼 raw payload 使用 `VARIANT`？
6. `DEV_STAGING` 名稱從哪裡來？
7. 哪些證據來自本機 tests、哪些來自真實 Snowflake account、哪些仍要等資料載入？
8. 為什麼 `.env` 不可以提交到 Git？
