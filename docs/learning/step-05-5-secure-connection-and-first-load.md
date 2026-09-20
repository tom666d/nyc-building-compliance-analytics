# Step 5.5：安全連線與第一次 Snowflake 真實資料載入

## 這一步要完成什麼

Step 5 已經在 Snowflake 網頁建立 database、warehouse、schemas、tables 和 roles。這一步要補上真正的 programmatic connection（程式連線）：

1. 不使用人的 Snowflake 密碼；
2. 建立專用 service user；
3. 使用 key-pair authentication；
4. 從本機 Python 分別驗證 loader、transformer、reader；
5. 對三個官方資料集各載入 1,000 筆真實資料；
6. 確認 raw row count、row hash 與 load metadata。

## 為什麼不直接使用我的 Snowflake 密碼

Human user（人類使用者）需要登入網頁、重設密碼或完成多因素驗證；pipeline（資料管線）則要在沒有人工操作時執行。若 ingestion 或 dbt 直接保存人的密碼，會有幾個問題：

- 人的密碼變更後，pipeline 會中斷；
- 密碼可能被誤貼到 Git、log 或設定畫面；
- query history 無法清楚分辨人與自動化程式；
- Snowflake 正在要求 service users 使用比 password 更強的 authentication。

因此本專案建立 `NYC_DOB_PIPELINE` service user，只讓它透過 private key 登入。

## 新名詞解釋

### Programmatic connection

Programmatic connection 是由程式、命令列或排程工具建立的連線，不是人在網頁上手動點擊。

### Service user

Service user 是代表應用程式或自動化工作的 Snowflake 身分。本專案的 service user 沒有人類密碼，透過 key pair 驗證身分。

### Key pair

Key pair 由兩個互相關聯的金鑰組成：

- Private key：只能保留在執行程式的安全環境；
- Public key：可以交給 Snowflake，用來驗證 private key 產生的簽章。

Public key 無法直接還原 private key，所以 Snowflake 不需要保存我們的登入秘密。

### Asymmetric cryptography

Asymmetric cryptography（非對稱密碼學）使用不同的 key 執行簽章與驗證。它與「雙方保存同一個 password」不同。

### PKCS#8

Public-Key Cryptography Standards number 8 是一種 private-key 檔案格式，通常寫成 PKCS#8。本專案使用 Advanced Encryption Standard 256-bit encryption 保護這個檔案。

### Passphrase

Passphrase 是解密 private-key file 的秘密。只有拿到 private key 檔案但沒有 passphrase，仍無法直接使用該金鑰。

### JSON Web Token

JSON Web Token 是一種可簽章的 token 格式，通常簡寫為 JWT。Snowflake Python Connector 使用 private key 產生短期簽章，Snowflake 再用 public key 驗證。

### Fingerprint

Fingerprint（金鑰指紋）是對 public key 計算的短摘要。比較本機與 Snowflake 的 fingerprint，可以確認兩端保存的是同一組 key pair，而不需要公開 private key。

### Key rotation

Key rotation 是定期以新金鑰取代舊金鑰。Snowflake 的 named key pair 能保留清楚的名稱與 rotation 操作。本專案的範本使用 `LOCAL_PORTFOLIO_KEY`。

## 實際安全設計

本機建立：

```text
.secrets/snowflake_rsa_key.p8   ← 加密的 private key
.secrets/snowflake_rsa_key.pub  ← public key
.env                            ← 本機連線參數和 passphrase
```

`.env`、`.secrets/`、`*.p8` 和 `*.pem` 都被 `.gitignore` 排除。Repository 只保存：

- environment variable 名稱；
- 建立 service user 的範例 SQL；
- 支援 key-pair authentication 的程式碼；
- 不包含 secret values 的測試。

## Least privilege 如何延續到程式連線

同一個開發用 service user 被授予三個 roles，但每次 connection 只啟用一個 primary role：

| Workload | Active role | 驗證結果 |
|---|---|---|
| Python ingestion | `NYC_DOB_LOADER` | 只看到 `RAW` 與三張 raw tables |
| dbt transformation | `NYC_DOB_TRANSFORMER` | 看到 raw 與三個 dbt development schemas |
| BI/read check | `NYC_DOB_READER` | 只看到 `DEV_MARTS`，看不到 raw tables |

三個 read-only connection checks 都回傳 `ready: true`。

## 第一次真實資料載入

執行 bounded sample：

```text
nyc-dob-ingest --all --limit 1000
```

結果：

| Raw table | Rows | Distinct source hashes | Load batches |
|---|---:|---:|---:|
| `RAW_DOB_NOW_PERMITS` | 1,000 | 1,000 | 1 |
| `RAW_DOB_COMPLAINTS` | 1,000 | 1,000 | 1 |
| `RAW_DOB_VIOLATIONS` | 1,000 | 1,000 | 1 |

Distinct source hashes 等於 row count，表示這三個 1,000-row samples 內沒有 byte-equivalent canonical payload duplicates。

## 為什麼先載入 1,000 筆，而不是六百多萬筆

這叫 bounded validation：先用有明確上限的小批真實資料證明 authentication、network、permissions、insertion、metadata 和下游 transformations 能完整工作。

如果設計有錯，小樣本能更快、成本更低地暴露問題。這不是用 synthetic data 取代真實資料；三個 samples 都直接來自官方 NYC Open Data API。

## 知識點總結

- Human user 與 service user 應有不同用途。
- Private key 留在本機；Snowflake 只保存 public key。
- 加密 key file 和 passphrase 都不能進 Git。
- Authentication 證明 service user 身分；role 決定該連線可以做什麼。
- Bounded sample 能以低成本驗證端到端流程。
- Raw layer 允許 append 多個 load batches；staging 再處理 exact duplicate payloads。

## 官方文件

- [Snowflake：Key-pair authentication and rotation](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Snowflake：Types of users](https://docs.snowflake.com/en/user-guide/admin-user-management)
- [Snowflake：Python Connector authentication](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect)
- [Snowflake：Strong authentication rollout](https://docs.snowflake.com/en/user-guide/security-mfa-rollout)
- [dbt：Snowflake setup](https://docs.getdbt.com/docs/local/connect-data-platform/snowflake-setup)

## 面試題與參考答案

### 1. Why did you use key-pair authentication instead of a password?

I used a dedicated service identity with an encrypted private key so automated ingestion and dbt runs do not depend on a human password or interactive login. Snowflake stores only the public key, while the private key and passphrase remain outside Git.

### 2. Did you give the service user ACCOUNTADMIN?

No. It receives the project loader, transformer, and reader roles. Each connection activates only the role required by that workload. Administrative roles were used only to provision account-level objects and grants.

### 3. How did you prove the permissions work?

I connected through the Python connector once for each workload role. The loader could see only raw objects, the transformer could see raw and development schemas, and the reader could see only the curated mart schema. All three checks returned ready.

### 4. Why did you start with 1,000 rows per source?

It was a bounded end-to-end validation using real public data. It proved authentication, API extraction, raw loading, metadata, and downstream dbt behavior before spending time and credits on more than 6.6 million source rows.
