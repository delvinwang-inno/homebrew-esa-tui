from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button, Label
)

class TaskSelectionView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Select Task to Perform:")
        yield Button("Update WAF Bot Settings", id="waf_task_btn")
        yield Button("Manage Cache Rules", id="cache_task_btn")
        yield Button("ASN Block (TEMP)", id="asn_block_btn")
        yield Button("IP Block (TEMP)", id="ip_block_btn")
        yield Button("IP Whitelist (TEMP)", id="ip_whitelist_btn")

    @on(Button.Pressed, "#waf_task_btn")
    def go_waf(self): self.app.switch_view("waf_task")

    @on(Button.Pressed, "#cache_task_btn")
    def go_cache(self): self.app.switch_view("cache_task")

    @on(Button.Pressed, "#asn_block_btn")
    def go_asn_block(self): self.app.switch_view("asn_block")

    @on(Button.Pressed, "#ip_block_btn")
    def go_ip_block(self): self.app.switch_view("ip_block")

    @on(Button.Pressed, "#ip_whitelist_btn")
    def go_ip_whitelist(self): self.app.switch_view("ip_whitelist")
