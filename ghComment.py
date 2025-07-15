import argparse
import requests
import json
import os

def get_github_comments(org, repo, pr_number, pat):
    """
    Fetches comments for a given GitHub Pull Request.
    Uses 'application/vnd.github+json' which returns the raw markdown body.

    Args:
        org (str): The GitHub organization name.
        repo (str): The GitHub repository name.
        pr_number (int): The Pull Request number.
        pat (str): Your GitHub Personal Access Token.

    Returns:
        list: A list of comment dictionaries if successful, None otherwise.
    """
    url = f"https://api.github.com/repos/{org}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json", # This media type returns the raw markdown body
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {pat}",
    }

    print(f"Attempting to GET comments from: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred during GET request: {e}")
        return None

def update_github_comment(org, repo, comment_id, pat, body_content):
    """
    Updates an existing GitHub comment. The body_content should be in Markdown format.

    Args:
        org (str): The GitHub organization name.
        repo (str): The GitHub repository name.
        comment_id (int): The ID of the comment to update.
        pat (str): Your GitHub Personal Access Token.
        body_content (str): The new content for the comment body (in Markdown).

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    url = f"https://api.github.com/repos/{org}/{repo}/issues/comments/{comment_id}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json" # Essential for sending JSON payload
    }
    payload = {"body": body_content}

    print(f"Attempting to PATCH comment ID {comment_id} at: {url}")
    print("******************************")
    print(json.dumps(payload))
    print("******************************")
    try:
        #response = requests.patch(url, headers=headers, data=json.dumps(payload))
        response = requests.patch(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"Successfully updated comment ID {comment_id}.")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred during PATCH: {e.response.status_code} - {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred during PATCH request: {e}")
        return False

def create_github_comment(org, repo, pr_number, pat, body_content):
    """
    Creates a new comment on a GitHub Pull Request. The body_content should be in Markdown format.

    Args:
        org (str): The GitHub organization name.
        repo (str): The GitHub repository name.
        pr_number (int): The Pull Request number.
        pat (str): Your GitHub Personal Access Token.
        body_content (str): The content for the new comment body (in Markdown).

    Returns:
        bool: True if the creation was successful, False otherwise.
    """
    url = f"https://api.github.com/repos/{org}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json" # Essential for sending JSON payload
    }
    payload = {"body": body_content}

    print(f"Attempting to POST new comment to PR #{pr_number} at: {url}")
    print("##############################")
    print(json.dumps(payload))
    print("##############################")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"Successfully created a new comment on PR #{pr_number}.")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred during POST: {e.response.status_code} - {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred during POST request: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Manage GitHub PR comments based on specific content.")
    parser.add_argument("--github_org", required=True, help="GitHub organization name.")
    parser.add_argument("--github_repo", required=True, help="GitHub repository name.")
    parser.add_argument("--github_pat", required=True, help="GitHub Personal Access Token.")
    parser.add_argument("--github_pr_number", type=int, required=True, help="GitHub Pull Request number.")
    parser.add_argument("--filename", required=True, help="Path to the file containing the comment body content (Markdown format).")

    args = parser.parse_args()

    # 1. Read the content of the filename
    if not os.path.exists(args.filename):
        print(f"Error: File '{args.filename}' not found.")
        return

    try:
        with open(args.filename, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error reading file '{args.filename}': {e}")
        return

    # 2. Get existing comments
    comments = get_github_comments(args.github_org, args.github_repo, args.github_pr_number, args.github_pat)

    if comments is None:
        print("Failed to retrieve comments. Exiting.")
        return

    found_comment_id = None
    search_string = "Checking analysis of application"
    #search_string = "Elango"

    # 3. Look for "Checking analysis of application" in element "body"
    for comment in comments:
        # The 'body' element contains the raw markdown, as per 'application/vnd.github+json'
        if search_string in comment.get("body", ""):
            found_comment_id = comment.get("id")
            print(f"Found existing comment with '{search_string}'. Comment ID: {found_comment_id}")
            break

    # 4. & 5. Conditional API call (PATCH or POST)
    if found_comment_id:
        # Update existing comment
        success = update_github_comment(args.github_org, args.github_repo, found_comment_id, args.github_pat, file_content)
        if success:
            print("Comment updated successfully.")
        else:
            print("Failed to update comment.")
    else:
        # Create new comment
        success = create_github_comment(args.github_org, args.github_repo, args.github_pr_number, args.github_pat, file_content)
        if success:
            print("New comment created successfully.")
        else:
            print("Failed to create new comment.")

if __name__ == "__main__":
    main()
