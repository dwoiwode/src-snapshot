from pathlib import Path

from src_snapshot import create_snapshot

# Snapshot the package source next to this repository's examples folder
create_snapshot("code.zip", source_folders=Path(__file__).parent.parent / "src")
