from github import Github
import base64

def upload_excel_to_github(token, repo_name, file_path, commit_message="Update User Data"):
    """
    Upload or update an Excel file to GitHub repository.

    Args:
        token (str): GitHub personal access token.
        repo_name (str): Format "username/repo".
        file_path (str): Local path to the Excel file.
        commit_message (str): Commit message.
    """
    g = Github(token)
    repo = g.get_repo(repo_name)
    file_name = file_path.split("/")[-1]

    with open(file_path, "rb") as f:
        content = f.read()
        content_b64 = base64.b64encode(content).decode("utf-8")

    try:
        contents = repo.get_contents(file_name)
        repo.update_file(contents.path, commit_message, content_b64, contents.sha)
        print(f"✅ Updated {file_name} in {repo_name}")
    except:
        repo.create_file(file_name, commit_message, content_b64)
        print(f"✅ Created {file_name} in {repo_name}")
