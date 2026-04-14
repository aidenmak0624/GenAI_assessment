"""
Generate mock policy PDFs for manual RAG upload testing.

The generated files use unique product and program names so they are easy to
retrieve after being uploaded into the app's policy knowledge base.
"""

from __future__ import annotations

from pathlib import Path
import textwrap

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "demo_assets" / "upload_pdfs" / "standard"
CONFLICT_OUTPUT_DIR = ROOT / "demo_assets" / "upload_pdfs" / "conflicts"


POLICIES = [
    {
        "filename": "orbitcare_priority_support_policy.pdf",
        "title": "OrbitCare Priority Support Policy",
        "subtitle": "Internal support coverage for the OrbitCare add-on program",
        "sections": [
            (
                "Coverage Tiers",
                [
                    "OrbitCare Starter includes email support during business hours only.",
                    "OrbitCare Plus includes email and live chat from 8:00 AM to 8:00 PM local time, Monday through Saturday.",
                    "OrbitCare Elite includes 24/7 live chat, weekend callback service, and expedited escalation review.",
                ],
            ),
            (
                "Response Targets",
                [
                    "Starter tickets receive an initial response within 12 business hours.",
                    "Plus tickets receive an initial response within 4 business hours.",
                    "Elite tickets receive an initial response within 45 minutes.",
                    "Critical outages for Elite customers should be escalated to the Duty Resolution Desk immediately after triage.",
                ],
            ),
            (
                "Escalation Rules",
                [
                    "Cases may be escalated after two unresolved contacts or when a promised callback window is missed.",
                    "Billing-only questions are not treated as critical incidents unless service access is blocked.",
                    "The Duty Resolution Desk reviews Elite escalations every 30 minutes until ownership is confirmed.",
                ],
            ),
        ],
    },
    {
        "filename": "flexreturn_device_exchange_policy.pdf",
        "title": "FlexReturn Device Exchange Policy",
        "subtitle": "Exchange and return guidance for the FlexReturn pilot catalog",
        "sections": [
            (
                "Standard Return Windows",
                [
                    "Most sealed FlexReturn devices can be returned within 21 calendar days of delivery.",
                    "Opened DeskPilot accessories can be returned within 14 calendar days if all packaging and cables are included.",
                    "NimbusPad tablets purchased with a FlexReturn Plus membership can be returned within 30 calendar days.",
                ],
            ),
            (
                "Fees And Exceptions",
                [
                    "Open-box NimbusPad tablet returns may incur a 10 percent restocking fee.",
                    "Custom engraved SkyDock hubs are final sale and cannot be returned.",
                    "Completed setup services are non-refundable once the installation session begins.",
                ],
            ),
            (
                "Damage Handling",
                [
                    "Transit damage must be reported within 72 hours of delivery to qualify for a no-fee replacement.",
                    "Cosmetic scratches that do not affect function are not treated as transit damage.",
                    "If the original device is not returned within 10 days after a replacement ships, the replacement is billed in full.",
                ],
            ),
        ],
    },
    {
        "filename": "nova_rewards_credit_policy.pdf",
        "title": "Nova Rewards Credit Policy",
        "subtitle": "Rules for promotional credits issued under the Nova Rewards program",
        "sections": [
            (
                "Credit Issuance",
                [
                    "Nova Rewards credits are issued after qualifying purchases, approved service recovery cases, or seasonal campaigns.",
                    "Credits appear in the customer wallet within 24 hours after issuance.",
                    "Promotional welcome credits are limited to one account per household.",
                ],
            ),
            (
                "Expiration Rules",
                [
                    "Standard Nova Rewards credits expire 90 days after they are issued.",
                    "Service recovery credits expire 180 days after they are issued.",
                    "Credits are forfeited immediately if an account is closed for fraud review or payment abuse.",
                ],
            ),
            (
                "Usage Restrictions",
                [
                    "Credits may be applied to hardware, accessories, and support plan renewals.",
                    "Credits cannot be redeemed for gift cards, tax charges, or third-party marketplace items.",
                    "Unused credits cannot be transferred between customer accounts or converted to cash.",
                ],
            ),
        ],
    },
]


PROMPTS_MD = """# Mock Upload Policy Test Pack

These PDFs are meant for manual upload testing in the Streamlit app.

## Files

- `orbitcare_priority_support_policy.pdf`
- `flexreturn_device_exchange_policy.pdf`
- `nova_rewards_credit_policy.pdf`

## Suggested Questions

1. `What does the OrbitCare policy say about Elite response times?`
2. `Can opened NimbusPad tablets incur a restocking fee under the FlexReturn policy?`
3. `How long do Nova Rewards service recovery credits last?`
4. `Are custom engraved SkyDock hubs returnable?`
5. `Can Nova Rewards credits be used for gift cards or transferred to another account?`

## Upload Tips

- Upload one PDF first and ask a question with its unique term, such as `OrbitCare`.
- Then upload the rest together and ask cross-file questions like:
  `Compare OrbitCare Elite response targets with FlexReturn damage reporting windows.`
- If your API key is already set in the app, the vector store should rebuild automatically after upload.
"""


CONFLICT_POLICIES = [
    {
        "filename": "auroracare_core_returns_policy.pdf",
        "title": "AuroraCare Core Returns Policy",
        "subtitle": "Baseline return rules for AuroraCare hardware and accessories",
        "sections": [
            (
                "Return Windows",
                [
                    "EchoLoop speakers purchased under the core program may be returned within 14 calendar days of delivery.",
                    "LumaDock charging hubs may be returned within 21 calendar days if all cables and adapters are included.",
                    "PulseBand wearables become final sale once they are activated and paired to an account.",
                ],
            ),
            (
                "Fees",
                [
                    "Open-box EchoLoop speaker returns incur a 15 percent restocking fee.",
                    "LumaDock returns do not incur a restocking fee unless the device is missing power accessories.",
                    "Transit damage reported within 48 hours qualifies for a replacement with no restocking fee.",
                ],
            ),
            (
                "Notes",
                [
                    "Completed white-glove setup services are not refundable once the onsite visit begins.",
                    "Exchange approvals are valid for 7 days after the replacement order is created.",
                ],
            ),
        ],
    },
    {
        "filename": "auroracare_platinum_member_addendum.pdf",
        "title": "AuroraCare Platinum Member Addendum",
        "subtitle": "Enhanced return rights for AuroraCare Platinum members",
        "sections": [
            (
                "Extended Return Windows",
                [
                    "Platinum members may return EchoLoop speakers within 30 calendar days of delivery.",
                    "Platinum members may return LumaDock charging hubs within 30 calendar days, even if the outer packaging is opened.",
                    "PulseBand wearables activated within the first 7 days may still be returned by Platinum members if all health data is wiped before inspection.",
                ],
            ),
            (
                "Fee Adjustments",
                [
                    "Open-box EchoLoop speaker returns for Platinum members incur a reduced 5 percent restocking fee.",
                    "No restocking fee applies when a Platinum return is approved for verified audio defects.",
                    "Expedited replacement shipping is included for Platinum-approved exchanges.",
                ],
            ),
            (
                "Escalation Rules",
                [
                    "If a Platinum return request is not acknowledged within 2 business hours, the case should be escalated to Member Resolution.",
                    "Member Resolution may grant one courtesy exception per rolling 12-month period.",
                ],
            ),
        ],
    },
    {
        "filename": "auroracare_canada_exception_sheet.pdf",
        "title": "AuroraCare Canada Exception Sheet",
        "subtitle": "Regional exceptions for products shipped to Canadian customers",
        "sections": [
            (
                "Canada-Specific Windows",
                [
                    "EchoLoop speakers shipped to Canada may be returned within 21 calendar days of delivery.",
                    "LumaDock charging hubs shipped to Canada may be returned within 21 calendar days.",
                    "PulseBand wearables shipped to Canada remain eligible for return within 10 calendar days, even after activation, unless the device shows visible damage.",
                ],
            ),
            (
                "Regional Fees",
                [
                    "Canada returns for EchoLoop speakers incur a flat 8 percent restocking fee when the box has been opened.",
                    "No restocking fee applies for weather-delay replacements approved by the Canada Logistics team.",
                    "Cross-border brokerage charges are never refunded unless the shipment was sent in error.",
                ],
            ),
            (
                "Priority Handling",
                [
                    "Canadian exception requests must reference the shipment province in the case notes.",
                    "The Toronto Review Queue checks Canada exception tickets three times each business day.",
                ],
            ),
        ],
    },
]


CONFLICT_PROMPTS_MD = """# Mock Conflict Policy Test Pack

These PDFs intentionally contain overlapping products with different rules so you can test retrieval quality and source citations.

## Files

- `auroracare_core_returns_policy.pdf`
- `auroracare_platinum_member_addendum.pdf`
- `auroracare_canada_exception_sheet.pdf`

## Suggested Questions

1. `What is the EchoLoop speaker return window in the AuroraCare core policy?`
2. `What does the Platinum addendum say about EchoLoop speaker restocking fees?`
3. `Does the Canada exception sheet allow activated PulseBand wearables to be returned?`
4. `Compare the EchoLoop return windows across the core policy, Platinum addendum, and Canada exception sheet.`
5. `Which uploaded file says EchoLoop speakers can be returned within 30 days?`
6. `Which uploaded file says opened EchoLoop speaker returns incur a 15 percent restocking fee?`

## Stress-Test Prompts

- `I found three different EchoLoop return windows. Summarize each one and cite the exact source file.`
- `Do the AuroraCare uploads conflict on activated PulseBand returns? If so, explain the difference by document.`
- `Tell me whether a Canadian Platinum customer returning an opened EchoLoop speaker should expect a 5 percent, 8 percent, or 15 percent fee, and call out any ambiguity.`

## What Good Retrieval Looks Like

- The answer should name the specific file when rules differ.
- The source block should show page and line references from the matching uploaded document.
- A good answer should mention uncertainty when two uploaded files conflict without enough customer context.
"""


def _new_page(doc: fitz.Document) -> tuple[fitz.Page, fitz.Rect]:
    page = doc.new_page(width=595, height=842)  # A4
    usable = fitz.Rect(56, 56, 539, 786)
    return page, usable


def _insert_wrapped_text(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    *,
    fontname: str = "helv",
    fontsize: int = 11,
    color: tuple[float, float, float] = (0.12, 0.12, 0.16),
    bullet: bool = False,
) -> float:
    """Insert wrapped text and return the bottom y-position."""
    max_chars = max(40, int(rect.width // (fontsize * 0.52)))
    lines = textwrap.wrap(text, width=max_chars)
    y = rect.y0
    for idx, line in enumerate(lines):
        prefix = "• " if bullet and idx == 0 else ("  " if bullet else "")
        page.insert_text(
            fitz.Point(rect.x0, y),
            f"{prefix}{line}",
            fontname=fontname,
            fontsize=fontsize,
            color=color,
        )
        y += fontsize + 6
    return y


def _draw_policy_pdf(output_path: Path, policy: dict) -> None:
    doc = fitz.open()
    page, usable = _new_page(doc)

    y = usable.y0
    page.insert_text(
        fitz.Point(usable.x0, y),
        policy["title"],
        fontname="hebo",
        fontsize=22,
        color=(0.07, 0.17, 0.31),
    )
    y += 30
    page.insert_text(
        fitz.Point(usable.x0, y),
        policy["subtitle"],
        fontname="helv",
        fontsize=11,
        color=(0.32, 0.35, 0.40),
    )
    y += 18
    page.draw_line(
        fitz.Point(usable.x0, y),
        fitz.Point(usable.x1, y),
        color=(0.76, 0.81, 0.88),
        width=1,
    )
    y += 22

    for heading, bullets in policy["sections"]:
        needed_height = 34 + len(bullets) * 34
        if y + needed_height > usable.y1:
            page, usable = _new_page(doc)
            y = usable.y0

        page.insert_text(
            fitz.Point(usable.x0, y),
            heading,
            fontname="hebo",
            fontsize=14,
            color=(0.15, 0.19, 0.28),
        )
        y += 22
        for bullet in bullets:
            y = _insert_wrapped_text(
                page,
                fitz.Rect(usable.x0, y, usable.x1, usable.y1),
                bullet,
                bullet=True,
            )
            y += 6
        y += 8

    for index, current_page in enumerate(doc, start=1):
        footer = f"Mock policy upload test pack - page {index}"
        current_page.insert_text(
            fitz.Point(56, 812),
            footer,
            fontname="helv",
            fontsize=9,
            color=(0.45, 0.48, 0.52),
        )

    doc.save(output_path)
    doc.close()


def _generate_policy_pack(
    policies: list[dict],
    prompts_md: str,
    output_dir: Path,
) -> list[Path]:
    """Generate one PDF policy pack and its prompt cheat sheet."""
    output_dir.mkdir(parents=True, exist_ok=True)

    created_files = []
    for policy in policies:
        output_path = output_dir / policy["filename"]
        _draw_policy_pdf(output_path, policy)
        created_files.append(output_path)

    prompt_guide = output_dir / "UPLOAD_TEST_QUERIES.md"
    prompt_guide.write_text(prompts_md, encoding="utf-8")
    created_files.append(prompt_guide)

    return created_files


def generate_mock_upload_pdfs(output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Generate the standard mock upload PDF pack."""
    return _generate_policy_pack(POLICIES, PROMPTS_MD, output_dir)


def generate_mock_conflict_upload_pdfs(
    output_dir: Path = CONFLICT_OUTPUT_DIR,
) -> list[Path]:
    """Generate a conflicting-policy pack for tougher RAG testing."""
    return _generate_policy_pack(CONFLICT_POLICIES, CONFLICT_PROMPTS_MD, output_dir)


if __name__ == "__main__":
    standard = generate_mock_upload_pdfs()
    conflict = generate_mock_conflict_upload_pdfs()
    print("Generated mock upload test pack:")
    for file_path in standard:
        print(f"  - {file_path}")
    print("Generated conflicting mock upload test pack:")
    for file_path in conflict:
        print(f"  - {file_path}")
