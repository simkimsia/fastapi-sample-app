from typing import Dict, List

from dagger import Secret
from github import Github


class GitHubClient:
    """Client for interacting with GitHub API for PR reviews and suggestions"""

    def __init__(self, token: Secret):
        """Initialize the GitHub client with an access token"""
        self.token = token
        self.github = Github(token.plaintext())

    async def get_pr_for_commit(self, repo: str, commit: str) -> int:
        """Get the pull request number associated with a commit"""
        repository = self.github.get_repo(repo)
        # Get all PRs that contain this commit
        pulls = repository.get_pulls(state="open")
        for pr in pulls:
            if pr.get_commits().reversed[0].sha == commit:
                return pr.number
        raise ValueError(f"No pull requests found for commit {commit}")

    async def create_review(
        self,
        repository: str,
        pull_number: int,
        commit_id: str,
        body: str,
        event: str,
        comments: List[Dict[str, any]],
    ) -> None:
        """Create a review with inline comments on a pull request

        Args:
            repository: Full repository name (e.g., "owner/repo")
            pull_number: Pull request number
            commit_id: SHA of the commit to review
            body: The review body text
            event: The review event (e.g., "COMMENT", "APPROVE", "REQUEST_CHANGES")
            comments: List of review comments with their positions
        """
        repo = self.github.get_repo(repository)
        pr = repo.get_pull(pull_number)

        # Create the review with all comments
        pr.create_review(body=body, event=event, commit_id=commit_id, comments=comments)
