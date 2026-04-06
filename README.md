# src_snapshot

Lightweight utility to snapshot your source code into a zip archive for reproducible experiments.

Designed for researchers who want a simple, reliable way to store the exact code used for a run (and some metadata).

## Installation

```bash
pip install src_snapshot
```

## Usage
```python
from src_snapshot import create_snapshot

create_snapshot("code.zip", source_folders="../src")
```

That’s it. A zip archive will be created containing your source files and optional metadata.

## Features
- Copy selected source folders into a zip archive
- Filter files by suffix (default: .py, .yaml)
- Include the main entrypoint script (automatically or manual path)
- Store current git commit and diff
- Generate a metadata file with environment and run information

## API
```python
def create_snapshot(
    filepath: Path | str,
    *,
    source_folders: Optional[Path | str | Iterable[Path | str]] = None,
    suffixes: Optional[str | tuple[str]] = (".py", ".yaml"),
    add_main_file: bool = True,
    add_git_diff: bool = True,
    add_metadata: bool = True,
)
```

### Arguments
- ``filepath``: Output zip file
- ``source_folders``: Folder(s) to include (default: current directory)
- ``suffixes``: File extensions to include
- ``add_main_file``: Include the main script
- ``add_git_diff``: Store uncommitted changes
- ``add_metadata``: Write a metadata file (timestamp, environment, git info)