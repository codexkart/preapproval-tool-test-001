"""
Step 2: Checklist Manager
Loads the YAML config, matches the form category, and separates
website-verifiable checks from internal (human-only) checks.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ChecklistManager:
    """Loads and manages category-specific checklists from YAML config."""

    def __init__(self, config_path: str = "config/checklists.yaml"):
        self._config_path = config_path
        self._categories = self._load()

    def _load(self) -> dict:
        with open(self._config_path, "r") as f:
            data = yaml.safe_load(f)
        return data.get("categories", {})

    def get_checklist(self, category: str) -> Optional[dict]:
        """Get the full checklist config for a category."""
        if category in self._categories:
            return self._categories[category]
        logger.warning("Unknown category: %s", category)
        return None

    def get_website_checks(self, category: str) -> List[dict]:
        """Get only the website-verifiable checklist items."""
        checklist = self.get_checklist(category)
        if not checklist:
            return []
        return checklist.get("website_checks", [])

    def get_internal_checks(self, category: str) -> List[str]:
        """Get the internal (human-only) checklist items."""
        checklist = self.get_checklist(category)
        if not checklist:
            return []
        return checklist.get("internal_checks", [])

    def get_display_name(self, category: str) -> str:
        """Get the human-readable category name."""
        checklist = self.get_checklist(category)
        if checklist:
            return checklist.get("display_name", category)
        return category

    def get_exclusion_list(self, category: str) -> List[str]:
        """Get the exclusion list for HRI/OTPS categories."""
        checklist = self.get_checklist(category)
        if not checklist:
            return []
        for check in checklist.get("website_checks", []):
            if "exclusion_list" in check:
                return check["exclusion_list"]
        return []

    def list_categories(self) -> List[str]:
        """List all available categories."""
        return list(self._categories.keys())
