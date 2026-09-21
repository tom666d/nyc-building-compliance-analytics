# Step 12：建立 Business Intelligence consumption layer 與面試展示

## 這一步完成了什麼

前十一個步驟已經完成資料取得、Snowflake、dbt models、資料品質、lineage、Airflow
與 Continuous Integration，但使用者仍然不能直接從 SQL tables 看出「現在應該先處理哪棟
building」。Step 12 把已治理的資料轉成真正可操作的產品：

> **NYC Building Compliance 360**

本步完成：

1. 新增三個專門提供 dashboard 使用的 dbt consumption marts；
2. 建立可解釋的 building attention score 與 tiers；
3. 在 Snowflake 真實建立三個 models，18 個 data tests 全數通過；
4. 建立 versioned JavaScript Object Notation data contract；
5. 建立 Overview、Building Explorer、Data Quality 三個可互動頁面；
6. 建立 Borough filter、building search 與 building selection；
7. 建立 snapshot consistency validator；
8. 將 dashboard build 加入 GitHub Continuous Integration；
9. 建立 production dependency security audit 與 optimized build；
10. 使用 resource monitor 控制 Snowflake 成本；
11. 發現並修正原先漏掉的 `0000000` placeholder Building Identification Number；
12. 明確揭露 bounded sample、單一 snapshot 與 attention score 的限制。

## 最終使用者看到什麼

Dashboard 有三個主要視角。

### Overview

回答：「目前 observed sample 有多少工作？集中在哪裡？」

- priority buildings；
- open complaints；
- open violations；
- median complaint resolution days；
- borough workload comparison；
- attention tier distribution；
- priority building queue。

### Building Explorer

回答：「為什麼這棟 building 排在前面？」

- 用 address、Building Identification Number 或 borough 搜尋；
- 查看 attention score 與 tier；
- 查看 open complaint 和 violation components；
- 查看 oldest open item age；
- 顯示 score 的可解釋原因。

### Data Quality

回答：「這些數字可以信任到什麼程度？」

- 每個 domain 的 source row count；
- building-key coverage；
- `PASS`、`WARN`、`ERROR`；
- 最新 dbt build evidence；
- bounded sample 與 normalization disclosure。

## 新名詞解釋

### Business Intelligence

Business Intelligence 常簡寫為 BI，中文常譯為「商業智慧」。它把資料轉成可以支援決策的
metrics、reports、dashboards 與分析介面。

BI 的重點不是圖漂亮，而是使用者能更快做出一致、有依據的決定。

### Consumption layer

Consumption layer 是資料被最終使用者或應用程式「消費」的那一層。它可能是：

- dashboard；
- report；
- semantic model；
- application programming interface；
- exported dataset；
- machine learning feature table。

本專案的 consumption layer 包含 dbt consumption marts、versioned snapshot contract 與
Building Compliance 360 dashboard。

### Data product

Data product 是把資料當成有使用者、有品質承諾、有文件、有維護責任的產品，而不只是一次性
SQL query。

Building Compliance 360 有：

- 明確使用者與商業問題；
- 可重複的 metrics；
- data quality contracts；
- lineage；
- refresh process；
- user interface；
- limitations。

### Consumption mart

Consumption mart 是為特定分析產品整理好的最後資料表。它的 grain、欄位與 metrics 都對應
使用情境。

這一步新增：

```text
mart_building_compliance_current
mart_borough_compliance_current
mart_compliance_overview
```

### Current-state mart

Current-state mart 只呈現目前最新狀態。本專案從 daily snapshot 找出最新 snapshot date，
建立一個每棟 building 一列的 current mart。

Daily snapshot 保留時間歷史；current mart 讓 dashboard 不必每次自己判斷哪一天最新。

### Grain

Grain 是一列資料代表什麼。

- `mart_building_compliance_current`：一列代表最新 snapshot 的一棟 building；
- `mart_borough_compliance_current`：一列代表最新 snapshot 的一個 borough；
- `mart_compliance_overview`：一列代表最新 snapshot 的整個 observed portfolio。

若沒有先定義 grain，dashboard sum 很容易 double count。

### Key Performance Indicator

Key Performance Indicator 常簡寫為 KPI，是反映目標或營運狀態的重要指標。

本 dashboard 的 KPI 不是任意數字，而是直接回答 stakeholder 問題，例如 open workload、
priority buildings 與 resolution time。

### Semantic layer

Semantic layer 是把技術欄位轉成一致商業概念與計算規則的層。不同工具都應使用相同的
「open complaint」與「priority building」定義。

本專案沒有把 metric formula 寫在 React page 裡；定義留在 dbt consumption marts。
因此未來若改成 Power BI、Tableau 或 Looker，也可以重複使用相同 metrics。

### Dashboard 與 report

- Dashboard：讓使用者監控、篩選、比較並採取行動，通常強調目前狀態。
- Report：常有固定版面與較完整敘事，可能針對某個期間定期產出。

Building Compliance 360 是 dashboard，因為它支援 borough filter、priority queue 與
building investigation。

### Drill-down 與 drill-through

- Drill-down：在同一分析層級中往更細層次，例如 city → borough。
- Drill-through：從 summary 跳到另一個 detail context，例如 priority queue → building detail。

本專案 Overview 的 borough filter 是 drill-down；Building Explorer 是 drill-through experience。

### Frontend

Frontend 是使用者在瀏覽器中看到和操作的部分。本專案使用 React component 建立 filter、
navigation、tables 與 detail views。

Frontend 不持有 Snowflake private key，也不重新定義 business metrics。

### Backend

Backend 是在使用者介面後方處理資料、權限或應用邏輯的服務。本 dashboard 沒有建立一個
per-request Snowflake backend；它在 build time 讀取 versioned snapshot。

這是刻意的成本與安全選擇，不是缺少技術能力。

### React

React 是建立互動使用者介面的 JavaScript library。介面由 components 組成，state 變動時，
React 更新需要變動的畫面。

### Component

Component 是可重複、可組合的介面單位，例如 KPI card、quality card 或 building detail。

Component 不應偷偷重新計算一套與 dbt 不同的 business definition。

### State

State 是介面目前的互動狀態，例如：

- 使用者選擇哪個 view；
- 選擇哪個 borough；
- search input 是什麼；
- 選中哪棟 building。

Changing state 只改變呈現與 filter，不修改 Snowflake source data。

### Next.js 與 Vinext

Next.js 是建立 React web applications 的 framework。Framework 提供 routing、build、
metadata 等完整應用結構。

本專案使用 Sites scaffold 搭配 Vinext，將 Next.js-style application 建成適合 hosting runtime
的 output。這是 presentation technology，不改變 analytics engineering 的資料責任邊界。

### Node.js

Node.js 是在瀏覽器外執行 JavaScript 的 runtime。它用來安裝 packages、執行 snapshot
validator、lint 與 build。

### npm

npm 是 Node.js package manager。它會根據 `package.json` 安裝 dependencies，並執行 scripts。

### `package.json`

`package.json` 宣告 application name、scripts、dependencies 與支援的 Node.js version。

### `package-lock.json`

`package-lock.json` 記錄實際解析後的完整 dependency tree。`npm ci` 依 lock file 安裝相同版本，
提高 Continuous Integration 的 reproducibility。

### Dependency audit

Dependency audit 檢查 packages 是否有已知 security advisories。本步執行：

```text
npm audit --omit=dev
```

`--omit=dev` 表示檢查 production runtime dependencies。結果為零個已知 production
vulnerabilities。Development tool dependencies 仍由 Dependabot 與後續 upgrades 管理。

### Production build

Production build 是把 source code 轉換、最佳化成可部署版本。它會檢查 TypeScript、imports、
bundling 與 runtime compatibility。

Development server 可以開啟不代表 production build 一定成功，所以兩者都要驗證。

### Responsive design

Responsive design 是讓同一個介面能依不同螢幕寬度重新排列。本 dashboard 在較窄畫面會：

- sidebar 變成上方 navigation；
- 四個 KPI cards 改成兩欄或一欄；
- side-by-side panels 改成上下排列；
- tables 保留可讀的水平空間。

### Accessibility

Accessibility 是讓不同能力的使用者都能操作內容。實作包含：

- semantic headings；
- 真正的 buttons、labels、inputs 與 tables；
- keyboard focus；
- accessible progress bar values；
- 不只依顏色傳達 status。

### JavaScript Object Notation

JavaScript Object Notation 常簡寫為 JSON，是結構化文字資料格式。Dashboard snapshot 包含
metrics、borough rows、priority buildings 與 quality status。

JSON 中沒有 Snowflake credential。

### Data contract

Data contract 是 producer 與 consumer 對 schema、欄位、類型、允許值與關係的約定。

Snapshot validator 會檢查：

- 必須有五個 boroughs；
- borough totals 必須等於 overview；
- attention tier totals 必須等於 observed building count；
- Building Identification Number 格式有效且不重複；
- total open items 等於 complaints 加 violations；
- quality status 只能是 `PASS`、`WARN` 或 `ERROR`。

### Static snapshot

Static snapshot 是某個時間點輸出的固定資料。網站 build 時讀入 snapshot，使用者瀏覽時不再
查 Snowflake。

優點：

- 沒有 browser credential；
- 沒有每次瀏覽的 warehouse cost；
- recruiter 可以重現；
- 即使 trial account 暫停，demo 仍可用。

代價：資料不會自動即時更新，必須重新 export 與 deploy。

### Live connection

Live connection 是每次使用介面時直接查詢資料平台。它適合真正 operational dashboard，
但需要 authentication、query cost、caching、availability 與 concurrency design。

Portfolio 階段不需要假裝已完成這整套 production infrastructure。

### Decoupling

Decoupling 中文可理解為「降低耦合」。Static snapshot 讓 dashboard runtime 不依賴 Snowflake
是否正在運作。Snowflake 仍是 metric source of truth，但不是每個 page request 的 runtime dependency。

### Bounded sample

Bounded sample 是刻意限制大小的資料切片。本專案每個 source 使用 1,000 records 控制成本與
執行時間。

Bounded 不等於 random，也不等於 representative。

### Population 與 sample

- Population：想研究的完整母體，例如全部 NYC buildings。
- Sample：實際被選取分析的部分資料。

目前 sample 是由來源 API 的排序和 limit 產生，不可以把結果說成「全 NYC 有多少 open violations」。

### Representativeness

Representativeness 是 sample 是否能合理代表 population。現在沒有 random sampling 或完整母體
baseline，因此 dashboard 明確使用「observed sample」而不是 citywide estimate。

### Selection bias

Selection bias 是資料選取方式使某些類型被過度或不足代表。目前 source first slice 包含較早的
legacy violation records，所以 item age 可能顯得特別高。

這不是 SQL bug，但會影響解讀。

### Composite score

Composite score 是把多個 signals 合併成一個數值。Attention score 使用：

```text
open complaints × 4
+ open violations × 6
+ complaints in last 30 days × 2
+ oldest-item age bonus
```

它被 cap 在 100，也就是最高不超過 100。

### Heuristic

Heuristic 是根據明確規則建立的實用判斷方法，不是經由 historical outcomes 訓練出的 statistical
model。

Attention score 是 heuristic。它的 weights 是可討論的 policy choices，不是科學真理。

### Threshold

Threshold 是將連續 score 分組的界線：

```text
CRITICAL  50–100
HIGH      20–49
MODERATE  10–19
LOW        0–9
```

Threshold 必須文件化，不能只存在 dashboard color formula。

### Attention score 與 risk score

我們刻意使用 attention score，不用 risk score。

目前 retained violation source 沒有完成 governed severity classification，也沒有 real-world safety
outcome 用來驗證。把 workload score 稱為 risk score 會造成不合理的決策暗示。

### Normalization

Normalization 在這裡是將 source identifiers 轉成一致、可使用形式。本專案原本只檢查 BIN 是否
為七位數。

Dashboard profiling 發現 `0000000` 雖然是七位數，第一位卻不是 borough code，因此不是可用的
building identity。

新規則要求：

```text
first digit = 1 through 5
seven digits total
not a borough code followed only by zeros
```

### Zero BIN / placeholder BIN

NYC 官方文件說明 Building Identification Number 第一位代表 borough。缺少有效 identifier 時，
某些系統可能出現 zero-style placeholder。

如果把 placeholder 當成 building key，多筆不相關 records 會被錯誤合併成一棟 building，這叫
false entity consolidation。

### Resource monitor

Resource monitor 是 Snowflake 控制 warehouse credit 使用量的機制。達到 quota 後可以通知或
停止 warehouse。

本步後段 resource monitor 達到 monthly quota，成功阻止額外 compute。我沒有提高 quota 或另創
warehouse，因為那會擴大成本授權。

### Source of truth

Source of truth 是被認定為權威定義的位置。dbt consumption marts 是 metrics 的 source of truth；
JSON 是 versioned delivery format；React application 是 presentation layer。

### Data freshness 與 snapshot date

- Snapshot date：mart 代表哪一天的資料狀態。
- Export date：何時把 mart 輸出給 dashboard。
- Source ingestion time：原始資料何時載入 warehouse。

三者不同，介面必須避免只顯示模糊的「last updated」。

### Social preview

Social preview 是分享網站連結時顯示的 title、description 與 preview image。它改善 portfolio link
在 recruiter 或社群工具中的可辨識度，不涉及 dashboard metrics。

## Step 12.1：把 business logic 留在 dbt

資料流程是：

```text
fct_building_compliance_daily
  -> mart_building_compliance_current
      -> mart_borough_compliance_current
      -> mart_compliance_overview
          -> JSON snapshot
              -> dashboard
```

如果另一個 BI tool 接上這些 marts，它會得到相同 priority counts 與 borough metrics。

## Step 12.2：不製造不存在的歷史趨勢

目前 warehouse 只有一個 daily snapshot date。只有一點不能形成 time series。

因此正式 dashboard 沒有使用 mockup 中的 12-month workload line。它改成 current borough workload
comparison。這是一個重要 analytics integrity 決策：圖表需求不能凌駕於實際 data grain。

## Step 12.3：建立透明 attention score

每個 score component 都能說明：

- complaints 代表客服／營運工作量；
- violations 代表既有 compliance workload，因此 weight 較高；
- recent complaints 代表近期 activity；
- oldest item age 代表長期 backlog。

Weights 和 tiers 存在 dbt SQL 與文件中，可 review、test、修改。

## Step 12.4：發現 `0000000` data issue

第一次 priority ranking 中，最高分 building 的 BIN 是 `0000000`，並聚合了 11 筆 violations。

這個結果不合理，因為合法 building identifier 的第一位必須代表 borough。檢查後確認原先的
regex 只保證七位數，沒有保證 borough semantics。

修正方式不是在 React table 中藏掉，而是：

1. 修改 shared `normalize_bin` macro；
2. 更新 staging tests；
3. 更新 dimension test；
4. 保留 unresolved source records；
5. 更新 coverage policy；
6. 在 dashboard disclosure 與 Architecture Decision Record 記錄。

## Step 12.5：為什麼 violation blocking floor 改成 98%

新的 normalization 會讓 11 筆 placeholder records 加上原本 2 筆 invalid records 無法對應 building，
coverage 約為 98.7%。

如果 blocking threshold 保持 99%，每次 development build 都會因已知 source defect 永久失敗。
因此分成：

```text
blocking floor for legacy violation fact = 98%
desired quality scorecard threshold       = 99%
```

低於 desired 99% 仍會對使用者顯示 `ERROR`，但 retained source defect 不會讓所有 transformation
development 永久停止。

## Step 12.6：建立 versioned snapshot

Exporter 使用 reader role，不使用 transformer 或 account administrator。它只讀最後 marts，並以
atomic write 更新 JSON。

Atomic write 是先完成 temporary file，再一次替換正式檔案，避免 process 中斷後留下半份 JSON。

## Step 12.7：在網站 build 前驗證資料

`validate-dashboard-data.mjs` 不需要 Snowflake，可以在每個 pull request 執行。

它能發現：

- overview 與 borough totals 不一致；
- tier totals 少資料；
- duplicate or placeholder BIN；
- open item arithmetic 錯誤；
- unexpected quality status。

這是 consumer-side contract，補強 warehouse tests，但不取代 dbt tests。

## Step 12.8：加入 Continuous Integration

Static workflow 現在也會：

```text
install locked Node.js dependencies
audit production dependencies
validate dashboard data
lint application code
create optimized production build
```

這些都不需要 Snowflake credentials。

## Step 12.9：真實驗證結果

Snowflake consumption build：

```text
3 models
18 data tests
1 exposure
PASS=21
WARN=0
ERROR=0
NO-OP=1
```

Dashboard local validation：

```text
snapshot contract passed
application lint passed
production dependency audit: 0 known runtime vulnerabilities
optimized production build passed
```

## Step 12.10：已驗證與尚未驗證

### 已驗證

- 三個 consumption marts 曾成功建立於 Snowflake；
- 新 marts 的 18 個 tests 通過；
- overview、borough、tier 與 priority results 曾被 reader role 查詢；
- snapshot totals 經 local contract reconciliation；
- dashboard interactions 可由 application state 驅動；
- local production build 成功；
- production dependency audit 為零漏洞。

### 尚未驗證

- zero-BIN normalization 修改後的完整 Snowflake rebuild；
- 修改後 98.7% violation coverage 的實際 Snowflake scorecard；
- 下一次 Airflow full run；
- long-term automatic dashboard refresh；
- full-volume citywide representativeness。

原因不是隱藏錯誤，而是 Snowflake resource monitor 已達 monthly quota。成本控制優先於為了
portfolio badge 擅自提高支出。

## Step 12.11：建立 owner-private deployment

網站已完成正式環境 build，並部署到：

[NYC Building Compliance 360](https://nyc-building-compliance-360-portfolio.hsieh203.chatgpt.site)

`Deployment`（部署）是把本機完成的網站版本放到可由網址存取的正式執行環境。這次先保留
`owner-private`，意思是只有網站擁有者可以開啟。這讓我們先驗證真正的 production artifact，
但不會在尚未決定 recruiter 分享方式前直接公開。網站檢視使用已輸出的 JSON snapshot，
因此不會把 Snowflake credential 放進 browser，也不會因為每次開頁而啟動 warehouse。

## 知識點總結

完成這一步後，你應該能說明：

1. Consumption layer 是資料產品交付使用者的最後一層；
2. Dashboard business logic 應由 governed marts 提供；
3. 每張 mart 都需要明確 grain；
4. Static snapshot 可以隔離 credential、availability 與 viewing cost；
5. Snapshot date、export date 與 source ingestion time 不同；
6. Bounded sample 不能被稱為 citywide estimate；
7. 一個 snapshot date 不能建立真實 trend；
8. Composite heuristic 必須公開 weights 與 thresholds；
9. Attention score 不等於 safety risk score；
10. Consumer contract 可以檢查 rollup reconciliation；
11. Valid syntax 不代表 valid business identity；
12. Placeholder BIN 可能造成 false entity consolidation；
13. Resource monitor 是有效的 cost governance；
14. Production build 與 development server 驗證不同風險；
15. Browser 不應取得 Snowflake credentials。
16. Private deployment 與 public sharing 是兩個不同決策；成功部署不代表已公開。

## 面試題與參考答案

### 1. What is the purpose of the BI consumption layer in this project?

**Answer:** It converts governed warehouse models into a decision-oriented product. Users can monitor unresolved workload, compare boroughs, prioritize buildings, and inspect data-quality limitations without writing SQL.

### 2. Why did you add consumption marts instead of querying facts directly from the dashboard?

**Answer:** Consumption marts make the grain and metric definitions reusable and testable. They prevent each visualization from redefining open status, current snapshot logic, borough rollups, or prioritization rules.

### 3. What are the grains of your dashboard marts?

**Answer:** The current building mart has one row per building in the latest snapshot, the borough mart has one row per borough in that snapshot, and the overview mart has one row for the full observed portfolio.

### 4. Why does the production dashboard not show the trend line from the original mockup?

**Answer:** The warehouse currently contains only one daily snapshot date. A single observation cannot support a time-series trend, so I replaced the mockup trend with a truthful current-workload comparison by borough.

### 5. Why use an attention score instead of a risk score?

**Answer:** The retained data does not provide a governed severity classification or validated safety outcome. The score only prioritizes operational review based on workload and age, so calling it risk would overstate what the data proves.

### 6. How is the attention score calculated?

**Answer:** It combines open complaints, open violations, complaints entered in the last 30 days, and an age bonus for the oldest open item. The score is capped at 100 and mapped to fixed, documented tiers.

### 7. Why export JSON instead of connecting the website directly to Snowflake?

**Answer:** The versioned snapshot keeps credentials out of the browser, avoids warehouse cost for page views, keeps the demo available when the trial warehouse is suspended, and makes recruiter review reproducible.

### 8. What is the tradeoff of using a static snapshot?

**Answer:** It improves security, cost, and availability, but it is only as current as the last export. A real operational deployment would need an approved refresh service, cache policy, and availability design.

### 9. How do you prevent the dashboard snapshot from becoming inconsistent?

**Answer:** A build-time validator reconciles borough totals to the overview, verifies tier totals, rejects duplicate or placeholder BINs, checks category domains, and confirms that total open items equal complaints plus violations.

### 10. What data-quality issue did the dashboard help you discover?

**Answer:** The highest-ranked row used BIN `0000000`. It passed the original seven-digit syntax check but violated the business meaning that the first digit is a borough code. Eleven unrelated violations had been consolidated into a false building.

### 11. How did you fix the zero-BIN problem?

**Answer:** I changed the shared normalization macro to require a borough-code first digit and reject borough-zero placeholders, updated staging and dimension tests, retained invalid source records for audit, and documented the effect on coverage.

### 12. Why did the violation blocking threshold change from 99 to 98 percent?

**Answer:** The corrected source profile has known retained placeholder records and would be about 98.7 percent matched. I use 98 percent as the build floor for that legacy fact, while the quality scorecard retains 99 percent as the desired threshold and reports lower coverage as an error.

### 13. Does that threshold change hide poor quality?

**Answer:** No. The source rows remain in the fact and exception views, and the dashboard displays coverage and status. The distinction is between allowing transformations to remain inspectable and claiming that the source meets the desired service level.

### 14. Why can you not call the current results citywide metrics?

**Answer:** Each source is bounded to 1,000 ordered records. The slice is not random and may overrepresent certain time periods or record types, so the interface explicitly calls it an observed portfolio sample.

### 15. How does the dashboard fit into your lineage?

**Answer:** The dbt exposure depends on the overview, borough, and building consumption marts plus the event facts. This connects the final named dashboard to upstream source, staging, fact, dimension, quality, and documentation nodes.

### 16. How do you control cost?

**Answer:** The deployed site reads a static snapshot, so views do not resume Snowflake. Refresh uses the reader role, source ingestion stays bounded, warehouses auto-suspend, and the monthly resource monitor stopped further compute when the quota was reached.

### 17. What happened when the resource monitor stopped the warehouse?

**Answer:** I did not raise or bypass it. The three consumption marts and their selected tests had already passed, so I completed the site with the verified bounded snapshot, documented the normalization reconciliation, and marked the post-fix rebuild as pending.

### 18. What would you change for a real production deployment?

**Answer:** I would establish representative full-volume ingestion, validate incremental watermarks, use a production Snowflake account and role, automate snapshot refresh after successful data-quality gates, define freshness objectives, add authenticated user access, and monitor usage and failures.

### 19. Why is the data-quality view part of the business product?

**Answer:** Users need to know whether an apparent drop is a real operational change or incomplete source coverage. Publishing quality context prevents false confidence and makes the analytical product more trustworthy.

### 20. How does this connect to your previous reporting experience?

**Answer:** In earlier reporting work I automated downstream reports and standardized metrics. This project moves that same problem upstream by governing identities, metrics, tests, lineage, orchestration, and a reusable consumption layer before the dashboard.

## 官方文件

- [dbt exposures](https://docs.getdbt.com/docs/build/exposures)
- [Snowflake resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [NYC Department of Buildings BIN guide](https://www.nyc.gov/assets/buildings/pdf/article_320_guide.pdf)
- [Next.js client components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [npm package-lock](https://docs.npmjs.com/cli/configuring-npm/package-lock-json)
- [npm audit](https://docs.npmjs.com/cli/commands/npm-audit)

## 本步完成檢查

- [x] Building、borough、overview consumption marts
- [x] Transparent attention score 與 tiers
- [x] dbt exposure 指向正式 dashboard models
- [x] 三個 Snowflake models 建立成功
- [x] 18 個新 data tests 通過
- [x] Overview、Building Explorer、Data Quality views
- [x] Borough filter 與 building search
- [x] Versioned JSON snapshot
- [x] Consumer-side snapshot contract
- [x] Responsive layout 與 semantic controls
- [x] Production runtime dependency audit
- [x] Optimized production build
- [x] GitHub Continuous Integration dashboard gates
- [x] Zero-BIN normalization correction
- [x] Bounded-sample、score 與 refresh limitations disclosed
- [x] Owner-private production deployment
- [ ] Post-normalization Snowflake rebuild pending resource-monitor reset
- [ ] Full-volume production baseline remains future work
