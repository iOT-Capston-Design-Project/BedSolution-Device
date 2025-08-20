import os
import sys
import time
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.layout import Layout
from rich.columns import Columns
from rich.text import Text
from rich.live import Live
import random
import numpy as np
import datetime

# Project Modules
from config_manager import config_manager
import api_client
from heatmap.heatmap import PressureHeatmap
from detection.config import Config

console = Console()

def clear_screen():
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    """Waits for the user to press Enter."""
    console.input("\n[yellow]Press Enter to return...[/yellow]")

def run_ui():
    """Run Screen UI using Rich.Live for a smoother real-time display."""
    clear_screen()

    # Check for prerequisites
    server_url = config_manager.get_setting("Server", "url")
    api_key = config_manager.get_setting("Server", "api_key")
    device_id = config_manager.get_setting("Device", "id")

    if not all([server_url, api_key, device_id]):
        error_content = "[red]❗ Server URL, API Key, and Device ID must be configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
        console.print(Panel(error_content, title="[bold red]Configuration Incomplete[/bold red]", title_align="left"))
        pause()
        return

    console.print(Panel("[bold yellow]Run Mode[/bold yellow]", title="[bold green]Starting Real-time Display[/bold green]"))
    console.print("This mode will display real-time data for a duration and then return to the main menu.")
    console.print("Press Ctrl+C at any time to force quit the program.")
    pause()  # Wait for user to acknowledge before starting

    # Initialize Heatmap Renderer
    heatmap_config = Config(value_min=0, value_max=1000)  # Use appropriate min/max values
    heatmap_renderer = PressureHeatmap(heatmap_config)

    # Real-time data buffer
    data_rows_buffer = []  # Stores (timestamp, pressure) tuples
    MAX_DATA_ROWS = 20

    # Main layout for Live display
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
        with Live(layout, console=console, screen=True, redirect_stderr=False, vertical_overflow="visible") as live:
            while True:
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

                # Simulate new data point
                data_rows_buffer.append((datetime.datetime.now().strftime("%H:%M:%S"), random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)))
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
                    realtime_table.add_row(row_data[0], str(row_data[1]), str(row_data[2]), str(row_data[3]), str(row_data[4]), str(row_data[5]))
                # Pad with empty rows
                for _ in range(MAX_DATA_ROWS - len(data_rows_buffer)):
                    realtime_table.add_row("", "")

                data_panel = Panel(realtime_table, title="Real-time Data", height=MAX_DATA_ROWS + 2)
                layout["data_stream"].update(data_panel)

                # Simulate and render heatmap
                H_data = np.random.rand(5, 5) * 1000
                B_data = np.random.rand(10, 10) * 1000
                head_coords = (random.uniform(0, 4), random.uniform(0, 4),
                               random.randint(100, 500)) if random.random() > 0.5 else None
                shoulder_coords = (random.uniform(0, 9), random.uniform(0, 9), random.randint(100, 500))
                hip_coords = (random.uniform(0, 9), random.uniform(0, 9), random.randint(100, 500))
                heels_coords = [(random.uniform(0, 9), random.uniform(0, 9), random.randint(100, 500)) for _ in
                                range(random.randint(0, 2))]
                threshold_val = 500

                heatmap_panel = heatmap_renderer._render(
                    H_data, B_data,
                    heatmap_renderer._overlay_heatmap(head_coords, shoulder_coords, hip_coords, heels_coords),
                    threshold_val
                )
                heatmap_panel.height = MAX_DATA_ROWS + 2
                layout["heatmap_display"].update(heatmap_panel)

                # Simulate data sending
                if sync_status:
                    api_client.send_data(server_url, api_key, device_id, {"occiput": random.randint(0, 100), "scapula": random.randint(0, 100), "elbow": random.randint(0, 100), "hip": random.randint(0, 100), "heel": random.randint(0, 100)})

                time.sleep(1)
    except KeyboardInterrupt:
        # Catch Ctrl+C to exit gracefully from the live display
        pass
    finally:
        # This block ensures that the screen is cleared and the session end message is shown
        # even if the loop is interrupted.
        clear_screen()
        console.print(Panel("[bold green]Run session ended. Returning to main menu.[/bold green]",
                            title="[bold yellow]Session Complete[/bold yellow]"))
        pause()

def display_log_details(date: str, server_url: str, api_key: str, device_id: str):
    """Fetches and displays the detailed logs for a specific date."""
    clear_screen()
    with console.status(f"[bold green]Fetching details for {date}...", spinner="dots") as status:
        time.sleep(1) # Simulate network delay
        details = api_client.get_log_details(server_url, api_key, device_id, date)

    if not details:
        console.print(Panel(f"No detailed logs found for [cyan]{date}[/cyan].", title="[bold red]Not Found[/bold red]"))
        pause()
        return

    table = Table(title=f"Detailed Log for {date}")
    headers = details[0].keys()
    for header in headers:
        table.add_column(header.capitalize(), justify="right", style="cyan")

    for item in details:
        table.add_row(*[str(value) for value in item.values()])

    console.print(table)
    pause()

def logs_ui():
    """Log Viewer UI"""
    clear_screen()
    # Check for prerequisites
    server_url = config_manager.get_setting("Server", "url")
    api_key = config_manager.get_setting("Server", "api_key")
    device_id = config_manager.get_setting("Device", "id")

    if not all([server_url, api_key, device_id]):
        error_content = "[red]❗ Server URL, API Key, and Device ID must be configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
        console.print(Panel(error_content, title="[bold red]Configuration Incomplete[/bold red]", title_align="left"))
        pause()
        return

    while True:
        clear_screen()
        console.print(Panel("View Logs", title="Function"))
        console.print()

        with console.status("[bold green]Fetching available log dates...", spinner="dots") as status:
            time.sleep(1) # Simulate network delay
            logs_summary = api_client.get_logs_by_date(server_url, api_key, device_id)

        if not logs_summary:
            console.print(Panel("No log dates found for this device.", title="[bold red]Not Found[/bold red]"))
            pause()
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
            display_log_details(choice, server_url, api_key, device_id)

def register_device_ui():
    """Device Registration UI"""
    clear_screen()

    panel_title = "[bold cyan]Device Registration[/bold cyan]"
    device_id = config_manager.get_setting("Device", "id")

    if device_id:
        panel_content = f"An existing device is already registered: [cyan]{device_id}[/cyan]"
        console.print(Panel(panel_content, title=panel_title, title_align="left"))
        console.print()
        confirm = questionary.confirm("Would you like to register a new device?", default=False).ask()
        if not confirm:
            return
        clear_screen()

    # Check for server settings before proceeding
    server_url = config_manager.get_setting("Server", "url")
    api_key = config_manager.get_setting("Server", "api_key")

    if not server_url or not api_key:
        error_content = "[red]❗ Server URL and API Key are not configured.[/red]\n\nPlease complete the configuration in 'Settings' and 'Register Device' first."
        console.print(Panel(error_content, title="[bold red]Error[/bold red]", title_align="left"))
        pause()
        return

    with console.status("[bold green]Registering device with the server...", spinner="dots") as status:
        time.sleep(2)  # Simulate network delay
        new_device_id = api_client.register_device(server_url, api_key)
        result_panel = None
        if new_device_id:
            config_manager.update_setting("Device", "id", new_device_id)
            result_content = f"[green]✔ Device registered successfully.[/green]\n- New Device ID: [cyan]{new_device_id}[/cyan]"
            result_panel = Panel(result_content, title="[bold green]Registration Successful[/bold green]", title_align="left")
        else:
            result_content = "[red]❗ Device registration failed.[/red]"
            result_panel = Panel(result_content, title="[bold red]Registration Failed[/bold red]", title_align="left")
    
    console.print(result_panel)
    pause()

def settings_ui():
    """Settings Screen UI"""
    while True:
        clear_screen()

        # Get current settings
        server_url = config_manager.get_setting("Server", "url", "Not set")
        api_key = config_manager.get_setting("Server", "api_key", "Not set")

        # Mask the API Key
        masked_api_key = "**********" + api_key[-4:] if len(api_key) > 4 else api_key

        # Prepare the text for the panel
        settings_text = (
            f"- Server URL: [cyan]{server_url}[/cyan]\n"
            f"- API Key:  [cyan]{masked_api_key}[/cyan]"
        )
        
        # Print the settings panel
        console.print(Panel(settings_text, title="[bold cyan]Settings[/bold cyan]", title_align="left"))
        console.print()

        choice = questionary.select(
            "Select an action:",
            choices=[
                "1. Change Server URL",
                "2. Change API Key",
                "3. Delete All Settings",
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
                config_manager.update_setting("Server", "url", new_url)
                console.print("[green]✔ Server URL saved successfully.[/green]")
                pause()

        elif choice == "2. Change API Key":
            new_key = questionary.password("Enter the new API Key:").ask()
            if new_key:
                config_manager.update_setting("Server", "api_key", new_key)
                console.print("[green]✔ API Key saved successfully.[/green]")
                pause()

        elif choice == "3. Delete All Settings":
            confirm = questionary.confirm(
                "Are you sure you want to delete all settings? This action cannot be undone.", default=False
            ).ask()
            if confirm:
                config_manager.delete_all_settings()
                console.print("[green]✔ All settings have been deleted.[/green]")
                pause()

def main():
    """Main function"""
    title_art = """
██████╗ ███████╗██████╗     ███████╗ ██████╗ ██╗     ██╗   ██╗████████╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔══██╗    ██╔════╝██╔═══██╗██║     ██║   ██║╚══██╔══╝██║██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║  ██║    ███████╗██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║  ██║    ╚════██║██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██║╚██╗██║
██████╔╝███████╗██████╔╝    ███████║╚██████╔╝███████╗╚██████╔╝   ██║   ██║╚██████╔╝██║ ╚████║
╚═════╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
    """
    while True:
        clear_screen()
        console.print(Align.center(f"[dark_orange]{title_art}[/dark_orange]"))
        console.print()

        choice = questionary.select(
            "Select an option:",
            choices=[
                "1. Run",
                "2. View Logs",
                "3. Register Device",
                "4. Settings",
                "q. Quit",
            ],
            use_indicator=True
        ).ask()

        if choice is None: # User pressed Ctrl+C
            break
        elif choice == "1. Run":
            run_ui()
        elif choice == "2. View Logs":
            logs_ui()
        elif choice == "3. Register Device":
            register_device_ui()
        elif choice == "4. Settings":
            settings_ui()
        elif choice == "q. Quit":
            break

    console.print("\nExiting program.")
    sys.exit(0)

if __name__ == "__main__":
    main()
