"""
AgriWater - Irrigation Needs Calculator
Main interactive CLI entry point.

Author: Mounia Tonazzini
Date: December 2025
"""

import logging
from agriwater.cli.interface import AgriWaterCLI


def main():
    """Main entry point for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )
    cli = AgriWaterCLI()
    cli.start()


if __name__ == "__main__":
    main()