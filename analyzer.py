#!/usr/bin/env python3
"""Website Analyzer - Main CLI interface."""

import argparse
import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse

from playwright.async_api import async_playwright


async def handle_cookie_consent(page, verbose=False):
    """Handle cookie consent banners automatically.

    Args:
        page: Playwright page object
        verbose: Print progress messages if True
    """
    try:
        # Common selectors for "Accept All" buttons
        accept_selectors = [
            # Text-based selectors (German and English)
            'button:has-text("Alle akzeptieren")',
            'button:has-text("Alle annehmen")',
            'button:has-text("Accept all")',
            'button:has-text("Accept All")',
            'button:has-text("Akzeptieren")',
            'a:has-text("Alle akzeptieren")',
            'a:has-text("Alle annehmen")',
            'a:has-text("Accept all")',
            'a:has-text("Accept All")',
            'a:has-text("Akzeptieren")',
            # Common ID/class selectors
            '#cookie-accept',
            '.cookie-accept',
            '[data-cookie-accept]',
            '#accept-all-cookies',
            '.accept-all-cookies',
            '[data-action="accept-all"]',
            '#onetrust-accept-btn-handler',
            '.cc-accept-all',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        ]

        # Try to find and click an accept button
        button_found = False
        for selector in accept_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=500):
                    await button.click()
                    button_found = True
                    # Wait for banner to disappear
                    await page.wait_for_timeout(1000)
                    if verbose:
                        print("Cookie banner handled")
                    return
            except Exception:
                # Selector didn't match, try next one
                continue

        # Fallback 1: Inject consent cookie and reload
        if not button_found:
            try:
                url = page.url
                await page.context.add_cookies([{
                    "name": "cookie_consent",
                    "value": "accepted",
                    "url": url
                }])
                await page.reload()
                await page.wait_for_timeout(1000)
                if verbose:
                    print("Cookie consent injected via cookie")
                return
            except Exception:
                pass

        # Fallback 2: Hide common cookie banner elements via CSS
        try:
            hide_css = """
                #cookie-banner,
                .cookie-banner,
                #cookie-consent,
                .cookie-consent,
                #cookiebanner,
                .cookiebanner,
                #cookie-notice,
                .cookie-notice,
                #gdpr-banner,
                .gdpr-banner,
                #onetrust-banner-sdk,
                .onetrust-banner-sdk,
                #CybotCookiebotDialog,
                .cc-window,
                .cookie-modal,
                #cookie-modal,
                [class*="cookie-consent"],
                [class*="cookie-banner"],
                [id*="cookie-consent"],
                [id*="cookie-banner"] {
                    display: none !important;
                    visibility: hidden !important;
                }
            """
            await page.add_style_tag(content=hide_css)
            if verbose:
                print("Cookie banners hidden via CSS")
        except Exception:
            pass

    except Exception as e:
        # Never crash even if cookie handling fails
        if verbose:
            print(f"Cookie consent handling failed: {e}")


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

    parser.add_argument(
        "--skip-cookies",
        action="store_true",
        help="Skip automatic cookie consent handling"
    )

    return parser.parse_args()


async def take_screenshots(url, output_dir, verbose=False, skip_cookies=False):
    """Take desktop and mobile screenshots of a URL.

    Args:
        url: The URL to screenshot
        output_dir: Directory to save screenshots
        verbose: Print progress messages if True
        skip_cookies: Skip cookie consent handling if True
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
                    # Handle cookie consent before screenshot
                    if not skip_cookies:
                        await handle_cookie_consent(desktop_page, verbose)
                        # Wait for page to stabilize after consent
                        await desktop_page.wait_for_timeout(2000)
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
                    # Handle cookie consent before screenshot
                    if not skip_cookies:
                        await handle_cookie_consent(mobile_page, verbose)
                        # Wait for page to stabilize after consent
                        await mobile_page.wait_for_timeout(2000)
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
    asyncio.run(take_screenshots(args.url, output_dir, args.verbose, args.skip_cookies))


if __name__ == "__main__":
    main()
