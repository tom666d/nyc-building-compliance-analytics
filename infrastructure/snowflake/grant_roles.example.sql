-- Replace the example username before running this file.
-- For a portfolio account, one developer can hold all three roles and switch
-- between them. A production system should use separate human and service users.

USE ROLE SECURITYADMIN;

SET PROJECT_USER = 'REPLACE_WITH_YOUR_SNOWFLAKE_USERNAME';

GRANT ROLE NYC_DOB_LOADER TO USER IDENTIFIER($PROJECT_USER);
GRANT ROLE NYC_DOB_TRANSFORMER TO USER IDENTIFIER($PROJECT_USER);
GRANT ROLE NYC_DOB_READER TO USER IDENTIFIER($PROJECT_USER);
