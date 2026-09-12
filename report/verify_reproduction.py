"""Compare a complete independent output directory with the saved analysis."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def verify(reproduced, reference, require_no_git=False):
    def files(folder):
        return {
            p.relative_to(folder): p
            for p in folder.rglob("*")
            if p.is_file() and p.name not in {"run_manifest.json", ".gitkeep"}
        }

    actual, expected = files(reproduced), files(reference)
    assert actual.keys() == expected.keys(), {
        "missing": sorted(str(p) for p in expected.keys() - actual.keys()),
        "extra": sorted(str(p) for p in actual.keys() - expected.keys()),
    }
    checked = []
    arrays = 0
    for name, path in sorted(expected.items()):
        a, b = actual[name], path
        if name.suffix == ".npz":
            with np.load(a) as x, np.load(b) as y:
                assert x.files == y.files, str(name)
                for key in x.files:
                    np.testing.assert_array_equal(x[key], y[key], err_msg=f"{name}:{key}")
                    arrays += 1
            method = "every array equal"
        else:
            assert a.read_bytes() == b.read_bytes(), str(name)
            method = "byte identical"
        checked.append({"file": str(name), "comparison": method})
    manifest = json.loads((reproduced / "run_manifest.json").read_text())
    if require_no_git:
        assert manifest["git_head"] is None, "This audit requires a source copy without Git metadata"
        assert manifest["worktree_has_uncommitted_changes"] is None
    for name, digest in manifest["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    result = {
        "passed": True,
        "command": "python -m swarmtrace.run --data-dir /path/to/data --with-temporal-audit",
        "execution": "Full analysis with optional temporal audit",
        "git_metadata_absent": manifest["git_head"] is None,
        "python": manifest["python"],
        "packages": manifest["packages"],
        "limitation": "Checks repeatability in this environment, not independent external replication",
        "files_compared": len(checked),
        "simulation_arrays_compared": arrays,
        "source_files_verified": len(manifest["source_sha256"]),
        "data_sha256": manifest["data_sha256"],
        "comparisons": checked,
    }
    (ROOT / "report" / "reproduction_validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(f"Verified {len(checked)} files, {arrays} simulation arrays and source hashes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproduced", type=Path)
    parser.add_argument("--reference", type=Path, default=ROOT / "outputs")
    parser.add_argument("--require-no-git", action="store_true")
    args = parser.parse_args()
    verify(args.reproduced, args.reference, args.require_no_git)
