-- Replace the placeholder public key before running this file.
-- Never place the matching private key or passphrase in this repository.

USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS NYC_DOB_PIPELINE
  TYPE = SERVICE
  DEFAULT_ROLE = NYC_DOB_LOADER
  DEFAULT_WAREHOUSE = NYC_DOB_WH
  DEFAULT_NAMESPACE = NYC_DOB_ANALYTICS.RAW
  DEFAULT_SECONDARY_ROLES = ()
  COMMENT = 'Local portfolio ingestion and dbt service identity';

-- Named key pairs support explicit naming and future rotation.
-- Run ADD KEY PAIR once. Use ALTER USER ... ROTATE KEY PAIR for replacement.
ALTER USER NYC_DOB_PIPELINE ADD KEY PAIR LOCAL_PORTFOLIO_KEY
  PUBLIC_KEY = '<PUBLIC_KEY_WITHOUT_PEM_HEADERS>'
  COMMENT = 'Encrypted private key remains outside source control';

USE ROLE SECURITYADMIN;

GRANT ROLE NYC_DOB_LOADER TO USER NYC_DOB_PIPELINE;
GRANT ROLE NYC_DOB_TRANSFORMER TO USER NYC_DOB_PIPELINE;
GRANT ROLE NYC_DOB_READER TO USER NYC_DOB_PIPELINE;
