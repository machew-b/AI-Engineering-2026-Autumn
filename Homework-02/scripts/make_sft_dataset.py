"""Homework 2 (Advanced): build the Q&A data (JSONL, "messages" format) from the course glossary.

Same entry point as the course script (`uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl`
prints the training data), with more options. The Colab notebook builds the same data by itself, so
running this is only needed if you want to look at the files.

    uv run python scripts/make_sft_dataset.py                       # training data to stdout
    uv run python scripts/make_sft_dataset.py --abstain             # + "not in the glossary" examples (run B)
    uv run python scripts/make_sft_dataset.py --out-dir data/generated   # train, valid, test, gold, manifest
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import glossary_data as gd  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--abstain", action="store_true", help="add examples whose answer is 'not in the glossary' (run B)")
    p.add_argument("--out-dir", help="write train/valid/test/gold/manifest here instead of printing training data")
    args = p.parse_args()
    data = gd.build_dataset(include_abstain=args.abstain)
    if not args.out_dir:
        for r in data["train"]:
            sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
        return
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gd.write_jsonl(data["train"], out / "train.jsonl")
    gd.write_jsonl(data["valid"], out / "valid.jsonl")
    gd.write_jsonl(data["test"], out / "test.jsonl")
    (out / "gold.json").write_text(json.dumps(data["gold"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(data["meta"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
