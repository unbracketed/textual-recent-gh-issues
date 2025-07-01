#!/usr/bin/env python
"""Test script to verify the GitHub issues app functionality."""

import subprocess
import json

# Test 1: Check if gh is installed
try:
    result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
    print(f"✓ gh CLI is installed: {result.stdout.strip()}")
except FileNotFoundError:
    print("✗ gh CLI is not installed")

# Test 2: Check if we're in a git repo
try:
    result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ In a git repository")
    else:
        print("✗ Not in a git repository")
except:
    print("✗ Git error")

# Test 3: Check if repo has a remote
try:
    result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Repository has remote: {result.stdout.strip()}")
    else:
        print("✗ No remote configured")
except:
    print("✗ Error checking remote")

# Test 4: Test gh issue list command
try:
    result = subprocess.run(
        ["gh", "issue", "list", "--limit", "10", "--json", "number,title,createdAt,labels,url"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        issues = json.loads(result.stdout)
        print(f"✓ gh issue list works, found {len(issues)} issues")
        if issues:
            print(f"  First issue: #{issues[0]['number']} - {issues[0]['title']}")
    else:
        print(f"✗ gh issue list failed: {result.stderr}")
except Exception as e:
    print(f"✗ Error running gh: {e}")

print("\nApp can be run with: uv run gh_issues.py")