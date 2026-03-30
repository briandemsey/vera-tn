# VERA-TN

**Verification Engine for Results & Accountability - Tennessee**

Post-ASD infrastructure for Tennessee's new three-tiered intervention system. Early warning signals the Achievement School District never had.

## Features

- **School Dashboard** - Browse 1,900+ Tennessee schools with live NCES data
- **Tiered Intervention** - Understand the new Tier 1/2/3 system launching 2026-27
- **County Explorer** - Drill into county-level school data
- **Locale Analysis** - Urban-rural education landscape insights

## Background

The Achievement School District (ASD) was shut down in 2025 after 15 years (75-15 legislative vote). Tennessee's new three-tiered intervention system launches 2026-27.

VERA provides the early warning infrastructure the ASD never had.

## Data Source

Live data from NCES EDGE (National Center for Education Statistics):
- Endpoint: nces.ed.gov/opengis/rest/services
- Coverage: All Tennessee public schools
- School Year: 2023-24

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Configured for Render.com auto-deployment via GitHub.

Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

## Part of H-EDU.Solutions

An initiative of [Hallucinations.cloud](https://hallucinations.cloud)
