"""Import-dependency contract for the gleaner client package.

The client is organized into packages that each fulfill one function
independently:

    sources/  — find & parse local IDE sessions   (no internal deps)
    remote/   — HTTP client for the Gleaner server (no internal deps)
    scrub/    — PII/secret scrubbing               (no internal deps)
    setup/    — config file + capture installers   (no internal deps)
    enrich    — classification + provenance        (no internal deps)
    vault/    — local session store                (may use sources, enrich)

Everything else (cli, pipeline, backfill, pull, hooks) is orchestration and
may depend on any of the above. These tests parse the import statements of
every module and fail when a package grows a dependency outside its
contract, so the boundaries survive future refactorings.
"""

import ast
from pathlib import Path

import pytest

GLEANER_DIR = Path(__file__).resolve().parent.parent / "gleaner"

# package -> internal packages/modules it may import from (itself is always allowed)
ALLOWED_INTERNAL_DEPS = {
    "sources": set(),
    "remote": set(),
    "scrub": set(),
    "setup": set(),
    "enrich": set(),
    "vault": {"sources", "enrich"},
}


def _gleaner_imports(path: Path) -> set[str]:
    """Top-level gleaner subpackage/module names imported by a file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "gleaner" or alias.name.startswith("gleaner."):
                    parts = alias.name.split(".")
                    found.add(parts[1] if len(parts) > 1 else "")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:  # relative import — resolve against gleaner/
                rel = path.relative_to(GLEANER_DIR).parts
                base = rel[: len(rel) - node.level]
                module = ".".join(("gleaner", *base, module) if module else ("gleaner", *base))
            if module == "gleaner":
                found.update(alias.name for alias in node.names)
            elif module.startswith("gleaner."):
                found.add(module.split(".")[1])
    return found


def _modules_of(package: str) -> list[Path]:
    root = GLEANER_DIR / package
    if root.is_dir():
        return sorted(root.rglob("*.py"))
    return [GLEANER_DIR / f"{package}.py"]


@pytest.mark.parametrize("package", sorted(ALLOWED_INTERNAL_DEPS))
def test_package_dependencies_stay_within_contract(package):
    """Each functional package only imports itself + its allowed dependencies."""
    allowed = ALLOWED_INTERNAL_DEPS[package] | {package}
    for module in _modules_of(package):
        illegal = _gleaner_imports(module) - allowed
        assert not illegal, (
            f"{module.relative_to(GLEANER_DIR.parent)} imports {sorted(illegal)}; "
            f"'{package}' may only depend on {sorted(allowed)}"
        )


def test_all_client_modules_are_importable():
    """Every module in the client package imports cleanly (catches syntax and
    wiring mistakes even in modules no other test touches)."""
    import importlib

    for path in sorted(GLEANER_DIR.rglob("*.py")):
        rel = path.relative_to(GLEANER_DIR.parent).with_suffix("")
        name = ".".join(rel.parts).removesuffix(".__init__")
        importlib.import_module(name)
