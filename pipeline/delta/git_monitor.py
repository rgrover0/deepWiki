import os
import git
from pathlib import Path


def get_changed_java_files(repo_path: str) -> dict:
    """
    Detect changed Java files in the repo.
    Returns dict with modified, added, deleted file lists.
    """
    repo = git.Repo(repo_path)
    result = {
        "modified": [],
        "added":    [],
        "deleted":  []
    }

    # Uncommitted modifications (working tree vs index)
    for item in repo.index.diff(None):
        path = os.path.join(repo_path, item.a_path)
        if item.a_path.endswith(".java"):
            result["modified"].append(path)

    # Staged changes (index vs HEAD)
    if repo.head.is_valid():
        for item in repo.index.diff("HEAD"):
            path = os.path.join(repo_path, item.a_path)
            if item.a_path.endswith(".java"):
                if item.change_type == "A":
                    result["added"].append(path)
                elif item.change_type == "D":
                    result["deleted"].append(path)
                elif item.change_type == "M":
                    if path not in result["modified"]:
                        result["modified"].append(path)

    # Untracked new files
    for f in repo.untracked_files:
        if f.endswith(".java") and "test" not in f.lower():
            result["added"].append(os.path.join(repo_path, f))

    return result


def get_last_commit_changes(repo_path: str) -> dict:
    """Get files changed in the most recent commit."""
    repo = git.Repo(repo_path)
    result = {"modified": [], "added": [], "deleted": []}

    if not repo.head.is_valid():
        return result

    commit = repo.head.commit
    if not commit.parents:
        return result

    diffs = commit.diff(commit.parents[0])
    for diff in diffs:
        if not diff.a_path.endswith(".java"):
            continue
        path = os.path.join(repo_path, diff.a_path)
        if diff.change_type == "A":
            result["added"].append(path)
        elif diff.change_type == "D":
            result["deleted"].append(path)
        else:
            result["modified"].append(path)

    return result


def extract_class_names_from_paths(file_paths: list[str]) -> list[str]:
    """Extract likely class names from file paths."""
    return [
        Path(f).stem
        for f in file_paths
        if Path(f).suffix == ".java"
    ]