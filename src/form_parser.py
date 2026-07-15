"""
Step 1: Parse the PDF
Reads a pre-approval application form and extracts who, what, where, how much.
Uses Gemini to handle scanned forms, varied layouts, and checkbox states.
"""

import json
import logging
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """You are reading a government pre-approval application form (PDF).
Extract these fields. Use null for anything not found. Be exact — copy text as-is.

Return this JSON:
{
  "participant_name": "the person's name",
  "participant_age": 0,
  "fi_coordinator": "coordinator name",
  "broker": "broker name",
  "category": "one of: community_classes, coaching, memberships, hri, otps, transition_program, appeal",
  "item_name": "the specific class, item, membership, or program requested",
  "provider_name": "the provider or vendor name",
  "website_url": "the URL/link from the form",
  "fee_stated": "the fee/price exactly as written, e.g. '$30 per session'",
  "fee_amount_numeric": 30.0,
  "fee_frequency": "per_session / per_class / per_course / monthly / yearly / one_time",
  "duration": "session duration if listed",
  "safety_features": "safety features if listed, else null",
  "valued_outcome": "the valued outcome text",
  "lp_date": "Life Plan date",
  "denial_reason": "for appeals: the reason for denial",
  "appeal_justification": "for appeals: the justification text",
  "form_checklist": {"question text": "YES or NO"}
}

Category detection:
- Form title has "Community Class" → "community_classes"
- "Coaching for Parents" or "Coaching" → "coaching"
- "Health Club" or "Membership" → "memberships"
- "Household Related" or "HRI" → "hri"
- "OTPS" or "Other Than Personal" → "otps"
- "Transition Program" → "transition_program"
- "Appeal" → "appeal"

Return ONLY valid JSON."""


class FormParser:
    """Parses pre-approval PDF forms using Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def parse(self, pdf_path: str) -> dict:
        """Parse a PDF form and return extracted fields."""
        logger.info("Parsing form: %s", pdf_path)

        pdf_bytes = Path(pdf_path).read_bytes()
        doc_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
        prompt_part = types.Part.from_text(text=EXTRACT_PROMPT)

        response = self._client.models.generate_content(
            model=self._model,
            contents=[types.Content(role="user", parts=[doc_part, prompt_part])],
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=4096),
        )

        data = self._clean_json(response.text)
        logger.info("Parsed: category=%s, provider=%s, url=%s",
                     data.get("category"), data.get("provider_name"), data.get("website_url"))
        return data

    @staticmethod
    def _clean_json(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)
