# Continuous integration

GitHub Actions defines two deliberately separate validation paths. The default path is
safe for untrusted pull-request code and has no external credentials. The live path is a
manual, environment-protected integration check that may consume Snowflake credits.

## Validation boundaries

| Workflow | Trigger | Credentials | External writes | Purpose |
|---|---|---|---|---|
| `CI` | Pull request, push to `main`, or manual run | None | None | Fast repository contracts for every proposed change |
| `Snowflake integration` | Manual run with cost confirmation | Protected environment secrets | Rebuilds development dbt models | Verify the transformation project against the real warehouse |

This separation prevents code submitted in a pull request from automatically receiving
Snowflake credentials. It also keeps routine feedback free of warehouse cost while retaining
an explicit path for integration evidence.

## Static CI gates

The `CI` workflow runs on a GitHub-hosted Ubuntu runner and enforces:

1. repository workflow security rules;
2. Python linting;
3. Python unit tests;
4. installed Python dependency consistency;
5. dbt package resolution;
6. dbt graph parsing without a warehouse connection;
7. Airflow Dag import and structural contracts;
8. locked Node.js dependency installation;
9. production website dependency auditing; and
10. dashboard snapshot validation, linting, and optimized build.

Placeholder connection values allow dbt to parse the profile. They are intentionally invalid,
contain no secrets, and are never used to open a Snowflake connection. The local equivalent is:

```text
make install
make ci-local
```

A non-zero exit code from any command stops the job and blocks a successful status.

## Workflow security contract

`scripts/check_ci_workflows.py` treats the workflows themselves as testable configuration. It
fails when a change removes a required gate or weakens a selected security boundary, including:

- repository token permissions broader than read-only contents;
- a third-party action that is not pinned to a full 40-character commit SHA;
- use of `pull_request_target`;
- GitHub secrets referenced by static pull-request validation;
- an automatic trigger on the live Snowflake workflow;
- missing protected-environment or explicit-cost controls;
- password authentication instead of key-pair authentication;
- missing job timeouts; or
- a context expression placed where GitHub does not make that context available.

The contract is not a universal GitHub Actions policy. It encodes the boundaries selected for
this repository so security-sensitive behavior cannot drift silently.

## Protected Snowflake integration

The live workflow performs only transformation-layer integration:

```text
manual dispatch + confirm_cost=true
  -> protected environment approval, when configured
  -> verify required secrets
  -> create a permission-restricted temporary private-key file
  -> verify transformer access
  -> dbt build and data tests
  -> generate and validate documentation
  -> remove the temporary key
```

It does not run source ingestion. This prevents a CI check from changing the raw extraction
history and confines the run to the development transformation schemas. The concurrency group
does not cancel an active integration run, because interrupting a warehouse build mid-operation
would be less safe than serial execution.

The private key is stored in GitHub as Base64 text because a secret value is text-oriented.
Base64 is an encoding, not encryption. GitHub secret storage and the protected environment are
the security boundaries. During a run, the key is decoded under the runner's temporary directory
with owner-only file permissions and deleted in an `always()` cleanup step.

## GitHub publication status

The project is published at
[tom666d/nyc-building-compliance-analytics](https://github.com/tom666d/nyc-building-compliance-analytics).
The credential-free `CI` workflow has run successfully on GitHub infrastructure. Enabling the
separate live warehouse path still requires deliberate account-side configuration:

1. create an environment named `snowflake-integration`;
2. add `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_B64`, and
   `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` as environment secrets;
3. configure an environment reviewer when the repository plan and visibility support it;
4. make the successful static status check required on the protected default branch; and
5. manually run `Snowflake integration` only after selecting `confirm_cost`.

Secret values must never be committed, added to documentation, or pasted into an issue or pull
request. The environment should use the existing least-privilege `NYC_DOB_TRANSFORMER` service
identity rather than an account administrator.

GitHub availability of environment protection rules varies by repository visibility and plan.
If required reviewers are unavailable, manual dispatch remains a useful control, but it is not
equivalent to independent approval.

## Supply-chain and maintenance controls

External actions execute code inside the job. `actions/checkout`, `actions/setup-python`, and
`actions/setup-node` are therefore pinned to immutable full commit SHAs, with a comment showing
the human-readable release. `persist-credentials: false` prevents the checkout step from leaving
its Git credential available to later commands.

Dependabot is configured to propose weekly updates for GitHub Actions and Python dependencies.
An update is still reviewed and validated before merge; automation proposes changes but does not
replace review.

The workflow grants the generated GitHub token only `contents: read`. This is the least privilege
needed to read the repository for validation. No job receives permission to modify repository
contents, issues, pull requests, or packages.

## Cost and concurrency controls

- Static CI cannot connect to Snowflake and therefore consumes no Snowflake credits.
- Live integration requires manual dispatch and a required Boolean cost confirmation.
- The integration job has a 30-minute timeout.
- Integration runs share one concurrency group and are not overlapped.
- Static validation cancels stale runs for the same pull request or branch.
- The existing Snowflake resource monitor and small development warehouse remain the final
  warehouse-side cost controls.

## Verified evidence

On 2026-09-21, the full local equivalent completed successfully:

```text
Python lint                         passed
Python tests                        25 passed
GitHub workflow contract            passed
Python dependency consistency       passed
dbt dependency resolution           passed
dbt parse without Snowflake          passed
Airflow nine-task Dag contract      passed
Airflow dependency consistency      passed
Dashboard production audit          passed, zero known runtime vulnerabilities
Dashboard snapshot contract         passed
Dashboard lint and build            passed
```

The first hosted run exposed a portability defect: `dotenv run` required a local `.env` file that
correctly does not exist on a clean runner. The Makefile now loads `.env` only when present and
otherwise reads the runner environment. After that correction, the GitHub-hosted
[CI run 35674860951](https://github.com/tom666d/nyc-building-compliance-analytics/actions/runs/35674860951)
completed successfully on 2026-09-21. This proves the credential-free workflow can install and
validate the repository in a clean hosted Linux environment. It does not prove that the protected
Snowflake integration workflow has run.

## Known limitations

- Branch protection, a required status check, and an environment reviewer are not configured yet.
- The protected Snowflake integration workflow has not run from GitHub.
- The integration workflow uses the shared development dbt target. A production team should use
  a dedicated CI role and isolated per-change schema before enabling automatic warehouse tests.
- Key-pair secrets are long-lived compared with identity federation. Rotation is still required.
- Python dependencies use compatible version ranges rather than a complete transitive lock file.
- The website has a reproducible package lock, but development-only package audit findings may
  remain even when the deployable production dependency audit is clean.
- Static CI parses dbt and Airflow structure but cannot detect failures that require live source
  APIs or Snowflake behavior.
- Continuous deployment is not implemented. A passing check does not publish a production release.

## Official references

- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Secrets](https://docs.github.com/en/actions/concepts/security/secrets)
- [Deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)
- [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Dependabot version updates](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuring-dependabot-version-updates)
