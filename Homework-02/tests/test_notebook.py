import ast
import json
import re
import urllib.parse

from app import glossary_data as gd

NB_PATH = gd.ROOT / "notebooks" / "lora_glossary_tuning.ipynb"
NB = json.loads(NB_PATH.read_text(encoding="utf-8"))
CODE = [("".join(c["source"])) for c in NB["cells"] if c["cell_type"] == "code"]
ALL = "\n".join(CODE)


def test_every_code_cell_parses_and_has_no_saved_output():
    for src in CODE:
        ast.parse("\n".join("pass" if line.lstrip().startswith("%") else line for line in src.split("\n")))
    assert all(c["outputs"] == [] for c in NB["cells"] if c["cell_type"] == "code")
    assert NB["nbformat"] == 4 and NB["metadata"]["colab"]["gpuType"] == "T4"


def test_default_run_is_run_a_with_course_settings():
    assert 'RUN_NAME = "run_a"' in ALL and "INCLUDE_ABSTAIN = False" in ALL
    for text in ('"base_model": "Qwen/Qwen3.5-0.8B"', '"revision": "2fc06364715b967f1860aea9cf38778875588b17"', '"lr": 2e-4',
                 '"lora_r": 16', '"lora_alpha": 32', '"seed": 42', '"do_sample": False', '"transformers": "5.18.0"',
                 '"peft": "0.21.1"', '"trl": "1.14.2"'):
        assert text in ALL, text


def test_notebook_only_calls_functions_that_exist():
    from app import retrieval, scoring
    for name in re.findall(r"(?<![/\w])gd\.(\w+)", ALL):
        assert hasattr(gd, name), name
    for name in re.findall(r"(?<![/\w])scoring\.(\w+)", ALL):
        assert hasattr(scoring, name), name
    for name in re.findall(r"(?<![/\w])retrieval\.(\w+)", ALL):
        assert hasattr(retrieval, name), name


def test_downloaded_files_exist_in_the_repo_folder():
    files = ast.literal_eval(re.search(r"FILES = (\[.*?\])", ALL, re.S).group(1))
    for rel in files:
        assert (gd.ROOT / rel).is_file(), rel
    base = re.search(r'REPO_RAW = "([^"]+)"', ALL).group(1)
    assert urllib.parse.urlparse(base).path.endswith("/AI-Engineering-2026-Autumn/main/Homework-02")


def test_notebook_keeps_the_same_prompt_for_training_and_evaluation():
    assert ALL.count("gd.build_messages") == 1                 # evaluation; training data comes from gd.build_dataset
    assert "Dataset.from_list(train)" in ALL and "enable_thinking=False" in ALL
