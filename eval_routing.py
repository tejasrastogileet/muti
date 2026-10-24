import json
import random
from pathlib import Path

from router import keyword_route, route


def accuracy(rows: list[dict], router) -> float:
    if not rows:
        return 0.0
    correct = sum(router(row["query"]) == row["label"] for row in rows)
    return correct / len(rows)


def main() -> None:
    data_path = Path(__file__).with_name("eval_data.json")
    with data_path.open(encoding="utf-8") as data_file:
        examples = json.load(data_file)

    random.Random(42).shuffle(examples)
    midpoint = len(examples) // 2
    splits = {
        "dev": examples[:midpoint],
        "test": examples[midpoint:],
    }

    for split_name, rows in splits.items():
        print(f"{split_name} ({len(rows)} queries)")
        print(f"  keyword_route: {accuracy(rows, keyword_route):.2%}")
        print(f"  route:         {accuracy(rows, route):.2%}")


if __name__ == "__main__":
    main()
