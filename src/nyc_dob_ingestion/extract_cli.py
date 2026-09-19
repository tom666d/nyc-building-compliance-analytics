import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

from .datasets import DATASETS
from .extract import extract_to_jsonl
from .socrata import SocrataClient


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract a bounded real-data sample from NYC Open Data to JSON Lines"
    )
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--limit", type=positive_int, default=100)
    parser.add_argument("--page-size", type=positive_int, default=1000)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    dataset = DATASETS[args.dataset]
    output = args.output or Path("work/samples") / f"{dataset.name}.jsonl"
    client = SocrataClient(os.getenv("NYC_OPEN_DATA_APP_TOKEN"))
    manifest = extract_to_jsonl(
        client,
        dataset,
        output,
        limit=args.limit,
        page_size=args.page_size,
    )
    print(json.dumps(asdict(manifest), indent=2))


if __name__ == "__main__":
    main()
