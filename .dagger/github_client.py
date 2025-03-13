from typing import List, Optional, Union

try:
    from git import Diff as GitDiff

    GIT_SUPPORT = True
except ImportError:
    GIT_SUPPORT = False

from github import Github, PullRequest
from workspace.src.workspace.suggestions import parse_diff


class GithubClient:
    """Client for interacting with GitHub API for PR reviews and suggestions"""

    def __init__(self, token: str):
        """Initialize the GitHub client with an access token"""
        self.github = Github(token)
        self.token = token

    def get_pr_for_commit(
        self, repo_name: str, commit_sha: str
    ) -> Optional[PullRequest]:
        """Get the pull request associated with a commit"""
        repo = self.github.get_repo(repo_name)
        # Get all PRs that contain this commit
        prs = repo.get_pulls(state="open")
        for pr in prs:
            if pr.get_commits().reversed[0].sha == commit_sha:
                return pr
        return None

    def post_code_suggestions(
        self,
        repo_name: str,
        pr_number: int,
        commit_sha: str,
        diff: Union[str, "GitDiff", List["GitDiff"]],
    ) -> None:
        """Post code suggestions as review comments on a PR

        Args:
            repo_name: Full repository name (e.g., "owner/repo")
            pr_number: Pull request number
            commit_sha: SHA of the commit to comment on
            diff: A raw diff text string (recommended) or optionally GitPython Diff object(s)
        """
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Parse the diff into suggestions
        suggestions = parse_diff(diff)

        # Create a review with suggestions
        review_body = "Code suggestions from automated review"
        review_comments = []

        for suggestion in suggestions:
            comment = self._format_suggestion(
                suggestion.file, suggestion.line, suggestion.suggestion
            )
            review_comments.append(comment)

        # Create the review with all comments
        if review_comments:
            pr.create_review(
                body=review_body,
                event="COMMENT",
                commit_id=commit_sha,
                comments=review_comments,
            )

    def _format_suggestion(
        self, file_path: str, line_number: int, suggestion_lines: list[str]
    ) -> dict:
        """Format a code suggestion for GitHub's API"""
        suggestion_text = "\n".join(suggestion_lines)
        return {
            "path": file_path,
            "position": line_number,
            "body": f"```suggestion\n{suggestion_text}\n```",
            "line": line_number,
            "side": "RIGHT",
        }
