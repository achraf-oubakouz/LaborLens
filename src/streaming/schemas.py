JOB_OFFER_SCHEMA = """
{
  "type": "record",
  "name": "JobOfferRaw",
  "namespace": "laborlens",
  "fields": [
    {"name": "source", "type": "string"},
    {"name": "title", "type": ["null", "string"], "default": null},
    {"name": "company", "type": ["null", "string"], "default": null},
    {"name": "city", "type": ["null", "string"], "default": null},
    {"name": "sector", "type": ["null", "string"], "default": null},
    {"name": "description", "type": ["null", "string"], "default": null},
    {"name": "experience_level", "type": ["null", "string"], "default": null},
    {"name": "contract_type", "type": ["null", "string"], "default": null},
    {"name": "published_at", "type": ["null", "string"], "default": null},
    {"name": "url", "type": ["null", "string"], "default": null},
    {"name": "scraped_at", "type": "string"}
  ]
}
"""

