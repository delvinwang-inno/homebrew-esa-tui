from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button, Label, Input
)

class CacheTaskView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Manage Cache Rules:")
        yield Input(placeholder="Keyword to filter rule names", id="keyword_input")
        yield Horizontal(
            Button("Enable Matching Rules", id="enable_btn", variant="success"),
            Button("Disable Matching Rules", id="disable_btn", variant="error"),
        )
        yield Button("Back", id="back_btn")

    @on(Button.Pressed, "#enable_btn, #disable_btn")
    @work(thread=True)
    def update_rules(self, event: Button.Pressed):
        keyword = self.query_one("#keyword_input").value.lower()
        enable = event.button.id == "enable_btn"
        
        if not keyword:
            self.app.log_message("[yellow]Please enter a keyword.[/yellow]")
            return

        for site in self.app.selected_sites:
            self.app.log_message(f"Fetching rules for {site['name']}...")
            try:
                rules = self.app.manager.list_cache_rules(site['id'])
                matching = [r for r in rules if keyword in (r.rule_name or "").lower()]
                if not matching:
                    self.app.log_message(f"No matches for {site['name']}")
                    continue
                for rule in matching:
                    req_id = self.app.manager.update_cache_rule_status(site['id'], rule.config_id, enable)
                    action = "Enabled" if enable else "Disabled"
                    self.app.log_message(f"✔ {action} '{rule.rule_name}' on [cyan]{site['name']}[/cyan] | Req: {req_id}")
            except Exception as e:
                self.app.log_message(f"✖ Error on {site['name']}: {e}")

    @on(Button.Pressed, "#back_btn")
    def back(self): self.app.switch_view("task_selection")
