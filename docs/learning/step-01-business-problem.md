# Step 1：定義商業問題與成功標準

## 這一步要完成什麼

在選擇 Snowflake、dbt 或任何程式工具以前，先確定這個專案要幫助誰、解決什麼問題，以及如何判斷它有價值。

完成這一步後，你應該能在不提技術工具的情況下，用兩分鐘向面試官說清楚：

1. 使用者目前遇到什麼困難；
2. 這個專案提供什麼改善；
3. 使用者能因此做出什麼更好的決策；
4. 專案第一階段包含與不包含什麼。

## 為什麼不能先從工具開始

公司聘請 Analytics Engineer，不只是為了「會用 dbt」或「會寫 Structured Query Language」。工具的目的，是把原始資料轉換成可信任、可重複使用的資訊，幫助公司做決策。

如果沒有先定義商業問題，容易發生三件事：

- 建立很多資料表，卻沒有人知道要拿來做什麼；
- 指標看起來合理，但不同使用者對「open」或「active」有不同理解；
- 為了展示技術而增加不必要的複雜度。

因此，這個 portfolio project 的順序是：

```text
使用者的決策
    ↓
需要回答的問題
    ↓
需要定義的指標
    ↓
需要的資料
    ↓
最後才選擇資料模型與工具
```

## 真實情境

假設一位 building compliance manager 想了解某棟建築物目前的合規狀況。他可能需要分別查看：

- 最近收到哪些 complaints；
- 有哪些尚未處理的 violations；
- 有哪些 permits 已核准、發出或即將到期。

這些資訊位於不同的 New York City Department of Buildings（紐約市建築局，以下簡稱 NYC DOB）公開資料集，使用的狀態、日期和識別欄位也不完全相同。使用者必須自己搜尋、整理並解釋資料，分析人員也可能各自定義「尚未結案」或「有效許可」。

## 一句話商業問題

> NYC building compliance data is fragmented across permit, complaint, and violation datasets, making it difficult to obtain a consistent and timely view of a building's regulatory activity and unresolved workload.

中文意思：

> 紐約市建築合規資料分散在許可、投訴與違規資料集中，使用者難以及時取得某棟建築一致的監管活動與未解決工作量全貌。

這句話刻意使用 **regulatory activity** 和 **unresolved workload**，而不是直接宣稱一棟建築「安全」或「危險」。公開資料中的投訴不一定成立，違規資料也可能有來源範圍限制，因此我們不能做超過資料證據的法律或安全判斷。

## 提議的解決方案

建立一個 Building Compliance and Permit Analytics Platform，將官方公開資料轉換成：

- 可追溯到來源的 permit、complaint 和 violation 明細；
- 一致的 building identity；
- 清楚定義的 open、active、resolution time 等指標；
- 每棟建築一列的每日摘要，供 dashboard 或進一步分析使用；
- 可看見更新時間、資料品質問題和定義的文件。

## 利害關係人、決策與資料產品

| 利害關係人 | 他需要做的決策 | 專案提供的資訊 | 未來主要模型 |
|---|---|---|---|
| Department of Buildings operations manager | 哪些案件或建築應優先檢查或處理？ | 未結投訴、未結違規、案件年齡 | `fct_complaints`、`fct_violations` |
| Property compliance manager | 哪些物業需要後續行動？ | 建築層級的未結項目與近期活動 | `fct_building_compliance_daily` |
| Construction program manager | 許可流程在哪裡變慢？ | 核准到發照天數、狀態與到期日 | `fct_permit_records` |
| Real-estate risk analyst | 哪些物業需要更深入的人工盡職調查？ | 可解釋的合規活動與資料涵蓋標記 | building daily snapshot 與明細 facts |
| Analytics team | 如何避免每份報告重新定義指標？ | 受測試、受文件化、可重複使用的模型 | 全部 analytics marts |

這些角色是用來定義可能的分析需求，不代表本專案由 NYC Department of Buildings 委託，也不代表已訪談這些單位。

## 第一階段的成功標準

第一階段成功，不以 dashboard 漂不漂亮判斷，而看以下項目是否成立：

1. 能從官方 NYC Open Data 載入一小批真實資料，而不是使用 synthetic data；
2. 同一個 complaint、permit 或 violation 不會因重複載入而在模型中被重複計算；
3. 每個主要資料模型都有明確 grain；
4. 使用者能追查一個 building summary 數字來自哪些明細與官方來源；
5. 關鍵欄位、關聯與資料新鮮度有自動化檢查；
6. 缺少 Building Identification Number 的紀錄不會被悄悄丟棄；
7. 限制、假設與尚未完成的資料範圍有明確文件。

## 第一階段不做什麼

- 不把分析結果當作官方法律或安全判定；
- 不建立無法解釋的綜合風險分數；
- 不用模糊地址比對強迫連接無法確認是同一棟建築的紀錄；
- 不聲稱已涵蓋所有 Department of Buildings 系統；
- 不直接合併可能互相重複的新舊 violation 資料。

清楚寫出 non-goals 並不是示弱，而是證明我們了解資料邊界，沒有為了讓結果看起來完整而犧牲可信度。

## 新名詞解釋

### Analytics Engineer

Analytics Engineer（分析工程師）負責把原始資料轉換成可信任、容易分析且能重複使用的資料模型。這個角色介於 Data Engineer（資料工程師）與 Data Analyst（資料分析師）之間：既關心資料轉換、測試與部署，也關心指標是否符合商業語意。

### Stakeholder

Stakeholder（利害關係人）是會使用、影響，或受到專案結果影響的人或團隊。例如 operations manager、property manager 和 analytics team。

### Data product

Data product（資料產品）是為特定使用者和決策持續提供價值的資料資產。它不只是一次性的查詢或圖表，還需要有明確用途、品質、文件、負責人與更新方式。

### Metric

Metric（衡量指標）是依照固定商業定義計算的數值，例如 open complaint count 或 average resolution days。只有公式不夠，還需要說明範圍、狀態定義、時間邏輯和例外情況。

### Key Performance Indicator

Key Performance Indicator（關鍵績效指標）是用來判斷重要業務目標是否達成的指標。不是所有 metric 都是 Key Performance Indicator；只有和目標直接相關的衡量方式才算。

### Grain

Grain（資料粒度）說明一張資料表中的「每一列代表什麼」。例如 complaint fact 的每一列代表一筆 complaint；building daily snapshot 的每一列代表某一天的某一棟建築。資料粒度不清楚，是重複計算最常見的原因之一。

### Source of truth

Source of truth（可信任的統一資料來源）是團隊共同採用的資料與定義來源。它不代表資料永遠完美，而是定義、更新方式、品質和限制都透明，避免每個人各算一套。

### Synthetic data

Synthetic data（合成資料）是人工製造、模擬真實資料特性的資料。它適合測試某些情境，但這個 portfolio 優先使用官方公開資料，因為真實資料中的缺值、重複、狀態差異與來源限制，更能展示 Analytics Engineering 能力。

### Permit、complaint 與 violation

- Permit（許可證）是主管機關核准特定建築工作的正式許可紀錄。
- Complaint（投訴）是主管機關收到的問題通報；它本身不等於問題已被證實。
- Violation（違規紀錄）是主管機關認定未符合適用規定而發出的紀錄。本專案使用的不同 violation 資料來源可能有不同涵蓋範圍。

### Fact table

Fact table（事實表）記錄可被計數、衡量或分析的業務事件。這個專案的 complaint fact table 每一列代表一筆 complaint，permit fact table 每一列代表一筆特定粒度的 permit 紀錄。

### Data mart

Data mart（主題資料集市）是針對特定分析主題整理好的資料模型集合。例如 compliance operations data mart 會集中提供未結投訴、違規和許可活動，而不是要求使用者直接理解原始資料。

### Dashboard

Dashboard（儀表板）是把重要指標與趨勢以圖表、數字卡或表格呈現的使用介面。儀表板是資料的消費方式，不是本專案唯一的資料產品。

### Portfolio project

Portfolio project（作品集專案）是用來展示個人能力、思考過程和成果的專案。本專案必須清楚區分真實官方資料、我們自己的設計假設，以及尚未經領域使用者驗證的定義。

## 與 CBES 經驗的連結

這個專案與 CBES 的產業不同，但解決問題的方式一致：

```text
CBES：分散的 sales、pricing、inventory、foreign exchange 資料
  → 統一衡量方式與 reporting workflow
  → 減少人工整理，支援更快決策

NYC DOB project：分散的 permit、complaint、violation 資料
  → 統一 building identity 與指標定義
  → 減少人工查找，支援 compliance 與 operations 決策
```

共同主線是：

> Fragmented operational data → standardized business logic → reusable data products → self-service decision support

也就是：分散的營運資料 → 統一商業邏輯 → 可重複使用的資料產品 → 使用者可自行取得決策資訊。

## 兩分鐘面試說法

> I built this project to solve a common analytics engineering problem: operational data existed, but it was fragmented across separate permit, complaint, and violation datasets with inconsistent identifiers and status definitions. I designed a building-level analytics platform that preserves source-level detail, standardizes business logic, tests data quality, and publishes a daily compliance summary for operational prioritization and drill-through analysis. I deliberately avoided an opaque risk score and documented source coverage limitations, because the goal is to create trusted and explainable decision support rather than overstate what the public data can prove.

如果面試官問到和過去經驗的關係：

> At CBES, I encountered a similar pattern with fragmented pricing, sales, inventory, and foreign-exchange data. I initially improved the downstream reporting process through automation and reusable reports. This project shows how I would now solve the same class of problem further upstream by creating tested, documented, reusable data models.

## 知識點總結

- 技術專案應從使用者決策開始，而不是從工具開始。
- 商業問題必須包含使用者、目前痛點和預期改善。
- 每個 metric 都需要明確定義；不能只看名稱猜意思。
- grain 決定每列代表什麼，是資料模型設計的基礎。
- non-goals 和限制能提升可信度，不是專案缺點。
- 真實資料的價值在於能展示如何處理不完整、重複和不一致。
- 這個專案和 CBES 的連結是問題解決模式，不是產業本身。

## 官方資料與延伸閱讀

- [NYC Open Data：DOB NOW Build Approved Permits](https://data.cityofnewyork.us/d/rbx6-tga4)
- [NYC Open Data：DOB Complaints Received](https://data.cityofnewyork.us/d/eabe-havv)
- [NYC Open Data：DOB Violations](https://data.cityofnewyork.us/d/3h2n-5cm9)
- [NYC Department of Buildings：Construction Safety and Compliance](https://www.nyc.gov/site/buildings/dob/construction-safety-compliance.page)
- [dbt Labs：What is analytics engineering?](https://www.getdbt.com/what-is-analytics-engineering)

## 面試題與參考答案

### 1. Why did you choose this project?

I wanted a project that demonstrates more than dashboard development. NYC Department of Buildings data contains realistic analytics engineering challenges: separate operational sources, inconsistent status logic, shared but imperfect building identifiers, changing source records, and the need for explainable metrics. It lets me demonstrate how I turn fragmented operational data into a trusted analytical product.

### 2. Who is the primary user?

The initial product is designed for an operations or property compliance user who needs a building-level view of unresolved complaints, violations, and permit activity. Other users can consume the event-level facts, but the first design priority is operational prioritization rather than general exploration.

### 3. What is the business value?

The platform reduces repeated manual lookup across separate datasets, creates consistent metric definitions, makes unresolved workload easier to prioritize, and gives analysts reusable models instead of requiring every report to reconstruct the same logic.

### 4. Why not create a building risk score immediately?

A single score would require validated weights, domain agreement, and careful interpretation of complaints and violations. In Phase 1, I prefer transparent counts, dates, aging measures, and coverage flags. This makes the output explainable and gives stakeholders evidence to validate before introducing a composite score.

### 5. How do you know the project is successful?

I defined both technical and user-oriented criteria: the pipeline must load real public data, prevent duplicated business records, test keys and relationships, expose freshness and limitations, and let a user trace a building-level number back to detailed source records.

### 6. How does this connect to your previous CBES experience?

The industry is different, but the problem pattern is the same. At CBES, fragmented operational data and duplicated reporting logic created manual work. This project demonstrates how I would now solve that problem upstream by standardizing identifiers and business definitions in tested, reusable data models.

## 自我檢查

在進入 Step 2 以前，應該能不看文件回答：

- 這個專案的主要使用者是誰？
- 他現在為什麼需要跨多個資料來源工作？
- 專案提供的第一個 data product 是什麼？
- 為什麼現在不建立 risk score？
- grain 是什麼？building daily snapshot 的 grain 是什麼？
- 這個專案如何連接到 CBES 經驗？
