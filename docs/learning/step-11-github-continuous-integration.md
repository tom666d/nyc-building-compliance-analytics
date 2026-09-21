# Step 11：使用 GitHub Actions 建立持續整合

## 這一步完成了什麼

Step 10 已經讓 Airflow 能按順序執行資料管線，但程式碼一旦改動，仍要靠人記得執行所有檢查。Step 11 加入 Continuous Integration，中文是「持續整合」，讓每次準備合併程式碼時，都用同一套規則自動驗證。

本步實際完成：

1. 建立不需要任何密碼、也不連 Snowflake 的主要檢查流程；
2. 建立需要人工啟動、確認可能產生成本、並使用受保護 credentials 的 Snowflake integration 流程；
3. 把 Python、dbt 與 Airflow 的檢查串成一致的 quality gates；
4. 把 GitHub workflow 本身也變成可測試的 configuration；
5. 將第三方 Actions 固定到不可變的完整 commit SHA；
6. 限制 GitHub 自動產生的 token 只能讀取 repository；
7. 新增 Dependabot 每週提出 dependency 更新；
8. 在本機完整模擬 CI，25 個 Python tests 全數通過；
9. 清楚記錄：目前還沒有 GitHub remote，所以沒有假裝已經在 GitHub cloud 成功執行。

## 先回答：現在需要再創帳號嗎？

撰寫與本機驗證這一步，不需要新帳號，我已經完成。

若要讓 GitHub 在雲端自動執行這些 workflows，之後需要：

- 一個 GitHub 帳號；
- 一個 GitHub repository；
- 把目前本機的 Git commits 推送到該 repository。

Snowflake 帳號已經存在，不需要再創一個。未來 GitHub 只是替我們執行檢查；真正的資料倉儲仍是現有 Snowflake account。

我沒有自行發布到 GitHub，因為 repository 要公開或私人、名稱、帳號歸屬，都是會改變外部狀態的重要選擇，應由你決定。

## 為什麼需要持續整合

如果沒有自動檢查，一個很小的修改也可能造成：

- Python 程式無法執行；
- dbt model reference 拼錯；
- Airflow Dag 無法載入；
- 原本通過的資料品質規則被破壞；
- workflow 不小心開始讀取 secrets；
- 同事說「我電腦上可以」，但另一台機器無法重現。

持續整合的核心問題是：

> 每次將多人的修改整合進主要版本前，能不能在乾淨、一致的環境中，自動證明最重要的契約仍然成立？

## 新名詞解釋

### Git 與 GitHub

- Git 是版本控制工具，追蹤本機檔案修改與 commits。
- GitHub 是代管 Git repositories 的線上平台，並提供 pull requests、權限與自動執行服務。

本專案目前有完整的本機 Git history，但還沒有設定 GitHub remote。

### Local repository、remote repository 與 remote

- Local repository：自己電腦上的版本庫。
- Remote repository：放在線上服務的版本庫，例如 GitHub。
- Remote：本機記住的遠端地址，通常命名為 `origin`。

沒有 remote 不代表 Git 沒有作用；只代表 commits 尚未推送到 GitHub。

### Continuous Integration

Continuous Integration 常縮寫成 CI，意思是開發者頻繁整合修改，系統對每次修改自動執行驗證。

本專案的 CI 負責「驗證」，不是把資料產品自動發布到 production。

### Continuous Delivery 與 Continuous Deployment

兩者常縮寫成 CD，但含義不同：

- Continuous Delivery：通過檢查後，成品保持隨時可以發布，但通常仍需人工批准。
- Continuous Deployment：通過檢查後自動發布到 production。

本專案尚未實作 CD。不要在面試時把「有 GitHub Actions」直接說成「我完成 production deployment」。

### GitHub Actions

GitHub Actions 是 GitHub 提供的 automation platform。它會讀取 `.github/workflows/` 裡的 YAML files，依指定事件啟動工作。

### Workflow

Workflow 是一整份自動化流程。本專案有兩份：

- `CI`：沒有 secrets 的日常驗證；
- `Snowflake integration`：人工啟動的真實 Snowflake 驗證。

### YAML

YAML 是用縮排表達結構的文字格式。GitHub workflow 用 YAML 定義 triggers、permissions、jobs 與 steps。

縮排本身有意義，因此少兩個空白就可能改變設定。這也是我們把 workflow 納入 tests 的原因。

### Event 與 trigger

Event 是 GitHub 發生的事件；trigger 是哪些事件會啟動 workflow。例如：

- `pull_request`：建立或更新 pull request；
- `push`：推送 commit；
- `workflow_dispatch`：人從介面或 API 手動啟動。

### Pull request

Pull request 常縮寫成 PR，是提出「請把這個 branch 的變更合併到另一個 branch」的審查單位。它同時放置程式差異、討論、review 與自動檢查結果。

### Branch 與 main

Branch 是一條獨立的開發線。`main` 通常代表主要、應保持可用的版本。實際團隊多在 feature branch 修改，通過 pull request 後再合併進 `main`。

### Runner

Runner 是實際執行 workflow 的電腦。本專案指定 GitHub-hosted Ubuntu runner，代表 GitHub 準備一台暫時的 Linux 虛擬機器。

每次 job 通常從乾淨環境開始，因此不能依賴開發者電腦上剛好存在的檔案。

### Job

Job 是 workflow 裡的一組 steps，通常在同一台 runner 上依序執行。本專案主要 CI 有一個 `static-validation` job。

### Step

Step 是 job 裡的一個動作，例如安裝 Python、執行 tests 或解析 dbt graph。前一個 step 失敗時，後面一般不再執行。

### Action

Action 是可重複使用的 GitHub Actions 元件。例如：

- `actions/checkout` 把 repository 內容放到 runner；
- `actions/setup-python` 安裝指定 Python 版本。

Action 會在 runner 裡執行程式碼，所以它也是 software supply chain 的一部分。

### Checkout

Checkout 是把 Git repository 的檔案取到 runner。沒有這一步，runner 看不到我們要測試的程式碼。

本專案使用 `persist-credentials: false`，避免 checkout 完成後仍把 Git credential 留給後續 steps。

### Commit SHA

Commit SHA 是 Git commit 的雜湊識別碼。GitHub 建議高安全性做法把第三方 Action 固定到完整 40 字元 SHA，因為 tag 可能被移動，完整 commit 則是不可變的特定版本。

註解仍保留 `v7.0.1` 等人類容易閱讀的版本名稱。

### Software supply chain

Software supply chain 是從 dependency、建置工具、第三方 Action 到發布流程的整條軟體供應鏈。若引用的 Action 被偷偷換掉，它可能在 runner 中讀取檔案或 secrets。

完整 SHA pinning、最小 permissions 與 dependency updates 都是供應鏈控制。

### Exit code

每個 terminal command 結束會回傳數字：

- `0` 通常代表成功；
- 非 `0` 代表失敗。

GitHub Actions 用 exit code 判斷 step 是否通過。自動化測試的價值不只在印出文字，而是失敗時必須回傳非零，才能真正阻止合併。

### Lint

Lint 是靜態檢查程式風格與可疑錯誤，不需要真的執行完整業務流程。本專案使用 Ruff 檢查 Python。

Lint 不等於 test：格式正確的程式仍可能算錯結果。

### Unit test

Unit test 驗證小範圍、可隔離的功能。本專案的 Python tests 不需要 Snowflake 或 NYC Open Data，因此快速、可重複、適合每次修改都執行。

### Static validation

Static validation 在不連接真實外部服務的情況下檢查程式與設定。本專案包含：

- Python lint 與 unit tests；
- dbt graph parse；
- Airflow Dag structural contract；
- GitHub workflow security contract。

名稱中的 static 不是說所有工具都只讀文字，而是強調不會對外部 Snowflake 產生讀寫與費用。

### Parse

Parse 是把原始文字讀成工具理解的結構。`dbt parse` 可以發現 project、YAML、references 與 Jinja 的許多錯誤，但不執行 models，也不保證 SQL 在 Snowflake 一定成功。

### Integration test

Integration test 驗證多個真實元件是否能一起工作。Snowflake workflow 會真正連接 warehouse、建立 dbt models、執行 data tests 並驗證 documentation。

它比較接近真實環境，但較慢、需要 credentials，也可能產生成本，所以不和無 secrets 的 CI 混在一起。

### Quality gate 與 status check

Quality gate 是必須通過才能繼續的檢查。Workflow 在 GitHub 上執行後，會產生 status check。

未來可在 branch protection 設定中，把 `Python, dbt, and Airflow contracts` 設成 required status check。如此一來，檢查失敗就不能合併到 `main`。

目前尚未有 GitHub repository，所以這項設定還沒有實際開啟。

### Branch protection

Branch protection 是保護重要 branch 的 GitHub 規則，例如：

- 禁止直接 push；
- 必須經過 pull request；
- 必須有 review；
- required status checks 必須成功。

Workflow 定義「怎麼檢查」，branch protection 定義「檢查失敗能不能合併」。兩者缺一不可。

### Secret

Secret 是不應出現在 repository 或 logs 的敏感值，例如 private key 或 passphrase。GitHub 能以加密形式儲存 secret，workflow 執行時才注入。

不能因為變成 GitHub Secret，就把它輸出到 log。Secret masking 是額外保護，不是任意輸出的許可。

### GitHub environment

GitHub environment 是 deployment 或外部系統存取的保護邊界，可以有自己的 secrets 與 protection rules。

本專案要求一個名為 `snowflake-integration` 的 environment。未來可以設定 required reviewer，讓 workflow 在取得 Snowflake secrets 前等待人工批准。

### Required reviewer

Required reviewer 是 environment protection rule：指定的人批准後，job 才能繼續並取得 environment secrets。

是否可用取決於 GitHub plan 與 repository visibility，所以文件沒有假裝每個免費私人 repository 都一定具備相同功能。

### GitHub token

GitHub 會為 workflow 產生短期 token，常稱 `GITHUB_TOKEN`，用來呼叫 GitHub 或操作 repository。

本專案只授權：

```text
contents: read
```

它可以讀取 repository，但不能寫入 contents、issues 或 pull requests。

### Permission 與 least privilege

Permission 是被允許執行的操作。Least privilege 中文是「最小權限」：只給完成工作真正需要的權限。

驗證程式只需要讀檔，所以不給 write permission。Snowflake integration 也使用既有的 transformer role，而不是 account administrator。

### Fork

Fork 是在另一個帳號下複製 repository，常用於開放原始碼貢獻。來自 fork 的 pull request 應視為不受信任的程式碼。

主要 CI 完全不讀 Snowflake secrets，所以就算未來接受 fork PR，也不會因日常驗證把資料庫 credentials 交給該程式碼。

### `pull_request_target`

`pull_request_target` 是一種在目標 repository 權限脈絡中執行的 event。若同時 checkout 並執行不受信任的 PR 程式碼，可能形成嚴重 secret 風險。

本專案的 contract 直接禁止這個 trigger。

### `workflow_dispatch`

`workflow_dispatch` 是手動啟動按鈕。Snowflake integration 只接受這個 trigger，並要求 `confirm_cost=true`。

這不是完美的安全控制，但會防止每次 push 自動花費 Snowflake credits。

### Input 與 cost confirmation

Input 是啟動 workflow 時提供的參數。`confirm_cost` 是 Boolean，也就是 true 或 false。若沒有勾選，Snowflake job 不會執行。

它讓成本意圖變成可見紀錄，而不是隱藏在操作習慣裡。

### Concurrency

Concurrency 控制同時執行的 workflow 數量。

- Static CI 對同一個 pull request 有新 commit 時，取消舊的 stale run，節省時間。
- Snowflake integration 不互相重疊，也不取消已經在改 warehouse 的 active run。

### Timeout

Timeout 是 job 最長可執行時間。即使 command 卡住，也不會永久占用 runner 或 warehouse。本專案 static CI 是 25 分鐘，live integration 是 30 分鐘。

### Context

Context 是 GitHub 在 workflow expression 中提供的資料集合，例如 `github`、`secrets`、`inputs` 與 `runner`。

不同 YAML 位置可使用的 contexts 不完全相同。本次實作原先把 `runner.temp` 放在 job-level `env`，對照官方 context table 後發現該位置不可用，因此改成在執行 step 裡讀取 `RUNNER_TEMP`，並新增 regression test。這是一個很好的非照抄工程痕跡：設定能通過 YAML 語法，不代表符合執行時規則。

### Environment variable、`RUNNER_TEMP` 與 `GITHUB_ENV`

Environment variable 是 process 執行時的 key-value 設定。

- `RUNNER_TEMP` 是 runner 提供的暫存目錄；
- `GITHUB_ENV` 是特殊檔案，寫入 `NAME=value` 後，後續 steps 可以取得該環境變數。

Snowflake workflow 在執行時才建立 private-key path，不把本機絕對路徑寫進 repository。

### Base64

Base64 是把 binary content 表示成文字的 encoding，方便放入文字型 secret。它不是 encryption；任何拿到 Base64 字串的人都能解碼。

真正的保護來自 GitHub Secret、environment approval、最小權限與 key rotation。

### Cache

Cache 儲存可以重新下載或重建的內容，以加快下一次 workflow。本專案讓 `setup-python` cache Python packages。

Cache 不是 source of truth，也不能拿來保存 secrets 或唯一資料；即使 cache miss，workflow 仍應能正確執行。

### Dependency

Dependency 是專案依賴的外部 package，例如 dbt、Snowflake connector 與 Ruff。Dependency 可能修正漏洞，也可能帶來不相容改動，因此需要持續更新但不能盲目更新。

### Dependabot

Dependabot 是 GitHub 提供的 dependency update service。本專案設定每週檢查 GitHub Actions 與 Python dependencies，提出 pull request，再由相同 CI 驗證。

### Deterministic 與 reproducible

- Deterministic：相同輸入與版本應產生相同結果。
- Reproducible：另一個乾淨環境能重現結果。

完整 SHA、指定 Python 版本、dbt package lock、Airflow constraints 與自動 tests 都在提高可重現性。Python 的 transitive dependencies 尚未完整 lock，這項限制也有明確記錄。

## Step 11.1：先分開「免費驗證」與「真實整合」

我們沒有讓每個 pull request 都拿到 Snowflake credentials。設計如下：

```text
Pull request / main push
  -> no secrets
  -> lint + unit tests + dbt parse + Airflow contract

Manual request + confirm cost
  -> protected environment
  -> key-pair authentication
  -> real dbt build + tests + docs contract
```

原因不是 integration test 不重要，而是不同測試有不同 trust、cost 與速度。先用快速、便宜的 gates 擋掉大部分問題，再在明確授權下使用 warehouse。

## Step 11.2：主要 CI 檢查什麼

主要 workflow 執行：

```text
make install
make ci-workflow-check
make lint
make test
pip check
make dbt-deps
make dbt-parse
make airflow-check
```

各自回答不同問題：

| Gate | 回答的問題 | 不代表什麼 |
|---|---|---|
| Ruff lint | Python 是否符合靜態規則 | 業務結果一定正確 |
| Pytest | 已定義的功能契約是否通過 | 真實 Snowflake 一定成功 |
| `pip check` | 已安裝 packages 的版本要求是否衝突 | 所有未來版本都相容 |
| dbt deps | dbt packages 能否依 lock 解析 | models 已在 warehouse 執行 |
| dbt parse | dbt graph 與設定能否解析 | SQL 已在 Snowflake 編譯成功 |
| Airflow check | Dag tasks、dependencies 與安全設定正確 | scheduler 已經 production deployment |
| Workflow check | CI 安全邊界沒有被悄悄移除 | GitHub 自身沒有任何平台風險 |

## Step 11.3：把 workflow 本身變成測試對象

一般人只用 workflow 測程式，我們也測 workflow：

- 禁止 static CI 使用 `secrets.*`；
- 禁止 live workflow 被 pull request 自動啟動；
- 必須有 timeout；
- 必須使用 read-only token；
- Actions 必須使用完整 SHA；
- 必須使用 protected environment；
- 必須明確確認成本；
- private key 必須在 runner temporary directory 建立；
- 禁止在不支援的位置使用 `runner` context。

這叫 policy as code：重要規則不是只寫在人腦或文件，而是由程式自動判斷。

## Step 11.4：保護 Snowflake private key

未來真正設定 GitHub 時，需要 environment secrets：

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PRIVATE_KEY_B64
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

只有變數名稱能進 Git。真正值不能：

- commit 到 repository；
- 貼進 README；
- 貼進 pull request 或 issue；
- 印進 workflow log；
- 傳給面試官。

Workflow 將 Base64 secret 解碼成 owner-only 的 temporary file，執行結束後，不論成功或失敗，都執行 cleanup。

## Step 11.5：控制成本與競爭條件

Live integration 有四層控制：

1. 只能手動啟動；
2. 必須勾選 cost confirmation；
3. 最多執行 30 分鐘；
4. 同時間只允許一個 integration run。

此外，Snowflake 內仍有 warehouse auto-suspend 與 resource monitor。CI-side controls 與 warehouse-side controls 是不同層的 defense in depth，也就是多層防護。

## Step 11.6：本機驗證結果

本機執行與 GitHub static CI 相同的 command：

```text
make install
make ci-local
```

2026-09-21 的結果：

```text
Ruff                              passed
Python tests                      25 passed
Workflow security contract       passed
Python dependency check          passed
dbt package resolution           passed
dbt parse                         passed
Airflow Dag contract             passed, 9 tasks
Airflow dependency check         passed
```

這次沒有連接 Snowflake，所以不會使用 Snowflake credits。

## 已驗證與尚未驗證

### 已驗證

- 兩份 workflow YAML 能被 parser 讀取；
- 所有 repository-owned workflow contracts 通過；
- 本機完整 static CI commands 通過；
- 25 個 Python tests 通過；
- dbt graph 可以離線解析；
- Airflow Dag 的 9 個 tasks 與 controls 通過；
- static workflow 沒有引用 GitHub secrets；
- 外部 Actions 都固定到完整 SHA。

### 尚未驗證

- GitHub-hosted runner 的實際 run；
- GitHub branch protection 與 required check；
- GitHub environment reviewer；
- GitHub secrets 注入；
- 從 GitHub runner 連接 Snowflake 的 live integration。

原因是目前沒有 GitHub remote。這不是隱藏失敗，而是尚未進行的外部發布階段。

## 本步的設計決策

Architecture Decision Record 0011 記錄：

> Pull requests 執行無 credentials 的 static validation；Snowflake integration 則保持人工、受保護、確認成本且序列化。

這個決策同時處理四個現實問題：secret safety、trial-account cost、shared schema concurrency 與 honest evidence。

## 知識點總結

完成這一步後，你應該能說明：

1. Git 是本機版本控制，GitHub 是線上代管與 automation 平台；
2. Continuous Integration 在合併前以一致環境自動驗證修改；
3. Workflow 由 triggers、jobs、steps、actions 與 permissions 組成；
4. Lint、unit test、static validation 與 integration test 解決不同風險；
5. Workflow 成功不等於 production deployment；
6. 不受信任的 pull-request code 不應自動取得外部 credentials；
7. GitHub environment 可以隔離 secrets 並加入 approval；
8. `GITHUB_TOKEN` 應遵守 least privilege；
9. 外部 Actions 應固定到完整 commit SHA；
10. `workflow_dispatch`、confirmation、timeout 與 concurrency 能控制成本；
11. Base64 是 encoding，不是 encryption；
12. Branch protection 才能把成功 status check 變成合併條件；
13. Policy as code 能防止 workflow 的安全規則無聲退化；
14. 本機驗證與 GitHub hosted evidence 必須清楚區分。

## 面試題與參考答案

### 1. What problem does continuous integration solve in this project?

**Answer:** It gives every proposed change the same automated validation path before merge. It catches Python, dbt graph, Airflow structure, dependency, and workflow-policy regressions without relying on a developer to remember each command.

### 2. Why did you create two workflows instead of one?

**Answer:** The checks have different trust and cost boundaries. Pull-request validation needs no external credentials and should be fast and free, while a real dbt build needs Snowflake secrets, changes development relations, and consumes credits. Separate workflows make that boundary explicit.

### 3. Why does the pull-request workflow not connect to Snowflake?

**Answer:** Pull-request code should not automatically receive warehouse credentials, especially if forks are allowed. It also avoids routine warehouse cost and concurrency against a shared development schema. I still retain a protected manual integration path.

### 4. What does `dbt parse` prove, and what does it not prove?

**Answer:** It proves that dbt can read the project, resolve much of the graph, YAML, macros, and references. It does not execute SQL against Snowflake, so it cannot prove warehouse permissions, runtime SQL behavior, or data-test results.

### 5. How do you protect GitHub secrets?

**Answer:** Static CI never references them. Live credentials belong to a named GitHub environment, the token has read-only repository permission, key-pair authentication replaces password authentication, the temporary key file has restricted permissions, and cleanup runs even after failure.

### 6. Why pin Actions to a full commit SHA?

**Answer:** A release tag can be moved, while a full commit SHA identifies immutable code. Since an Action executes inside the runner and may have access to repository data or secrets, pinning reduces supply-chain drift.

### 7. What is the difference between CI and continuous deployment?

**Answer:** CI validates integrated changes. Continuous deployment automatically releases passing changes to production. This project implements CI and a manually triggered integration check; it does not claim automatic production deployment.

### 8. How do you control Snowflake cost in CI?

**Answer:** Default CI has no Snowflake connection. Live integration is manual, requires explicit cost confirmation, has a 30-minute timeout, runs serially, and still relies on Snowflake warehouse auto-suspend and the resource monitor.

### 9. Why do you not cancel an active Snowflake integration run?

**Answer:** Static validation is safe to cancel when a newer commit arrives. A live build may already be modifying warehouse relations, so abruptly canceling it can leave less predictable state. I serialize those runs instead.

### 10. What is branch protection, and is it configured here?

**Answer:** Branch protection can require pull requests, reviews, and successful status checks before merging to `main`. The workflow is ready to provide that check, but the repository currently has no GitHub remote, so I have not claimed that cloud-side protection is configured.

### 11. How did you test the CI configuration itself?

**Answer:** I created a Python contract that parses both YAML workflows and rejects broader permissions, mutable Action references, static secret use, unsafe triggers, missing timeouts, missing environment protection, and invalid context placement. Regression tests deliberately inject each unsafe condition.

### 12. Why is Base64 not a security control?

**Answer:** Base64 only converts bytes into text and is reversible without a key. The security controls are GitHub Secret storage, protected environment access, least privilege, restricted temporary-file permissions, and key rotation.

### 13. What does a clean GitHub-hosted runner help prove?

**Answer:** It reduces dependence on files or packages that happen to exist on one developer's computer. Installing and testing from the repository in a fresh environment improves reproducibility.

### 14. Why use Dependabot if dependencies are already version constrained?

**Answer:** Constraints limit incompatible upgrades, but they do not proactively propose security and maintenance updates. Dependabot creates reviewable update pull requests, and CI then verifies whether each proposed change still satisfies the project contracts.

### 15. What would you improve before automatically testing every pull request against Snowflake?

**Answer:** I would create a dedicated CI role with narrower permissions, generate an isolated schema per pull request, clean it up reliably, define concurrency and cost limits, and ensure untrusted fork code can never access those credentials.

### 16. Tell me about a problem you found while building the workflow.

**Answer:** The first version used the `runner` context in a job-level environment block. GitHub's context-availability table shows that context is unavailable there. I moved temporary-path creation into a run step using `RUNNER_TEMP`, exported it through `GITHUB_ENV`, and added a test so the mistake cannot return silently.

### 17. How is this connected to analytics engineering rather than only software engineering?

**Answer:** The gates protect analytics-specific contracts: the dbt graph, dimensional models, source definitions, data tests, documentation lineage, Airflow publication sequence, and real warehouse integration. CI makes the governed data product repeatable, not just the Python package.

## 官方文件

- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Actions secrets](https://docs.github.com/en/actions/concepts/security/secrets)
- [Deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)
- [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Dependabot version updates](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuring-dependabot-version-updates)

## 本步完成檢查

- [x] Static CI 不使用任何 GitHub Secret
- [x] Pull request、main push 與手動執行皆有 static trigger
- [x] Live Snowflake integration 只能手動啟動
- [x] Live integration 要求 cost confirmation
- [x] Live integration 使用 protected environment 與 key-pair authentication
- [x] GitHub token 只有 repository contents read permission
- [x] External Actions 固定到完整 commit SHA
- [x] 所有 jobs 有 timeout
- [x] Stale static runs 可以取消，live runs 不重疊
- [x] Dependabot 每週提出 dependency updates
- [x] Workflow security contract 與 regression tests 完成
- [x] 本機完整 CI simulation 通過
- [ ] GitHub remote 與 hosted run 尚待明確發布決定
- [ ] Branch protection 與 environment reviewer 尚待 repository 建立後設定

下一步是 Step 12：建立 business intelligence consumption layer，把已測試的 models 轉成 stakeholder 可使用、也能在面試中展示的 dashboard 與 decision workflow。
