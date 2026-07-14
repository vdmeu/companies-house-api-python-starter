"""
Companies House REST API -- Python starter kit.

Covers the three things that trip people up when they first integrate:
  1. Auth: HTTP Basic Auth with your API key as the *username* (empty password)
  2. Rate limits: 600 requests / 5 minutes, returns 429 + Retry-After when exceeded
  3. Pagination: officer/PSC/filing-history lists use start_index + items_per_page

Get a free API key: https://developer.company-information.service.gov.uk
(Applications are usually approved within minutes.)
"""

import os
import time

import requests

BASE_URL = "https://api.company-information.service.gov.uk"


def request_with_backoff(url: str, api_key: str, params: dict | None = None, max_retries: int = 5) -> dict:
    """GET with Companies House's auth scheme and 429 backoff.

    CH doesn't use a bearer token or an X-API-Key header -- your key goes
    in as the HTTP Basic Auth *username*, with an empty password. Passing
    it any other way returns a 401 with a message that doesn't make this
    obvious.
    """
    for attempt in range(max_retries):
        response = requests.get(url, auth=(api_key, ""), params=params, timeout=10)
        if response.status_code == 429:
            # CH sends Retry-After in seconds -- respect it rather than guessing.
            wait_seconds = int(response.headers.get("Retry-After", 5))
            time.sleep(wait_seconds)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Still rate-limited after {max_retries} retries")


def get_company(company_number: str, api_key: str) -> dict:
    """Basic company profile."""
    return request_with_backoff(f"{BASE_URL}/company/{company_number}", api_key)


def get_all_officers(company_number: str, api_key: str, page_size: int = 35) -> list[dict]:
    """Officer lists are paginated -- items_per_page + start_index, not a page number.

    A company with a long history of appointments needs several requests
    to get everyone; naive code that only reads the first page silently
    drops officers.
    """
    officers: list[dict] = []
    start_index = 0
    while True:
        page = request_with_backoff(
            f"{BASE_URL}/company/{company_number}/officers",
            api_key,
            params={"items_per_page": page_size, "start_index": start_index},
        )
        officers.extend(page.get("items", []))
        start_index += page_size
        if start_index >= page.get("total_results", 0):
            break
    return officers


def get_latest_accounts_status(company_number: str, api_key: str) -> dict:
    """The iXBRL-vs-PDF gotcha that catches almost everyone building on top of CH.

    filing-history only gives you *metadata* about a filing, not the document
    itself. To check whether structured financial data actually exists:
      1. Find the latest "accounts" filing in filing-history
      2. Follow links.document_metadata to the Document API
      3. Check the `resources` map for which content types are available
      4. Only request content with an Accept header matching one you found

    Crucially: `resources` frequently lists only application/pdf, not
    application/xhtml+xml (iXBRL). A large share of UK companies file
    small-company or micro-entity accounts that Companies House stores as
    flat, sometimes scanned, PDFs -- there is no structured data in them
    to parse, no matter how good your XBRL parser is. Always check
    `resources` before assuming iXBRL exists; don't find out from a
    parse failure three steps downstream.
    """
    history = request_with_backoff(
        f"{BASE_URL}/company/{company_number}/filing-history",
        api_key,
        params={"category": "accounts"},
    )
    items = history.get("items", [])
    if not items:
        return {"available": False, "reason": "no accounts filings found"}

    latest = items[0]
    doc_metadata_url = latest.get("links", {}).get("document_metadata")
    if not doc_metadata_url:
        return {"available": False, "reason": "filing has no linked document"}

    metadata = request_with_backoff(doc_metadata_url, api_key)
    resources = metadata.get("resources", {})

    if "application/xhtml+xml" in resources:
        return {"available": True, "format": "ixbrl", "filed_on": latest.get("date")}
    if "application/pdf" in resources:
        return {"available": False, "reason": "PDF only -- no structured iXBRL data to parse", "filed_on": latest.get("date")}
    return {"available": False, "reason": f"unrecognised formats: {list(resources)}"}


if __name__ == "__main__":
    api_key = os.environ.get("CH_API_KEY", "")
    if not api_key:
        raise SystemExit("Set CH_API_KEY -- get one free at https://developer.company-information.service.gov.uk")

    company_number = "00445790"  # Tesco PLC -- a large, active company good for testing

    company = get_company(company_number, api_key)
    print(f"{company['company_name']} ({company['company_number']}) -- {company['company_status']}")

    officers = get_all_officers(company_number, api_key)
    print(f"{len(officers)} officer records (including resigned)")

    accounts = get_latest_accounts_status(company_number, api_key)
    print(f"Latest accounts: {accounts}")
