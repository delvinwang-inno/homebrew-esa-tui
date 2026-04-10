import json
import os
from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import (
    Button, DataTable, Label
)

class AccountSelectionView(Vertical):
    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("space", "select_cursor", "Select"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("Select Alibaba Cloud Account:")
        yield DataTable(id="accounts_table")
        yield Button("Proceed with Selected", variant="primary", id="proceed_btn")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Account Name", "Access Key ID")
        table.cursor_type = "row"
        self.selected_idx = None
        self.load_accounts()

    def load_accounts(self):
        table = self.query_one(DataTable)
        accounts_dir = Path.home() / ".esa-tui"
        accounts_file = accounts_dir / "accounts.json"

        # Ensure directory exists
        if not accounts_dir.exists():
            accounts_dir.mkdir(parents=True, exist_ok=True)

        # Ensure file exists
        if not accounts_file.exists():
            with open(accounts_file, "w") as f:
                json.dump([], f)
            self.app.accounts = []
        else:
            try:
                with open(accounts_file, "r") as f:
                    self.app.accounts = json.load(f)
            except Exception as e:
                self.app.log_message(f"[red]Error loading {accounts_file}: {e}[/red]")
                self.app.accounts = []

        for idx, acc in enumerate(self.app.accounts):
            table.add_row(acc["name"], acc["ak_id"], key=str(idx))

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        self.selected_idx = int(event.row_key.value)

    @on(Button.Pressed, "#proceed_btn")
    def proceed(self):
        if self.selected_idx is not None:
            account = self.app.accounts[self.selected_idx]
            self.app.current_account_name = account["name"]
            self.app.initialize_manager(account["ak_id"], account["ak_secret"])
            self.app.log_message(f"Logged in as: [cyan]{account['name']}[/cyan]")
            self.app.switch_view("site_selection")
        else:
            self.app.log_message("[yellow]Please select (double click or press Enter) an account first.[/yellow]")

    def action_cursor_down(self):
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self):
        self.query_one(DataTable).action_cursor_up()

    def action_select_cursor(self):
        self.query_one(DataTable).action_select_cursor()
