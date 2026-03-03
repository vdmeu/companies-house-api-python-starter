# registrum-python

Python starter kit for the [Registrum API](https://registrum.co.uk) — structured UK company data built on Companies House.

## Quick start

```bash
pip install requests
```

```python
import requests

API_KEY = "rg_live_YOUR_KEY_HERE"
BASE_URL = "https://api.registrum.co.uk/v1"

res = requests.get(
    f"{BASE_URL}/company/00445790",
    headers={"X-API-Key": API_KEY},
)
print(res.json())
```

## Get an API key

Free tier: 50 calls/month, no credit card required.

→ [registrum.co.uk](https://registrum.co.uk/#get-key)

## What you get

The Registrum API enriches raw Companies House data with:

- **Structured financials** — turnover, net assets, employees in clean GBP values
- **Director networks** — 2-degree board traversal to find connected entities
- **Intelligent caching** — 24h company data, 7-day financials, resilient during CH outages
- **Fuzzy search** — company name → enriched profile in one call

## API reference

Full documentation: [api.registrum.co.uk/docs](https://api.registrum.co.uk/docs)

## License

Examples in this repo are MIT licensed. Data is sourced under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
