# src-snapshot

[![CI](https://github.com/dwoiwode/src-snapshot/actions/workflows/ci.yml/badge.svg)](https://github.com/dwoiwode/src-snapshot/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/src-snapshot)](https://pypi.org/project/src-snapshot/)
[![Python](https://img.shields.io/pypi/pyversions/src-snapshot)](https://pypi.org/project/src-snapshot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Lightweight utility to snapshot your source code into a zip archive for reproducible experiments.

Designed for researchers who want a simple, reliable way to store the exact code used for a run (and some metadata).

## Installation

```bash
pip install src-snapshot
```

The package is installed as `src-snapshot` and imported as `src_snapshot`.

## Usage
```python
from src_snapshot import create_snapshot

create_snapshot("code.zip", source_folders="src")
```

That’s it. A zip archive will be created containing your source files and optional metadata.

## Features
- Copy selected source folders into a zip archive
- Filter files by suffix (default: .py, .yaml)
- Include the main entrypoint script (automatically or manual path)
- Store current git commit and diff
- Generate a metadata file with environment, hardware, SLURM and run information

## API
```python
def create_snapshot(
    filepath: Path | str,
    *,
    source_folders: Optional[Path | str | Iterable[Path | str]] = None,
    suffixes: Optional[str | tuple[str]] = (".py", ".yaml"),
    add_main_file: bool | Path | str = True,
    add_git_diff: bool = True,
    add_metadata: bool = True,
)
```

### Arguments
- ``filepath``: Output zip file (must not exist yet)
- ``source_folders``: Folder(s) to include (default: current directory)
- ``suffixes``: File extensions to include
- ``add_main_file``: Include the main script as ``__main__.py``. ``True`` detects it automatically; pass a path to choose it explicitly.
  In interactive sessions (Jupyter, REPL, ``python -c``) there is no main script, so it is skipped with a warning.
- ``add_git_diff``: Store uncommitted changes as ``git_diff.patch``
- ``add_metadata``: Write ``metadata.json`` (timestamp, environment, git info, installed packages)

## Archive contents
```
code.zip
├── <source_folder>/...   # your source files
├── __main__.py           # the entrypoint script
├── git_diff.patch        # uncommitted changes
└── metadata.json         # run metadata
```

## Privacy
``metadata.json`` contains the username, hostname, working directory, command line and the list of installed packages.
Keep this in mind before sharing snapshots publicly, or set ``add_metadata=False``.

## Releasing
Releases are published to PyPI by GitHub Actions using [trusted publishing](https://docs.pypi.org/trusted-publishers/):

1. Bump ``version`` in ``pyproject.toml``.
2. Commit, then tag and push: ``git tag v0.1.0 && git push origin v0.1.0``.

The workflow runs the tests, checks that the tag matches the version, builds and uploads the package.

## License
[MIT](LICENSE)
