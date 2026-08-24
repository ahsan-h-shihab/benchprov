import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT, base_record, with_derived

from benchprov.build import build
from benchprov.model import canonical_dumps


def make_mini_repo(tmp_path: Path, records: list[dict]) -> Path:
    root = tmp_path / "mini"
    (root / "schema").mkdir(parents=True)
    (root / "sources" / "records").mkdir(parents=True)
    (root / "registry").mkdir()
    shutil.copy(REPO_ROOT / "schema" / "provenance.schema.json", root / "schema")
    shutil.copy(REPO_ROOT / "registry" / "families.json", root / "registry" / "families.json")
    for rec in records:
        p = root / "sources" / "records" / f"{rec['record_id']}.json"
        p.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    return root


def second_record() -> dict:
    rec = base_record()
    rec["dataset"]["id"] = "example-org/mmlu-yy"
    rec["dataset"]["url"] = "https://huggingface.co/datasets/example-org/mmlu-yy"
    rec["target_languages"] = ["yy"]
    rec["record_id"] = "example-org-mmlu-yy__yy"
    return with_derived(rec)


def test_build_deterministic(tmp_path):
    root = make_mini_repo(tmp_path, [second_record(), base_record()])
    report, changed = build(root)
    assert report.ok, [str(f) for f in report.errors]
    assert changed
    text1 = (root / "registry" / "provenance.jsonl").read_text(encoding="utf-8")
    # rebuild -> unchanged, byte-identical
    report2, changed2 = build(root)
    assert report2.ok and not changed2
    text2 = (root / "registry" / "provenance.jsonl").read_text(encoding="utf-8")
    assert text1 == text2
    # sorted by record_id
    ids = [json.loads(l)["record_id"] for l in text1.splitlines()]
    assert ids == sorted(ids)


def test_build_check_detects_stale(tmp_path):
    root = make_mini_repo(tmp_path, [base_record()])
    build(root)
    # tamper with generated registry
    reg = root / "registry" / "provenance.jsonl"
    rec = json.loads(reg.read_text(encoding="utf-8"))
    rec["license"] = "tampered"
    reg.write_text(canonical_dumps(rec) + "\n", encoding="utf-8")
    report, mismatch = build(root, check_only=True)
    assert mismatch
    assert any(f.check == "registry-stale" for f in report.errors)


def test_build_refuses_on_invalid_source(tmp_path):
    bad = base_record()
    bad["completeness"] = 0.99  # stale on purpose
    root = make_mini_repo(tmp_path, [bad])
    report, _ = build(root)
    assert not report.ok
    assert not (root / "registry" / "provenance.jsonl").exists()


def test_build_filename_must_match_record_id(tmp_path):
    root = make_mini_repo(tmp_path, [base_record()])
    src = root / "sources" / "records"
    (src / "example-org-mmlu-zz__zz.json").rename(src / "wrong-name.json")
    report, _ = build(root)
    assert any(f.check == "filename" for f in report.errors)


# ------------------------------------------------------------------ CLI smoke

def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "benchprov.cli", *args],
        cwd=cwd, capture_output=True, text=True, timeout=120,
        encoding="utf-8",  # the CLI reconfigures its streams to UTF-8
    )


@pytest.fixture(scope="module")
def mini(tmp_path_factory) -> Path:
    root = make_mini_repo(tmp_path_factory.mktemp("cli"), [base_record(), second_record()])
    report, _ = build(root)
    assert report.ok
    return root


def test_cli_validate_repo(mini):
    res = run_cli(["validate"], cwd=mini)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PASS" in res.stdout


def test_cli_validate_bad_file(mini, tmp_path):
    bad = base_record()
    bad["translation_type"] = "sorcery"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    res = run_cli(["validate", str(p)], cwd=mini)
    assert res.returncode == 1
    assert "FAIL" in res.stdout


def test_cli_inspect_headlines(mini):
    res = run_cli(["inspect", "example-org/mmlu-zz"], cwd=mini)
    assert res.returncode == 0, res.stderr
    for needle in ["Machine translated?", "Human verified?", "Evidence:",
                   "gpt-3.5-turbo", "UNKNOWN — no public statement found",
                   "Unknown dimensions", "human_verification"]:
        assert needle in res.stdout, f"missing {needle!r} in:\n{res.stdout}"


def test_cli_inspect_json(mini):
    res = run_cli(["inspect", "example-org-mmlu-zz__zz", "--json"], cwd=mini)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["record_id"] == "example-org-mmlu-zz__zz"


def test_cli_inspect_not_found(mini):
    res = run_cli(["inspect", "no-such-thing"], cwd=mini)
    assert res.returncode == 1


def test_cli_stats(mini):
    res = run_cli(["stats", "--json"], cwd=mini)
    assert res.returncode == 0, res.stderr
    s = json.loads(res.stdout)
    assert s["records"] == 2
    assert s["by_translation_type"] == {"machine": 2}


def test_cli_build_check(mini):
    res = run_cli(["build", "--check"], cwd=mini)
    assert res.returncode == 0
    assert "up to date" in res.stdout


def test_packaged_data_in_sync():
    canonical = (REPO_ROOT / "schema" / "provenance.schema.json").read_bytes()
    packaged = (REPO_ROOT / "src" / "benchprov" / "_data" / "provenance.schema.json").read_bytes()
    assert canonical == packaged, "run: cp schema/provenance.schema.json src/benchprov/_data/"
    canonical_f = (REPO_ROOT / "registry" / "families.json").read_bytes()
    packaged_f = (REPO_ROOT / "src" / "benchprov" / "_data" / "families.json").read_bytes()
    assert canonical_f == packaged_f, "run: cp registry/families.json src/benchprov/_data/"
