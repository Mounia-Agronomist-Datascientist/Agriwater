"""
This script displays a synthetic and actionnable report.

Author: Mounia Tonazzini
Date: December 2025
"""

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table


def display_complete_agronomic_summary(console: Console, summary: dict) -> None:
    """
    Displays an actionable irrigation report.
    """

    # 1. Header
    # Header de Statut (Plus grand et stylisé)
    status_style = "bold white on red" if summary["irrigation_required"] else "bold white on green"
    status_text = " IRRIGATION REQUIRED " if summary["irrigation_required"] else " NO IRRIGATION NEEDED "
    
    header_panel = Panel(
        Text(f"\n{status_text}\n", justify="center", style=status_style),
        title="[bold blue]Decision Support[/bold blue]",
        width=40,
        padding=(0, 1)
    )
    centered_header = Align.center(header_panel)

    # 2. Site & Crop Context
    context_table = Table.grid(expand=False, padding=(0, 2))
    context_table.add_column(style="bold cyan", justify="right")
    context_table.add_column(justify="left")
    
    context_table.add_row("Crop:", f"{summary['crop_name'].title()} ({summary['crop_stage'].replace('_', ' ').title()})")
    context_table.add_row("Area:", f"{summary['surface_ha']:.1f} ha")
    context_table.add_row("Period:", f"Last {summary['period_days']} days")
    context_table.add_row("Efficiency:", f"{summary.get('efficiency', 0.85)*100:.0f}%")
    centered_context = Align.center(context_table)

    console.print()

    # 3. Water Balance Chart (with bar outlines)
    etc = summary["total_etc_mm"]
    precip = summary["total_precip_mm"]
    irrigation = summary["recommended_mm"]
    max_val = max(etc, precip, irrigation, 10) # Minimum scale of 10mm

    def get_bar(value: float, max_v: float, width: int = 25) -> str:
        filled = int((value / max_v) * width)
        # Using ░ for empty track and █ for filled bar to show the "contour"
        return f"[green]{'█' * filled}[/green][grey37]{'░' * (width - filled)}[/grey37]"

    # Using a Table to ensure vertical alignment of labels, bars, and values
    chart_table = Table.grid(padding=(0, 1))
    chart_table.add_column(width=15, justify="right", style="bold") # Label
    chart_table.add_column()  # Bar
    chart_table.add_column(justify="right", width=10) # Value
    
    chart_table.add_row("Crop Demand", get_bar(etc, max_val), f"{etc:>5.1f} mm")
    chart_table.add_row("Net Rainfall", get_bar(precip, max_val), f"{precip:>5.1f} mm")
    chart_table.add_row("Water Need", get_bar(irrigation, max_val), f"{irrigation:>5.1f} mm")
    centered_chart = Align.center(chart_table)


    # 4. Final Recommendation & Volumes
    if summary["irrigation_required"]:

        # Table to align Status and recommendation to the left
        footer_table = Table.grid(padding=(0, 1))
        footer_table.add_column()

        # Status block
        status_msg= Text.assemble(
            ("\n\nSTATUS", "bold red"),
            (f"\nWater balance is negative ({summary['water_balance_mm']:.1f} mm).\nThe total precipitation over the last {summary['period_days']} days \nis not enough to cover your crop water needs.", 
            "red")
        )

        # Recommendation block
        vol_info = Text.assemble(
            ("\n\nRECOMMENDATION", "bold red"),
            (f"\nRecommended application rate: {summary['recommended_m3_per_ha']:.0f} m³ per hectare. \nTotal volume required for this field: {summary['recommended_total_m3']:.0f} m³.", 
            "red")
        )
        footer_table.add_row(status_msg)
        footer_table.add_row(vol_info)
        footer_content = Align.center(footer_table)

    else:
        status_msg = Text.assemble(
            ("\n\nSTATUS", "bold green"),
            (f"\n\nWater balance is positive (+{summary['water_balance_mm']:.1f} mm).\nThe total precipitation over the last {summary['period_days']} days \nis enough to cover your crop water needs.", 
            "green")
        )
        footer_content = Align.center(status_msg)
        
    # Assemble Global Report    
    report_content = Group(
        Text("\n"), 
        centered_header,
        Text("\n"),
        centered_context,
        Text("\n" + "─" * 50 + "\n", justify="center", style="grey37"),
        Text("WATER BALANCE\n", justify="center", style="bold"),
        centered_chart,
        footer_content,
        Text("\n") 
    )

    # Global panel with a frame
    global_report = Panel(
        report_content,
        title="[bold]AGRIWATER COMPLETE REPORT[/bold]",
        border_style="bright_blue",
        expand=False,
        padding=(1, 4)
    )

    console.print("\n") 
    console.print(Align.center(global_report))
