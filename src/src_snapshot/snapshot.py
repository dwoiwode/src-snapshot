import datetime
import json
import os
import tempfile
import warnings
from pathlib import Path
from typing import Optional, Iterable
from zipfile import ZipFile, ZIP_DEFLATED

from src_snapshot.utils import git_diff, create_metadata, zip_file_folders, get_main_script_path


def create_snapshot(
        filepath: Path | str,
        *,
        source_folders: Optional[Path | str | Iterable[Path | str]] = None,
        suffixes: Optional[str | tuple[str]] = (".py", ".yaml"),
        add_main_file: bool | Path | str = True,
        add_git_diff: bool = True,
        add_metadata: bool = True
):
    # Prepare source folders (default: current directory)
    if source_folders is None:
        source_folders = (Path.cwd(),)
    elif isinstance(source_folders, (str, Path)):
        source_folders = (source_folders,)
    else:
        source_folders = tuple(source_folders)

    # Prepare output folder
    filepath = Path(filepath)
    if filepath.exists():
        raise FileExistsError(f"Code already exists at {filepath.absolute()}!")

    filepath.parent.mkdir(exist_ok=True, parents=True)

    # Write to a temp file next to the target and rename at the end,
    # so a failed run never leaves a half-written zip behind.
    fd, tmp_name = tempfile.mkstemp(dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        _write_zip(tmp_path, source_folders, suffixes, add_main_file, add_git_diff, add_metadata)
        os.replace(tmp_path, filepath)
    finally:
        tmp_path.unlink(missing_ok=True)


def _write_zip(zip_path, source_folders, suffixes, add_main_file, add_git_diff, add_metadata):
    with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED) as zip_file:
        n = 0
        for source_folder in source_folders:
            source_folder = Path(source_folder).resolve()
            n += zip_file_folders(zip_file, source_folder, source_folder.name, suffixes=suffixes)

        # Add main file
        if add_main_file:
            if isinstance(add_main_file, (Path, str)):
                main_file = Path(add_main_file)
                if not main_file.is_file():
                    raise FileNotFoundError(f"Main file not found: {main_file.absolute()}")
            else:
                main_file = get_main_script_path()

            if main_file is None:
                # e.g. Jupyter, REPL or `python -c`: nothing to copy
                warnings.warn(
                    "Could not determine the main script (interactive session?); "
                    "skipping __main__.py. Pass add_main_file=<path> to set it explicitly.",
                    stacklevel=3,
                )
            else:
                main_file_content = (
                    f"# Originally copied on {datetime.datetime.now():%Y-%m-%d %H:%M:%S} from {main_file.absolute()}\n\n"
                    f"{main_file.read_text(encoding='utf-8')}"
                )
                zip_file.writestr('__main__.py', main_file_content)
                n += 1

        # Add git diff
        if add_git_diff:
            n += 1
            zip_file.writestr('git_diff.patch', git_diff())

        # Add metadata
        if add_metadata:
            n += 1
            meta = create_metadata()
            meta["files_copied"] = n
            zip_file.writestr('metadata.json', json.dumps(meta, indent=2))
