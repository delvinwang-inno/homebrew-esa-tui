from dataclasses import dataclass
from typing import Optional
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button, Label, RadioSet, RadioButton
)

@dataclass
class WafConfig:
    definite_action: Optional[str] = None
    likely_action: Optional[str] = None
    verified_action: Optional[str] = None

class WafTaskView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("WAF Bot Configuration (Allow/Monitor/Skip):")
        yield Label("Definite Bots:")
        yield RadioSet(
            RadioButton("Allow", id="def_allow"), 
            RadioButton("Monitor", id="def_monitor"), 
            RadioButton("Keep Current", id="def_skip", value=True), 
            id="def_set"
        )
        yield Label("Likely Bots:")
        yield RadioSet(
            RadioButton("Allow", id="lik_allow"), 
            RadioButton("Monitor", id="lik_monitor"), 
            RadioButton("Keep Current", id="lik_skip", value=True), 
            id="lik_set"
        )
        yield Label("Verified Bots:")
        yield RadioSet(
            RadioButton("Allow", id="ver_allow"), 
            RadioButton("Monitor", id="ver_monitor"), 
            RadioButton("Keep Current", id="ver_skip", value=True), 
            id="ver_set"
        )
        yield Horizontal(
            Button("Apply Settings", variant="primary", id="apply_btn"),
            Button("Back", id="back_btn"),
        )

    @on(Button.Pressed, "#apply_btn")
    @work(thread=True)
    def apply_waf(self):
        def get_action(prefix):
            if self.query_one(f"#{prefix}_allow").value:
                return "allow"
            if self.query_one(f"#{prefix}_monitor").value:
                return "monitor"
            return None

        config = WafConfig(
            definite_action=get_action("def"),
            likely_action=get_action("lik"),
            verified_action=get_action("ver")
        )
        
        if config.definite_action is None and config.likely_action is None and config.verified_action is None:
            self.app.log_message("No changes selected.")
            return

        for site in self.app.selected_sites:
            self.app.log_message(f"Processing {site['name']}...")
            try:
                current = self.app.manager.get_waf_settings(site['id'])
                req_id = self.app.manager.update_waf_settings(site['id'], config, current.bot_management)
                self.app.log_message(f"✔ Updated [cyan]{site['name']}[/cyan] | ReqID: {req_id}")
            except Exception as e:
                self.app.log_message(f"✖ Failed {site['name']}: {e}")

    @on(Button.Pressed, "#back_btn")
    def back(self): self.app.switch_view("task_selection")
