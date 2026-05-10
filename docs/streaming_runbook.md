# Streaming Runbook

Use this when Docker or the app has been shut down and you want to restart the streaming pipeline.

## Start From A Clean Local Session

Open Docker Desktop and wait until it is running.

Open PowerShell:

```powershell
cd C:\Projects\LaborLens
.\venv\Scripts\activate
```

Start services, apply schema, and create Kafka topics:

```powershell
.\scripts\start_streaming_stack.ps1
```

Start the consumer in terminal 1:

```powershell
.\scripts\run_consumer.ps1
```

Start producers through the supervisor in terminal 2:

```powershell
.\scripts\run_streaming_supervisor.ps1
```

Open Superset:

```text
http://localhost:8089
```

Refresh the streaming dashboard.

## Optional LinkedIn Import

Create a local LinkedIn CSV from the template:

```powershell
Copy-Item .\data\imports\linkedin_jobs_template.csv .\data\imports\linkedin_jobs.csv
```

Edit `data/imports/linkedin_jobs.csv`, then publish:

```powershell
.\scripts\publish_linkedin_import.ps1 -CsvPath data/imports/linkedin_jobs.csv
```

## Health Checks

```powershell
docker compose ps
```

Expected services:

- `emploi_maroc_postgres`
- `laborlens_kafka`
- `laborlens_schema_registry`
- `emploi_maroc_superset`

Check row counts:

```powershell
docker compose exec postgres psql -U emploi -d emploi_maroc -c "SELECT COUNT(*) FROM jobs_clean_stream;"
docker compose exec postgres psql -U emploi -d emploi_maroc -c "SELECT COUNT(*) FROM job_skills_stream;"
docker compose exec postgres psql -U emploi -d emploi_maroc -c "SELECT status, COUNT(*) FROM stream_producer_runs GROUP BY status;"
docker compose exec postgres psql -U emploi -d emploi_maroc -c "SELECT status, COUNT(*) FROM stream_consumer_batches GROUP BY status;"
```

## Stop Safely

Stop Python processes with `Ctrl+C`.

Stop containers without deleting data:

```powershell
docker compose stop
```

Avoid this unless you want to reset all local data:

```powershell
docker compose down -v
```

