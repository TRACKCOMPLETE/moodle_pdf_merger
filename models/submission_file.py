from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubmissionFile:
    path: Path
    index: int = 0
    total: int = 0