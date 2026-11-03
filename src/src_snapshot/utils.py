import datetime
import getpass
import inspect
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional

import psutil


def dependencies():
    # full freeze can be large; keep it optional or filter if needed
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        return out.decode().splitlines()
    except Exception:
        return []


def environment_info():
    info = {
        "python": sys.version.replace("\n", " "),
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hardware": {
            "GPU": gpu_info(),
            "RAM": ram_info()
        }
    }
    return info


def git_info():
    def _run(cmd):
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return "unknown"

    return {
        "repo_url": _run(["git", "config", "--get", "remote.origin.url"]),
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "short_commit": _run(["git", "rev-parse", "--short", "HEAD"]),
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(_run(["git", "status", "--porcelain"])),
        "tag": _run(["git", "describe", "--tags", "--abbrev=0"]),
    }

def git_diff():
    try:
        return subprocess.check_output(["git", "diff"], stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        # git missing or not inside a repository
        return ""

def create_metadata():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    main_file = get_main_script_path()
    meta = {
        "timestamp_utc": now,
        "provenance": git_info(),
        "user": user_info(),
        "execution": {
            "entrypoint": f"{main_file.absolute() if main_file else 'unknown'}",
            "sys.argv": " ".join(sys.orig_argv),
            "cwd": str(Path.cwd()),
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
        },
        "environment": environment_info(),
        "slurm": slurm_info(),
        "dependencies": dependencies(),
    }
    return meta

def zip_file_folders(
        zip_file,
        in_dir: Path,
        archive_path: str,
        *,
        suffixes: Optional[str | tuple[str]] = None
) -> int:
    if in_dir.is_dir():
        n = 0
        for file_folder in in_dir.iterdir():
            n += zip_file_folders(zip_file, file_folder, f"{archive_path}/{file_folder.name}", suffixes=suffixes)
        return n
    elif in_dir.is_file():
        if isinstance(suffixes, str) and not in_dir.suffix == suffixes:
            return 0

        if isinstance(suffixes, tuple | list) and in_dir.suffix not in suffixes:
            return 0

        # Add file to zip
        zip_file.write(in_dir, archive_path)
        return 1

    else:
        raise TypeError(f"What is {in_dir} if not file or folder?")


def get_main_script_path() -> Optional[Path]:
    """
    This function gets the current frame and then recursively goes back to the calling function until
        - no more calling function exists (-> reached most top level file)
        - the __name__ of the current file is "__main__"
    :return:
    """

    current_frame = inspect.currentframe()
    while current_frame is not None:
        # Check if the module is the main module
        if current_frame.f_globals.get("__name__") == "__main__":
            return Path(current_frame.f_globals.get("__file__"))
        current_frame = current_frame.f_back
    return None

def slurm_info():
    def env(key):
        return os.environ.get(key)

    info = {
        "job_id": env("SLURM_JOB_ID"),
        "job_name": env("SLURM_JOB_NAME"),
        "array_job_id": env("SLURM_ARRAY_JOB_ID"),
        "array_task_id": env("SLURM_ARRAY_TASK_ID"),
        "partition": env("SLURM_JOB_PARTITION"),
        "node_list": env("SLURM_NODELIST"),
        "num_nodes": env("SLURM_JOB_NUM_NODES"),
        "num_tasks": env("SLURM_NTASKS"),
        "cpus_per_task": env("SLURM_CPUS_PER_TASK"),
        "cpus_on_node": env("SLURM_CPUS_ON_NODE"),
        "gpus": env("SLURM_GPUS"),
        "gpus_per_node": env("SLURM_GPUS_ON_NODE"),
        "ntasks_per_node": env("SLURM_NTASKS_PER_NODE"),
        "local_id": env("SLURM_LOCALID"),
        "global_id": env("SLURM_PROCID"),
    }

    # remove keys that are not set
    info = {k: v for k, v in info.items() if v is not None}

    return info if info else None

def gpu_info():
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=index,name,memory.total",
            "--format=csv,noheader,nounits"
        ]).decode().strip().splitlines()
    except (OSError, subprocess.CalledProcessError):
        # nvidia-smi missing or failing (e.g. no driver) -> no GPU info
        return []

    gpus = []
    for line in out:
        try:
            idx, name, mem = [x.strip() for x in line.split(",")]
        except ValueError:
            continue
        gpus.append({
            "index": int(idx) if idx.isdigit() else idx,
            "name": name,
            "memory_mb": int(mem) if mem.isdigit() else None,
        })
    return gpus

def ram_info():
    vm = psutil.virtual_memory()
    return {
        "total_bytes": vm.total,
        "available_bytes": vm.available,
        "used_bytes": vm.used,
    }

def user_info():
    return {
        "username": getpass.getuser(),
        "uid": os.getuid() if hasattr(os, "getuid") else None,
    }