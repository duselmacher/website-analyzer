#!/usr/bin/env python3
"""Website Analyzer - Main CLI interface."""

import argparse
import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse

from playwright.async_api import async_playwright


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


async def take_screenshots(url, output_dir, verbose=False):
    """Take desktop and mobile screenshots of a URL.

    Args:
        url: The URL to screenshot
        output_dir: Directory to save screenshots
        verbose: Print progress messages if True
    """
    screenshots_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    try:
        async with async_playwright() as p:
            # Launch browser
            if verbose:
                print("Launching browser...")

            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as e:
                print(f"Error launching browser: {e}")
                return

            try:
                # Desktop screenshot
                if verbose:
                    print("Taking desktop screenshot...")

                desktop_context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                desktop_page = await desktop_context.new_page()

                try:
                    await desktop_page.goto(url, timeout=30000)
                    await desktop_page.screenshot(
                        path=os.path.join(screenshots_dir, "desktop.png")
                    )
                except Exception as e:
                    print(f"Error taking desktop screenshot: {e}")
                finally:
                    await desktop_context.close()

                # Mobile screenshot
                if verbose:
                    print("Taking mobile screenshot...")

                mobile_context = await browser.new_context(
                    viewport={"width": 375, "height": 667}
                )
                mobile_page = await mobile_context.new_page()

                try:
                    await mobile_page.goto(url, timeout=30000)
                    await mobile_page.screenshot(
                        path=os.path.join(screenshots_dir, "mobile.png")
                    )
                except Exception as e:
                    print(f"Error taking mobile screenshot: {e}")
                finally:
                    await mobile_context.close()

                if verbose:
                    print("Screenshots completed.")

            finally:
                await browser.close()

    except Exception as e:
        print(f"Error during screenshot capture: {e}")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate URL
    try:
        parsed_url = urlparse(args.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            print(f"Error: Invalid URL '{args.url}'")
            return
        domain = parsed_url.netloc
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return

    # Create output directory structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, domain, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    if args.verbose:
        print(f"URL: {args.url}")
        print(f"Output directory: {output_dir}")

    # Take screenshots
    asyncio.run(take_screenshots(args.url, output_dir, args.verbose))


if __name__ == "__main__":
    main()
