#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import os
import sys
import time
import requests
import logging
from typing import Dict, Any, List, Optional
from requests.exceptions import RequestException
import uuid

# === Settings ===
#TAIGA_URL = "http://taiga.site.az:9000"
TAIGA_URL = os.getenv("TAIGA_URL", "http://taiga.site.az:9000")
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admint")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin2025")
PROJECT_SLUG = os.getenv("PROJECT_SLUG", "synapps2025")
CSV_FILE = os.getenv("CSV_FILE", "Jira_fixed.csv")
USER_CSV_FILE = os.getenv("USER_CSV_FILE", "export-users.csv")
DEFAULT_US_STATUS_NAME = "New"
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "0.3"))
USER_CACHE: Dict[str, Optional[int]] = {}
STATUS_CACHE: Dict[str, int] = {}

# Logging configuration
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
skipped_logger = logging.getLogger("skipped")
skipped_handler = logging.FileHandler("skipped.log")
skipped_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
skipped_logger.addHandler(skipped_handler)
skipped_logger.setLevel(logging.INFO)

# Initial mapping (can be updated)
STATUS_MAP = {
    "Ready to go online": "Ready to go online",
    "Offline done": "Offline done",
    "To Do": "To Do",
    "In Progress": "In Progress",
    "Done": "Done",
}

# User names -> email mapping
USER_EMAIL_MAP = {
    "Aisha": "admin@site.az",
}

if not TAIGA_PASSWORD:
    print("❌ Set TAIGA_PASSWORD")
    sys.exit(1)

def _session(token: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s

# --- AUTH ---
def taiga_authenticate() -> str:
    url = f"{TAIGA_URL}/api/v1/auth"
    payload = {"type": "normal", "username": TAIGA_USERNAME, "password": TAIGA_PASSWORD}
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        token = r.json().get("auth_token")
        print("✅ Authentication successful")
        return token
    except RequestException as e:
        print(f"❌ Authentication error: {e}")
        sys.exit(1)

# --- PROJECT ---
def get_project_by_slug(token: str, slug: str) -> Dict[str, Any]:
    s = _session(token)
    try:
        r = s.get(f"{TAIGA_URL}/api/v1/projects/by_slug", params={"slug": slug}, timeout=30)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        print(f"❌ Project not found: {e}")
        sys.exit(1)

# --- USERS ---
def find_user_id(token: str, term: str) -> Optional[int]:
    if not term:
        return None
    key = term.strip().lower()
    if key in USER_CACHE:
        return USER_CACHE[key]
    s = _session(token)
    email = USER_EMAIL_MAP.get(term, None)
    try:
        r = s.get(f"{TAIGA_URL}/api/v1/users", params={"search": term}, timeout=30)
        users = r.json() if r.ok else []
        uid = users[0]["id"] if users else None
        USER_CACHE[key] = uid
        if uid is None and email:
            r = s.get(f"{TAIGA_URL}/api/v1/users", params={"search": email}, timeout=30)
            users = r.json() if r.ok else []
            uid = users[0]["id"] if users else None
            USER_CACHE[key] = uid
        if uid is None:
            print(f"⚠️ User not found: {term}")
        return uid
    except RequestException as e:
        print(f"⚠️ Error searching for user {term}: {e}")
        USER_CACHE[key] = None
        return None

# --- CREATE USER ---
def create_user(token: str, username: str, email: str, full_name: str) -> None:
    s = _session(token)
    payload = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": "TempPass123!",  # Temporary password, user should change
    }
    try:
        r = s.post(f"{TAIGA_URL}/api/v1/users", json=payload, timeout=30)
        r.raise_for_status()
        print(f"✅ Created user: {username}")
    except RequestException as e:
        print(f"❌ Failed to create user {username}: {e}")

def process_users_csv(token: str) -> None:
    if not os.path.exists(USER_CSV_FILE):
        print(f"⚠️ User CSV file not found: {USER_CSV_FILE}")
        return
    try:
        with open(USER_CSV_FILE, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = (row.get("username") or "").strip()
                email = (row.get("email") or "").strip()
                full_name = (row.get("full_name") or "").strip()
                if not username or not email:
                    print("⚠️ Skipped user: missing username or email")
                    continue
                # Check if exists
                existing_id = find_user_id(token, username)
                if existing_id:
                    print(f"↪️ User {username} already exists")
                    continue
                create_user(token, username, email, full_name)
    except Exception as e:
        print(f"💥 Error processing users CSV: {e}")

# --- STATUSES (User Stories) ---
def get_or_create_us_status(token: str, project_id: int, name: str) -> int:
    if not STATUS_CACHE:
        s = _session(token)
        try:
            r = s.get(f"{TAIGA_URL}/api/v1/userstory-statuses", params={"project": project_id}, timeout=30)
            r.raise_for_status()
            for st in r.json():
                STATUS_CACHE[st.get("name", "").strip().lower()] = st["id"]
        except RequestException as e:
            print(f"❌ Error retrieving statuses: {e}")
            sys.exit(1)
    target = name.strip().lower()
    if target in STATUS_CACHE:
        return STATUS_CACHE[target]
    # Creating new status
    s = _session(token)
    payload = {
        "name": name,
        "color": f"#{uuid.uuid4().hex[:6]}",  # Random color in HEX
        "project": project_id,
        "is_closed": name.lower() in ["done", "offline done"],  # Mark as closed if contains "done"
    }
    try:
        r = s.post(f"{TAIGA_URL}/api/v1/userstory-statuses", json=payload, timeout=30)
        r.raise_for_status()
        new_status_id = r.json()["id"]
        STATUS_CACHE[target] = new_status_id
        print(f"✅ Created new status: {name} (ID={new_status_id})")
        return new_status_id
    except RequestException as e:
        print(f"⚠️ Failed to create status {name}: {e}")
        return STATUS_CACHE.get(DEFAULT_US_STATUS_NAME.lower(), list(STATUS_CACHE.values())[0])

# --- LABELS ---
def parse_labels_cell(val: str) -> List[str]:
    if not val:
        return []
    parts = [p.strip() for p in val.replace(";", ",").split(",")]
    return [p for p in parts if p]

def collect_all_labels(row: Dict[str, str]) -> List[str]:
    acc: List[str] = []
    for k, v in row.items():
        if k == "Labels" or k.startswith("Labels."):
            val = (v or "").strip()
            if val:
                acc.extend(parse_labels_cell(val))
    seen = set(); out = []
    for x in acc:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# --- IDEMPOTENCY ---
def userstory_with_tag_exists(token: str, project_id: int, jira_tag: str) -> bool:
    s = _session(token)
    try:
        r = s.get(f"{TAIGA_URL}/api/v1/userstories", params={"project": project_id, "tags": jira_tag}, timeout=30)
        if r.ok:
            exists = bool(r.json())
            if exists:
                skipped_logger.info(f"Skipped User Story with tag {jira_tag}")
            return exists
        return False
    except RequestException as e:
        print(f"⚠️ Error checking User Story existence: {e}")
        logging.error(f"Error checking User Story existence for tag {jira_tag}: {e}")
        return False

# --- CREATE USER STORY ---
def create_userstory(
    token: str,
    project_id: int,
    subject: str,
    description: str,
    status_name_from_csv: Optional[str],
    assignee_name: Optional[str],
    tags: List[str],
    jira_key: Optional[str],
) -> None:
    s = _session(token)
    final_tags = list(tags)
    jira_tag = None
    if jira_key:
        jira_tag = f"jira:{jira_key}"
        if jira_tag not in final_tags:
            final_tags.append(jira_tag)

    if jira_tag and userstory_with_tag_exists(token, project_id, jira_tag):
        print(f"↪️ Skipped (exists {jira_tag})")
        return

    status_id = get_or_create_us_status(token, project_id, status_name_from_csv or DEFAULT_US_STATUS_NAME)
    assigned_to = find_user_id(token, assignee_name) if assignee_name else None

    description = description.replace("\r\n", "\n").strip() if description else ""
    if jira_key:
        description = f"**Jira Key**: {jira_key}\n\n{description}".strip()

    payload = {
        "project": project_id,
        "subject": (subject or "")[:250] or "(no subject)",
        "status": status_id,
        "description": description,
        "tags": final_tags,
    }
    if assigned_to:
        payload["assigned_to"] = assigned_to

    for attempt in range(3):
        try:
            r = s.post(f"{TAIGA_URL}/api/v1/userstories", json=payload, timeout=30)
            if r.status_code == 201:
                obj = r.json()
                print(f"✅ Created User Story ID={obj.get('id')} | {subject[:100]}")
                return
            elif r.status_code == 429:
                print(f"⚠️ API limit, attempt {attempt + 1}/3, waiting 5 seconds...")
                time.sleep(5)
                continue
            else:
                error_msg = f"❌ Error creating User Story ({r.status_code}) for {jira_key}: {r.text[:300]}"
                print(error_msg)
                logging.error(error_msg)
                return
        except RequestException as e:
            error_msg = f"❌ Network error for {jira_key}: {e}"
            print(error_msg)
            logging.error(error_msg)
            time.sleep(5)
            continue
    error_msg = f"❌ Failed to create User Story {jira_key} after 3 attempts"
    print(error_msg)
    logging.error(error_msg)

def main() -> None:
    print("🚀 Import Jira → Taiga (Users and User Stories)")
    token = taiga_authenticate()
    process_users_csv(token)
    project = get_project_by_slug(token, PROJECT_SLUG)
    project_id = project["id"]
    print(f"📂 Project: {project['name']} (ID={project_id})")

    processed = errors = 0

    try:
        with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                summary = (row.get("Summary") or "").strip()
                if not summary:
                    print(f"⚠️ Task {i} skipped: missing Summary")
                    continue
                jira_key = (row.get("Issue key") or "").strip()
                description = (row.get("Description") or "").strip()
                assignee = (row.get("Assignee") or "").strip()
                status_csv = (row.get("Status") or "").strip()
                tags = collect_all_labels(row)

                print(f"\n=== Task {i} ===")
                print(f"Summary: {summary[:100]}")
                if assignee:
                    print(f"Assignee: {assignee}")
                if status_csv:
                    print(f"Status (Jira): {status_csv}")
                try:
                    create_userstory(
                        token=token,
                        project_id=project_id,
                        subject=summary,
                        description=description,
                        status_name_from_csv=status_csv or None,
                        assignee_name=assignee or None,
                        tags=tags,
                        jira_key=jira_key or None,
                    )
                    processed += 1
                except Exception as e:
                    errors += 1
                    error_msg = f"💥 Error processing task {i} ({jira_key}): {e}"
                    print(error_msg)
                    logging.error(error_msg)
                if RATE_LIMIT > 0:
                    time.sleep(RATE_LIMIT)
    except FileNotFoundError:
        print(f"❌ File not found: {CSV_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)

    print("\n=== Summary ===")
    print(f"Processed: {processed}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    main()
