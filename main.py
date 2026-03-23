#!/usr/bin/env python3
import csv
import os
from datetime import datetime, timezone

import requests

EQUAL_SIGNS_COUNT = 90


def print_help():
    """Displays a quick guide on how to get the GitHub Token and setup the CSV."""
    print("\n" + "=" * EQUAL_SIGNS_COUNT)
    print("📖 HOW TO GET YOUR GITHUB TOKEN")
    print("=" * EQUAL_SIGNS_COUNT)
    print("1. Go to GitHub.com -> Settings -> Developer Settings.")
    print("2. Personal Access Tokens -> Fine-grained tokens -> Generate new.")
    print("3. Name: 'Competition Monitor' | Expiration: 7-30 days.")
    print("4. Repository access: 'Public Repositories (read-only)'.")
    print("6. COPY the token (it starts with 'github_pat_...').")
    print("=" * EQUAL_SIGNS_COUNT + "\n")


def get_repos_from_csv() -> list[dict[str, str]]:
    """Reads repository names from a CSV file."""
    while True:

        file_path = input("\nEnter the path to your CSV file (e.g., repos.csv): ").strip()
        if not os.path.exists(file_path):
            print(f"⚠️  Warning: '{file_path}' not found!")
            continue
        if os.path.isdir(file_path):
            print(f"⚠️  Warning: Entered path is a directory: {file_path}. Try again!")
            continue
        if file_path == 'q':
            exit(0)
        break

    participants = []
    repo_keys = ['repository', 'repo']
    team_keys = ['team', 'teamname', 'team name', 'group']

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_values = list(row.values())
            if not row_values:
                continue

            # 1. Logic for REPO: Look for header, else use first column
            repo_raw = next((row[k] for k in row if k and k.lower() in repo_keys), row_values[0])

            # 2. Logic for TEAM: Look for header, else use second column if it exists
            # If only one column exists, use "Team [RepoName]" as a fallback
            team_name = next((row[k] for k in row if k and k.lower() in team_keys), None)

            if not team_name:
                if len(row_values) > 1:
                    team_name = row_values[1]
                else:
                    # Fallback for 1-column CSV: use a portion of the repo name
                    team_name = f"Team ({repo_raw.split('/')[-1]})"

            if repo_raw:
                repo_clean = repo_raw.replace("https://github.com/", "").strip("/")
                participants.append({
                    "repo": repo_clean,
                    "team": team_name.strip()
                })

    print(f"📂 Loaded {len(participants)} teams from {file_path}.")
    return participants


def validate_github_token(token: str) -> bool:
    """Checks if the token is valid by making a dummy request to GitHub API."""
    print("⏳ Validating token...")
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token valid! Logged in as: {user_data.get('login')}")
            return True
        elif response.status_code == 401:
            print("❌ Invalid token! GitHub returned 401 Unauthorized.")
            return False
        else:
            print(f"⚠️  Unexpected response from GitHub: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"📡 Connection error during validation: {e}")
        return False


def get_github_token() -> str:
    """Retrieves and validates the token from user input."""
    while True:
        token = input("Please paste your GitHub Token: ").strip()

        if not token:
            print("❌ No token provided.")
            user_choice = input("Press 'q' to quit or Enter to try again: ").strip().lower()
            if user_choice == 'q':
                exit(0)
            continue

        if validate_github_token(token):
            return token
        else:
            print("Please try again or check your token permissions.")


def convert_time_to_utc(local_time: str) -> str | None:
    try:
        # 1. Parse the string into a "naive" datetime object
        naive_dt = datetime.strptime(local_time, "%Y-%m-%d %H:%M")

        # 2. Tell Python this is LOCAL time, then convert to UTC
        # .astimezone() with no arguments defaults to your local system time
        local_dt = naive_dt.astimezone()
        utc_dt = local_dt.astimezone(timezone.utc)

        # 3. Format for GitHub (ISO 8601)
        since_date = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"✅ Local: {local_dt.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"🌐 GitHub (UTC): {since_date}\n")
        return since_date

    except ValueError:
        print("❌ Invalid format! Please use YYYY-MM-DD HH:MM (e.g., 2024-01-01 15:30)")
        return None


def print_initial_setup():
    print('\n')
    print("=" * EQUAL_SIGNS_COUNT)
    print("Welcome the The Hub Repo Checker!")
    print("This applet scans github repos for late commits")
    print("=" * EQUAL_SIGNS_COUNT)
    print_help()


def print_final_summary(good_repos_count: int, violations: list[dict[str, str]], total_length: int) -> None:
    # Final Competition Summary
    print("\n" + "=" * EQUAL_SIGNS_COUNT)
    print(f"🏁 SCAN COMPLETE")
    print(f"Total Teams Checked: {good_repos_count + len(violations)}")
    print(f"Total Violations:    {len(violations)}")

    if violations:
        print("\n🚨 DISQUALIFIED LIST:")
        for v in violations:
            print(f"  - TEAM: {v['team']} | REPO: {v['repo']} ({v['count']} late pushes)")
    elif good_repos_count == total_length and total_length > 0:
        print("\n🏆 All teams followed the deadline! No violations found.")
    print("=" * EQUAL_SIGNS_COUNT)


def check_repos(deadline_utc: str, participants: list, gh_token: str):
    headers = {"Authorization": f"token {gh_token}"}
    violations = []

    print(f"\n{'TEAM NAME':<25} | {'REPO':<35} | {'RESULT'}")
    print("-" * EQUAL_SIGNS_COUNT)

    good_repos_count = 0
    for p in participants:
        repo = p['repo']
        team = p['team']
        url = f"https://api.github.com/repos/{repo}/commits?since={deadline_utc}"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commits = response.json()
                if len(commits) > 0:
                    print(f"{team[:25]:<25} | {repo[:35]:<35} | 🚩 VIOLATION: {len(commits)} commits")
                    violations.append({
                        "team": team,
                        "repo": repo,
                        "count": len(commits)
                    })
                else:
                    good_repos_count += 1
                    print(f"{team[:25]:<25} | {repo[:35]:<35} | ✅ CLEAN")
            else:
                print(f"{team[:25]:<25} | {repo[:35]:<35} | ⚠️ Error {response.status_code}")
        except Exception:
            print(f"{team[:25]:<25} | {repo[:35]:<35} | 📡 Connection Error")
    print_final_summary(good_repos_count, violations, len(participants))


def main_loop(gh_token: str, participants: list[dict[str, str]]) -> None:
    while True:
        print("Date and Time Format: YYYY-MM-DD HH:MM")
        print("Example: 2024-01-01 15:30")
        local_input = input("\nEnter your local date and time, 'r' to change repos source or 'q' to quit:").strip()

        if local_input.lower() == 'q':
            print("👋 Goodbye!")
            break
        if local_input.lower() == 'r':
            participants = get_repos_from_csv()
            continue
        deadline_utc = convert_time_to_utc(local_input)
        if deadline_utc is None:
            continue

        check_repos(deadline_utc, participants, gh_token)


print_initial_setup()
gh_token = get_github_token()
repos = get_repos_from_csv()
main_loop(gh_token, repos)
