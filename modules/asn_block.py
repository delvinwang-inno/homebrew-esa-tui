from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button, Label, Input
)

class AsnBlockView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("ASN Block Configuration:")
        yield Label("Enter ASNs (comma separated, e.g., 13335, 15169):")
        yield Input(placeholder="e.g., 13335, 15169", id="asn_input")
        yield Horizontal(
            Button("Apply ASN Block", variant="primary", id="apply_btn"),
            Button("Back", id="back_btn"),
        )

    @on(Button.Pressed, "#apply_btn")
    @work(thread=True)
    def apply_asn_block(self):
        asn_text = self.query_one("#asn_input").value.strip()
        if not asn_text:
            self.app.log_message("[yellow]Please enter at least one ASN.[/yellow]")
            return

        asns = [asn.strip() for asn in asn_text.split(",") if asn.strip().isdigit()]
        if not asns:
            self.app.log_message("[red]Invalid ASNs format.[/red]")
            return
        
        # Required expression format: ip.geoip.asnum in {asn1 asn2}
        expression = f"ip.geoip.asnum in {{{' '.join(asns)}}}"
        rule_name = "Block specific ASNs (TEMP)"
        phase = "http_custom"

        for site in self.app.selected_sites:
            self.app.log_message(f"Processing {site['name']}...")
            try:
                # 1. Get ruleset for http_custom phase
                rulesets = self.app.manager.list_waf_rulesets(site['id'], phase)
                
                ruleset_id = None
                if rulesets:
                    ruleset_id = rulesets[0].id
                else:
                    # 2. Create ruleset if it doesn't exist
                    self.app.log_message(f"No ruleset for {phase} found. Creating one...")
                    ruleset_id = self.app.manager.create_waf_ruleset(site['id'], "Custom Ruleset", phase)

                # 3. Create the rule with exact parameters
                self.app.manager.create_waf_rule(
                    site_id=site['id'], 
                    ruleset_id=ruleset_id, 
                    name=rule_name, 
                    expression=expression, 
                    action="deny", 
                    phase=phase
                )

                self.app.log_message(f"✔ Created rule '[cyan]{rule_name}[/cyan]' on [cyan]{site['name']}[/cyan]")
                    
            except Exception as e:
                self.app.log_message(f"✖ Error on {site['name']}: {e}")

    @on(Button.Pressed, "#back_btn")
    def back(self): self.app.switch_view("task_selection")
