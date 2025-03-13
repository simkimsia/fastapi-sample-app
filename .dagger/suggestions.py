import re
from dataclasses import dataclass
from typing import List, Union

try:
    from git import Diff as GitDiff
    from git.diff import Hunk

    GIT_SUPPORT = True
except ImportError:
    GIT_SUPPORT = False


@dataclass
class CodeSuggestion:
    """Represents a code suggestion for a specific file and line"""

    file: str
    line: int
    suggestion: List[str]


def parse_diff(
    diff_input: Union[str, "GitDiff", List["GitDiff"]],
) -> List[CodeSuggestion]:
    """Parse a diff into code suggestions

    Args:
        diff_input: A raw diff text string (default and recommended),
                   or optionally a GitPython Diff object(s) if GitPython is installed
    """
    # Handle raw diff text (primary use case)
    if isinstance(diff_input, str):
        return _parse_raw_diff(diff_input)

    # Handle GitPython objects if available
    if GIT_SUPPORT:
        if isinstance(diff_input, list):
            return _parse_git_diffs(diff_input)
        elif isinstance(diff_input, GitDiff):
            return _parse_git_diffs([diff_input])

    raise ValueError(
        f"Unsupported diff input type: {type(diff_input)}. "
        "Use raw diff text string or install GitPython for Git object support."
    )


def parse_raw_diff(diff_text: str) -> List[CodeSuggestion]:
    """Parse a unified diff format text into code suggestions (alias for parse_diff)"""
    return _parse_raw_diff(diff_text)


def _parse_raw_diff(diff_text: str) -> List[CodeSuggestion]:
    """Parse a unified diff format text into code suggestions"""
    suggestions = []
    current_file = ""
    current_line = 0
    new_code = []
    removal_reached = False

    # Regular expressions for file detection and line number parsing
    file_regex = re.compile(r"^\+\+\+ b/(.+)")
    line_regex = re.compile(r"^@@ .* \+(\d+),?")

    for line in diff_text.splitlines():
        # Detect file name
        if match := file_regex.match(line):
            current_file = match.group(1)
            continue

        # Detect modified line number in the new file
        if match := line_regex.match(line):
            current_line = (
                int(match.group(1)) - 1
            )  # Convert to 0-based index for tracking
            new_code = []  # Reset new code buffer
            removal_reached = False
            continue

        # Extract new code (ignoring metadata lines)
        if line.startswith("+") and not line.startswith("+++"):
            new_code.append(line[1:])  # Remove '+'
            continue

        if not removal_reached:
            current_line += 1  # Track line modifications

        # If a removed line ('-') appears after '+' lines, store the suggestion
        if line.startswith("-") and not line.startswith("---"):
            if new_code and current_file:
                suggestions.append(
                    CodeSuggestion(
                        file=current_file, line=current_line, suggestion=new_code
                    )
                )
                new_code = []  # Reset new code buffer
            removal_reached = True

    # If there's a pending multi-line suggestion, add it
    if new_code and current_file:
        suggestions.append(
            CodeSuggestion(file=current_file, line=current_line, suggestion=new_code)
        )

    return suggestions


if GIT_SUPPORT:

    def _parse_git_diffs(diffs: List[GitDiff]) -> List[CodeSuggestion]:
        """Parse GitPython diff objects into code suggestions"""
        suggestions = []

        for diff in diffs:
            if diff.is_binary:
                continue

            file_path = diff.b_path or diff.a_path
            if not file_path:
                continue

            current_line = 0
            for hunk in diff:
                current_line = _parse_hunk(hunk, file_path, current_line, suggestions)

        return suggestions

    def _parse_hunk(
        hunk: Hunk, file_path: str, start_line: int, suggestions: List[CodeSuggestion]
    ) -> int:
        """Parse a single hunk from a GitPython diff"""
        current_line = start_line
        new_code = []

        for line in hunk.lines:
            if line.line_origin == " ":
                if new_code:  # Store any pending suggestion before context line
                    suggestions.append(
                        CodeSuggestion(
                            file=file_path, line=current_line, suggestion=new_code
                        )
                    )
                    new_code = []
                current_line += 1
            elif line.line_origin == "+":
                new_code.append(line.content)
                current_line += 1
            elif line.line_origin == "-":
                if new_code:  # Store suggestion when we hit a deletion
                    suggestions.append(
                        CodeSuggestion(
                            file=file_path, line=current_line, suggestion=new_code
                        )
                    )
                    new_code = []

        # Store any remaining suggestion
        if new_code:
            suggestions.append(
                CodeSuggestion(file=file_path, line=current_line, suggestion=new_code)
            )

        return current_line
