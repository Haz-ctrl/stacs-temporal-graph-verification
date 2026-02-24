import json
from pathlib import Path
from typing import Dict, List, Any

def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file (one object per line)

    Parameters:
    path : str OR Path
        Path to the dataset file, can be represented as a string or Path object

    Returns:
    List[Dict[str, Any]]
    """
    path = Path(path)
    items: List[Dict[str, Any]] = []
    
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as err:
                raise ValueError(f"Invalid JSON on line {i} of {path}: {err}") from err
    
    return items