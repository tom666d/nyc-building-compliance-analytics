# Step 3：理解 Git、repository 與專案目錄

## 這一步要完成什麼

這一步先不新增資料功能，而是理解：

1. Git 為什麼對面試作品重要；
2. repository、commit、branch 和 working tree 是什麼；
3. 專案中每個資料夾負責什麼；
4. 哪些檔案應提交，哪些檔案絕對不能提交；
5. 資料如何從官方來源流向最後的分析結果。

完成後，即使還看不懂每一行程式，也應該能向面試官解釋整個 repository 的結構與各工具的責任邊界。

## Git 與 GitHub 不一樣

### Git

Git 是 distributed version control system（分散式版本控制系統）。它在本機記錄檔案如何隨時間改變，讓我們可以：

- 比較修改前後差異；
- 保存一系列有意義的版本；
- 建立不同開發路線；
- 找出某項設計何時、為什麼改變；
- 在出錯時理解歷史，而不是只剩最後結果。

Distributed 表示每個完整 clone 通常都有自己的專案歷史，不是所有操作都必須連上中央伺服器。

### GitHub

GitHub 是託管 Git repositories 並提供協作、Pull Request、issue、權限和自動化功能的平台。Git 可以完全在本機使用；GitHub 是可能的 remote hosting platform，不是 Git 本身。

目前這個專案已是本機 Git repository，但尚未在本步驟假設它已發布到 GitHub。

## 核心名詞

### Repository

Repository（版本庫，常簡稱 repo）是 Git 管理的專案與歷史集合。它包含目前檔案，也包含 `.git` 隱藏目錄中的版本歷史與設定。

### Working tree

Working tree（工作目錄）是現在可以看到和修改的檔案版本。修改檔案後，working tree 會與最近一次 commit 不同。

### Tracked、untracked 與 ignored

- Tracked file：Git 已經知道並追蹤的檔案。
- Untracked file：存在於工作目錄，但尚未加入 Git 的檔案。
- Ignored file：符合 `.gitignore` 規則，Git 通常不會提示加入的檔案。

例如 `.env` 應該是 ignored，因為它可能包含 Snowflake password。

### Staging area

Staging area（暫存區，也稱 index）是下一個 commit 的候選內容。修改檔案不等於它會自動進入 commit；先選擇要提交的變更，可以避免把不相關內容混在一起。

概念流程：

```text
修改 working tree
    ↓ git add
放入 staging area
    ↓ git commit
形成新的歷史快照
```

### Commit

Commit 是專案內容的一個版本快照，包含作者、時間、訊息、內容和父 commit。好的 commit 應代表一個可以理解的改變，而不是把所有工作一次塞進去。

### Commit hash

Commit hash 是 Git 用內容計算出的識別碼。畫面通常顯示縮短版本，例如：

```text
a943513 docs: profile live NYC DOB sources and revise grain assumptions
```

`a943513` 是縮短的 commit hash，後面是 commit message。

### Branch

Branch（分支）是一條可以獨立前進的開發路線。這個專案目前在 `main` branch。實際團隊通常會建立 feature branch，在完成測試和 review 後再合併。

### HEAD

HEAD 是 Git 用來表示目前所在 branch 或 commit 的參照。現在 HEAD 指向 `main` 的最新 commit。

### Diff

Diff 是兩個版本之間的內容差異。Review 的核心不是重新讀完整檔案，而是檢查這次 diff 是否符合目的、是否引入風險。

### Remote、clone、push 與 pull

- Remote：遠端 repository 的簡稱或位置。
- Clone：從遠端取得完整 repository 和歷史。
- Push：把本機 commits 上傳到遠端。
- Pull：取得遠端更新並整合到目前 branch；它通常包含 fetch 與 merge 或 rebase。

目前逐步教學只需要本機 commits，不需要先建立 remote。

### Pull Request

Pull Request 是 GitHub 上提出「請 review 並合併這組變更」的協作流程。它不是 Git 的 commit，而是 GitHub 建立在 branches、commits 和 diffs 上的 review 功能。

## 為什麼 Git 歷史是作品集的一部分

只有最後程式碼，面試官很難判斷：

- 哪些設計是你自己做的；
- 你是否先理解問題再寫程式；
- 發現錯誤假設後如何處理；
- 是否知道怎麼驗證與拆分工作。

目前的歷史已呈現以下順序：

```text
商業問題與來源邊界
  -> ingestion 與 Snowflake 骨架
  -> dbt、orchestration 與 automation 骨架
  -> 排除本機產生物
  -> Step 1 商業問題教材
  -> Step 2 真實來源 profiling 並修正 permit grain 假設
```

其中最重要的不是 commit 數量，而是每個 commit 都能說明「做了什麼以及為什麼」。

## 專案目錄總覽

```text
.
├── README.md
├── CONTRIBUTING.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
├── .github/workflows/
├── src/nyc_dob_ingestion/
├── tests/
├── infrastructure/snowflake/
├── dbt/nyc_building_compliance/
├── airflow/dags/
└── docs/
```

## Root files：專案入口與共用設定

### `README.md`

README 是面試官或新協作者最先閱讀的專案入口。它應快速說明問題、價值、架構、開始方式和目前範圍。

### `CONTRIBUTING.md`

說明如何對專案做出變更，包括 commit 習慣、驗證要求和 review 內容。

### `Makefile`

Makefile 把較長的指令包裝成容易記住的 command。例如 `make test` 可以代表執行專案測試。它不是主要商業邏輯，只是開發者操作介面。

### `pyproject.toml`

`pyproject.toml` 是 Python 專案的標準設定檔。本專案用它定義：

- package 名稱與版本；
- 支援的 Python 版本；
- dependencies；
- command-line entry point；
- test 和 lint 工具設定。

TOML 是 Tom's Obvious, Minimal Language，一種設定檔格式。

### `.env.example`

Environment variable（環境變數）是在程式外部提供設定值的方法，例如帳號、warehouse 名稱或 password。

`.env.example` 只列出需要哪些變數，不放真實值。真正的 `.env` 被 `.gitignore` 排除。

### `.gitignore`

`.gitignore` 告訴 Git 哪些本機或自動產生檔案不應被追蹤，例如：

- `.env`：可能有 credentials；
- `.venv/`：可以重新安裝的 Python environment；
- `work/`：下載樣本與暫存分析；
- caches、logs 和 build outputs。

Credentials 是用來證明身分或取得系統權限的資訊，例如 password、token 或 private key。

## `src/nyc_dob_ingestion`：Python 原始碼

`src` 是 source 的縮寫。這裡放專案自己的 Python package：

- `datasets.py`：資料集識別碼與設定；
- `socrata.py`：向 NYC Open Data 發出分頁請求；
- `snowflake_loader.py`：準備 raw payload 並載入 Snowflake；
- `cli.py`：把使用者 command 和各元件連接起來。

Package 是一組可以一起安裝、匯入與使用的程式模組。Command-line interface 是在終端機中透過文字命令操作程式的介面，常簡寫為 CLI。

## `tests`：自動測試

Tests 用來自動驗證行為。現在的 unit tests 不需要連接網路或 Snowflake，就能檢查 dataset identifiers 和 row hash 是否穩定。

Unit test（單元測試）針對小範圍、可隔離的程式行為；integration test（整合測試）會驗證多個元件或外部系統一起工作。

## `infrastructure/snowflake`：環境建立

這裡的 Structured Query Language 檔案負責建立 Snowflake roles、warehouse、database、schemas、permissions 和 raw tables。

Infrastructure as code（基礎設施即程式碼）表示用可版本控制的檔案描述環境設定，而不是只依賴人工點選操作。

## `dbt/nyc_building_compliance`：資料轉換

dbt 是產品名稱，主要讓分析工程師用 Structured Query Language 建立、測試與文件化資料模型。

資料依責任分層：

```text
sources
  -> staging
  -> intermediate
  -> marts
  -> Business Intelligence consumption
```

- Staging：針對單一來源改名、轉型態和基本清理。
- Intermediate：可重複使用，但不是最終交付的中間邏輯。
- Marts：針對分析使用者整理的事實表、維度表和決策資料產品。
- Macros：可重複使用、能產生 Structured Query Language 的小型程式邏輯。
- YAML files：模型描述、測試、關係和資料血緣設定。

YAML 是一種容易閱讀的設定檔格式。

目前這些 dbt 檔案是 scaffold（可執行骨架），不是已完成的 production models。Step 2 已經找出 permit grain 與 violation status mapping 需要修改。

## `airflow/dags`：工作排程與順序

Apache Airflow 是 workflow orchestration platform（工作流程協調平台）。

Directed Acyclic Graph（有向無環圖，常簡稱 DAG）描述工作以及先後依賴關係：

```text
ingest data -> check freshness -> build and test models
```

Airflow 負責安排何時做、先做什麼；真正的資料轉換仍放在 ingestion code 和 dbt，不重複寫進 Airflow。

## `.github/workflows`：自動驗證

GitHub Actions 可以在 push 或 Pull Request 時執行自動化 workflow，例如：

- 檢查程式格式；
- 執行 unit tests；
- 確認 dbt project 能被解析；
- 有安全 credentials 時執行 Snowflake integration tests。

這類每次變更都自動執行的驗證通常稱為 Continuous Integration（持續整合）。

## `docs`：商業語意與設計證據

- 正式 business、architecture 與 technical documents 使用英文。
- `docs/learning` 使用繁體中文協助逐步學習。
- `docs/decisions` 保存 Architecture Decision Records。
- `source_profile.md` 保存時間點統計與來源證據。

文件不是程式完成後才補的裝飾。沒有商業定義和限制說明，再正確的 Structured Query Language 也可能產生錯誤決策。

## 資料如何通過整個專案

```text
Official NYC Open Data
    ↓
Python ingestion：取得並載入原始 payload
    ↓
Snowflake RAW：保留來源資料與載入 metadata
    ↓
dbt staging：來源專屬清理與型態標準化
    ↓
dbt intermediate：可重複使用的轉換
    ↓
dbt marts：事實表、維度表與 building summary
    ↓
Business Intelligence layer：dashboard 或 self-service analysis
```

旁邊的支援元件：

- `tests/` 驗證程式行為；
- `infrastructure/` 建立 Snowflake 環境；
- `airflow/` 協調執行順序；
- `.github/workflows/` 自動驗證變更；
- `docs/` 說明每個數字的意義和限制。

## 本次 repository hygiene 改善

Repository hygiene 指保持版本庫乾淨、可理解、可重建的習慣。

這一步：

- 將 `.ruff_cache/` 加入 `.gitignore`；
- 將 macOS 自動產生的 `.DS_Store` 加入 `.gitignore`；
- 將 `outputs/` 加入 `.gitignore`；
- 移除沒有用途的空 `ingestion/` 目錄；
- 保留 `work/` 供本機 source profiling，但不提交原始樣本。

## 常用但目前不需要你操作的 Git commands

```text
git status       查看 working tree 狀態
git diff         查看尚未提交的差異
git add          選擇要放入 staging area 的變更
git commit       建立版本快照
git log          查看 commit 歷史
git branch       查看或管理 branches
git show         查看某個 commit 的內容
```

重點不是背指令，而是理解「檢查 → 選擇 → 驗證 → commit」的工作流程。

## 知識點總結

- Git 是版本控制工具；GitHub 是託管與協作平台。
- Working tree、staging area 和 commit 是三個不同階段。
- 小而有意義的 commits 能展示真實思考過程。
- `.gitignore` 可避免 secrets、cache、raw data 和 build output 進入歷史。
- 每個資料夾應有清楚且不重複的責任。
- Airflow 負責協調，dbt 負責轉換，Snowflake 負責儲存與運算。
- 正式英文文件和繁體中文教材服務不同讀者，但描述同一套設計。
- Scaffold 是起始骨架，不等於 production-ready implementation。

## 官方文件

- [Git User Manual](https://git-scm.com/docs/user-manual)
- [Git Reference](https://git-scm.com/docs)
- [GitHub Docs：Ignoring files](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files)
- [Python Packaging User Guide：pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [dbt Docs：About dbt projects](https://docs.getdbt.com/docs/build/projects)
- [Apache Airflow：Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [GitHub Docs：Workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)

## 面試題與參考答案

### 1. How did you organize the repository?

I separated source ingestion, warehouse infrastructure, dbt transformations, orchestration, automated tests, continuous integration, and documentation by responsibility. This makes ownership clear and prevents transformation logic from being duplicated across tools.

### 2. Why do you keep the learning notes separate from the main documentation?

The main project documentation is written in English for recruiters and technical reviewers. The learning directory records detailed Traditional Chinese explanations and interview preparation. Both describe the same design, but they serve different audiences.

### 3. What should never be committed to Git?

Credentials, real environment files, private keys, local virtual environments, caches, generated logs, warehouse build output, and large raw data exports should not be committed. The repository should contain code, configuration templates, tests, and reproducible documentation.

### 4. What makes a good commit?

A good commit represents one understandable change, has a message that explains its intent, and includes relevant validation. It should be small enough to review but complete enough to leave the project in a coherent state.

### 5. What is the difference between Git and GitHub?

Git is the distributed version control system that stores local project history. GitHub is a hosting and collaboration platform built around Git repositories, adding features such as Pull Requests, issue tracking, permissions, and hosted automation.

### 6. Why separate ingestion, transformation, and orchestration?

They solve different problems. Ingestion moves source data into the warehouse, transformation turns raw data into analytical models, and orchestration controls execution order and scheduling. Separating them makes each component easier to test, replace, and reason about.

### 7. How does the Git history prove this is your work?

The history shows the sequence from business framing and source boundaries to executable scaffolding, then live-source profiling that disproved a permit-grain assumption. The commits and Architecture Decision Records preserve not only the final answer but also the evidence and design corrections.

### 8. Why is `.env.example` committed while `.env` is ignored?

`.env.example` documents which configuration values a developer must provide without exposing real secrets. `.env` contains local values and credentials, so it must remain outside version control.

## 自我檢查

進入下一步前，應能回答：

- Git 和 GitHub 有什麼不同？
- Working tree、staging area 和 commit 的關係是什麼？
- `.gitignore` 為什麼重要？
- `src`、`tests`、`dbt`、`airflow`、`infrastructure` 各自負責什麼？
- 為什麼不把原始資料樣本提交到 Git？
- 為什麼 Airflow 不應重寫 dbt transformation logic？
- 目前哪些內容只是 scaffold，還不是 production-ready？
