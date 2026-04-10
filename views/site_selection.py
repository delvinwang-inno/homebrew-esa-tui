from typing import List
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button, DataTable, Label
)
from textual.message import Message

class SiteSelectionView(Vertical):
    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("space", "select_cursor", "Select"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="site_header"):
            yield Label("Fetching sites...", id="status_label")
        yield DataTable(id="sites_table")
        yield Horizontal(
            Button("Select All", id="select_all_btn"),
            Button("Refresh", id="refresh_btn"),
            Button("Proceed with Selected", variant="primary", id="proceed_btn"),
            classes="button_row"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        self.col_keys = table.add_columns("Select", "Site Name", "Site ID")
        table.cursor_type = "row"
        if self.app.manager:
            self.fetch_sites()

    @work(thread=True)
    def fetch_sites(self):
        if not self.app.manager:
            return
        self.post_message(self.UpdateStatus("Fetching ESA sites..."))
        try:
            sites = self.app.manager.list_all_sites()
            self.post_message(self.PopulateTable(sites))
        except Exception as e:
            self.app.log_message(f"Error fetching sites: {e}")

    class UpdateStatus(Message):
        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__()

    class PopulateTable(Message):
        def __init__(self, sites) -> None:
            self.sites = sites
            super().__init__()

    @on(UpdateStatus)
    def handle_status_update(self, message: UpdateStatus):
        self.query_one("#status_label").update(message.message)

    @on(PopulateTable)
    def handle_populate_table(self, message: PopulateTable):
        table = self.query_one(DataTable)
        table.clear()
        for site in message.sites:
            table.add_row("[white][ ][/white]", site.site_name, str(site.site_id), key=str(site.site_id))
        self.query_one("#status_label").update(f"Found {len(message.sites)} sites.")
        self.query_one("#select_all_btn").label = "Select All"

    @on(DataTable.RowSelected)
    def toggle_selection(self, event: DataTable.RowSelected):
        table = self.query_one(DataTable)
        column_key = self.col_keys[0]
        current_val = table.get_cell(event.row_key, column_key)
        if "[X]" in current_val:
            new_val = "[white][ ][/white]"
        else:
            new_val = "[bold green][X][/bold green]"
        table.update_cell(event.row_key, column_key, new_val)

    @on(Button.Pressed, "#select_all_btn")
    def select_all(self):
        table = self.query_one(DataTable)
        column_key = self.col_keys[0]
        # Check if any are NOT selected
        any_not_selected = any("[ ]" in table.get_cell(rk, column_key) for rk in table.rows)
        
        new_val = "[bold green][X][/bold green]" if any_not_selected else "[white][ ][/white]"
        for row_key in table.rows:
            table.update_cell(row_key, column_key, new_val)
        
        btn = self.query_one("#select_all_btn", Button)
        btn.label = "Deselect All" if any_not_selected else "Select All"

    @on(Button.Pressed, "#proceed_btn")
    def proceed(self):
        table = self.query_one(DataTable)
        column_key = self.col_keys[0]
        selected = []
        for row_key in table.rows:
            if "[X]" in table.get_cell(row_key, column_key):
                row = table.get_row(row_key)
                selected.append({"name": row[1], "id": row[2]})
        
        if not selected:
            self.app.log_message("[red]No sites selected![/red]")
            return
        
        self.app.selected_sites = selected
        self.app.switch_view("task_selection")

    @on(Button.Pressed, "#refresh_btn")
    def handle_refresh(self):
        self.fetch_sites()

    def action_cursor_down(self):
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self):
        self.query_one(DataTable).action_cursor_up()

    def action_select_cursor(self):
        self.query_one(DataTable).action_select_cursor()
