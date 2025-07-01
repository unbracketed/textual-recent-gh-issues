#!/usr/bin/env python
# /// script
# dependencies = ["textual>=0.47.0"]
# ///

import subprocess
import json
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding
from textual import events, work


@dataclass
class Issue:
    number: int
    title: str
    created_at: str
    labels: List[str]
    url: str


def fetch_issues() -> List[Issue]:
    """Fetch the 10 most recent issues from the current git repository using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--limit", "10", "--json", "number,title,createdAt,labels,url"],
            capture_output=True,
            text=True,
            check=True
        )
        
        issues_data = json.loads(result.stdout)
        issues = []
        
        for item in issues_data:
            labels = [label["name"] for label in item.get("labels", [])]
            issue = Issue(
                number=item["number"],
                title=item["title"],
                created_at=item["createdAt"],
                labels=labels,
                url=item["url"]
            )
            issues.append(issue)
        
        return issues
    
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr:
            raise RuntimeError("Not in a git repository")
        elif "gh: command not found" in str(e):
            raise RuntimeError("gh CLI not found. Please install GitHub CLI: https://cli.github.com")
        else:
            raise RuntimeError(f"Failed to fetch issues: {e.stderr}")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse GitHub response")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")


def get_repo_name() -> str:
    """Get the repository name from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        # Extract repo name from URL (works for both HTTPS and SSH)
        if url.endswith('.git'):
            url = url[:-4]
        parts = url.split('/')
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        return "Unknown Repository"
    except:
        return "Unknown Repository"


class IssuesApp(App):
    """A Textual app to display GitHub issues."""
    
    CSS = """
    DataTable {
        height: 1fr;
    }
    
    DataTable > .datatable--cursor {
        background: $boost;
    }
    
    DataTable > .datatable--header {
        background: $primary;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("enter", "open_issue", "Open Issue", priority=True),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.issues: List[Issue] = []
        repo_name = get_repo_name()
        self.title = f"GitHub Issues - {repo_name}"
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DataTable(cursor_type="row")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when app starts."""
        table = self.query_one(DataTable)
        table.add_columns("Issue #", "Title", "Date", "Labels")
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        self.load_issues()
    
    @work(thread=True)
    def load_issues(self) -> None:
        """Load issues and populate the table."""
        table = self.query_one(DataTable)
        table.clear()
        
        try:
            self.issues = fetch_issues()
            
            if not self.issues:
                table.add_row("", "No issues found", "", "")
                return
            
            for issue in self.issues:
                # Format date
                date = datetime.fromisoformat(issue.created_at.replace('Z', '+00:00'))
                date_str = date.strftime("%Y-%m-%d")
                
                # Format labels
                labels_str = ", ".join(issue.labels) if issue.labels else ""
                
                # Truncate title if too long
                title = issue.title
                if len(title) > 80:
                    title = title[:77] + "..."
                
                table.add_row(
                    str(issue.number),
                    title,
                    date_str,
                    labels_str,
                    key=str(issue.number)
                )
        
        except RuntimeError as e:
            table.add_row("", str(e), "", "")
            self.issues = []
    
    async def action_open_issue(self) -> None:
        """Open the selected issue in the browser."""
        table = self.query_one(DataTable)
        
        if not self.issues:
            self.notify("No issues loaded", severity="warning")
            return
            
        if table.cursor_row < 0:
            self.notify("No row selected", severity="warning")
            return
        
        try:
            # Use coordinate_to_cell_key to get the row key from cursor position
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            self.notify(f"Debug: row_key={row_key}, cursor_coordinate={table.cursor_coordinate}")
            
            issue = next((i for i in self.issues if str(i.number) == row_key), None)
            
            if issue:
                self.notify(f"Debug: Found issue #{issue.number}, URL: {issue.url}")
                webbrowser.open(issue.url)
                self.notify(f"Opening issue #{issue.number}")
            else:
                self.notify(f"Could not find issue with key: {row_key}", severity="error")
        except Exception as e:
            self.notify(f"Failed to open issue: {str(e)}", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh the issues list."""
        self.notify("Refreshing issues...")
        self.load_issues()
        self.notify("Issues refreshed")


def main():
    """Run the application."""
    app = IssuesApp()
    app.run()


if __name__ == "__main__":
    main()