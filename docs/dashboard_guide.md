# Dashboard Guide

LaborLens ships two final dashboard deliverables: `LaborLens Analytics` for batch warehouse analytics and `LaborLens Streaming` for near-real-time monitoring.

## LaborLens Analytics

Use these datasets:

- `offres_clean`
- `offer_skills`
- `offres_par_jour`
- `offres_par_ville`
- `offres_par_secteur`
- `offres_par_contrat`
- `top_competences`

Recommended charts:

| Chart | Dataset | Configuration |
|---|---|---|
| Weekly Offer Volume | offres_clean | Time-series or bar chart, time column = `published_at`, grain = week, metric = `COUNT(*)` |
| Total Offers | offres_clean | Big Number, `COUNT(*)` |
| Unique Companies | offres_clean | Big Number, distinct company count |
| Offers By Source | offres_clean | Bar chart, X = source, Metric = `COUNT(*)` |
| Offers By City / Region | offres_par_ville or offres_clean | Bar chart, X = city, Metric = `SUM(nb_offres)` or `COUNT(*)`, top 20 |
| Top Sectors This Month | offres_clean | Bar chart, filter `published_at` to current month, X = sector, Metric = `COUNT(*)`, top 10 |
| Offers By Contract Type | offres_clean | Bar chart, X = contract_type, Metric = `COUNT(*)` |
| Top Skills | offer_skills | Bar chart, X = skill, Metric = `COUNT(*)`, top 20 |
| Recent Offers | offres_clean | Table with published_at, source, title, company, city, contract_type, url |

Map note: Superset map visualizations can use `city`/region fields after adding coordinates. For the local demo, the city/region bar chart is the reliable default.

Recommended filters:

- source
- city
- contract_type
- published_at

## LaborLens Streaming

Use these datasets:

- `jobs_clean_stream`
- `job_skills_stream`
- `stream_producer_runs`
- `stream_consumer_batches`
- `stream_dead_letter_jobs`
- `data_quality_results`

Recommended charts:

| Chart | Dataset | Configuration |
|---|---|---|
| Live Total Offers | jobs_clean_stream | Big Number, `COUNT(*)` |
| Live Offers By Source | jobs_clean_stream | Bar chart, X = source, Metric = `COUNT(*)` |
| Live Top Skills | job_skills_stream | Bar chart, X = skill, Metric = `COUNT(*)` |
| Recent Streamed Offers | jobs_clean_stream | Table |
| Rows Published By Source | stream_producer_runs | Bar chart, X = source, Metric = `SUM(rows_published)` |
| Recent Producer Runs | stream_producer_runs | Table |
| Rows Processed Over Time | stream_consumer_batches | Line chart over finished_at |
| Recent Consumer Batches | stream_consumer_batches | Table |
| Dead Letter Count | stream_dead_letter_jobs | Big Number, `COUNT(*)` |
| Quality Results | data_quality_results | Table or bar chart by status |

Set dashboard auto-refresh to 60 seconds for streaming demos.

## Export / Recreation

When dashboard export is available in the local Superset UI, export both dashboards from Settings > Export. If export is unavailable, recreate them manually from the chart matrix above; all required datasets are populated by `load_gold_to_postgres.py`, the streaming consumer, and `quality/ge_runner.py --persist`.
