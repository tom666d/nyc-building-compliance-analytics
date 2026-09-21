# ADR 0011: Separate static CI from live warehouse integration

- Status: Accepted
- Date: 2026-09-21

## Context

The repository needs automated feedback for every proposed change. Python tests, dbt parsing, and
Airflow structure can be validated without external services. A complete dbt build, however,
requires Snowflake credentials, changes development relations, and consumes warehouse credits.

Providing warehouse credentials to automatic pull-request jobs would increase secret-exposure
risk, especially when evaluating untrusted code. Running every check against one shared
development schema could also create concurrent builds, nondeterministic failures, and avoidable
trial-account cost. The project does not yet have a dedicated CI role or isolated per-change
Snowflake schemas.

## Decision

Use two GitHub Actions workflows with different trust and cost boundaries:

1. run credential-free static validation for pull requests, pushes to `main`, and manual requests;
2. run live Snowflake integration only through manual dispatch with explicit cost confirmation;
3. place live credentials in a GitHub environment named `snowflake-integration`;
4. use the least-privilege transformer identity with key-pair authentication;
5. serialize live integration runs and never cancel one already modifying the warehouse;
6. keep ingestion outside CI so validation does not alter raw extraction history;
7. give the GitHub token read-only repository-content permission;
8. pin external actions to immutable commit SHAs; and
9. test these boundaries with a repository-owned workflow contract.

## Consequences

### Benefits

- Pull-request code receives no Snowflake secrets.
- The default feedback loop is free of Snowflake credit consumption.
- Most syntax, unit, dbt-graph, and Airflow-contract failures are found before warehouse use.
- A protected manual path still proves the dbt project against the real platform.
- Workflow security choices are executable tests rather than undocumented conventions.
- Immutable action references reduce dependency supply-chain drift.

### Costs and limitations

- Static validation cannot detect every live Snowflake behavior or permission problem.
- Integration evidence depends on a human trigger until isolated CI infrastructure exists.
- The current live check shares development schemas and therefore must be serialized.
- GitHub environment approval features depend on repository visibility and account plan.
- A separate GitHub repository setup step is required before hosted evidence exists.

## Alternatives considered

### Run Snowflake integration automatically on every pull request

Rejected for the current phase because it would expose credentials to a broader execution path,
consume credits routinely, and run concurrent changes against shared schemas. It can be revisited
after a dedicated CI identity and disposable schema strategy exist.

### Use one workflow with conditional secret steps

Rejected because separate workflow files make the trust boundary visible and reduce the chance
that a trigger edit accidentally places live credentials in the pull-request path.

### Use a Snowflake password secret

Rejected because the project already established key-pair service authentication, which avoids a
reusable login password and supports deliberate key rotation.

### Skip live integration entirely

Rejected because static parsing cannot demonstrate real warehouse permissions, model creation,
data tests, or physical documentation coverage.
