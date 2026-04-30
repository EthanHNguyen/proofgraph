from __future__ import annotations

from pathlib import Path
from importlib import resources
import yaml

from proofgraph.schemas import Profile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = PROJECT_ROOT / "profiles"
BUNDLED_PROFILE_PACKAGE = "proofgraph.bundled_profiles"
ALIASES = {"starter": "starter.yaml", "starter-security-profile": "starter.yaml"}


def profile_path(name_or_path: str | Path) -> Path:
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate
    key = str(name_or_path)
    filename = ALIASES.get(key, key if key.endswith(('.yaml', '.yml')) else f"{key}.yaml")
    source_path = PROFILE_DIR / filename
    if source_path.exists():
        return source_path
    try:
        bundled = resources.files(BUNDLED_PROFILE_PACKAGE).joinpath(filename)
        if bundled.is_file():
            return Path(str(bundled))
    except ModuleNotFoundError:
        pass
    return source_path


def _read_profile_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Path may be an importlib Traversable represented as a string inside a wheel.
    filename = path.name
    bundled = resources.files(BUNDLED_PROFILE_PACKAGE).joinpath(filename)
    return bundled.read_text(encoding="utf-8")


def load_profile(name_or_path: str | Path = "starter") -> Profile:
    path = profile_path(name_or_path)
    try:
        text = _read_profile_text(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"profile not found: {path}") from exc
    data = yaml.safe_load(text) or {}
    return Profile.model_validate(data)


def list_profiles() -> list[Profile]:
    seen: set[str] = set()
    profiles: list[Profile] = []
    paths = list(PROFILE_DIR.glob("*.y*ml")) if PROFILE_DIR.exists() else []
    try:
        paths.extend(Path(str(p)) for p in resources.files(BUNDLED_PROFILE_PACKAGE).iterdir() if p.name.endswith((".yaml", ".yml")))
    except ModuleNotFoundError:
        pass
    for path in sorted(paths, key=lambda p: p.name):
        profile = load_profile(path)
        if profile.id not in seen:
            profiles.append(profile)
            seen.add(profile.id)
    if not profiles:
        raise FileNotFoundError("no bundled or local profiles found")
    return profiles
