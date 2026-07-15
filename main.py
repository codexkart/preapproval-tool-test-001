#!/usr/bin/env python3
"""
Pre-Approval Website-Verification Tool
=======================================

Reads a pre-approval application PDF, visits the provider's website,
gathers evidence, and produces an audit-ready report.

Usage:
    python main.py review samples/Sample-01.pdf
    python main.py review samples/Sample-04.pdf --no-headless
    python main.py batch samples/
    python main.py interactive
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from src.form_parser import FormParser
from src.checklist_manager import ChecklistManager
from src.web_researcher import WebResearcher
from src.report_generator import ReportGenerator

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tool.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("preapproval-tool")


class PreApprovalTool:
    """
    Main orchestrator — runs the full workflow:
    PDF → Parse → Checklist → Website Research → Report
    """

    def __init__(self, api_key: str = None, model: str = None, headless: bool = True):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._headless = headless

        if not self._api_key:
            print("ERROR: GEMINI_API_KEY not set. Create a .env file or set the environment variable.")
            sys.exit(1)

        self._parser = FormParser(api_key=self._api_key, model=self._model)
        self._checklist = ChecklistManager(config_path="config/checklists.yaml")
        self._researcher = WebResearcher(
            api_key=self._api_key, model=self._model,
            headless=self._headless, output_dir="output",
        )
        self._reporter = ReportGenerator()

    def review(self, pdf_path: str) -> str:
        """
        Run the full review workflow on a single PDF.
        Returns the path to the generated report.
        """
        pdf_name = Path(pdf_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_subdir = "{}_{}".format(pdf_name, timestamp)
        output_dir = os.path.join("output", output_subdir)

        print("\n" + "=" * 60)
        print("PRE-APPROVAL WEBSITE VERIFICATION")
        print("=" * 60)
        print("Form: {}".format(pdf_path))
        print()

        # Step 1: Parse the form
        print("[1/5] Parsing the application form...")
        form_data = self._parser.parse(pdf_path)

        category = form_data.get("category", "")
        provider = form_data.get("provider_name", "Unknown")
        item = form_data.get("item_name", "Unknown")
        url = form_data.get("website_url", "None")
        fee = form_data.get("fee_stated", "Not specified")

        print("  Category:  {}".format(self._checklist.get_display_name(category)))
        print("  Provider:  {}".format(provider))
        print("  Item:      {}".format(item))
        print("  URL:       {}".format(url))
        print("  Fee:       {}".format(fee))
        print()

        # Step 2: Get the applicable checklist
        print("[2/5] Loading checklist for '{}'...".format(
            self._checklist.get_display_name(category)
        ))
        website_checks = self._checklist.get_website_checks(category)
        internal_checks = self._checklist.get_internal_checks(category)

        if not website_checks:
            print("  WARNING: No website checks found for category '{}'.".format(category))
            print("  The tool may not have a checklist for this form type.")

        print("  {} website-verifiable items".format(len(website_checks)))
        print("  {} internal items (left for human reviewer)".format(len(internal_checks)))
        print()

        # Exclusion list pre-check for HRI/OTPS
        if category in ("hri", "otps"):
            exclusion_list = self._checklist.get_exclusion_list(category)
            item_lower = (item or "").lower()
            for excluded in exclusion_list:
                if excluded.lower() in item_lower:
                    print("  *** EXCLUSION FLAG: '{}' may match excluded item '{}' ***".format(
                        item, excluded
                    ))
                    break

        # Step 3: Visit the website and gather evidence
        print("[3/5] Visiting website and gathering evidence...")
        print("  This may take 30-60 seconds...")
        findings = self._researcher.research(
            form_data=form_data,
            website_checks=website_checks,
            output_subdir=output_subdir,
        )
        print("  Done. {} items checked.".format(len(findings)))
        print()

        # Step 4: Print summary
        print("[4/5] Results summary:")
        found = sum(1 for f in findings.values() if f.get("status") == "FOUND")
        not_found = sum(1 for f in findings.values() if f.get("status") == "NOT_FOUND")
        review = sum(1 for f in findings.values() if f.get("status") == "NEEDS_REVIEW")

        print("  ✓ Found:        {}".format(found))
        print("  ✗ Not Found:    {}".format(not_found))
        print("  ⚠ Needs Review: {}".format(review))
        print()

        for check in website_checks:
            finding = findings.get(check["id"], {})
            status = finding.get("status", "?")
            symbol = {"FOUND": "✓", "NOT_FOUND": "✗", "NEEDS_REVIEW": "⚠"}.get(status, "?")
            print("  {} {} — {}".format(symbol, check["question"][:60], status))

        print()

        # Step 5: Generate report
        print("[5/5] Generating report...")
        category_name = self._checklist.get_display_name(category)
        report_path = self._reporter.generate(
            form_data=form_data,
            category_name=category_name,
            website_checks=website_checks,
            internal_checks=internal_checks,
            findings=findings,
            output_dir=output_dir,
        )

        print()
        print("=" * 60)
        print("REPORT SAVED: {}".format(report_path))
        print("EVIDENCE DIR: {}/evidence/".format(output_dir))
        print("=" * 60)
        print()

        return report_path

    def batch(self, folder: str):
        """Run reviews on all PDFs in a folder."""
        pdf_files = sorted(Path(folder).glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found in: {}".format(folder))
            return

        print("Found {} PDF files. Processing...\n".format(len(pdf_files)))
        reports = []

        for pdf in pdf_files:
            try:
                report = self.review(str(pdf))
                reports.append((str(pdf), report, "OK"))
            except Exception as e:
                logger.error("Failed to process %s: %s", pdf, str(e))
                reports.append((str(pdf), None, str(e)))

        print("\n" + "=" * 60)
        print("BATCH COMPLETE — {} files processed".format(len(reports)))
        print("=" * 60)
        for pdf_path, report_path, status in reports:
            if report_path:
                print("  ✓ {} → {}".format(Path(pdf_path).name, report_path))
            else:
                print("  ✗ {} — ERROR: {}".format(Path(pdf_path).name, status))

    def interactive(self):
        """Interactive mode — reviewer can give commands in plain language."""
        print("\n" + "=" * 60)
        print("PRE-APPROVAL VERIFICATION TOOL — Interactive Mode")
        print("=" * 60)
        print()
        print("Commands:")
        print('  review <path>     — Review an application (e.g., "review samples/Sample-01.pdf")')
        print('  batch <folder>    — Review all PDFs in a folder')
        print("  help              — Show this help")
        print("  quit              — Exit")
        print()

        last_report = None
        last_output_dir = None

        while True:
            try:
                user_input = input(">> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            lower = user_input.lower()

            if lower in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            elif lower in ("help", "h", "?"):
                print("Commands: review <path>, batch <folder>, help, quit")

            elif lower.startswith("review "):
                path = user_input[7:].strip().strip('"').strip("'")
                if not os.path.exists(path):
                    print("File not found: {}".format(path))
                    continue
                try:
                    last_report = self.review(path)
                    last_output_dir = str(Path(last_report).parent)
                except Exception as e:
                    print("Error: {}".format(str(e)))

            elif lower.startswith("batch "):
                folder = user_input[6:].strip().strip('"').strip("'")
                if not os.path.isdir(folder):
                    print("Folder not found: {}".format(folder))
                    continue
                self.batch(folder)

            else:
                print("Unknown command. Type 'help' for available commands.")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-Approval Website-Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py review samples/Sample-01.pdf
  python main.py review samples/Sample-04.pdf --no-headless
  python main.py batch samples/
  python main.py interactive
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # review command
    review_parser = subparsers.add_parser("review", help="Review a single application")
    review_parser.add_argument("pdf", help="Path to the PDF application form")
    review_parser.add_argument("--no-headless", action="store_true",
                                help="Show the browser window (for debugging)")

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Review all PDFs in a folder")
    batch_parser.add_argument("folder", help="Folder containing PDF files")
    batch_parser.add_argument("--no-headless", action="store_true")

    # interactive command
    subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    headless = not getattr(args, "no_headless", False)
    tool = PreApprovalTool(headless=headless)

    if args.command == "review":
        tool.review(args.pdf)

    elif args.command == "batch":
        tool.batch(args.folder)

    elif args.command == "interactive":
        tool.interactive()


if __name__ == "__main__":
    main()
