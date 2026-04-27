import argparse
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.besci.models import BeSciTextSample
from app.besci.service import analyze_text_samples


def _load_entries(args: argparse.Namespace) -> list[str]:
    entries: list[str] = []
    if args.entry:
        entries.extend(args.entry)
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
        entries.extend(line.strip() for line in content.splitlines() if line.strip())
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a local BeSci longitudinal text analysis demo."
    )
    parser.add_argument(
        "--entry",
        action="append",
        help="Add one longitudinal text sample. Pass multiple times to build a sequence.",
    )
    parser.add_argument(
        "--file",
        help="Path to a text file where each non-empty line is treated as one time-ordered sample.",
    )
    args = parser.parse_args()

    entries = _load_entries(args)
    if not entries:
        raise SystemExit("Provide at least one --entry or a --file with non-empty lines.")

    analysis = analyze_text_samples([BeSciTextSample(text=entry) for entry in entries])
    print(json.dumps(analysis.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
