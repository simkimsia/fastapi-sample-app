from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type


@object_type
class Agent:
    @function
    def heal(
        self,
        source: Annotated[dagger.Directory, DefaultPath("/")]
    ) -> dagger.Container:
        before = dag.workspace(source=source)

        prompt = f"""
        You are an expert in the Python FastAPI framework, with a deep understanding of its lifecycle and ecosystem. You are also an expert in Pydantic, SQLAlchemy and the Repository pattern. You are tasked with resolving failing unit tests in a FastAPI application which uses Pydantic and SQLAlchemy. You hae access to a workspace wth write_file, read_file, ls, diff, and test tools.

        Follow these instructions:

        1. Focus only on Python files within the /app directory.
        2. Begin by reading relevant files from the workspace.
        3. Run thetest tool to identify the failing tests. Do not use pytest or any other tool.
        4. Read the error messages and identify the root cause of the failures.
        5. Update the relevant files and/or tests to fix the failing tests.
        6. Run the tests again with the test tool to confirm all tests pass.
        7. If the tests fail, return to step 4 and try again.

        You must follow these rules:

        Use the write_file, read_file, ls, diff, and test tools only.
        Do not interact directly with the database; use the test tool only.
        Make the smallest change required to fix the failing tests.
        Write changes directly to the original files.
        Use diff to compare your changes with the original files.
        Confirm the tests pass by running the test tool (not pytest or any other tool).
        Provide a thorough explanation of your reasoning and process.
        """
        after = (
            dag.llm()
            .with_workspace(before)
            .with_prompt(prompt)
            .workspace()
        )

        return after.container()
