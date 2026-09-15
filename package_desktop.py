"""Verify and zip an already-built desktop bundle; write hashes and a test record."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT.parent / "desktop-dist/QuestionnaireReview")
    parser.add_argument("--output", type=Path, default=ROOT.parent / "dist/QuestionnaireReview-Portable-1.0.0.zip")
    args = parser.parse_args()
    bundle, output = args.bundle.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Choose a new output filename: {output}")
    check_root = ROOT.parent / "desktop-checks"
    check_root.mkdir(exist_ok=True)
    check = Path(tempfile.mkdtemp(prefix="frozen-", dir=check_root))
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL"):
        environment.pop(key, None)
    environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    executable = bundle / "QuestionnaireReview.exe"
    started = time.monotonic()
    result = subprocess.run([str(executable), "--self-test", str(check)], cwd=check,
                            env=environment, timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    report = json.loads((check / "desktop-self-test.json").read_text(encoding="utf-8"))
    if result.returncode or not report.get("passed") or not report.get("frozen"):
        raise RuntimeError(f"Frozen application failed: {report}; inspect {check}")
    report.update(seconds=round(time.monotonic() - started, 3), test_directory=str(check),
                  python_removed_from_path=True, separate_clean_vm_tested=False)
    files = [p for p in sorted(bundle.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    manifest = {}
    for path in files:
        relative = path.relative_to(bundle).as_posix()
        if path.is_symlink() or path.suffix in (".sqlite3", ".db") or path.name == ".env":
            raise ValueError(f"Unexpected file in bundle: {relative}")
        manifest[relative] = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "QuestionnaireReview/" + path.relative_to(bundle).as_posix())
        archive.writestr("QuestionnaireReview/BUNDLE_MANIFEST.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    digest = hashlib.file_digest(output.open("rb"), "sha256").hexdigest()
    report.update(archive=output.name, sha256=digest, bytes=output.stat().st_size, payload_files=len(files))
    output.with_suffix(".validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    output.with_suffix(".sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
