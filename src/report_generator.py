"""
Step 5: Report Generator
Creates a clean, professional HTML report that a reviewer can
open in any browser, save, and share.
"""

import os
import base64
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates HTML reports with embedded evidence for pre-approval reviews."""

    def generate(self, form_data: dict, category_name: str,
                 website_checks: list, internal_checks: list,
                 findings: dict, output_dir: str) -> str:
        """
        Generate the HTML report.

        Args:
            form_data: Extracted form fields.
            category_name: Display name of the category.
            website_checks: List of website-verifiable items.
            internal_checks: List of internal-only items.
            findings: Results from web research.
            output_dir: Where to save the report.

        Returns:
            Path to the generated report.
        """
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "report.html")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        evidence_dir = os.path.join(output_dir, "evidence")

        # Count statuses
        found_count = sum(1 for f in findings.values() if f.get("status") == "FOUND")
        not_found_count = sum(1 for f in findings.values() if f.get("status") == "NOT_FOUND")
        review_count = sum(1 for f in findings.values() if f.get("status") == "NEEDS_REVIEW")
        total = len(findings)

        # Build evidence images list
        evidence_images = []
        if os.path.exists(evidence_dir):
            for fname in sorted(os.listdir(evidence_dir)):
                if fname.endswith((".png", ".jpg", ".jpeg")):
                    fpath = os.path.join(evidence_dir, fname)
                    evidence_images.append({
                        "filename": fname,
                        "path": fpath,
                        "b64": self._img_to_base64(fpath),
                    })

        # Fee comparison
        fee_stated = form_data.get("fee_stated", "Not specified")
        fee_found = "See findings below"
        fee_verdict = "See detailed findings"
        for check_id, finding in findings.items():
            if "fee" in check_id.lower() and "match" in check_id.lower():
                if finding["status"] == "FOUND":
                    fee_verdict = "Matches application"
                    fee_found = finding.get("quote", finding.get("note", ""))
                elif finding["status"] == "NOT_FOUND":
                    fee_verdict = "Not published on website"
                else:
                    fee_verdict = "Needs manual review"
                    fee_found = finding.get("note", "")
                break

        # For categories without explicit fee_match check, look for published_fee/published_fees
        if fee_verdict == "See detailed findings":
            for check_id, finding in findings.items():
                if "published_fee" in check_id or "fee_cap" in check_id:
                    fee_found = finding.get("note", "See findings")
                    if finding["status"] == "FOUND":
                        fee_verdict = "Published fee found — see note"
                    elif finding["status"] == "NOT_FOUND":
                        fee_verdict = "Fee not found on website"
                    else:
                        fee_verdict = "Needs manual review"
                    break

        html = self._render(
            form_data=form_data,
            category_name=category_name,
            timestamp=timestamp,
            website_checks=website_checks,
            internal_checks=internal_checks,
            findings=findings,
            evidence_images=evidence_images,
            found_count=found_count,
            not_found_count=not_found_count,
            review_count=review_count,
            total=total,
            fee_stated=fee_stated,
            fee_found=fee_found,
            fee_verdict=fee_verdict,
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info("Report saved to: %s", report_path)
        return report_path

    def _render(self, **ctx) -> str:
        """Render the HTML report."""

        # Build checklist rows
        check_rows = ""
        for check in ctx["website_checks"]:
            cid = check["id"]
            finding = ctx["findings"].get(cid, {})
            status = finding.get("status", "NEEDS_REVIEW")
            note = finding.get("note", "No data collected")
            quote = finding.get("quote", "")
            url = finding.get("evidence_url", "")

            if status == "FOUND":
                badge = '<span class="badge found">&#10003; Found</span>'
            elif status == "NOT_FOUND":
                badge = '<span class="badge not-found">&#10007; Not Found</span>'
            else:
                badge = '<span class="badge review">&#9888; Needs Review</span>'

            quote_html = ""
            if quote:
                quote_html = '<div class="quote">&ldquo;{}&rdquo;</div>'.format(
                    self._esc(quote)
                )

            url_html = ""
            if url:
                url_html = '<div class="evidence-url"><a href="{}" target="_blank">{}</a></div>'.format(
                    self._esc(url), self._esc(url[:80])
                )

            check_rows += """
            <tr>
                <td class="check-question">{question}</td>
                <td class="check-status">{badge}</td>
                <td class="check-evidence">
                    <div class="note">{note}</div>
                    {quote_html}
                    {url_html}
                </td>
            </tr>""".format(
                question=self._esc(check["question"]),
                badge=badge,
                note=self._esc(note),
                quote_html=quote_html,
                url_html=url_html,
            )

        # Internal checks rows
        internal_rows = ""
        for item in ctx["internal_checks"]:
            internal_rows += """
            <tr>
                <td class="check-question">{}</td>
                <td class="check-status"><span class="badge internal">Internal</span></td>
                <td class="check-evidence"><div class="note">Not verifiable from the website — requires internal review.</div></td>
            </tr>""".format(self._esc(item))

        # Evidence images
        images_html = ""
        for img in ctx["evidence_images"]:
            images_html += """
            <div class="evidence-capture">
                <h4>{filename}</h4>
                <img src="data:image/png;base64,{b64}" alt="{filename}" />
            </div>""".format(filename=img["filename"], b64=img["b64"])

        fd = ctx["form_data"]

        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pre-Approval Review — {provider}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; background: #f5f5f5; }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
  .header {{ background: #1a1a2e; color: white; padding: 24px 32px; border-radius: 8px 8px 0 0; }}
  .header h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .header .subtitle {{ color: #a0a0c0; font-size: 14px; }}
  .card {{ background: white; border-radius: 0 0 8px 8px; padding: 24px 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px; }}
  .section-title {{ font-size: 16px; font-weight: 700; color: #1a1a2e; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 2px solid #e8e8f0; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }}
  .info-item {{ padding: 8px 0; }}
  .info-label {{ font-size: 11px; text-transform: uppercase; color: #666; letter-spacing: 0.5px; }}
  .info-value {{ font-size: 15px; font-weight: 500; margin-top: 2px; }}
  .info-value a {{ color: #2563eb; text-decoration: none; }}
  .summary-bar {{ display: flex; gap: 16px; margin: 16px 0; }}
  .summary-item {{ flex: 1; text-align: center; padding: 12px; border-radius: 8px; }}
  .summary-item.found {{ background: #ecfdf5; color: #065f46; }}
  .summary-item.not-found {{ background: #fef2f2; color: #991b1b; }}
  .summary-item.review {{ background: #fffbeb; color: #92400e; }}
  .summary-count {{ font-size: 28px; font-weight: 700; }}
  .summary-label {{ font-size: 12px; margin-top: 4px; }}
  .fee-comparison {{ background: #f8f9ff; border: 1px solid #e0e4f0; border-radius: 8px; padding: 16px; margin: 16px 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }}
  .fee-box {{ text-align: center; }}
  .fee-box .label {{ font-size: 11px; text-transform: uppercase; color: #666; }}
  .fee-box .value {{ font-size: 18px; font-weight: 600; margin-top: 4px; }}
  .fee-box .verdict {{ font-size: 13px; color: #2563eb; font-weight: 500; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  th {{ background: #1a1a2e; color: white; padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #e8e8f0; vertical-align: top; font-size: 14px; }}
  tr:hover {{ background: #f8f9ff; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
  .badge.found {{ background: #d1fae5; color: #065f46; }}
  .badge.not-found {{ background: #fee2e2; color: #991b1b; }}
  .badge.review {{ background: #fef3c7; color: #92400e; }}
  .badge.internal {{ background: #e8e8f0; color: #666; }}
  .check-question {{ width: 35%; }}
  .check-status {{ width: 15%; }}
  .check-evidence {{ width: 50%; }}
  .note {{ color: #374151; line-height: 1.5; }}
  .quote {{ margin-top: 6px; padding: 6px 10px; background: #f0fdf4; border-left: 3px solid #22c55e; font-style: italic; font-size: 13px; color: #065f46; }}
  .evidence-url {{ margin-top: 4px; font-size: 12px; }}
  .evidence-capture {{ margin: 16px 0; }}
  .evidence-capture h4 {{ font-size: 13px; color: #666; margin-bottom: 8px; }}
  .evidence-capture img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
  .footer {{ text-align: center; padding: 16px; color: #999; font-size: 12px; }}
  .disclaimer {{ background: #fffbeb; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #92400e; }}
  @media print {{
    body {{ background: white; }}
    .container {{ max-width: none; padding: 0; }}
    .card {{ box-shadow: none; border: 1px solid #ddd; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Pre-Approval Website Verification Report</h1>
  <div class="subtitle">{category} | Review Date: {timestamp}</div>
</div>

<div class="card">
  <div class="section-title">Request Summary</div>
  <div class="info-grid">
    <div class="info-item">
      <div class="info-label">Participant</div>
      <div class="info-value">{participant} (Age: {age})</div>
    </div>
    <div class="info-item">
      <div class="info-label">Provider / Vendor</div>
      <div class="info-value">{provider}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Item / Class / Service</div>
      <div class="info-value">{item}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Website</div>
      <div class="info-value"><a href="{url}" target="_blank">{url_display}</a></div>
    </div>
    <div class="info-item">
      <div class="info-label">FI Coordinator</div>
      <div class="info-value">{coordinator}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Broker</div>
      <div class="info-value">{broker}</div>
    </div>
  </div>

  <div class="section-title">Rate Comparison</div>
  <div class="fee-comparison">
    <div class="fee-box">
      <div class="label">Fee on Application</div>
      <div class="value">{fee_stated}</div>
    </div>
    <div class="fee-box">
      <div class="label">Fee Found on Website</div>
      <div class="value">{fee_found_display}</div>
    </div>
    <div class="fee-box">
      <div class="label">Verdict</div>
      <div class="verdict">{fee_verdict}</div>
    </div>
  </div>

  <div class="summary-bar">
    <div class="summary-item found">
      <div class="summary-count">{found}</div>
      <div class="summary-label">Found</div>
    </div>
    <div class="summary-item not-found">
      <div class="summary-count">{not_found}</div>
      <div class="summary-label">Not Found</div>
    </div>
    <div class="summary-item review">
      <div class="summary-count">{review}</div>
      <div class="summary-label">Needs Review</div>
    </div>
  </div>

  <div class="disclaimer">
    <strong>&#9888; This report assists the reviewer.</strong> It does not approve or deny any request.
    A human reviewer must make the final determination. "Not Found" and "Needs Review" are valid
    outcomes indicating the tool could not verify the item from the public website.
  </div>

  <div class="section-title">Website-Verifiable Checklist</div>
  <table>
    <thead>
      <tr><th>Requirement</th><th>Status</th><th>Evidence / Notes</th></tr>
    </thead>
    <tbody>
      {check_rows}
    </tbody>
  </table>

  <div class="section-title">Internal Items (Not Website-Verifiable)</div>
  <table>
    <thead>
      <tr><th>Requirement</th><th>Status</th><th>Notes</th></tr>
    </thead>
    <tbody>
      {internal_rows}
    </tbody>
  </table>

  <div class="section-title">Evidence Captures</div>
  <p style="font-size: 13px; color: #666; margin-bottom: 12px;">
    Date-stamped screenshots of the provider website at the time of review.
    Each capture shows the URL and timestamp in the header bar.
  </p>
  {images_html}

</div>

<div class="footer">
  Generated by Pre-Approval Website-Verification Tool | {timestamp}<br>
  This is an automated research report — final approval decisions are made by authorized staff.
</div>

</div>
</body>
</html>""".format(
            category=self._esc(ctx["category_name"]),
            timestamp=ctx["timestamp"],
            participant=self._esc(fd.get("participant_name", "N/A")),
            age=fd.get("participant_age", "N/A"),
            provider=self._esc(fd.get("provider_name", "N/A")),
            item=self._esc(fd.get("item_name", "N/A")),
            url=self._esc(fd.get("website_url", "")),
            url_display=self._esc((fd.get("website_url") or "")[:60]),
            coordinator=self._esc(fd.get("fi_coordinator", "N/A")),
            broker=self._esc(fd.get("broker", "N/A")),
            fee_stated=self._esc(ctx["fee_stated"]),
            fee_found_display=self._esc(ctx["fee_found"][:80] if ctx["fee_found"] else "N/A"),
            fee_verdict=self._esc(ctx["fee_verdict"]),
            found=ctx["found_count"],
            not_found=ctx["not_found_count"],
            review=ctx["review_count"],
            check_rows=check_rows,
            internal_rows=internal_rows,
            images_html=images_html,
        )

    @staticmethod
    def _esc(text: str) -> str:
        if not text:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    @staticmethod
    def _img_to_base64(filepath: str) -> str:
        try:
            with open(filepath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
