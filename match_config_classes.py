from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MatchFieldConfig:
    field: str
    weight: float


@dataclass
class MatchConfig:
    fields: List[MatchFieldConfig]
    length_weight: float
    threshold: float
    block_field: str
    group_fields: Optional[List[str]] = None
    sort_before_match: bool = False

