#!/usr/bin/env python3
"""Website Analyzer - Main CLI interface."""

import argparse


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze websites for various metrics and information."
    )

    parser.add_argument(
        "--url",
        required=True,
        help="URL of the website to analyze"
    )

    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory for results (default: ./output)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    print(f"URL: {args.url}")
    print(f"Output directory: {args.output}")
    print(f"Verbose: {args.verbose}")


if __name__ == "__main__":
    main()
