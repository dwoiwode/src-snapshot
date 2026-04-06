import datetime
import json
from pathlib import Path
from typing import Optional, Iterable
from zipfile import ZipFile

from src_snapshot.utils import git_diff, create_metadata, zip_file_folders, get_main_script_path


def create_snapshot(
        filepath: Path | str,
        *,
        source_folders: Optional[Path | str | Iterable[Path | str]] = None,
        suffixes: Optional[str | tuple[str]] = (".py", ".yaml"),
        add_main_file=True,
        add_git_diff=True,
        add_metadata=True
):
    # Prepare source folder
    if not isinstance(source_folders, (tuple, list, set)):
        source_folders = (source_folders,)

    # Prepare output folder
    filepath = Path(filepath)
    if filepath.exists():
        raise FileExistsError(f"Code already exists at {filepath.absolute()}!")

    filepath.parent.mkdir(exist_ok=True, parents=True)

    # Create zip file
    with ZipFile(filepath, 'w') as zip_file:
        n = 0
        for source_folder in source_folders:
            source_folder = Path(source_folder)
            n += zip_file_folders(zip_file, source_folder, source_folder.name, suffixes=suffixes)

        # Add main file
        if add_main_file:
            n += 1
            if isinstance(add_main_file, (Path, str)):
                main_file = Path(add_main_file)
            else:
                main_file = get_main_script_path()
            main_file_content = (
                f"# Originally copied on {datetime.datetime.now():%Y-%m-%d %H:%M:%S} from {main_file.absolute()}\n\n"
                f"{main_file.read_text(encoding='utf-8')}"
            )

            zip_file.writestr('__main__.py', main_file_content)

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
