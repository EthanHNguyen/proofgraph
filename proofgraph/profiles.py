from __future__ import annotations

from pathlib import Path
import yaml

from proofgraph.schemas import Profile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = PROJECT_ROOT / "profiles"
ALIASES = {"starter": "starter.yaml", "starter-security-profile": "starter.yaml"}


def profile_path(name_or_path: str | Path) -> Path:
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate
    key = str(name_or_path)
    if key in ALIASES:
        return PROFILE_DIR / ALIASES[key]
    if not key.endswith(('.yaml', '.yml')):
        key = f"{key}.yaml"
    return PROFILE_DIR / key


def load_profile(name_or_path: str | Path = "starter") -> Profile:
    path = profile_path(name_or_path)
    if not path.exists():
        raise FileNotFoundError(f"profile not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Profile.model_validate(data)


def list_profiles() -> list[Profile]:
    profiles: list[Profile] = []
    for path in sorted(PROFILE_DIR.glob("*.y*ml")):
        profiles.append(load_profile(path))
    return profiles
