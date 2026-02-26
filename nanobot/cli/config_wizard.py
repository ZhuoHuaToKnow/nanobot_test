# -*- coding: utf-8 -*-
"""Nanobot 配置向导 - 多级菜单交互式配置系统"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from nanobot.config.loader import load_config, save_config, get_config_path
from nanobot.config.schema import Config
from nanobot.providers.registry import PROVIDERS
from pathlib import Path
import json

console = Console()


# ==================== 辅助函数 ====================

def format_current(value, is_password=False, mask_len=10):
    """格式化当前值显示"""
    if not value:
        return "[red]未设置[/red]"
    if is_password:
        return f"{'*' * mask_len}"
    return str(value)


def parse_list(value: str) -> list:
    """解析逗号分隔的列表"""
    if not value or value == "*":
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def format_list(value: list) -> str:
    """格式化列表显示"""
    if not value:
        return "所有人"
    return ", ".join(value)


# ==================== 配置向导类 ====================

class ConfigWizard:
    """Nanobot 配置向导 - 多级菜单系统"""

    def __init__(self):
        self.current_path = []
        self.running = True

    # ==================== 基础UI方法 ====================

    def get_breadcrumb(self) -> str:
        return " > ".join(self.current_path) if self.current_path else "[主菜单]"

    def show_header(self, title: str):
        console.print()
        console.print(f"[cyan bold]>>> {title} <<<[/cyan bold]")
        console.print(f"[dim]路径: {self.get_breadcrumb()}[/dim]")
        console.print(f"[dim]配置文件: {get_config_path()}[/dim]")
        console.print()

    def show_menu(self, options: dict):
        for key, desc in options.items():
            console.print(f"  [cyan]{key}[/cyan]. {desc}")
        console.print()

    # ==================== 通用输入方法 ====================

    def _prompt_str(self, obj, field: str, label: str, is_password: bool = False, show_current: bool = True) -> bool:
        """通用字符串输入，返回是否修改"""
        current = getattr(obj, field, None) or ""
        if show_current:
            console.print(f"[dim]当前值: {format_current(current, is_password)}[/dim]")

        value = Prompt.ask(
            f"请输入 {label} (直接回车保持原值)" if show_current else f"请输入 {label}",
            password=is_password,
            default=current
        )

        if value != current:
            setattr(obj, field, value)
            console.print(f"[green]✓[/green] {label} 已保存\n")
            return True
        console.print("[yellow]未修改[/yellow]\n")
        return False

    def _prompt_int(self, obj, field: str, label: str, min_val: int = None, max_val: int = None, show_current: bool = True) -> bool:
        """通用整数输入，返回是否修改"""
        current = getattr(obj, field)
        if show_current:
            console.print(f"[dim]当前值: {current}[/dim]")

        value = Prompt.ask(
            f"请输入 {label} (直接回车保持原值)" if show_current else f"请输入 {label}",
            default=str(current)
        )

        try:
            int_val = int(value)
            if (min_val is None or int_val >= min_val) and (max_val is None or int_val <= max_val):
                if int_val != current:
                    setattr(obj, field, int_val)
                    console.print(f"[green]✓[/green] {label} 已设置为: {int_val}\n")
                    return True
                console.print("[yellow]未修改[/yellow]\n")
                return True
            console.print(f"[red]✗[/red] 值必须在 {min_val}-{max_val} 之间\n")
            return False
        except ValueError:
            console.print("[red]✗[/red] 无效的数值\n")
            return False

    def _prompt_float(self, obj, field: str, label: str, min_val: float = None, max_val: float = None) -> bool:
        """通用浮点数输入，返回是否修改"""
        current = getattr(obj, field)
        console.print(f"[dim]当前值: {current}[/dim]")

        value = Prompt.ask(f"请输入 {label} (直接回车保持原值)", default=str(current))

        try:
            float_val = float(value)
            if (min_val is None or float_val >= min_val) and (max_val is None or float_val <= max_val):
                if float_val != current:
                    setattr(obj, field, float_val)
                    console.print(f"[green]✓[/green] {label} 已设置为: {float_val}\n")
                    return True
                console.print("[yellow]未修改[/yellow]\n")
                return True
            console.print(f"[red]✗[/red] 值必须在 {min_val}-{max_val} 之间\n")
            return False
        except ValueError:
            console.print("[red]✗[/red] 无效的数值\n")
            return False

    def _prompt_bool(self, obj, field: str, label: str) -> bool:
        """通用布尔值输入，返回是否修改"""
        current = getattr(obj, field)
        console.print(f"[dim]当前状态: {'启用' if current else '禁用'}[/dim]")

        value = Confirm.ask(f"{label}? (直接回车保持原值)", default=current)

        if value != current:
            setattr(obj, field, value)
            console.print(f"[green]✓[/green] 已{'启用' if value else '禁用'}\n")
            return True
        console.print("[yellow]未修改[/yellow]\n")
        return False

    def _prompt_choice(self, obj, field: str, label: str, choices: list) -> bool:
        """通用选择输入，返回是否修改"""
        current = getattr(obj, field)
        console.print(f"[dim]当前值: {current}[/dim]")

        value = Prompt.ask(f"选择 {label} (直接回车保持原值)", choices=choices, default=current)

        if value != current:
            setattr(obj, field, value)
            console.print(f"[green]✓[/green] {label} 已设置为: {value}\n")
            return True
        console.print("[yellow]未修改[/yellow]\n")
        return False

    def _prompt_list(self, obj, field: str, label: str) -> bool:
        """通用列表输入，返回是否修改"""
        current = getattr(obj, field) or []
        console.print(f"[dim]当前值: {format_list(current)}[/dim]")
        console.print("[dim]格式: 逗号分隔，* 表示所有人[/dim]")

        current_display = "*" if not current else ",".join(current)
        value = Prompt.ask(f"请输入 {label} (直接回车保持原值)", default=current_display)

        new_list = parse_list(value)
        if new_list != current:
            setattr(obj, field, new_list)
            console.print(f"[green]✓[/green] {label} 已设置为: {format_list(new_list)}\n")
            return True
        console.print("[yellow]未修改[/yellow]\n")
        return False

    # ==================== 通用菜单运行器 ====================

    def _run_field_menu(self, title: str, obj, fields: list, show_panel: bool = True):
        """
        运行字段配置菜单
        fields: [(key, label, type), ...]
        type: str, int, float, bool, choice:xxx, list
        """
        self.current_path.append(title)

        while self.running:
            self.show_header(title)

            # 显示当前配置
            if show_panel:
                panel_lines = []
                for key, label, type_info in fields:
                    current = getattr(obj, key, None)
                    if isinstance(current, list):
                        display = format_list(current)
                    elif isinstance(current, bool):
                        display = "启用" if current else "禁用"
                    else:
                        display = str(current) if current else "[red]未设置[/red]"
                    panel_lines.append(f"[bold]{label}:[/bold] {display}")
                console.print(Panel.fit("\n".join(panel_lines), title="[当前配置]", border_style="cyan"))
                console.print()

            # 显示菜单
            menu_items = {}
            for i, (key, label, type_info) in enumerate(fields, 1):
                menu_items[str(i)] = f"设置 {label}"
            menu_items["b"] = "返回上级"
            menu_items["q"] = "退出程序"
            self.show_menu(menu_items)

            choices = [str(i) for i in range(1, len(fields) + 1)] + ["b", "q"]
            choice = Prompt.ask("请选择", choices=choices, default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            else:
                idx = int(choice) - 1
                key, label, type_info = fields[idx]
                self._handle_field_input(obj, key, label, type_info)
                save_config(load_config())

        self.current_path.pop()

    def _handle_field_input(self, obj, key: str, label: str, type_info: str):
        """处理字段输入"""
        if type_info == "str":
            self._prompt_str(obj, key, label)
        elif type_info == "password":
            self._prompt_str(obj, key, label, is_password=True)
        elif type_info == "int":
            self._prompt_int(obj, key, label)
        elif type_info == "float":
            self._prompt_float(obj, key, label)
        elif type_info == "bool":
            self._prompt_bool(obj, key, label)
        elif type_info.startswith("choice:"):
            choices = type_info[6:].split(",")
            self._prompt_choice(obj, key, label, choices)
        elif type_info == "list":
            self._prompt_list(obj, key, label)
        else:
            self._prompt_str(obj, key, label)

    # ==================== 主菜单 ====================

    def run(self):
        console.print("\n[bold cyan]========================================[/bold cyan]")
        console.print("[bold cyan]    Nanobot 配置向导[/bold cyan]")
        console.print("[bold cyan]========================================[/bold cyan]\n")

        menu_handlers = {
            "1": self.agents_menu,
            "2": self.providers_menu,
            "3": self.channels_menu,
            "4": self.gateway_menu,
            "5": self.tools_menu,
        }

        while self.running:
            self.show_header("Nanobot 配置管理")
            self.show_menu({
                "1": "Agents - 智能体配置（模型、温度、工作区等）",
                "2": "Providers - LLM 提供商配置（API Key、Base URL）",
                "3": "Channels - 消息渠道配置（Telegram、WhatsApp 等）",
                "4": "Gateway - 网关配置（端口、心跳）",
                "5": "Tools - 工具配置（Web 搜索、MCP 服务器）",
                "0": "退出程序"
            })

            choice = Prompt.ask("请选择", choices=["0", "1", "2", "3", "4", "5"], default="0")

            if choice == "0":
                self.running = False
            else:
                menu_handlers[choice]()

        console.print("\n[yellow]感谢使用 Nanobot 配置系统！[/yellow]\n")

    # ==================== Agents 菜单 ====================

    def agents_menu(self):
        config = load_config()
        agent = config.agents.defaults

        fields = [
            ("model", "模型", "str"),
            ("temperature", "温度", "float"),
            ("max_tokens", "最大 Tokens", "int"),
            ("max_tool_iterations", "最大迭代次数", "int"),
            ("memory_window", "记忆窗口", "int"),
            ("workspace", "工作区", "str"),
        ]

        self._run_field_menu("Agents - 智能体配置", agent, fields)
        save_config(config)

    # ==================== Providers 菜单 ====================

    def providers_menu(self):
        self.current_path.append("Providers")
        config = load_config()

        while self.running:
            self.show_header("Providers - LLM 提供商配置")

            # 显示提供商列表
            table = Table(show_header=True, title="[提供商状态]")
            table.add_column("序号", style="cyan", width=6)
            table.add_column("提供商", style="cyan", width=20)
            table.add_column("状态", justify="center", width=10)
            table.add_column("API Base", style="dim")

            for i, spec in enumerate(PROVIDERS, 1):
                provider_cfg = getattr(config.providers, spec.name, None)
                has_key = provider_cfg and bool(provider_cfg.api_key)
                status = "[green]配置[/green]" if has_key else "[red]未配置[/red]"
                api_base = provider_cfg.api_base if provider_cfg else None
                base_display = api_base or "默认"
                table.add_row(str(i), spec.label, status, base_display)

            console.print(table)
            console.print()

            self.show_menu({
                "输入序号": "配置对应提供商",
                "b": "返回上级菜单",
                "q": "退出程序"
            })

            provider_choices = [str(i) for i in range(1, len(PROVIDERS) + 1)] + ["b", "q"]
            choice = Prompt.ask("请选择", choices=provider_choices, default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            else:
                idx = int(choice) - 1
                provider_spec = PROVIDERS[idx]
                self._configure_provider(config, provider_spec)
                save_config(config)

        self.current_path.pop()

    def _configure_provider(self, config: Config, provider_spec):
        self.current_path.append(provider_spec.label)
        provider_cfg = getattr(config.providers, provider_spec.name)

        while self.running:
            self.show_header(f"配置 {provider_spec.label} 提供商")

            # 显示当前配置
            api_key_display = format_current(provider_cfg.api_key, is_password=True, mask_len=20)
            api_base_display = provider_cfg.api_base or "使用默认"
            headers_display = "已设置" if provider_cfg.extra_headers else "未设置"

            console.print(Panel.fit(
                f"[bold]API Key:[/bold] {api_key_display}\n"
                f"[bold]API Base:[/bold] {api_base_display}\n"
                f"[bold]Extra Headers:[/bold] {headers_display}",
                title="[当前配置]",
                border_style="cyan"
            ))
            console.print()

            self.show_menu({
                "1": "设置 API Key",
                "2": "设置 API Base URL",
                "3": "设置 Extra Headers",
                "4": "清除配置",
                "b": "返回上级",
                "q": "退出程序"
            })

            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "b", "q"], default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            elif choice == "1":
                self._prompt_str(provider_cfg, "api_key", f"{provider_spec.label} API Key", is_password=True)
            elif choice == "2":
                self._set_provider_api_base(provider_cfg)
            elif choice == "3":
                self._set_provider_headers(provider_cfg)
            elif choice == "4":
                if Confirm.ask("确认清除该提供商的配置?", default=False):
                    provider_cfg.api_key = ""
                    provider_cfg.api_base = None
                    provider_cfg.extra_headers = None
                    console.print("[green]✓[/green] 配置已清除\n")

        self.current_path.pop()

    def _set_provider_api_base(self, provider_cfg):
        current = provider_cfg.api_base
        use_custom = Confirm.ask("使用自定义 API Base? (直接回车保持原值)", default=bool(current))

        if use_custom:
            self._prompt_str(provider_cfg, "api_base", "API Base URL")
        else:
            if current is not None:
                provider_cfg.api_base = None
                console.print("[green]✓[/green] 将使用默认 API Base\n")
            else:
                console.print("[yellow]已经是默认值[/yellow]\n")

    def _set_provider_headers(self, provider_cfg):
        current = provider_cfg.extra_headers

        if current:
            console.print(f"[dim]当前值: {json.dumps(current, ensure_ascii=False)}[/dim]")
        else:
            console.print("[dim]当前值: 未设置[/dim]")

        if not Confirm.ask("修改 Extra Headers?", default=False):
            console.print("[yellow]未修改[/yellow]\n")
            return

        console.print("[dim]格式: JSON 对象，如 {\"Authorization\": \"Bearer xxx\"}[/dim]")

        current_json = json.dumps(current, ensure_ascii=False) if current else ""
        headers_input = Prompt.ask("请输入 JSON (直接回车保持原值)", default=current_json)

        if headers_input and headers_input != current_json:
            try:
                provider_cfg.extra_headers = json.loads(headers_input)
                console.print("[green]✓[/green] Extra Headers 已保存\n")
            except json.JSONDecodeError:
                console.print("[red]✗[/red] JSON 格式错误\n")
        else:
            console.print("[yellow]未修改[/yellow]\n")

    # ==================== Channels 菜单 ====================

    def channels_menu(self):
        self.current_path.append("Channels")
        config = load_config()

        channels = [
            ("WhatsApp", config.channels.whatsapp),
            ("Telegram", config.channels.telegram),
            ("Discord", config.channels.discord),
            ("飞书", config.channels.feishu),
            ("钉钉", config.channels.dingtalk),
            ("Slack", config.channels.slack),
            ("QQ", config.channels.qq),
            ("Email", config.channels.email),
        ]

        while self.running:
            self.show_header("Channels - 消息渠道配置")

            # 显示渠道列表
            table = Table(show_header=True, title="[渠道状态]")
            table.add_column("序号", style="cyan", width=6)
            table.add_column("渠道", style="cyan", width=12)
            table.add_column("状态", justify="center", width=8)
            table.add_column("配置详情", style="dim")

            for i, (name, cfg) in enumerate(channels, 1):
                enabled = cfg.enabled
                status = "[green]启用[/green]" if enabled else "[red]禁用[/red]"
                details = self._get_channel_details(name, cfg)
                table.add_row(str(i), name, status, details)

            console.print(table)
            console.print()

            self.show_menu({
                "输入序号": "配置对应渠道",
                "b": "返回上级菜单",
                "q": "退出程序"
            })

            channel_choices = [str(i) for i in range(1, len(channels) + 1)] + ["b", "q"]
            choice = Prompt.ask("请选择", choices=channel_choices, default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            else:
                idx = int(choice) - 1
                channel_name, channel_cfg = channels[idx]
                self._configure_channel(config, channel_name, channel_cfg)
                save_config(config)

        self.current_path.pop()

    def _get_channel_details(self, name: str, cfg) -> str:
        details = []
        if name == "WhatsApp":
            details.append(f"URL: {cfg.bridge_url}")
            if cfg.bridge_token:
                details.append("Token: 已设置")
        elif name == "Telegram":
            details.append("Token: " + ("已设置" if cfg.token else "未设置"))
            if cfg.proxy:
                details.append(f"代理: {cfg.proxy}")
        elif name == "Discord":
            details.append("Token: " + ("已设置" if cfg.token else "未设置"))
        elif name == "飞书":
            details.append("App ID: " + ("已设置" if cfg.app_id else "未设置"))
        elif name == "钉钉":
            details.append("Client ID: " + ("已设置" if cfg.client_id else "未设置"))
        elif name == "Slack":
            details.append("Bot Token: " + ("已设置" if cfg.bot_token else "未设置"))
        elif name == "QQ":
            details.append("App ID: " + ("已设置" if cfg.app_id else "未设置"))
        elif name == "Email":
            details.append(f"IMAP: {cfg.imap_host or '未设置'}")
        return " | ".join(details)

    def _configure_channel(self, config: Config, channel_name: str, channel_cfg):
        self.current_path.append(channel_name)

        # 定义各渠道的配置字段
        channel_fields = {
            "Telegram": [
                ("token", "Bot Token", "password"),
                ("proxy", "代理地址", "str"),
                ("reply_to_message", "回复引用原消息", "bool"),
            ],
            "WhatsApp": [
                ("bridge_url", "Bridge URL", "str"),
                ("bridge_token", "Bridge Token", "password"),
            ],
            "Discord": [
                ("token", "Bot Token", "password"),
                ("gateway_url", "Gateway URL", "str"),
            ],
            "飞书": [
                ("app_id", "App ID", "str"),
                ("app_secret", "App Secret", "password"),
                ("encrypt_key", "加密密钥", "password"),
                ("verification_token", "验证令牌", "password"),
            ],
            "钉钉": [
                ("client_id", "Client ID", "str"),
                ("client_secret", "Client Secret", "password"),
            ],
            "Slack": [
                ("bot_token", "Bot Token", "password"),
                ("app_token", "App Token", "password"),
            ],
            "QQ": [
                ("app_id", "App ID", "str"),
                ("secret", "Secret", "password"),
            ],
            "Email": [
                ("imap_host", "IMAP 主机", "str"),
                ("imap_port", "IMAP 端口", "int"),
                ("imap_username", "IMAP 用户名", "str"),
                ("imap_password", "IMAP 密码", "password"),
                ("smtp_host", "SMTP 主机", "str"),
                ("smtp_port", "SMTP 端口", "int"),
                ("smtp_username", "SMTP 用户名", "str"),
                ("smtp_password", "SMTP 密码", "password"),
                ("from_address", "发件人地址", "str"),
            ],
        }

        # 通用的 allow_from 字段（所有渠道都有）
        if channel_name != "Email":
            channel_fields[channel_name].append(("allow_from", "允许用户", "list"))
        else:
            channel_fields[channel_name].append(("allow_from", "允许发件人", "list"))

        while self.running:
            self.show_header(f"配置 {channel_name} 渠道")

            # 显示启用状态
            console.print(Panel(
                f"[bold]启用状态:[/bold] {'[green]启用[/green]' if channel_cfg.enabled else '[red]禁用[/red]'}",
                title="[当前状态]",
                border_style="cyan"
            ))
            console.print()

            # 构建菜单
            menu_options = {
                "1": "启用/禁用渠道",
                "b": "返回上级",
                "q": "退出程序"
            }

            for i, (key, label, type_info) in enumerate(channel_fields.get(channel_name, []), 2):
                menu_options[str(i)] = f"设置 {label}"

            self.show_menu(menu_options)

            # 动态生成选项
            choice_keys = [k for k in menu_options.keys() if k not in ["b", "q"]]
            all_choices = choice_keys + ["b", "q"]
            choice = Prompt.ask("请选择", choices=all_choices, default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            elif choice == "1":
                self._prompt_bool(channel_cfg, "enabled", f"启用 {channel_name} 渠道")
            else:
                idx = int(choice) - 2
                if idx < len(channel_fields.get(channel_name, [])):
                    key, label, type_info = channel_fields[channel_name][idx]
                    self._handle_field_input(channel_cfg, key, label, type_info)

        self.current_path.pop()

    # ==================== Gateway 菜单 ====================

    def gateway_menu(self):
        config = load_config()

        # 主配置字段
        main_fields = [
            ("host", "主机地址", "str"),
            ("port", "端口", "int"),
        ]

        self._run_field_menu("Gateway - 网关配置", config.gateway, main_fields, show_panel=False)

        # 心跳配置单独处理
        self._configure_gateway_heartbeat(config.gateway)

        save_config(config)

    def _configure_gateway_heartbeat(self, heartbeat_cfg):
        self.current_path.append("心跳配置")

        while self.running:
            self.show_header("Gateway - 心跳配置")

            console.print(Panel.fit(
                f"[bold]状态:[/bold] {'启用' if heartbeat_cfg.enabled else '禁用'}\n"
                f"[bold]间隔:[/bold] {heartbeat_cfg.interval_s} 秒",
                title="[当前配置]",
                border_style="cyan"
            ))
            console.print()

            self.show_menu({
                "1": "启用/禁用心跳",
                "2": "设置心跳间隔",
                "b": "返回上级",
                "q": "退出程序"
            })

            choice = Prompt.ask("请选择", choices=["1", "2", "b", "q"], default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            elif choice == "1":
                self._prompt_bool(heartbeat_cfg, "enabled", "启用心跳")
            elif choice == "2":
                if heartbeat_cfg.enabled:
                    self._prompt_int(heartbeat_cfg, "interval_s", "心跳间隔 (秒)")
                else:
                    console.print("[yellow]请先启用心跳[/yellow]\n")

        self.current_path.pop()

    # ==================== Tools 菜单 ====================

    def tools_menu(self):
        self.current_path.append("Tools")
        config = load_config()

        while self.running:
            self.show_header("Tools - 工具配置")

            mcp_count = len(config.tools.mcp_servers)
            console.print(Panel.fit(
                f"[bold]Web 搜索 API Key:[/bold] {'已设置' if config.tools.web.search.api_key else '[red]未设置[/red]'}\n"
                f"[bold]命令执行超时:[/bold] {config.tools.exec.timeout}秒\n"
                f"[bold]限制工作区:[/bold] {'是' if config.tools.restrict_to_workspace else '否'}\n"
                f"[bold]MCP 服务器:[/bold] {mcp_count} 个",
                title="[当前配置]",
                border_style="cyan"
            ))
            console.print()

            self.show_menu({
                "1": "设置 Web 搜索",
                "2": "设置命令执行超时",
                "3": "切换工作区限制",
                "4": "管理 MCP 服务器",
                "b": "返回上级菜单",
                "q": "退出程序"
            })

            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "b", "q"], default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            elif choice == "1":
                self._configure_web_search(config.tools.web.search)
            elif choice == "2":
                self._prompt_int(config.tools.exec, "timeout", "超时时间 (秒)")
            elif choice == "3":
                self._prompt_bool(config.tools, "restrict_to_workspace", "限制工具只能在工作区内执行")
            elif choice == "4":
                self._mcp_servers_menu(config)

            save_config(config)

        self.current_path.pop()

    def _configure_web_search(self, search_cfg):
        console.print("\n[cyan]配置 Web 搜索[/cyan]")

        self._prompt_str(search_cfg, "api_key", "Brave Search API Key", is_password=True)
        self._prompt_int(search_cfg, "max_results", "最大结果数")

    def _mcp_servers_menu(self, config: Config):
        self.current_path.append("MCP 服务器")

        while self.running:
            self.show_header("MCP 服务器管理")

            mcp_servers = config.tools.mcp_servers
            if mcp_servers:
                table = Table(show_header=True)
                table.add_column("名称", style="cyan")
                table.add_column("类型", justify="center")
                table.add_column("配置")

                for name, cfg in mcp_servers.items():
                    server_type = "HTTP" if cfg.url else "Stdio"
                    if cfg.url:
                        conf_desc = f"URL: {cfg.url}"
                    else:
                        conf_desc = f"命令: {cfg.command} {' '.join(cfg.args)}"
                    table.add_row(name, server_type, conf_desc)

                console.print(table)
            else:
                console.print("[yellow]暂无 MCP 服务器配置[/yellow]")

            console.print()

            menu_options = {
                "a": "添加 MCP 服务器",
                "b": "返回上级",
                "q": "退出程序"
            }
            if mcp_servers:
                menu_options["d"] = "删除 MCP 服务器"

            self.show_menu(menu_options)

            choices = ["a", "d", "b", "q"] if mcp_servers else ["a", "b", "q"]
            choice = Prompt.ask("请选择", choices=choices, default="b")

            if choice == "b":
                break
            elif choice == "q":
                self.running = False
                return
            elif choice == "a":
                self._add_mcp_server(config)
            elif choice == "d" and mcp_servers:
                server_name = Prompt.ask("请输入要删除的服务器名称", choices=list(mcp_servers.keys()))
                del config.tools.mcp_servers[server_name]
                console.print(f"[green]✓[/green] {server_name} 已删除\n")

        self.current_path.pop()

    def _add_mcp_server(self, config: Config):
        console.print("\n[cyan]添加 MCP 服务器[/cyan]")

        name = Prompt.ask("服务器名称 (直接回车取消)", default="")
        if not name:
            console.print("[yellow]已取消[/yellow]\n")
            return
        if name in config.tools.mcp_servers:
            console.print(f"[red]✗[/red] 服务器 '{name}' 已存在\n")
            return

        from nanobot.config.schema import MCPServerConfig
        server_cfg = MCPServerConfig()

        server_type = Prompt.ask(
            "服务器类型 (直接回车使用默认)",
            choices=["stdio", "http"],
            default="stdio"
        )

        if server_type == "stdio":
            self._prompt_str(server_cfg, "command", "命令 (如 npx)", show_current=False)
            args_input = Prompt.ask("参数 (空格分隔，直接回车跳过)", default="")
            server_cfg.args = args_input.split() if args_input else []
        else:
            self._prompt_str(server_cfg, "url", "HTTP URL", show_current=False)
            if not server_cfg.url:
                console.print("[yellow]已取消[/yellow]\n")
                return

        self._prompt_int(server_cfg, "tool_timeout", "工具超时 (秒)", show_current=False)

        config.tools.mcp_servers[name] = server_cfg
        console.print(f"[green]✓[/green] MCP 服务器 '{name}' 已添加\n")

    # ==================== 显示当前配置 ====================

    def show_current_config(self):
        """显示当前配置摘要"""
        config = load_config()

        console.print("\n[cyan bold]>>> Nanobot 配置概览 <<<[/cyan bold]\n")
        console.print(f"[dim]配置文件: {get_config_path()}[/dim]\n")

        # Agents
        console.print(Panel.fit(
            f"[bold]模型:[/bold] {config.agents.defaults.model}\n"
            f"[bold]温度:[/bold] {config.agents.defaults.temperature}\n"
            f"[bold]工作区:[/bold] {config.agents.defaults.workspace}",
            title="[Agents]",
            border_style="cyan"
        ))
        console.print()

        # Providers
        provider_table = Table(title="[Providers]", show_header=True)
        provider_table.add_column("提供商", style="cyan", width=20)
        provider_table.add_column("状态", justify="center", width=10)

        for spec in PROVIDERS:
            provider_cfg = getattr(config.providers, spec.name, None)
            has_key = provider_cfg and bool(provider_cfg.api_key)
            status = "[green]OK[/green]" if has_key else "[red]--[/red]"
            provider_table.add_row(spec.label, status)

        console.print(provider_table)
        console.print()

        # Channels
        channel_table = Table(title="[Channels]", show_header=True)
        channel_table.add_column("渠道", style="cyan", width=12)
        channel_table.add_column("状态", justify="center", width=8)

        channels = [
            ("WhatsApp", config.channels.whatsapp.enabled),
            ("Telegram", config.channels.telegram.enabled),
            ("Discord", config.channels.discord.enabled),
            ("飞书", config.channels.feishu.enabled),
            ("钉钉", config.channels.dingtalk.enabled),
            ("Slack", config.channels.slack.enabled),
            ("QQ", config.channels.qq.enabled),
            ("Email", config.channels.email.enabled),
        ]

        for name, enabled in channels:
            status = "[green]ON[/green]" if enabled else "[red]OFF[/red]"
            channel_table.add_row(name, status)

        console.print(channel_table)
        console.print()

        # MCP 服务器
        mcp_servers = config.tools.mcp_servers
        if mcp_servers:
            mcp_table = Table(title="[MCP 服务器]", show_header=True)
            mcp_table.add_column("名称", style="cyan", width=20)
            mcp_table.add_column("类型", justify="center", width=10)
            mcp_table.add_column("配置", style="dim")
            mcp_table.add_column("超时", justify="right", width=8)

            for name, cfg in mcp_servers.items():
                server_type = "[cyan]HTTP[/cyan]" if cfg.url else "[cyan]Stdio[/cyan]"
                if cfg.url:
                    conf_desc = cfg.url
                else:
                    conf_desc = f"{cfg.command} {' '.join(cfg.args[:2])}{'...' if len(cfg.args) > 2 else ''}"
                timeout_desc = f"{cfg.tool_timeout}s"

                mcp_table.add_row(name, server_type, conf_desc, timeout_desc)

            console.print(mcp_table)
            console.print()
        else:
            console.print("[yellow]暂无 MCP 服务器配置[/yellow]")
            console.print()

    # ==================== 快速配置 ====================

    def quick_setup(self):
        """快速配置流程"""
        console.print("\n[cyan bold]>>> Nanobot 快速配置 <<<[/cyan bold]\n")
        console.print("[dim]这个向导将帮助你完成最基本的配置[/dim]\n")

        config = load_config()

        # 步骤 1: 选择提供商
        console.print("[bold yellow]步骤 1: 选择 LLM 提供商[/bold yellow]")
        console.print("可用的提供商:")
        for i, spec in enumerate(PROVIDERS, 1):
            console.print(f"  {i}. {spec.label}")

        provider_choice = Prompt.ask(
            "\n选择提供商 (输入数字)",
            choices=[str(i) for i in range(1, len(PROVIDERS) + 1)],
            default="1"
        )
        provider = PROVIDERS[int(provider_choice) - 1]

        # 步骤 2: 输入 API Key
        console.print(f"\n[bold yellow]步骤 2: 配置 {provider.label}[/bold yellow]")
        api_key = Prompt.ask(f"{provider.label} API Key", password=True)
        if api_key:
            provider_cfg = getattr(config.providers, provider.name)
            provider_cfg.api_key = api_key
            console.print(f"[dim]  → API Key 已设置[/dim]")

        # 步骤 3: 选择模型
        console.print("\n[bold yellow]步骤 3: 选择模型[/bold yellow]")
        model = Prompt.ask("模型名称", default=config.agents.defaults.model)
        config.agents.defaults.model = model
        console.print(f"[dim]  → 模型: {model}[/dim]")

        # 步骤 4: 配置渠道（可选）
        console.print("\n[bold yellow]步骤 4: 配置消息渠道 (可选)[/bold yellow]")
        configure_channel = Confirm.ask("是否配置消息渠道?", default=False)

        if configure_channel:
            console.print("\n可用渠道:")
            channels = ["Telegram", "WhatsApp", "Discord", "飞书", "钉钉"]
            for i, ch in enumerate(channels, 1):
                console.print(f"  {i}. {ch}")

            channel_choice = Prompt.ask(
                "选择渠道",
                choices=[str(i) for i in range(1, len(channels) + 1)],
                default="1"
            )
            channel_name = channels[int(channel_choice) - 1].lower()

            if channel_name == "telegram":
                config.channels.telegram.enabled = Confirm.ask("启用 Telegram?", default=False)
                if config.channels.telegram.enabled:
                    token = Prompt.ask("Bot Token", password=True)
                    config.channels.telegram.token = token

        # 保存配置
        save_config(config)

        # 完成
        console.print("\n[bold green]>>> 配置完成！ <<<[/bold green]\n")
        console.print("[dim]配置摘要:[/dim]")
        console.print(f"  提供商: [cyan]{provider.label}[/cyan]")
        console.print(f"  模型: [cyan]{model}[/cyan]")
        console.print(f"  温度: [cyan]{config.agents.defaults.temperature}[/cyan]")
        console.print()
        console.print("[dim]下一步:[/dim]")
        console.print("  1. 查看配置: [cyan]nanobot config show[/cyan]")
        console.print("  2. 启动网关: [cyan]nanobot gateway[/cyan]")
        console.print("  3. 完整配置: [cyan]nanobot config wizard[/cyan]")
        console.print()
