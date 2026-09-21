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
6. dbt graph parsing without a warehouse connection; and
7. Airflow Dag import and structural contracts.

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

## GitHub setup still required

The repository currently has no GitHub remote, so the tracked workflows have been tested locally
but have not yet executed on GitHub infrastructure. Activating the cloud checks requires an
explicit publishing decision:

1. create a GitHub repository and push this Git history;
2. create an environment named `snowflake-integration`;
3. add `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_B64`, and
   `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` as environment secrets;
4. configure an environment reviewer when the repository plan and visibility support it;
5. run `CI` once and make its status check required on the protected default branch; and
6. manually run `Snowflake integration` only after selecting `confirm_cost`.

Secret values must never be committed, added to documentation, or pasted into an issue or pull
request. The environment should use the existing least-privilege `NYC_DOB_TRANSFORMER` service
identity rather than an account administrator.

GitHub availability of environment protection rules varies by repository visibility and plan.
If required reviewers are unavailable, manual dispatch remains a useful control, but it is not
equivalent to independent approval.

## Supply-chain and maintenance controls

External actions execute code inside the job. Both `actions/checkout` and
`actions/setup-python` are therefore pinned to immutable full commit SHAs, with a comment showing
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
```

This verifies repository behavior on the local machine. It does not prove that a GitHub-hosted
runner or the protected Snowflake workflow has run. That distinction remains explicit until a
remote repository is created and the resulting run URL can be recorded.

## Known limitations

- No GitHub remote, hosted run, required status check, or environment reviewer is configured yet.
- The integration workflow uses the shared development dbt target. A production team should use
  a dedicated CI role and isolated per-change schema before enabling automatic warehouse tests.
- Key-pair secrets are long-lived compared with identity federation. Rotation is still required.
- Python dependencies use compatible version ranges rather than a complete transitive lock file.
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
