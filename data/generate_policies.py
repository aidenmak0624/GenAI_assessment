"""
Download publicly available company policy PDFs for the knowledge base.

These PDFs come from official company-hosted URLs so the seeded document corpus
matches the assignment brief more closely than synthetic demo policies.
"""

from __future__ import annotations

import json
import os
import urllib.request

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
POLICY_MANIFEST_PATH = os.path.join(DOCS_DIR, "policy_sources.json")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
LEGACY_POLICY_FILENAMES = [
    "refund_policy.pdf",
    "privacy_policy.pdf",
    "support_policy.pdf",
]

POLICY_SOURCES = [
    {
        "filename": "bestbuy_return_exchange_policy.pdf",
        "title": "Best Buy Return & Exchange Policy",
        "provider": "Best Buy",
        "url": (
            "https://partners.bestbuy.com/documents/20126/3029894/"
            "Return%2B%26%2BExchange%2BPolicy.pdf/"
            "ee165181-38ed-21af-be39-30c2c7b34597?t=1629819812060"
        ),
        "topic": "refunds_returns",
    },
    {
        "filename": "apple_privacy_policy.pdf",
        "title": "Apple Privacy Policy",
        "provider": "Apple",
        "url": "https://www.apple.com/legal/privacy/pdfs/apple-privacy-policy-en-ww.pdf",
        "topic": "privacy",
    },
    {
        "filename": "azure_support_plans.pdf",
        "title": "Microsoft Azure Support Plans Datasheet",
        "provider": "Microsoft Azure",
        "url": (
            "https://azure.microsoft.com/mediahandler/files/resourcefiles/"
            "azure-support-plans-datasheet/Azure%20Support%20Datasheet_FINAL.pdf"
        ),
        "topic": "support_sla",
    },
]


def _download_pdf(url: str, destination: str) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get("content-type", "")

    if "pdf" not in content_type.lower() and not payload.startswith(b"%PDF"):
        raise ValueError(f"URL did not return a PDF document: {url}")

    with open(destination, "wb") as file_obj:
        file_obj.write(payload)
    return len(payload)


def _write_manifest() -> None:
    with open(POLICY_MANIFEST_PATH, "w", encoding="utf-8") as file_obj:
        json.dump(POLICY_SOURCES, file_obj, indent=2)


def _cleanup_seeded_policy_files() -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)
    managed_filenames = [policy["filename"] for policy in POLICY_SOURCES]
    for filename in managed_filenames + LEGACY_POLICY_FILENAMES:
        path = os.path.join(DOCS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)


def _download_policy_document(policy: dict) -> str:
    os.makedirs(DOCS_DIR, exist_ok=True)
    destination = os.path.join(DOCS_DIR, policy["filename"])
    size_bytes = _download_pdf(policy["url"], destination)
    print(
        f"  Downloaded: {policy['filename']} "
        f"({size_bytes // 1024} KB) from {policy['provider']}"
    )
    return destination


def generate_refund_policy() -> str:
    return _download_policy_document(POLICY_SOURCES[0])


def generate_privacy_policy() -> str:
    return _download_policy_document(POLICY_SOURCES[1])


def generate_support_policy() -> str:
    return _download_policy_document(POLICY_SOURCES[2])


def generate_all_policies() -> list[str]:
    """Download the default public-company policy PDFs into docs/."""
    print("Downloading public policy PDFs...")
    _cleanup_seeded_policy_files()
    downloaded_files = [
        generate_refund_policy(),
        generate_privacy_policy(),
        generate_support_policy(),
    ]
    _write_manifest()
    print(f"  Wrote manifest: {POLICY_MANIFEST_PATH}")
    print("Done.")
    return downloaded_files


if __name__ == "__main__":
    generate_all_policies()
