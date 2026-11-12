import io
import pathlib
import subprocess
import sys
import tokenize

import nextgram
from nextgram import aiogram_rich, http_rich, ptb_rich, rich_ui

ROOT = pathlib.Path(__file__).resolve().parents[2]


def python_files():
    files = [ROOT / "bot.py"]
    for folder in ("nextgram", "tests"):
        files += sorted((ROOT / folder).rglob("*.py"))
    return files


def test_no_comments_in_python_files():
    offenders = []
    for path in python_files():
        source = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                offenders.append(f"{path.relative_to(ROOT)}:{token.start[0]}")
    assert not offenders, "comment lines found: " + ", ".join(offenders)


def test_every_exported_name_exists():
    for name in nextgram.__all__:
        assert hasattr(nextgram, name), name
    for name in rich_ui.__all__:
        assert hasattr(rich_ui, name), name


def test_all_has_no_duplicates():
    assert len(rich_ui.__all__) == len(set(rich_ui.__all__))
    assert len(nextgram.__all__) == len(set(nextgram.__all__))


def test_public_helpers_are_documented_in_the_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [name for name in rich_ui.__all__ if name != "RICH_AVAILABLE" and name not in readme]
    assert not missing, "missing from README: " + ", ".join(missing)


def test_version_matches_pyproject_dynamic_attr():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'attr = "nextgram.__version__"' in pyproject
    assert nextgram.__version__


def test_kurigram_is_credited_with_the_right_link():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/kurigram-org/kurigram" in readme
    assert "KurimuzonAkuma/kurigram" not in readme


def test_multiframework_module_exports_exist():
    for module in (http_rich, aiogram_rich, ptb_rich):
        for name in module.__all__:
            assert hasattr(module, name), f"{module.__name__}.{name}"


def test_nextgram_imports_without_any_pyrogram_fork_installed():
    guard = (
        "import sys, builtins;"
        "real_import = builtins.__import__;"
        "builtins.__import__ = lambda name, *a, **k: "
        "(_ for _ in ()).throw(ImportError('simulated')) "
        "if name == 'pyrogram' or name.startswith('pyrogram.') "
        "else real_import(name, *a, **k);"
        "import nextgram;"
        "assert nextgram.RICH_AVAILABLE is False;"
        "assert hasattr(nextgram, 'rich_heading');"
        "print('OK')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", guard],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
  
