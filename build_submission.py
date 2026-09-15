"""Build an allowlisted zip; --test checks its extracted copy in a fresh venv."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = [
    "README.md", "SUBMISSION_NOTES.md", "DESIGN.md", "DESIGN_REVIEW.md", "RUNBOOK.md",
    "answer-format.md", "approved-answers.md", "requirements.txt", "requirements-lock.txt",
    "app.py", "workflow.py", "semantic.py", "commitments.py", "secure_settings.py", "verify.py",
    "evaluate_retrieval.py", "test_detailed.py", "test_semantic.py", "test_commitments.py",
    "build_submission.py", "verification/VERIFICATION_REPORT.md",
    "app_paths.py", "desktop_launcher.py", "desktop.spec", "desktop-installer.iss",
    "desktop-hooks/hook-workflow.py", "requirements-desktop.txt", "requirements-desktop-lock.txt",
    "test_desktop.py", "package_desktop.py", "DESKTOP_GUIDE.md",
    "verification/commitment-guardrails.md", "verification/commitment-results.json",
    "verification/commitment-tests.txt", "verification/retrieval_live.json",
    "verification/retrieval_offline.json", "verification/q1-fixture-output.csv",
    "verification/q1-fixture-review.xlsx",
]


def build(destination):
    paths = sorted([ROOT / name for name in FILES]
                   + list((ROOT / "knowledge-base").glob("*.md"))
                   + list((ROOT / "questionnaires").glob("*.csv")))
    assert len(list((ROOT / "knowledge-base").glob("*.md"))) == 10
    assert len(list((ROOT / "questionnaires").glob("*.csv"))) == 3
    manifest = {}
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}; choose a new --output name")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError(f"Unsafe package source: {path.name}")
            name = path.relative_to(ROOT).as_posix()
            payload = path.read_bytes()
            # Explicit selection is the primary boundary; also catch common key formats.
            if path.suffix in (".py", ".md", ".json", ".txt", ".csv"):
                if re.search(rb"AIza[0-9A-Za-z_-]{35}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", payload):
                    raise ValueError(f"Potential credential in {name}; refusing package")
            manifest[name] = hashlib.sha256(payload).hexdigest()
            archive.writestr("questionnaire-review/" + name, payload)
        archive.writestr("questionnaire-review/MANIFEST.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(manifest) + 1
    return manifest


def verify_archive(destination, manifest):
    # Retain this isolated directory and logs for inspection; never touch user DBs.
    check_root = ROOT.parent / "submission-checks"
    check_root.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="clean-", dir=check_root))
    with zipfile.ZipFile(destination) as archive:
        for item in archive.infolist():
            target = (stage / item.filename).resolve()
            if not target.is_relative_to(stage.resolve()):
                raise ValueError("Unsafe archive path")
        archive.extractall(stage)
    project = stage / "questionnaire-review"
    for name, digest in manifest.items():
        assert hashlib.sha256((project / name).read_bytes()).hexdigest() == digest
    assert not list(project.rglob("*.sqlite3"))
    environment = os.environ.copy()
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_MODEL", "PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    environment.update(PYTHONNOUSERSITE="1", PYTHONUTF8="1")
    report = {"archive": destination.name, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
              "python": sys.version.split()[0], "platform": platform.platform(), "files": len(manifest) + 1,
              "isolated_directory": str(stage), "live_google_calls": False, "steps": []}

    def run(label, command):
        print(f"Running {label} ...", flush=True)
        started = time.monotonic()
        with (stage / (label + ".log")).open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=project, env=environment, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=1200)
        report["steps"].append({"name": label, "exit_code": result.returncode,
                                "seconds": round(time.monotonic() - started, 3)})
        if result.returncode:
            raise RuntimeError(f"{label} failed; inspect {stage / (label + '.log')}")

    try:
        run("create-venv", [sys.executable, "-m", "venv", str(stage / ".venv")])
        python = stage / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run("install-locked", [str(python), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
                               "--no-compile", "--index-url", "https://pypi.org/simple",
                               "--require-hashes", "-r", "requirements-lock.txt"])
        run("pip-check", [str(python), "-m", "pip", "check"])
        run("credential-backend", [str(python), "-c",
             "import keyring; assert type(keyring.get_keyring()).__name__ == 'WinVaultKeyring'"])
        run("environment", [str(python), "-m", "pip", "freeze", "--all"])
        run("tests", [str(python), "test_commitments.py"])
        report["tests"] = json.loads((project / "verification/commitment-results.json").read_text(encoding="utf-8"))
        run("q1-fixture", [str(python), "verify.py"])
        report["passed"] = True
    except Exception as exc:
        report.update(passed=False, error=str(exc))
        raise
    finally:
        report_path = destination.with_suffix(".validation.json")
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Validation report: {report_path}", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "dist/questionnaire-review-submission.zip")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = build(output)
    if args.test:
        verify_archive(output, manifest)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    print(f"Created {output} ({output.stat().st_size} bytes, {len(manifest) + 1} files)")
    print(f"SHA256 {digest}")
