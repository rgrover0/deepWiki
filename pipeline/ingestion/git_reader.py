import os
import git
from pathlib import Path


def clone_repo(repo_url: str, target_dir: str) -> str:
    """Clone repo if not already cloned. Returns local path."""
    if os.path.exists(target_dir):
        print(f"✅ Repo already exists at {target_dir}")
        return target_dir

    print(f"⬇️  Cloning {repo_url}...")
    git.Repo.clone_from(repo_url, target_dir, depth=1)
    print(f"✅ Cloned to {target_dir}")
    return target_dir


def get_java_files(repo_path: str) -> list[str]:
    """Recursively find all Java files in repo."""
    java_files = []
    for path in Path(repo_path).rglob("*.java"):
        # Skip test files for now
        if "test" not in str(path).lower():
            java_files.append(str(path))
    return sorted(java_files)


def get_repo_metadata(repo_path: str) -> dict:
    """Get basic repo info."""
    repo = git.Repo(repo_path)
    return {
        "path": repo_path,
        "branch": repo.active_branch.name,
        "last_commit": repo.head.commit.hexsha[:8],
        "last_commit_message": repo.head.commit.message.strip()
    }