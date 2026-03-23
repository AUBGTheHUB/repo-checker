# 🏆 Competition Deadline Monitor

--- 
A command-line tool designed for hackathons and coding competitions to verify that no participants pushed code after a
specific deadline.

The Rule: In this app, finding commits is a bad thing. Any activity found after your specified local deadline is flagged
as a violation.

### ✨ Features

Local Time Input: Enter your deadline in your own timezone; the app handles the UTC conversion for the GitHub API.

CSV Bulk Scanning: Check dozens of repositories at once via a simple CSV file.

URL Auto-Cleanup: Automatically handles full URLs (https://github.com/...) or shorthand (owner/repo) from the CSV.

### 🚀 Setup Instructions

1. Generate a GitHub Token

   You need a Fine-grained Personal Access Token to bypass GitHub's rate limits:

    - Go to Settings > Developer Settings > Personal access tokens > Fine-grained tokens.

    - Click Generate new token.

    - Repository access: Select "Public Repositories (read-only)".

    - Copy the token (starts with github_pat_).


2. Prepare the Repository List (repos.csv)
   Create a CSV file. The app will look at the first column for the repository names.

Format: owner/repository

Example:

```
repository
octocat/Hello-World
google/googletest
https://github.com/python/cpython
```

(Note: Full URLs are automatically cleaned by the app)

### 🛠️ How to Run

For Ubuntu 24.04 & macOS (Python Script)

1. Clone the repo
2. Install Dependencies:

```Bash
pip3 install requests
```

3. Run the App:

```Bash
python3 main.py
```