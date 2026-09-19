import argparse
import os

import snowflake.connector
from dotenv import load_dotenv

from .datasets import DATASETS
from .snowflake_loader import load_rows
from .socrata import SocrataClient


def connection_from_env():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE", "NYC_DOB_TRANSFORMER"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "NYC_DOB_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "NYC_DOB_ANALYTICS"),
        schema="RAW",
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Load NYC DOB Open Data into Snowflake RAW")
    parser.add_argument("dataset", nargs="?", choices=DATASETS)
    parser.add_argument("--all", action="store_true", help="load all configured datasets")
    parser.add_argument("--limit", type=int, help="maximum records per dataset")
    parser.add_argument("--page-size", type=int, default=10_000)
    args = parser.parse_args()
    if not args.all and not args.dataset:
        parser.error("choose a dataset or --all")
    return args


def main():
    load_dotenv()
    args = parse_args()
    selected = DATASETS.values() if args.all else [DATASETS[args.dataset]]
    client = SocrataClient(os.getenv("NYC_OPEN_DATA_APP_TOKEN"))
    with connection_from_env() as connection:
        for dataset in selected:
            total = 0
            for rows in client.pages(dataset, limit=args.limit, page_size=args.page_size):
                total += load_rows(connection, dataset.target_table, dataset.dataset_id, rows)
            print(f"loaded {total} rows into {dataset.target_table}")


if __name__ == "__main__":
    main()
