import os
import asyncio
from typing import List, Optional, Union
from dataclasses import dataclass

from dotenv import load_dotenv
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import (
    Header, Footer, Static, Button, Checkbox, 
    Label, Input, RichLog, ContentSwitcher, DataTable
)
from textual.screen import Screen
from textual.message import Message

from alibabacloud_esa20240910 import models as esa_models
from alibabacloud_esa20240910.client import Client as EsaClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

# Load environment variables
load_dotenv()

from modules.waf_task import WafConfig, WafTaskView
from modules.cache_task import CacheTaskView
from modules.asn_block import AsnBlockView
from modules.ip_block import IpBlockView
from modules.ip_whitelist import IpWhitelistView
from views.account_selection import AccountSelectionView
from views.site_selection import SiteSelectionView
from views.task_selection import TaskSelectionView

@dataclass
class EsaManager:
    def __init__(self, ak_id: str, ak_secret: str, endpoint: str = "esa.cn-hangzhou.aliyuncs.com"):
        config = open_api_models.Config(
            access_key_id=ak_id,
            access_key_secret=ak_secret,
            endpoint=endpoint,
        )
        self.client = EsaClient(config)
        self.runtime = util_models.RuntimeOptions()

    def list_all_sites(self) -> List[esa_models.ListSitesResponseBodySites]:
        sites = []
        page_number = 1
        while True:
            request = esa_models.ListSitesRequest(page_size=50, page_number=page_number)
            response = self.client.list_sites_with_options(request, self.runtime)
            if not response.body or not response.body.sites: break
            sites.extend(response.body.sites)
            if len(response.body.sites) < 50: break
            page_number += 1
        return sites

    def get_waf_settings(self, site_id: Union[int, str]):
        request = esa_models.GetSiteWafSettingsRequest(site_id=int(site_id))
        return self.client.get_site_waf_settings_with_options(request, self.runtime).body.settings

    def update_waf_settings(self, site_id: Union[int, str], config: WafConfig, current_bot):
        waf_settings = esa_models.WafSiteSettings(
            bot_management=esa_models.WafSiteSettingsBotManagement(
                definite_bots=esa_models.WafSiteSettingsBotManagementDefiniteBots(
                    action=config.definite_action or current_bot.definite_bots.action
                ),
                likely_bots=esa_models.WafSiteSettingsBotManagementLikelyBots(
                    action=config.likely_action or current_bot.likely_bots.action
                ),
                verified_bots=esa_models.WafSiteSettingsBotManagementVerifiedBots(
                    action=config.verified_action or current_bot.verified_bots.action
                ),
            )
        )
        request = esa_models.EditSiteWafSettingsRequest(site_id=int(site_id), settings=waf_settings)
        return self.client.edit_site_waf_settings_with_options(request, self.runtime).body.request_id

    def list_cache_rules(self, site_id: Union[int, str]):
        request = esa_models.ListCacheRulesRequest(site_id=int(site_id))
        res = self.client.list_cache_rules_with_options(request, self.runtime)
        return res.body.configs if res.body and res.body.configs else []

    def update_cache_rule_status(self, site_id: Union[int, str], config_id: int, enable: bool):
        request = esa_models.UpdateCacheRuleRequest(
            site_id=int(site_id), config_id=config_id, rule_enable="on" if enable else "off"
        )
        return self.client.update_cache_rule_with_options(request, self.runtime).body.request_id

    def list_waf_rulesets(self, site_id: Union[int, str], phase: Optional[str] = "http_custom"):
        request = esa_models.ListWafRulesetsRequest(site_id=int(site_id), phase=phase)
        return self.client.list_waf_rulesets_with_options(request, self.runtime).body.rulesets

    def create_waf_ruleset(self, site_id: Union[int, str], name: str, phase: str = "http_custom"):
        request = esa_models.CreateWafRulesetRequest(
            site_id=int(site_id),
            name=name,
            phase=phase
        )
        return self.client.create_waf_ruleset_with_options(request, self.runtime).body.id

    def create_waf_rule(self, site_id: Union[int, str], ruleset_id: int, name: str, expression: str, 
                        action: Optional[str] = None, 
                        actions: Optional[esa_models.WafRuleConfigActions] = None,
                        phase: str = "http_custom",
                        rule_type: str = "custom"):
        config = esa_models.WafRuleConfig(
            name=name,
            status="on",
            action=action,
            actions=actions,
            expression=expression,
            type=rule_type
        )
        request = esa_models.CreateWafRuleRequest(
            site_id=int(site_id),
            ruleset_id=ruleset_id,
            phase=phase,
            config=config,
            site_version=0
        )
        return self.client.create_waf_rule_with_options(request, self.runtime).body.id

    def get_top_5xx_ips(self, site_id: Union[int, str]):
        from datetime import datetime, timedelta, timezone
        import json
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Try a few dimensions for IP
        for dim in ["client_ip", "ip", "ClientIp"]:
            query = {
                "SiteId": str(site_id),
                "StartTime": start,
                "EndTime": end,
                "Limit": "5",
                "Fields": json.dumps([{"FieldName": "Requests", "Dimension": [dim]}]),
                "Filters": json.dumps([{"Key": "status_code", "Value": "5xx"}])
            }
            
            req = open_api_models.OpenApiRequest(query=query)
            params = open_api_models.Params(
                action='DescribeSiteTopData', version='2024-09-10', protocol='HTTPS', pathname='/',
                method='POST', auth_type='AK', style='RPC', req_body_type='formData', body_type='json'
            )
            
            try:
                response = self.client.call_api(params, req, self.runtime)
                data_list = response.get("body", {}).get("Data", [])
                if data_list and data_list[0].get("DetailData"):
                    return [{"ip": item.get("DimensionValue"), "count": item.get("Value")} for item in data_list[0]["DetailData"]]
            except Exception:
                continue
        
        # Fallback to total 5xx if IP breakdown fails
        query = {
            "SiteId": str(site_id), "StartTime": start, "EndTime": end, "Limit": "1",
            "Fields": json.dumps([{"FieldName": "Requests", "Dimension": ["ALL"]}]),
            "Filters": json.dumps([{"Key": "status_code", "Value": "5xx"}])
        }
        try:
            req = open_api_models.OpenApiRequest(query=query)
            response = self.client.call_api(params, req, self.runtime)
            val = response.get("body", {}).get("Data", [{}])[0].get("DetailData", [{}])[0].get("Value", 0)
            return [{"ip": "Total 5xx", "count": val}]
        except Exception:
            return []

class EsaTuiApp(App):
    CSS = """
    #main_container {
        padding: 1;
        layout: vertical;
    }
    ContentSwitcher {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
        border: double white;
        margin-bottom: 1;
    }
    #log_container {
        height: 11;
        border: solid gray;
        background: $surface;
        margin-top: 1;
    }
    #top_ips_table {
        height: 8;
        border: solid $accent;
        margin: 0 1;
        display: none;
    }
    #top_ips_label {
        width: 1fr;
        content-align: center middle;
        text-style: bold italic;
        color: $accent;
        margin: 0;
        display: none;
    }
    #log_header {
        height: auto;
        align: right middle;
        background: $boost;
        padding: 0 1;
    }
    #log_title {
        width: 1fr;
    }
    #global_log {
        height: 8;
    }
    Button {
        margin-right: 1;
        margin-bottom: 1;
    }
    #nav_logout_btn, #nav_back_sites_btn {
        display: none;
        margin: 0;
        min-width: 10;
    }
    .button_row {
        height: auto;
    }
    RadioSet {
        margin-bottom: 1;
    }
    Label {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
    }
    #site_header {
        height: auto;
        align: left middle;
    }
    #account_display_label, #global_account_display {
        width: 1fr;
        content-align: right middle;
        padding-right: 1;
        margin-bottom: 1;
    }
    #global_account_display {
        display: none;
    }
    TaskSelectionView {
        align: center middle;
    }
    TaskSelectionView Button {
        width: 32;
        margin: 0;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.manager = None
        self.selected_sites = []
        self.accounts = []
        self.current_account_name = None

    def initialize_manager(self, ak_id: str, ak_secret: str):
        self.manager = EsaManager(ak_id, ak_secret)
        # Update account display label
        if self.current_account_name:
            self.query_one("#global_account_display").update(f"Account: [cyan]{self.current_account_name}[/cyan]")
        # Notify the SiteSelectionView that it can now fetch sites
        self.query_one(SiteSelectionView).fetch_sites()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"):
            yield Label("", id="global_account_display")
            with ContentSwitcher(initial="account_selection"):
                yield AccountSelectionView(id="account_selection")
                yield SiteSelectionView(id="site_selection")
                yield TaskSelectionView(id="task_selection")
                yield WafTaskView(id="waf_task")
                yield CacheTaskView(id="cache_task")
                yield AsnBlockView(id="asn_block")
                yield IpBlockView(id="ip_block")
                yield IpWhitelistView(id="ip_whitelist")
            
            yield Label("Top 5xx Requests (Past 12h)", id="top_ips_label")
            yield DataTable(id="top_ips_table")
            
            with Vertical(id="log_container"):
                with Horizontal(id="log_header"):
                    yield Label("Console Log", id="log_title")
                    yield Button("Back to Sites", id="nav_back_sites_btn", variant="error")
                    yield Button("Logout", id="nav_logout_btn", variant="error")
                yield RichLog(id="global_log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#top_ips_table", DataTable)
        table.add_columns("Site", "IP / Metric", "Count")
        table.cursor_type = "row"

    @work(thread=True)
    def refresh_top_data(self):
        if not self.manager or not self.selected_sites:
            return
            
        table = self.query_one("#top_ips_table", DataTable)
        table.clear()
        
        self.log_message("[yellow]Fetching top 5xx error IPs for selected sites...[/yellow]")
        for site in self.selected_sites:
            try:
                data = self.manager.get_top_5xx_ips(site["id"])
                if not data:
                    table.add_row(site["name"], "No 5xx data", "0")
                for item in data:
                    table.add_row(site["name"], item["ip"], str(item["count"]))
            except Exception as e:
                self.log_message(f"✖ Error top data for {site['name']}: {e}")

    def logout(self):
        self.manager = None
        self.selected_sites = []
        self.current_account_name = None
        # Clear the global account display label
        try:
            self.query_one("#global_account_display").update("")
        except Exception:
            pass
        # Clear the sites table for the next account
        try:
            sites_view = self.query_one(SiteSelectionView)
            sites_view.query_one(DataTable).clear()
            sites_view.query_one("#status_label").update("Please select an account first.")
            sites_view.query_one("#select_all_btn").label = "Select All"
        except Exception:
            pass

    def log_message(self, message: str):
        self.query_one("#global_log", RichLog).write(message)

    def switch_view(self, view_id: str):
        self.query_one(ContentSwitcher).current = view_id
        # Update global account display visibility
        self.query_one("#global_account_display").display = (view_id != "account_selection")
        # Update nav button visibility
        # Logout visible everywhere except account selection
        self.query_one("#nav_logout_btn").display = (view_id != "account_selection")
        # Back to Sites visible everywhere except site selection and account selection
        self.query_one("#nav_back_sites_btn").display = (view_id not in ["site_selection", "account_selection"])
        
        # Toggle visibility of Top 5xx table (only for ASN and IP block)
        show_stats = (view_id in ["asn_block", "ip_block"])
        self.query_one("#top_ips_label").display = show_stats
        self.query_one("#top_ips_table").display = show_stats
        
        # Refresh top 5xx data when entering task selection
        if view_id == "task_selection":
            self.refresh_top_data()

    @on(Button.Pressed, "#nav_logout_btn")
    def handle_nav_logout(self):
        self.logout()
        self.log_message("[yellow]Logged out. Switching back to account selection.[/yellow]")
        self.switch_view("account_selection")

    @on(Button.Pressed, "#nav_back_sites_btn")
    def handle_nav_back_sites(self):
        self.switch_view("site_selection")

def main():
    app = EsaTuiApp()
    app.run()

if __name__ == "__main__":
    main()

