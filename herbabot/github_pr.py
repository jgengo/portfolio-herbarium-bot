import logging
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

import requests

from herbabot.config import GITHUB_REPO_NAME, GITHUB_REPO_OWNER, GITHUB_REPO_URL

logger = logging.getLogger(__name__)


def create_pr_from_plant_entries(
    tmp_dir: Path, repo_url: str, github_token: str, repo_owner: str, repo_name: str
) -> Optional[str]:
    if not tmp_dir.exists():
        logger.warning(f"Tmp directory {tmp_dir} does not exist")
        return None

    # Find all markdown files in tmp directory
    md_files = list(tmp_dir.glob("*.md"))
    if not md_files:
        logger.warning("No markdown files found in tmp directory")
        return None

    with tempfile.TemporaryDirectory() as temp_clone_dir:
        try:
            # Clone the repo
            clone_path = Path(temp_clone_dir)
            clone_repo(clone_path, repo_url, github_token)

            # Create branch
            branch_name = f"bot_{uuid.uuid4().hex[:8]}"
            create_branch(clone_path, branch_name)

            # Copy files
            files_copied = copy_plant_files(tmp_dir, clone_path)
            if not files_copied:
                logger.warning("No files were copied")
                return None

            # Commit and push
            commit_message = (
                f"Add plant entries: {', '.join([f.name for f in md_files])}"
            )
            commit_and_push(clone_path, commit_message, branch_name)

            # Create pull request
            pr_url = create_pull_request(
                branch_name, commit_message, github_token, repo_owner, repo_name
            )

            logger.info(f"Pull request created successfully: {pr_url}")
            return pr_url

        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return None


def clone_repo(clone_path: Path, repo_url: str, github_token: str) -> None:
    """Clone the repository to the specified path."""
    logger.info(f"Cloning repository to {clone_path}")

    # Use HTTPS with token for authentication
    if repo_url.startswith("git@github.com:"):
        # Convert SSH URL to HTTPS with token
        repo_path = repo_url.replace("git@github.com:", "")
        auth_url = f"https://{github_token}@github.com/{repo_path}"
    else:
        # Already HTTPS URL, just add token
        auth_url = repo_url.replace("https://", f"https://{github_token}@")

    result = subprocess.run(
        ["git", "clone", auth_url, str(clone_path)],
        capture_output=True,
        text=True,
        cwd=clone_path.parent,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repository: {result.stderr}")

    logger.info("Repository cloned successfully")


def create_branch(repo_path: Path, branch_name: str) -> None:
    """Create a new branch in the repository."""
    logger.info(f"Creating branch: {branch_name}")

    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create branch: {result.stderr}")

    logger.info(f"Branch {branch_name} created successfully")


def copy_plant_files(tmp_dir: Path, repo_path: Path) -> bool:
    """Copy plant entry files from tmp to the appropriate directories in the repo."""
    files_copied = False

    # Create target directories if they don't exist
    plants_data_dir = repo_path / "src" / "data" / "plants"
    plants_public_dir = repo_path / "public" / "plants"

    plants_data_dir.mkdir(parents=True, exist_ok=True)
    plants_public_dir.mkdir(parents=True, exist_ok=True)

    # Copy markdown files
    for md_file in tmp_dir.glob("*.md"):
        dest_path = plants_data_dir / md_file.name
        shutil.copy2(md_file, dest_path)
        logger.info(f"Copied markdown file: {md_file.name}")
        files_copied = True

    # Copy image files
    for img_file in tmp_dir.glob("*.jpg"):
        dest_path = plants_public_dir / img_file.name
        shutil.copy2(img_file, dest_path)
        logger.info(f"Copied image file: {img_file.name}")
        files_copied = True

    return files_copied


def commit_and_push(repo_path: Path, commit_message: str, branch_name: str) -> None:
    """Commit changes and push to the remote repository."""
    logger.info("Committing and pushing changes")

    # Add all files
    result = subprocess.run(
        ["git", "add", "."], capture_output=True, text=True, cwd=repo_path
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to add files: {result.stderr}")

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to commit: {result.stderr}")

    # Push
    result = subprocess.run(
        ["git", "push", "origin", branch_name],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to push: {result.stderr}")

    logger.info("Changes committed and pushed successfully")


def create_pull_request(
    branch_name: str, title: str, github_token: str, repo_owner: str, repo_name: str
) -> str:
    """Create a pull request using GitHub API."""
    logger.info("Creating pull request via GitHub API")

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "title": title,
        "body": f"Automated PR from Herbabot\n\nBranch: {branch_name}\n\nThis PR was automatically generated by the Herbabot plant identification system.",
        "head": branch_name,
        "base": "main",  # Assuming main is the default branch
    }

    api_base = "https://api.github.com"
    url = f"{api_base}/repos/{repo_owner}/{repo_name}/pulls"

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 201:
        raise RuntimeError(
            f"Failed to create PR: {response.status_code} - {response.text}"
        )

    pr_data = response.json()
    return pr_data["html_url"]


def create_plant_pr(tmp_dir: Path, github_token: str) -> Optional[str]:
    return create_pr_from_plant_entries(
        tmp_dir, GITHUB_REPO_URL, github_token, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
    )
