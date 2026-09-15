"""Verify the approved, unchanged release artifacts before deserialization."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports" / "artifact_manifest.json"


def require_experiment_directory(directory):
    """Research scripts must explicitly target a new directory, never the release."""
    resolved = Path(directory).resolve()
    for protected in (ROOT / "models", ROOT / "data", ROOT / "reports"):
        if resolved == protected or resolved.is_relative_to(protected):
            raise ValueError("Use a separate experiment directory; approved release files are protected")


def verify_artifacts(models_dir=None):
    directory = Path(models_dir) if models_dir else ROOT / "models"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name, expected in manifest["sha256"].items():
        path = directory / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Artifact integrity verification failed: {name}")
    return manifest
