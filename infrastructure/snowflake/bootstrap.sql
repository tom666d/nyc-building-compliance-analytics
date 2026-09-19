-- Run with a Snowflake role permitted to create roles, warehouse, database, and schemas.
create role if not exists NYC_DOB_LOADER;
create role if not exists NYC_DOB_TRANSFORMER;
create warehouse if not exists NYC_DOB_WH warehouse_size = 'XSMALL' auto_suspend = 60;
create database if not exists NYC_DOB_ANALYTICS;
create schema if not exists NYC_DOB_ANALYTICS.RAW;
create schema if not exists NYC_DOB_ANALYTICS.DEV;

grant usage on warehouse NYC_DOB_WH to role NYC_DOB_LOADER;
grant usage on warehouse NYC_DOB_WH to role NYC_DOB_TRANSFORMER;
grant usage on database NYC_DOB_ANALYTICS to role NYC_DOB_LOADER;
grant usage on database NYC_DOB_ANALYTICS to role NYC_DOB_TRANSFORMER;
grant usage, create table on schema NYC_DOB_ANALYTICS.RAW to role NYC_DOB_LOADER;
grant usage on schema NYC_DOB_ANALYTICS.RAW to role NYC_DOB_TRANSFORMER;
grant select on future tables in schema NYC_DOB_ANALYTICS.RAW to role NYC_DOB_TRANSFORMER;
grant usage, create table, create view on schema NYC_DOB_ANALYTICS.DEV to role NYC_DOB_TRANSFORMER;

use schema NYC_DOB_ANALYTICS.RAW;
create table if not exists RAW_DOB_NOW_PERMITS (
  raw_payload variant, source_dataset_id varchar, source_row_hash varchar,
  load_id varchar, ingested_at timestamp_tz
);
create table if not exists RAW_DOB_COMPLAINTS like RAW_DOB_NOW_PERMITS;
create table if not exists RAW_DOB_VIOLATIONS like RAW_DOB_NOW_PERMITS;
