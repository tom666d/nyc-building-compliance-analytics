from dataclasses import dataclass


@dataclass(frozen=True)
class Dataset:
    name: str
    dataset_id: str
    target_table: str
    order_by: str


DATASETS = {
    "permits": Dataset("permits", "rbx6-tga4", "RAW_DOB_NOW_PERMITS", "job_filing_number"),
    "complaints": Dataset("complaints", "eabe-havv", "RAW_DOB_COMPLAINTS", "complaint_number"),
    "violations": Dataset("violations", "3h2n-5cm9", "RAW_DOB_VIOLATIONS", "isn_dob_bis_viol"),
}
