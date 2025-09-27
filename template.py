import os
from pathlib import Path

# --- Configuration ---
PROJECT_NAME = "crewai_websocket_project"

# --- List of all files and directories to be created ---
# For subdirectories, we list the files within them.
# The script will create the necessary parent directories automatically.
files_and_dirs_to_create = [
    ".gitignore",
    "README.md",
    "requirements.txt",
    ".env.example",  # An example file for environment variables
    "config.py",
    "websocket_server.py",
    "test_client.py",
    "crew/__init__.py", # The __init__.py makes 'crew' a Python package
    "crew/agents.py",
    "crew/tasks.py",
    "crew/main_crew.py"
]

def create_project_structure():
    """
    Creates the project directory and all specified empty files.
    """
    project_path = Path(PROJECT_NAME)

    # First, create the main project directory
    if project_path.exists():
        print(f"Error: Directory '{PROJECT_NAME}' already exists. Aborting.")
        return
    
    print(f"Creating project directory: {project_path}")
    project_path.mkdir()

    # Create all the specified files
    for file_path_str in files_and_dirs_to_create:
        # Construct the full path for the file
        full_path = project_path / file_path_str

        # Create parent directories if they don't exist (e.g., for the 'crew' folder)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the empty file
        print(f"  - Creating empty file: {full_path}")
        full_path.touch()

    print("\n✅ Basic project structure created successfully!")
    print(f"\nNext step: Navigate into your new project by running:")
    print(f"cd {PROJECT_NAME}")

if __name__ == "__main__":
    create_project_structure()