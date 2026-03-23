#!/usr/bin/env python3
import csv
import re
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


def get_google_sheets_url() -> str:
    """Prompts the user for a Google Sheets URL and validates its format."""
    # Pattern to match the unique ID in a Google Sheets URL
    gsheet_pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)"

    while True:
        print("\n📋 GOOGLE SHEETS SETUP")
        print("1. Ensure your Sheet is shared as 'Anyone with the link can view'.")
        print("2. Paste the browser URL below.")

        url = input("Enter Google Sheet URL (or 'q' to quit): ").strip()

        if url.lower() == 'q':
            exit(0)

        # Validate that it is actually a Google Sheets URL
        match = re.search(gsheet_pattern, url)
        if match:
            # We extract the base part of the URL to ensure it's clean
            sheet_id = match.group(1)
            clean_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            print(f"✅ URL recognized! Sheet ID: {sheet_id}")
            return clean_url
        else:
            print("❌ Invalid URL. Please provide a standard Google Sheets link.")
            print("Example: https://docs.google.com/spreadsheets/d/abc123xyz/edit")


def get_repos_from_google_sheets(sheet_url: str) -> list[dict]:
    """Downloads a public Google Sheet as a CSV and parses it."""
    try:
        # Convert the standard sharing URL to a CSV export URL
        # We use /export?format=csv to get the raw data
        export_url = sheet_url.rstrip('/') + "/export?format=csv"

        print("📡 Fetching team list from Google Sheets...")
        response = requests.get(export_url)
        response.raise_for_status()  # Check for download errors

        # Use the CSV module to parse the downloaded text
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)

        participants = []
        for row in reader:
            row_values = list(row.values())
            if not row_values: continue

            # Reuse your existing logic for Repo and Team columns
            repo_raw = next((row[k] for k in row if k and k.lower() in ['repository', 'repo']), row_values[0])
            team_name = next((row[k] for k in row if k and k.lower() in ['team', 'teamname']),
                             row_values[1] if len(row_values) > 1 else f"Team ({repo_raw})")

            if repo_raw:
                participants.append({
                    "repo": repo_raw.replace("https://github.com/", "").strip("/"),
                    "team": team_name.strip()
                })
        participants_count = len(participants)
        print(f"📂 Loaded {len(participants)} team{'s' if participants_count > 1 else ''} from Google Sheets.")
        return participants
    except Exception as e:
        print(f"❌ Failed to load Google Sheet: {e}")
        return []


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


def main_loop(gh_token: str, participants: list[dict[str, str]], google_sheets_url: str) -> None:
    # Calculate the inner width (total - 2 for the borders)
    inner_w = EQUAL_SIGNS_COUNT - 2

    while True:
        # Dashboard UI
        print(f"\n┌{'─' * inner_w}┐")
        print(f"│{'CONTROL PANEL':^{inner_w}}│")
        print(f"├{'─' * inner_w}┤")

        # Helper to print a consistent row
        def print_row(cmd, desc):
            # 20 chars for cmd, the rest for desc, minus padding
            # We use [:width] to truncate if it's too long
            left_side = f" {cmd:<20} -> {desc}"
            padding = " " * (inner_w - len(left_side))
            print(f"│{left_side}{padding}│")

        print_row("YYYY-MM-DD HH:MM", "Run deadline scan (Local Time)")
        print_row("[r]", "Refresh data from Google Sheet")
        print_row("[q]", "Exit application")

        print(f"└{'─' * inner_w}┘")
        local_input = input("👉 Enter command: ").strip()

        if local_input.lower() == 'q':
            print("👋 Goodbye!")
            break
        if local_input.lower() == 'r':
            get_repos_from_google_sheets(google_sheets_url)
            continue

        if local_input.lower() == 'c':
            google_sheets_url = get_google_sheets_url()
            participants = get_repos_from_google_sheets(google_sheets_url)

        # Check if the input looks like a date before trying to convert
        if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", local_input):
            deadline_utc = convert_time_to_utc(local_input)
            if deadline_utc:
                check_repos(deadline_utc, participants, gh_token)
        else:
            print("❌ Unknown command or invalid date format.")


print_initial_setup()
gh_token = get_github_token()

google_sheets_url = get_google_sheets_url()
repos = get_repos_from_google_sheets(google_sheets_url)
main_loop(gh_token, repos, google_sheets_url)
