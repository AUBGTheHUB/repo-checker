#!/usr/bin/env python3
import csv
import os
from datetime import datetime, timezone

import requests

EQUAL_SIGNS_COUNT = 70


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
    # print("\nCSV SETUP:")
    # print("- Create a file named 'repos.csv'.")
    # print("- First column should be the repo paths (e.g., 'owner/repo').")
    print("=" * EQUAL_SIGNS_COUNT + "\n")


def get_repos_from_csv() -> list[str]:
    """Reads repository names from a CSV file."""
    file_path = input("\nEnter the path to your CSV file (e.g., repos.csv): ").strip()
    if not os.path.exists(file_path):
        print(f"⚠️  Warning: '{file_path}' not found!")
        return []

    repo_list = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        # DictReader handles headers automatically
        reader = csv.DictReader(f)
        for row in reader:
            # Assumes column is named 'repository' or uses the first column
            repo = row.get('repository') or list(row.values())[0]
            if repo:
                clean = repo.replace("https://github.com/", "").strip("/")
                repo_list.append(clean)

    print(f"📂 Loaded {len(repo_list)} repositories from {file_path}.")
    return repo_list


def get_github_token() -> str:
    """Retrieves the token from user input."""
    # getpass makes it so the characters don't appear on screen while pasting
    token = input("Please paste your GitHub Token: ").strip()

    if not token:
        print("❌ No token provided. Exiting.")
        exit(1)
    return token


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


def main_loop(gh_token: str, repos: list[str]) -> None:
    headers = {"Authorization": f"token {gh_token}"}

    while True:
        print("\nEnter your local date and time or q to quit.")
        print("Format: YYYY-MM-DD HH:MM")
        print("Example: 2024-01-01 15:30")

        local_input = input("\nDeadline (or 'q'): ").strip()

        if local_input.lower() == 'q':
            print("👋 Goodbye!")
            break
        deadline_utc = convert_time_to_utc(local_input)
        if deadline_utc is None:
            continue

        violations = []
        print(f"\n{'COMPETITOR REPO':<40} | {'RESULT'}")
        print("-" * EQUAL_SIGNS_COUNT)

        for repo in repos:
            url = f"https://api.github.com/repos/{repo}/commits?since={deadline_utc}"
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    commits = response.json()
                    if len(commits) > 0:
                        print(f"{repo:<40} | 🚩 VIOLATION: {len(commits)} late commits!")
                        violations.append((repo, len(commits)))
                    else:
                        print(f"{repo:<40} | ✅ CLEAN (No late commits)")
                else:
                    print(f"{repo:<40} | ⚠️ Error {response.status_code}")
            except Exception:
                print(f"{repo:<40} | 📡 Connection Error")

        # Final Competition Summary
        print("\n" + "=" * EQUAL_SIGNS_COUNT)
        print(f"🏁 SCAN COMPLETE")
        print(f"Total Repos Checked: {len(repos)}")
        print(f"Total Violations:    {len(violations)}")
        if violations:
            print("Violator Repos:")
            for v_repo, v_count in violations:
                print(f"  - {v_repo} ({v_count} late pushes)")
        else:
            print("All competitors followed the deadline! 🏆")
        print("=" * EQUAL_SIGNS_COUNT)


print_initial_setup()
gh_token = get_github_token()
repos = get_repos_from_csv()
main_loop(gh_token, repos)
