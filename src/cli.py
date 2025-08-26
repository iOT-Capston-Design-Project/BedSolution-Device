import os
import sys
import time
import logging
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
import datetime
from dataclasses import fields, asdict
from typing import get_type_hints

# Project Modules
from config_manager import config_manager
from api.api_client import APIClient
from heatmap.heatmap import PressureHeatmap
from detection.config import DetectionConfig
from serialcm.serial_communication import SerialCommunication
from detection.detection import Detection
from mllogging.mllogger import MLLogger


class BedSolutionCLI:

    def __init__(self):
        """Initializes the CLI application."""
        self.console = Console()
        self.config_manager = config_manager
        # APIClient를 설정의 기본값으로 초기화
        initial_server_url = self.config_manager.get_setting("Server", "url")
        initial_api_key = self.config_manager.get_setting("Server", "api_key")
        self.api_client = APIClient(initial_server_url, initial_api_key)
        self.title_art = """
██████╗ ███████╗██████╗     ███████╗ ██████╗ ██╗     ██╗   ██╗████████╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔══██╗    ██╔════╝██╔═══██╗██║     ██║   ██║╚══██╔══╝██║██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║  ██║    ███████╗██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║  ██║    ╚════██║██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██║╚██╗██║
██████╔╝███████╗██████╔╝    ███████║╚██████╔╝███████╗╚██████╔╝   ██║   ██║╚██████╔╝██║ ╚████║
╚═════╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
        """
        # 로깅 설정 초기화
        self._setup_logging()

    def _setup_logging(self):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        debug_mode = self.config_manager.get_setting("Logging", "debug_mode", "False").lower() == "true"
        log_level_str = self.config_manager.get_setting("Logging", "log_level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)
        
        if debug_mode:
            log_file = "bedsolution_debug.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logging.getLogger().addHandler(file_handler)
            
            logging.info("=== BedSolution Device Logging Started ===")
            logging.info(f"Debug mode: {debug_mode}")
            logging.info(f"Log level: {log_level_str}")
            logging.info(f"Log file: {log_file}")

    def _clear_screen(self):
        """Clears the console screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def _pause(self):
        """Waits for the user to press Enter."""
        self.console.input("\n[yellow]Press Enter to return...[/yellow]")

    def _get_server_config(self):
        """Fetches server configuration and device ID."""
        server_url = self.config_manager.get_setting("Server", "url")
        api_key = self.config_manager.get_setting("Server", "api_key")
        device_id = self.config_manager.get_setting("Device", "id")
        return server_url, api_key, device_id

    def _load_detection_config(self) -> DetectionConfig:
        """Loads detection settings from the config file, applying types."""
        config_values = {}
        # Create a default config instance to get field types and default values
        default_config = DetectionConfig()
        type_hints = get_type_hints(DetectionConfig)

        for field in fields(default_config):
            key = field.name
            # Get the value from config manager
            value_str = self.config_manager.get_setting("Detection", key)
            
            if value_str is not None:
                # If value exists in config, try to cast it to the correct type
                expected_type = type_hints[key]
                try:
                    if expected_type is bool:
                        # Handle boolean conversion for various string inputs
                        val = value_str.lower() in ('true', '1', 't', 'y', 'yes')
                    else:
                        # Cast to the appropriate type (int, float, str)
                        val = expected_type(value_str)
                    config_values[key] = val
                except (ValueError, TypeError):
                    # If casting fails, fall back to the default value
                    config_values[key] = getattr(default_config, key)
            else:
                # If value is not in config, use the default
                config_values[key] = getattr(default_config, key)

        return DetectionConfig(**config_values)

    def _run_ui(self):
        """Run Screen UI using Rich.Live for a smoother real-time display."""
        logging.info("Starting Run UI mode")
        self._clear_screen()

        server_url, api_key, device_id = self._get_server_config()

        if not all([server_url, api_key, device_id]):
            logging.error("Configuration incomplete - missing server URL, API key, or device ID")
            error_content = "[red]❗ Server URL, API Key, and Device ID must be configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
            self.console.print(Panel(error_content, title="[bold red]Configuration Incomplete[/bold red]", title_align="left"))
            self._pause()
            return

        self.console.print(Panel("[bold yellow]Run Mode[/bold yellow]", title="[bold green]Starting Real-time Display[/bold green]"))
        self.console.print("This mode will display real-time data for a duration and then return to the main menu.")
        self.console.print("Press Ctrl+C at any time to force quit the program.")
        self._pause()

        # Initialize Serial, Detection, and Heatmap
        serial_comm = SerialCommunication()

        if not serial_comm.start():
            logging.error("Failed to start serial communication")
            self._clear_screen()
            self.console.print(Panel(f"[red]❗ Error starting serial communication.[/red]", title="[bold red]Error[/bold red]", title_align="left"))
            self._pause()
            return

        detection_config = self._load_detection_config()
        detector = Detection(detection_config)
        heatmap_renderer = PressureHeatmap(detection_config)

        data_rows_buffer = []
        MAX_DATA_ROWS = 20

        layout = Layout()
        layout.split(
            Layout(name="header", size=4),
            Layout(name="main_content", ratio=1)
        )
        layout["main_content"].split_row(
            Layout(name="heatmap_display", ratio=2),
            Layout(name="data_stream", ratio=3)
        )

        sync_status = True  # Simulate sync status

        try:
            with Live(layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible") as live:
                for ts, head_raw, body_raw in serial_comm.stream():
                    # Simulate sync status toggle
                    sync_status = not sync_status
                    status_text = "[green]Syncing with server...[/green]" if sync_status else "[red]Local storage (offline)...[/red]"

                    # Construct and update the header
                    header_content = Text.assemble(
                        Text(f"Run [Device ID: ", style="bold"),
                        Text(f"{device_id}", style="cyan"),
                        Text("]\n", style="bold"),
                        Text("Status: ", style="bold"),
                        Text.from_markup(status_text),
                        Text("\nPress Ctrl+C to exit.", style="dim yellow")
                    )
                    layout["header"].update(
                        Panel(header_content, title="[bold green]Current Session[/bold green]", title_align="left"))

                    # Run detection
                    detection_result = detector.detect(head_raw, body_raw)

                    # Extract pressures for table and API
                    head_pressure = detection_result['head'][2] if detection_result['head'] else 0
                    shoulder_pressure = detection_result['shoulder'][2] if detection_result['shoulder'] else 0
                    hip_pressure = detection_result['hip'][2] if detection_result['hip'] else 0
                    heel_pressure = max(h[2] for h in detection_result['heels']) if detection_result['heels'] else 0

                    # Update data buffer
                    data_rows_buffer.append((
                        datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                        f"{head_pressure:.2f}",
                        f"{shoulder_pressure:.2f}",
                        "N/A",  # Elbow
                        f"{hip_pressure:.2f}",
                        f"{heel_pressure:.2f}"
                    ))
                    if len(data_rows_buffer) > MAX_DATA_ROWS:
                        data_rows_buffer.pop(0)

                    # Create and update the real-time data table
                    realtime_table = Table(show_header=True, show_edge=False, show_lines=False, box=None)
                    realtime_table.add_column("Time", style="dim")
                    realtime_table.add_column("Occiput", justify="right", style="green")
                    realtime_table.add_column("Scapula", justify="right", style="green")
                    realtime_table.add_column("Elbow", justify="right", style="green")
                    realtime_table.add_column("Hip", justify="right", style="green")
                    realtime_table.add_column("Heel", justify="right", style="green")
                    for row_data in data_rows_buffer:
                        realtime_table.add_row(str(row_data[0]), str(row_data[1]), str(row_data[2]), str(row_data[3]), str(row_data[4]), str(row_data[5]))
                    for _ in range(MAX_DATA_ROWS - len(data_rows_buffer)):
                        realtime_table.add_row("", "", "", "", "", "")

                    data_panel = Panel(realtime_table, title="Real-time Data", height=MAX_DATA_ROWS + 2)
                    layout["data_stream"].update(data_panel)

                    # Update heatmap
                    head_coords = detection_result['head']
                    shoulder_coords = detection_result['shoulder']
                    hip_coords = detection_result['hip']
                    heels_coords = detection_result['heels']
                    threshold_val = detection_result['threshold']

                    heatmap_panel = heatmap_renderer.render(head_raw, body_raw, head_coords, shoulder_coords, hip_coords, heels_coords, threshold_val)
                    heatmap_panel.height = MAX_DATA_ROWS + 2
                    layout["heatmap_display"].update(heatmap_panel)

                    # Simulate data sending
                    if sync_status:
                        self.api_client.send_data(None, None, device_id, {
                            "occiput": head_pressure, 
                            "scapula": shoulder_pressure, 
                            "elbow": 0, # Not detected
                            "hip": hip_pressure, 
                            "heel": heel_pressure
                        })

        except KeyboardInterrupt:
            pass
        finally:
            self._clear_screen()
            self.console.print(Panel("[bold green]Run session ended. Returning to main menu.[/bold green]",
                                title="[bold yellow]Session Complete[/bold yellow]"))
            self._pause()

    def _display_log_details(self, date: str):
        """Fetches and displays the detailed logs for a specific date."""
        self._clear_screen()
        server_url, api_key, device_id = self._get_server_config()
        with self.console.status(f"[bold green]Fetching details for {date}...", spinner="dots"):
            time.sleep(1)
            details = self.api_client.get_log_details(None, None, device_id, date)

        if not details:
            self.console.print(Panel(f"No detailed logs found for [cyan]{date}[/cyan].", title="[bold red]Not Found[/bold red]"))
            self._pause()
            return

        table = Table(title=f"Detailed Log for {date}")
        headers = details[0].keys()
        for header in headers:
            table.add_column(header.capitalize(), justify="right", style="cyan")

        for item in details:
            table.add_row(*[str(value) for value in item.values()])

        self.console.print(table)
        self._pause()

    def _logs_ui(self):
        """Log Viewer UI"""
        self._clear_screen()
        server_url, api_key, device_id = self._get_server_config()

        if not all([server_url, api_key, device_id]):
            error_content = "[red]❗ Server URL, API Key, and Device ID must be configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
            self.console.print(Panel(error_content, title="[bold red]Configuration Incomplete[/bold red]", title_align="left"))
            self._pause()
            return

        while True:
            self._clear_screen()
            self.console.print(Panel("View Logs", title="Function"))
            self.console.print()

            with self.console.status("[bold green]Fetching available log dates...", spinner="dots"):
                time.sleep(1)
                logs_summary = self.api_client.get_logs_by_date(device_id)

            if not logs_summary:
                self.console.print(Panel("No log dates found for this device.", title="[bold red]Not Found[/bold red]"))
                self._pause()
                break

            dates = [log['datetime'] for log in logs_summary]
            choices = dates + ["q. Back to Main Menu"]

            choice = questionary.select(
                "Select a date to view details, or go back:",
                choices=choices,
                use_indicator=True
            ).ask()

            if choice is None or choice == "q. Back to Main Menu":
                break
            else:
                self._display_log_details(choice)

    def _register_device_ui(self):
        """Device Registration UI"""
        self._clear_screen()

        panel_title = "[bold cyan]Device Registration[/bold cyan]"
        device_id = self.config_manager.get_setting("Device", "id")

        if device_id:
            panel_content = f"An existing device is already registered: [cyan]{device_id}[/cyan]"
            self.console.print(Panel(panel_content, title=panel_title, title_align="left"))
            self.console.print()
            confirm = questionary.confirm("Would you like to register a new device?", default=False).ask()
            if not confirm:
                return
            self._clear_screen()

        server_url, api_key, _ = self._get_server_config()

        if not server_url or not api_key:
            error_content = "[red]❗ Server URL and API Key are not configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
            self.console.print(Panel(error_content, title="[bold red]Error[/bold red]", title_align="left"))
            self._pause()
            return

        with self.console.status("[bold green]Registering device with the server...", spinner="dots"):
            time.sleep(2)
            new_device_id = self.api_client.register_device(None, None)
            result_panel = None
            if new_device_id:
                self.config_manager.update_setting("Device", "id", new_device_id)
                result_content = f"[green]✔ Device registered successfully.[/green]\n- New Device ID: [cyan]{new_device_id}[/cyan]"
                result_panel = Panel(result_content, title="[bold green]Registration Successful[/bold green]", title_align="left")
            else:
                result_content = "[red]❗ Device registration failed.[/red]"
                result_panel = Panel(result_content, title="[bold red]Registration Failed[/bold red]", title_align="left")
        
        self.console.print(result_panel)
        self._pause()

    def _detection_settings_ui(self):
        """Detection Settings Screen UI"""
        while True:
            self._clear_screen()

            # Load current config and prepare display
            loaded_config = self._load_detection_config()
            defaults = DetectionConfig()
            type_hints = get_type_hints(DetectionConfig)
            current_settings = asdict(loaded_config)
            default_settings = asdict(defaults)

            # Create a table to display settings
            table = Table(title="[bold cyan]Detection Settings[/bold cyan]")
            table.add_column("Setting", style="green")
            table.add_column("Current Value", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Default", style="dim")

            choices = []
            for i, (key, value) in enumerate(current_settings.items()):
                type_name = type_hints[key].__name__
                default_value = default_settings[key]
                table.add_row(key, str(value), type_name, str(default_value))
                choices.append(f"{i + 1}. Change {key}")

            choices.append("q. Return to Settings")
            
            self.console.print(table)
            self.console.print()

            # Prompt user for action
            choice = questionary.select(
                "Select an action:",
                choices=choices,
                use_indicator=True
            ).ask()

            if choice is None or choice == "q. Return to Settings":
                break

            # Extract setting key from choice
            setting_key = choice.split(" ", 2)[2]
            field_type = type_hints[setting_key]
            current_value = current_settings[setting_key]

            # Prompt for new value
            new_value_str = questionary.text(
                f"Enter new value for '{setting_key}' ({field_type.__name__}):",
                default=str(current_value)
            ).ask()

            if new_value_str is None:
                continue

            # Validate and save the new value
            try:
                if field_type is bool:
                    new_value = new_value_str.lower() in ('true', '1', 't', 'y', 'yes')
                else:
                    new_value = field_type(new_value_str)
                
                self.config_manager.update_setting("Detection", setting_key, str(new_value))
                self.console.print(f"[green]✔ '{setting_key}' updated successfully.[/green]")
                self._pause()

            except (ValueError, TypeError):
                self.console.print(f"[red]❗ Invalid value. Please enter a valid {field_type.__name__}.[/red]")
                self._pause()

    def _settings_ui(self):
        """Settings Screen UI"""
        logging.info("Opening Settings UI")
        while True:
            self._clear_screen()

            server_url = self.config_manager.get_setting("Server", "url", "Not set")
            api_key = self.config_manager.get_setting("Server", "api_key", "Not set")
            log_filename = self.config_manager.get_setting("Logging", "heatmap_log_file", "heatmap_log.csv")
            debug_mode = self.config_manager.get_setting("Logging", "debug_mode", "False")
            log_level = self.config_manager.get_setting("Logging", "log_level", "INFO")

            masked_api_key = "**********" + api_key[-4:] if len(api_key) > 4 else api_key

            settings_text = (
                f"- Server URL: [cyan]{server_url}[/cyan]\n"
                f"- API Key:  [cyan]{masked_api_key}[/cyan]\n"
                f"- Log File: [cyan]{log_filename}[/cyan]\n"
                f"- Debug Mode: [cyan]{debug_mode}[/cyan]\n"
                f"- Log Level: [cyan]{log_level}[/cyan]"
            )
            
            self.console.print(Panel(settings_text, title="[bold cyan]Settings[/bold cyan]", title_align="left"))
            self.console.print()

            choice = questionary.select(
                "Select an action:",
                choices=[
                    "1. Change Server URL",
                    "2. Change API Key",
                    "3. Change Log File Name",
                    "4. Toggle Debug Mode",
                    "5. Change Log Level",
                    "6. Detection Settings",
                    "7. Delete All Settings",
                    "q. Return to Main Menu",
                ],
                use_indicator=True
            ).ask()

            if choice is None or choice == "q. Return to Main Menu":
                break

            elif choice == "1. Change Server URL":
                new_url = questionary.text(
                    "Enter the new server URL:", default=server_url if server_url != "Not set" else ""
                ).ask()
                if new_url:
                    self.config_manager.update_setting("Server", "url", new_url)
                    logging.info(f"Server URL updated to: {new_url}")
                    self.console.print("[green]✔ Server URL saved successfully.[/green]")
                    # 변경된 설정을 반영하여 APIClient 재초기화
                    refreshed_api_key = self.config_manager.get_setting("Server", "api_key")
                    self.api_client = APIClient(new_url, refreshed_api_key)
                    self._pause()

            elif choice == "2. Change API Key":
                new_key = questionary.password("Enter the new API Key:").ask()
                if new_key:
                    self.config_manager.update_setting("Server", "api_key", new_key)
                    logging.info("API Key updated")
                    self.console.print("[green]✔ API Key saved successfully.[/green]")
                    # 변경된 설정을 반영하여 APIClient 재초기화
                    refreshed_server_url = self.config_manager.get_setting("Server", "url")
                    self.api_client = APIClient(refreshed_server_url, new_key)
                    self._pause()

            elif choice == "3. Change Log File Name":
                new_log_filename = questionary.text(
                    "Enter the new log file name:", default=log_filename
                ).ask()
                if new_log_filename:
                    self.config_manager.update_setting("Logging", "heatmap_log_file", new_log_filename)
                    logging.info(f"Log file name updated to: {new_log_filename}")
                    self.console.print("[green]✔ Log file name saved successfully.[/green]")
                    self._pause()

            elif choice == "4. Toggle Debug Mode":
                current_debug = debug_mode.lower() == "true"
                new_debug_mode = questionary.confirm(
                    f"Current debug mode: {'ON' if current_debug else 'OFF'}\nEnable debug mode?",
                    default=not current_debug
                ).ask()
                if new_debug_mode is not None:
                    new_debug_str = "True" if new_debug_mode else "False"
                    self.config_manager.update_setting("Logging", "debug_mode", new_debug_str)
                    logging.info(f"Debug mode {'enabled' if new_debug_mode else 'disabled'}")
                    self.console.print(f"[green]✔ Debug mode {'enabled' if new_debug_mode else 'disabled'} successfully.[/green]")
                    self.console.print("[yellow]Note: Restart the application for logging changes to take effect.[/yellow]")
                    self._pause()

            elif choice == "5. Change Log Level":
                log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                current_level = log_level.upper()
                if current_level not in log_levels:
                    current_level = "INFO"
                
                new_log_level = questionary.select(
                    "Select log level:",
                    choices=log_levels,
                    default=current_level
                ).ask()
                if new_log_level:
                    self.config_manager.update_setting("Logging", "log_level", new_log_level)
                    logging.info(f"Log level changed to: {new_log_level}")
                    self.console.print(f"[green]✔ Log level changed to {new_log_level} successfully.[/green]")
                    self.console.print("[yellow]Note: Restart the application for logging changes to take effect.[/yellow]")
                    self._pause()

            elif choice == "6. Detection Settings":
                self._detection_settings_ui()

            elif choice == "7. Delete All Settings":
                confirm = questionary.confirm(
                    "Are you sure you want to delete all settings? This action cannot be undone.", default=False
                ).ask()
                if confirm:
                    logging.warning("All settings deleted by user")
                    self.config_manager.delete_all_settings()
                    self.console.print("[green]✔ All settings have been deleted.[/green]")
                    self._pause()

    def _model_training_logs_ui(self):
        """Model Training Logs UI - Real-time data collection for model training"""
        logging.info("Starting Model Training Logs UI mode")
        self._clear_screen()

        self.console.print(Panel("[bold yellow]Model Training Logs Mode[/bold yellow]", title="[bold green]Starting Real-time Data Collection[/bold green]"))
        self.console.print("This mode will collect real-time sensor data for model training.")
        self.console.print("Press Ctrl+C to save logs and return to the main menu.")
        self._pause()

        # Initialize Serial Communication and MLLogger
        serial_comm = SerialCommunication()
        
        # 설정에서 로그 파일명 가져오기 (기본값: heatmap_log.csv)
        log_filename = self.config_manager.get_setting("Logging", "heatmap_log_file", fallback="heatmap_log.csv")
        mllogger = MLLogger(log_filename)
        
        if not serial_comm.start():
            self._clear_screen()
            self.console.print(Panel(f"[red]❗ Error starting serial communication.[/red]", title="[bold red]Error[/bold red]", title_align="left"))
            self._pause()
            return

        # Get current log file path and info
        log_file_path = os.path.abspath(log_filename)
        buffer_count = 0

        layout = Layout()
        layout.split(
            Layout(name="header", size=6),
            Layout(name="main_content", ratio=1)
        )
        layout["main_content"].split_row(
            Layout(name="data_stream", ratio=1)
        )

        data_rows_buffer = []
        MAX_DATA_ROWS = 20

        try:
            with Live(layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible") as live:
                for ts, head_raw, body_raw in serial_comm.stream():
                    mllogger.log_heatmap(head_raw, body_raw)

                    header_content = Text.assemble(
                        Text("Model Training Logs [", style="bold"),
                        Text("Real-time Collection", style="cyan"),
                        Text("]\n", style="bold"),
                        Text(f"Log File: ", style="bold"),
                        Text(f"{log_file_path}", style="cyan"),
                        Text(f"\nBuffer Count: ", style="bold"),
                        Text(f"{len(mllogger.buffer)}", style="yellow"),
                        Text("\nMax Display: ", style="bold"),
                        Text(f"{MAX_DATA_ROWS} rows", style="dim"),
                        Text("\nPress Ctrl+C to save and exit.", style="dim yellow")
                    )
                    layout["header"].update(
                        Panel(header_content, title="[bold green]Data Collection Session[/bold green]", title_align="left"))

                    # Create data row for display with individual array elements
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                    
                    # Extract head and body array values
                    head_values = [f"{float(val):.2f}" for val in head_raw.flatten()]
                    body_values = [f"{float(val):.2f}" for val in body_raw.flatten()]
                    
                    # Create row with timestamp, head values, body values (최대 8개씩 제한)
                    max_head_cols = min(len(head_values), 2)
                    max_body_cols = min(len(body_values), 4)
                    row_data = [timestamp] + head_values[:max_head_cols] + body_values[:max_body_cols]
                    data_rows_buffer.append(row_data)
                    
                    if len(data_rows_buffer) > MAX_DATA_ROWS:
                        data_rows_buffer.pop(0)

                    # Create and update the real-time data table
                    realtime_table = Table(show_header=True, show_edge=False, show_lines=False, box=None)
                    realtime_table.add_column("Timestamp", style="dim")
                    
                    for i in range(max_head_cols):
                        realtime_table.add_column(f"Head_{i}", justify="right", style="green")
                    
                    for i in range(max_body_cols):
                        realtime_table.add_column(f"Body_{i}", justify="right", style="blue")
                    
                    for row_data in data_rows_buffer:
                        realtime_table.add_row(*[str(cell) for cell in row_data])
                    
                    # Fill empty rows to maintain table height
                    for _ in range(MAX_DATA_ROWS - len(data_rows_buffer)):
                        empty_row = [""] * (1 + max_head_cols + max_body_cols)  # timestamp + head + body
                        realtime_table.add_row(*empty_row)

                    data_panel = Panel(realtime_table, title="Real-time Training Data", height=MAX_DATA_ROWS + 2)
                    layout["data_stream"].update(data_panel)

        except KeyboardInterrupt:
            pass
        finally:
            self._clear_screen()
            self.console.print(Panel("[bold green]Model training session ended. Logs saved. Returning to main menu.[/bold green]",
                                title="[bold yellow]Session Complete[/bold yellow]"))
            try:
                saved_path = mllogger.save()
                if saved_path:
                    self.console.print(f"[green]✔ Logs saved successfully to: {saved_path}[/green]")
                else:
                    self.console.print("[yellow]⚠ No data to save.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]❗ Error saving logs: {e}[/red]")
            
            self._pause()

    def run(self):
        """Main function to run the CLI applicatio  n."""
        logging.info("BedSolution CLI application started")
        while True:
            self._clear_screen()
            self.console.print(Align.center(f"[dark_orange]{self.title_art}[/dark_orange]"))
            self.console.print()

            choice = questionary.select(
                "Select an option:",
                choices=[
                    "1. Run",
                    "2. View Logs",
                    "3. Model Training Logs",
                    "4. Register Device",
                    "5. Settings",
                    "q. Quit",
                ],
                use_indicator=True
            ).ask()

            if choice is None:
                self.console.print("[bold yellow]No input detected, this can happen in non-interactive shells. Exiting.[/bold yellow]")
                time.sleep(2)
                break
            elif choice == "1. Run":
                logging.info("User selected: Run")
                self._run_ui()
            elif choice == "2. View Logs":
                logging.info("User selected: View Logs")
                self._logs_ui()
            elif choice == "3. Model Training Logs":
                logging.info("User selected: Model Training Logs")
                self._model_training_logs_ui()
            elif choice == "4. Register Device":
                logging.info("User selected: Register Device")
                self._register_device_ui()
            elif choice == "5. Settings":
                logging.info("User selected: Settings")
                self._settings_ui()
            elif choice == "q. Quit":
                logging.info("User selected: Quit - Exiting application")
                break

        logging.info("BedSolution CLI application exiting")
        self.console.print("\nExiting program.")
        sys.exit(0)


if __name__ == "__main__":
    cli = BedSolutionCLI()
    cli.run()
