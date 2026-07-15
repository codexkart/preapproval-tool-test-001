"""
Steps 2-4: Web Researcher
Visits the provider website, analyzes the content for evidence,
and captures date-stamped screenshots.

Uses Playwright for browsing and Gemini for intelligent page analysis.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright, Page
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class WebResearcher:
    """
    Visits provider websites, gathers evidence, and captures screenshots.

    For each website-verifiable checklist item, the researcher:
    1. Visits the URL from the application
    2. Navigates to find relevant pages (pricing, schedule, about)
    3. Analyzes page content using Gemini
    4. Captures date-stamped screenshots as evidence
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash",
                 headless: bool = True, output_dir: str = "output"):
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._headless = headless
        self._output_dir = output_dir

    def research(self, form_data: dict, website_checks: list,
                 output_subdir: str) -> dict:
        """
        Visit the website and gather evidence for each checklist item.

        Args:
            form_data: Extracted form fields (from FormParser).
            website_checks: List of website-verifiable checklist items.
            output_subdir: Subdirectory for evidence captures.

        Returns:
            Dict with findings per checklist item.
        """
        url = form_data.get("website_url")
        if not url:
            return self._no_url_result(website_checks)

        # Ensure URL has a scheme
        if not url.startswith("http"):
            url = "https://" + url

        evidence_dir = os.path.join(self._output_dir, output_subdir, "evidence")
        os.makedirs(evidence_dir, exist_ok=True)

        findings = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self._headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                # Step 1: Visit the main URL and capture full-page screenshot
                logger.info("Visiting: %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)

                # Capture the full-page evidence screenshot
                fullpage_path = os.path.join(evidence_dir, "01_full_page.png")
                self._capture_stamped_screenshot(page, fullpage_path, "Full page capture")

                # Get the page content for analysis
                page_text = self._get_page_text(page)
                page_title = page.title()

                # Step 2: Look for additional relevant pages (pricing, schedule, etc.)
                subpages = self._find_relevant_links(page, form_data)

                # Collect all page content for analysis
                all_content = {
                    "main_page": {
                        "url": page.url,
                        "title": page_title,
                        "text": page_text[:8000],
                    },
                    "subpages": [],
                }

                for i, link_info in enumerate(subpages[:4]):
                    try:
                        logger.info("Visiting subpage: %s", link_info["url"])
                        page.goto(link_info["url"], wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(2000)

                        sub_text = self._get_page_text(page)
                        sub_path = os.path.join(evidence_dir,
                                                "02_subpage_{}.png".format(i + 1))
                        self._capture_stamped_screenshot(
                            page, sub_path,
                            "Subpage: {}".format(link_info.get("label", ""))
                        )

                        all_content["subpages"].append({
                            "url": page.url,
                            "label": link_info.get("label", ""),
                            "text": sub_text[:6000],
                        })
                    except Exception as e:
                        logger.warning("Failed to visit subpage %s: %s",
                                       link_info["url"], str(e))

                # Step 3: Analyze all collected content against each checklist item
                logger.info("Analyzing website content against %d checklist items...",
                            len(website_checks))
                findings = self._analyze_evidence(
                    form_data, website_checks, all_content, evidence_dir, page
                )

            except Exception as e:
                logger.error("Failed to research %s: %s", url, str(e))
                findings = self._error_result(website_checks, str(e))

            finally:
                context.close()
                browser.close()

        return findings

    def _find_relevant_links(self, page: Page, form_data: dict) -> list:
        """Find links on the page that might lead to pricing, schedule, etc."""
        try:
            links = page.evaluate("""() => {
                const keywords = ['price', 'pricing', 'cost', 'fee', 'rate', 'tuition',
                                  'schedule', 'calendar', 'class', 'program', 'membership',
                                  'join', 'register', 'enroll', 'about', 'plan'];
                const results = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const text = (a.innerText || '').toLowerCase().trim();
                    const href = a.href;
                    if (text && href && !href.startsWith('javascript') && !href.startsWith('#')) {
                        for (const kw of keywords) {
                            if (text.includes(kw) || href.toLowerCase().includes(kw)) {
                                results.push({url: href, label: a.innerText.trim()});
                                break;
                            }
                        }
                    }
                });
                return results.slice(0, 10);
            }""")
            # Deduplicate by URL
            seen = set()
            unique = []
            for link in links:
                if link["url"] not in seen:
                    seen.add(link["url"])
                    unique.append(link)
            return unique
        except Exception:
            return []

    def _get_page_text(self, page: Page) -> str:
        """Extract visible text from the page."""
        try:
            return page.evaluate("""() => {
                return document.body ? document.body.innerText : '';
            }""")
        except Exception:
            return ""

    def _analyze_evidence(self, form_data: dict, checks: list,
                          content: dict, evidence_dir: str,
                          page: Page) -> dict:
        """Use Gemini to analyze website content against each checklist item."""

        item_name = form_data.get("item_name", "Unknown")
        provider = form_data.get("provider_name", "Unknown")
        fee_stated = form_data.get("fee_stated", "Unknown")
        category = form_data.get("category", "")
        denial_reason = form_data.get("denial_reason", "")

        checks_text = "\n".join([
            "- [{}] {}\n  How to check: {}".format(
                c["id"], c["question"], c.get("how_to_check", "")
            )
            for c in checks
        ])

        # Build content summary
        content_summary = "MAIN PAGE ({}):\n{}\n\n".format(
            content["main_page"]["url"],
            content["main_page"]["text"][:6000]
        )
        for sp in content["subpages"]:
            content_summary += "SUBPAGE — {} ({}):\n{}\n\n".format(
                sp["label"], sp["url"], sp["text"][:4000]
            )

        analysis_prompt = """You are a government pre-approval reviewer assistant.

APPLICATION DETAILS:
- Item/Class/Service: {item}
- Provider: {provider}
- Fee stated on form: {fee}
- Category: {category}
{denial_info}

WEBSITE CONTENT COLLECTED:
{content}

CHECKLIST ITEMS TO VERIFY:
{checks}

For EACH checklist item, analyze the website content and return a JSON array:
[
  {{
    "id": "the check id",
    "status": "FOUND" or "NOT_FOUND" or "NEEDS_REVIEW",
    "evidence_url": "the specific URL where evidence was found, or the main URL if not found",
    "note": "Plain-language explanation of what you found or didn't find. Quote specific text from the website when possible. Be specific — a reviewer needs to act on this.",
    "quote": "The exact text from the website that serves as evidence (if found)"
  }}
]

RULES:
- FOUND = clear evidence exists on the website supporting this item
- NOT_FOUND = looked but could not find evidence
- NEEDS_REVIEW = ambiguous, partially found, or requires human judgment
- For fee matching: state both the form fee and the website fee explicitly
- Never fabricate — if you didn't see it in the content above, say NOT_FOUND
- For exclusion list checks: if the item matches an excluded category, status should be NEEDS_REVIEW with a clear flag

Return ONLY the JSON array.""".format(
            item=item_name,
            provider=provider,
            fee=fee_stated,
            category=category,
            denial_info="- APPEAL — Denial reason: {}".format(denial_reason) if denial_reason else "",
            content=content_summary[:12000],
            checks=checks_text,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[types.Content(role="user", parts=[
                    types.Part.from_text(text=analysis_prompt)
                ])],
                config=types.GenerateContentConfig(temperature=0, max_output_tokens=4096),
            )

            results = self._clean_json(response.text)
            if not isinstance(results, list):
                results = [results]

            # Build findings dict
            findings = {}
            for item in results:
                check_id = item.get("id", "unknown")
                findings[check_id] = {
                    "status": item.get("status", "NEEDS_REVIEW"),
                    "evidence_url": item.get("evidence_url", ""),
                    "note": item.get("note", ""),
                    "quote": item.get("quote", ""),
                }

            return findings

        except Exception as e:
            logger.error("Gemini analysis failed: %s", str(e))
            return self._error_result(checks, str(e))

    def _capture_stamped_screenshot(self, page: Page, filepath: str,
                                     label: str = "") -> str:
        """Capture a full-page screenshot with date/time and URL stamp."""
        # Take the screenshot
        page.screenshot(path=filepath, full_page=True)

        # Add date stamp overlay
        try:
            img = Image.open(filepath)
            draw = ImageDraw.Draw(img)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_url = page.url
            stamp_text = "Captured: {} | URL: {}".format(timestamp, current_url)
            if label:
                stamp_text = "{} | {}".format(label, stamp_text)

            # Draw stamp bar at top
            bar_height = 30
            new_img = Image.new("RGB", (img.width, img.height + bar_height), "#1a1a2e")
            new_img.paste(img, (0, bar_height))

            draw = ImageDraw.Draw(new_img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except Exception:
                font = ImageFont.load_default()

            draw.text((10, 6), stamp_text, fill="white", font=font)
            new_img.save(filepath)

        except Exception as e:
            logger.warning("Failed to add date stamp: %s", str(e))

        return filepath

    def _no_url_result(self, checks: list) -> dict:
        """Return results when no URL was found on the form."""
        return {
            c["id"]: {
                "status": "NEEDS_REVIEW",
                "evidence_url": "",
                "note": "No URL was found on the application form. Cannot perform website verification.",
                "quote": "",
            }
            for c in checks
        }

    def _error_result(self, checks: list, error: str) -> dict:
        """Return results when an error occurred."""
        return {
            c["id"]: {
                "status": "NEEDS_REVIEW",
                "evidence_url": "",
                "note": "Website research failed: {}".format(error),
                "quote": "",
            }
            for c in checks
        }

    @staticmethod
    def _clean_json(raw: str):
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)
