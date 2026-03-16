import logging
import os

from github import ContentFile, Github, UnknownObjectException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepoAnalysisTools:
    """A collection of tools for scanning and analyzing the code within a repository."""

    def __init__(self):
        self.github_client = None
        self.repo_object = None

    def _get_repo_object(self, repo_url: str):
        """Helper method to get and cache the repository object."""
        github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_ACCESS_TOKEN environment variable not set.")

        # Initialize the github_client if it's not already set
        if not self.github_client:
            try:
                self.github_client = Github(github_token)
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                raise

        if self.repo_object and self.repo_object.clone_url.startswith(repo_url):
            return self.repo_object

        path_parts = repo_url.strip("/").split("/")
        if "github.com" in path_parts:
            start_index = path_parts.index("github.com") + 1
            if len(path_parts) > start_index + 1:
                owner = path_parts[start_index]
                repo_name_part = path_parts[start_index + 1]
                if repo_name_part.endswith(".git"):
                    repo_name_part = repo_name_part[:-4]
                repo_full_name = f"{owner}/{repo_name_part}"

                # This line will now succeed because self.github_client is an instance of Github
                self.repo_object = self.github_client.get_repo(repo_full_name)
                return self.repo_object
        raise ValueError("Invalid GitHub URL format.")

    def list_repository_files(self, repo_url: str) -> list[str]:
        """Scans a GitHub repository and returns a list of all file paths."""
        try:
            repo = self._get_repo_object(repo_url)
            logger.info(f"Scanning repository: {repo.full_name}")
            tree = repo.get_git_tree(repo.default_branch, recursive=True)
            file_paths = [
                element.path for element in tree.tree if element.type == "blob"
            ]
            logger.info(f"Found {len(file_paths)} files in {repo.full_name}.")
            return file_paths
        except Exception as e:
            logger.error(f"Error listing files for {repo_url}: {e}", exc_info=True)
            return []

    def get_file_content(self, repo_url: str, file_path: str) -> str:
        """Retrieves the text content of a single file from the repository."""
        try:
            repo = self._get_repo_object(repo_url)
            logger.info(f"Fetching content for: {file_path} in {repo.full_name}")
            content_file = repo.get_contents(file_path, ref=repo.default_branch)

            # If the content is a list (directory listing), return an error message
            if isinstance(content_file, list):
                return f"Error: '{file_path}' is a directory, not a file."

            # Decode the file content from base64
            decoded_content = content_file.decoded_content.decode("utf-8")
            return decoded_content

        except UnknownObjectException:
            logger.error(f"File not found: {file_path} in {repo_url}")
            return f"Error: File not found at path '{file_path}'."
        except Exception as e:
            logger.error(f"Error fetching content for {file_path}: {e}")
            return f"Error: Could not retrieve content for '{file_path}'."