# NYC Building Compliance 360 dashboard

This application is the shareable consumption layer for the analytics engineering project. It
imports a validated, versioned snapshot from the Snowflake/dbt marts at build time, so no warehouse
credential reaches the browser and viewing the site does not consume Snowflake credits.

## Commands

```text
npm ci                  Install exactly the dependency lock
npm run validate:data   Validate snapshot rollups and identifiers
npm test                Validate the snapshot and lint the application
npm run build           Create the optimized deployment build
npm run dev             Start the local dashboard
```

Refresh `data/dashboard-snapshot.json` from the repository root with
`make dashboard-export` after the dbt consumption marts have completed. The checked-in snapshot is
a bounded portfolio sample, not a citywide estimate.

See `docs/bi_consumption.md` in the repository root for metric definitions, architecture, evidence,
and limitations.

The owner-private deployed preview is available at
<https://nyc-building-compliance-360-portfolio.hsieh203.chatgpt.site>. Access remains restricted
until the owner explicitly changes the site's audience.
