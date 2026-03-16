import os
from typing import List

class RepoAnalysisTools:
    """Tools for analyzing a repository's structure and file contents."""

    def list_repository_files(self, root_dir: str = ".") -> List[str]:
        """Lists all files in the repository starting from root_dir.
        
        Args:
            root_dir (str): The root directory to start the search from. Defaults to ".".
            
        Returns:
            List[str]: A list of relative file paths.
        """
        files_list = []
        print(f"DEBUG: list_repository_files called with root_dir: {root_dir}")
        for root, _, files in os.walk(root_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                files_list.append(rel_path)
        return files_list

    def get_file_content(self, file_path: str) -> str:
        """Reads and returns the content of a specific file.
        
        Args:
            file_path (str): The path to the file to read.
            
        Returns:
            str: The content of the file or an error message.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
