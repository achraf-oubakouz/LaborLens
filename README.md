# Plateforme d'Analyse du Marche de l'Emploi au Maroc

Ce projet construit un pipeline data pour collecter, nettoyer et analyser les offres d'emploi publiees au Maroc.

L'objectif est de repondre a des questions concretes :

- Quels metiers sont les plus demandes ?
- Quelles competences reviennent le plus souvent ?
- Quelles villes concentrent les opportunites ?
- Quels secteurs et types de contrats recrutent le plus ?

## Architecture

```text
Sources web / CSV
  -> Airflow DAGs
  -> scraping/import Python
  -> MinIO data lake Bronze Avro / Silver Parquet / Gold CSV
  -> PostgreSQL warehouse
  -> Great Expectations quality summaries
  -> Superset dashboards
```

Version streaming locale en cours :

```text
Scrapers Python -> Kafka Avro -> Consumer Python
                             -> PostgreSQL streaming tables -> Superset
                             -> Parquet micro-batches
```

## Structure

```text
.
|-- config/
|   |-- skills.yml
|   `-- sources.yml
|-- data/
|   |-- bronze/
|   |-- silver/
|   `-- gold/
|-- dags/
|   |-- daily_scraping_batch.py
|   |-- medallion_transform_load.py
|   `-- data_quality_checks.py
|-- governance/
|   |-- data_dictionary.csv
|   |-- lineage.csv
|   `-- transformation_versions.csv
|-- great_expectations/
|   `-- expectations/
|-- quality/
|   |-- ge_runner.py
|   `-- validate_silver.py
|-- sql/
|   `-- schema.sql
|-- src/
|   |-- common/
|   |-- pipelines/
|   `-- scrapers/
|-- docker-compose.yml
|-- requirements.txt
`-- run_pipeline.py
```

## Documentation projet

- `docs/architecture.md` : architecture batch, streaming et medaillon.
- `docs/streaming_runbook.md` : comment demarrer, verifier et arreter le streaming local.
- `docs/data_dictionary.md` : dictionnaire des tables principales.
- `docs/dashboard_guide.md` : guide de creation des dashboards Superset.
- `governance/*.csv` : catalogue, lineage et versions de transformation.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Si vous avez deja cree l'environnement virtuel, relancez cette commande apres chaque mise a jour de `requirements.txt`.

## Lancer le MVP

Le MVP utilise des donnees exemple pour verifier toute la chaine sans dependre d'un site web.

```bash
python run_pipeline.py --sample
python quality/validate_silver.py
```

Pour scraper Rekrute :

```bash
python run_pipeline.py --source rekrute --pages 1
python quality/validate_silver.py
```

Pour scraper Emploi.ma :

```bash
python run_pipeline.py --source emploi_ma --pages 5 --all-bronze --load-postgres
python quality/validate_silver.py
```

Emploi.ma peut bloquer les URLs de recherche par mot-cle. Le scraper utilise donc les pages generales et filtre localement si un mot-cle est fourni.
Le scraper utilise `curl_cffi` pour imiter un navigateur lorsque le site bloque les requetes Python classiques.

Pour scraper MarocAnnonces :

```bash
python run_pipeline.py --source maroc_annonces --pages 5 --all-bronze --load-postgres
python quality/validate_silver.py
```

Pour ajouter LinkedIn comme source locale :

```powershell
Copy-Item .\data\imports\linkedin_jobs_template.csv .\data\imports\linkedin_jobs.csv
```

Remplir `data/imports/linkedin_jobs.csv`, puis publier dans Kafka :

```powershell
.\scripts\publish_linkedin_import.ps1 -CsvPath data/imports/linkedin_jobs.csv
```

LinkedIn est integre comme import CSV/API, pas comme scraper direct, afin d'eviter les blocages et les problemes de conditions d'utilisation.

Option avec mot-cle :

```bash
python run_pipeline.py --source rekrute --pages 2 --keyword python
```

Option recommandee pour un dashboard plus riche avec Rekrute :

```bash
python run_pipeline.py --source rekrute --pages 5 --keywords data,python,finance,marketing,rh,commercial,comptable,logistique,ingenieur,developpeur --all-bronze --load-postgres
```

Option recommandee pour un dashboard multi-sources :

```bash
python run_pipeline.py --source all --pages 10 --keywords data,python,finance,marketing,rh,commercial,comptable,logistique,ingenieur,developpeur --all-bronze --load-postgres
```

Cette commande :

- scrape plusieurs mots-cles ;
- conserve chaque collecte dans `data/bronze/` ;
- reconstruit Silver et Gold depuis tout l'historique Bronze ;
- recharge PostgreSQL pour Superset.

La source `all` combine Rekrute et MarocAnnonces. Emploi.ma reste disponible separement, mais peut etre bloque par le site.
Avec `--source all`, les mots-cles sont appliques a Rekrute. MarocAnnonces est collecte en mode large pour recuperer plus d'offres.

Pour reconstruire les tables analytiques depuis les fichiers Bronze deja collectes :

```bash
python run_pipeline.py --source all --rebuild-only --load-postgres
```

Pour verifier les sources presentes dans Silver :

```bash
python inspect_sources.py
```

Pour charger les tables Gold dans PostgreSQL :

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U emploi -d emploi_maroc < sql/schema.sql
python load_gold_to_postgres.py
```

Ou en une seule commande apres le pipeline :

```bash
python run_pipeline.py --source rekrute --pages 1 --keyword python --load-postgres
```

Par defaut, le chargement utilise :

```text
postgresql+psycopg2://emploi:emploi@127.0.0.1:5432/emploi_maroc
```

Vous pouvez utiliser une autre base avec la variable `DATABASE_URL`.

Les sorties sont generees dans :

- `data/bronze/` : offres brutes Avro, avec JSON de debug
- `data/silver/` : offres nettoyees Parquet, avec CSV de debug
- `data/gold/` : agregats pour dashboard

MinIO est la cible officielle du data lake. Les dossiers `data/` restent un miroir local de debug.

Variables MinIO par defaut :

```text
MINIO_ENDPOINT=http://127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=laborlens
```

Initialiser le bucket :

```bash
python setup_minio_bucket.py
```

Chemins lake canoniques :

- Bronze : `bronze/<source>/<yyyy-mm-dd>/<run_id>/offers.avro`
- Silver : `silver/jobs/date=<yyyy-mm-dd>/part-*.parquet`
- Gold : `gold/<table_name>/<yyyy-mm-dd>.csv`

Le pipeline garde des CSV/JSON pour inspection locale, mais les formats principaux sont :

- Bronze : Avro schema-based
- Silver : Parquet analytique
- Gold : CSV lake et PostgreSQL pour Superset

## Superset

Ajouter les datasets suivants depuis PostgreSQL :

- `offres_clean` : table detaillee pour filtres, KPI et exploration.
- `offres_par_jour` : evolution du nombre d'offres.
- `offres_par_ville` : offres par ville ou region.
- `offres_par_secteur` : offres par secteur.
- `offres_par_contrat` : offres par type de contrat.
- `top_competences` : competences les plus mentionnees.
- `offer_skills` : une ligne par offre et competence detectee.

Charts recommandes avec `offres_clean` :

- KPI total : nombre de lignes.
- KPI entreprises : nombre distinct de `company`.
- KPI regions : nombre distinct de `city`.
- Bar chart : offres par `source`.
- Bar chart : offres par `source` et `contract_type`.
- Table : `title`, `company`, `city`, `contract_type`, `published_at`, `url`.

Filtres dashboard recommandes :

- `source`
- `city`
- `contract_type`
- `published_at`

Charts recommandes avec `offer_skills` :

- Bar chart : top competences par `source`.
- Bar chart : top competences par `city`.
- Line chart : mentions de competences par `published_at`.
- Table : `published_at`, `source`, `title`, `company`, `city`, `skill`, `url`.

Datasets streaming a ajouter dans Superset :

- `jobs_clean_stream` : offres nettoyees en quasi temps reel.
- `job_skills_stream` : competences extraites en quasi temps reel.
- `stream_producer_runs` : suivi des collectes/publish Kafka.
- `stream_consumer_batches` : suivi des batchs consommes et charges.
- `stream_dead_letter_jobs` : messages invalides rejetes par le consumer.
- `data_quality_results` : resultats des controles qualite batch et streaming.

Ces tables sont alimentees par Kafka et peuvent remplacer progressivement `offres_clean` et `offer_skills` dans les dashboards.

Charts de monitoring recommandes :

- Big Number : dernier `finished_at` avec `status = success` dans `stream_producer_runs`.
- Bar chart : `SUM(rows_published)` par `source`.
- Table : derniers runs producteurs avec `source`, `keyword`, `status`, `rows_published`, `error_message`.
- Big Number : dernier `finished_at` dans `stream_consumer_batches`.
- Bar chart : `SUM(rows_processed)` par heure.
- Table : derniers batchs consommateurs avec `status`, `rows_processed`, `skills_processed`, `error_message`.
- Big Number : nombre de lignes dans `stream_dead_letter_jobs`.
- Bar chart : dead letters par `reason`.
- Table : derniers rejets avec `created_at`, `source`, `title`, `reason`, `url`.
- Bar chart : controles qualite par `status`.
- Table : derniers resultats qualite avec `target`, `check_name`, `severity`, `status`, `failed_count`, `details`.

## Qualite des donnees

Les controles qualite couvrent :

- titre obligatoire ;
- source obligatoire ;
- URL unique quand elle existe ;
- date de publication presente ou flaggee ;
- ville connue ou normalisee ;
- contenu d'au moins 50 caracteres.

Appliquer le schema avant de persister les resultats :

```powershell
.\scripts\apply_schema.ps1
```

Controle batch Silver :

```powershell
.\scripts\run_batch_quality.ps1
```

Controle batch avec Great Expectations :

```bash
python quality/ge_runner.py --target batch --persist
```

Controle streaming PostgreSQL :

```powershell
.\scripts\run_stream_quality.ps1
```

Controle streaming avec Great Expectations :

```bash
python quality/ge_runner.py --target stream --persist
```

Les resultats sont stockes dans `data_quality_results` pour Superset.

Suites Great Expectations :

- `great_expectations/expectations/offres_clean.json`
- `great_expectations/expectations/jobs_clean_stream.json`

## Streaming local

Installer les dependances :

```bash
pip install -r requirements.txt
```

Demarrage rapide PowerShell :

```powershell
.\scripts\start_streaming_stack.ps1
```

Terminal 1 - consumer :

```powershell
.\scripts\run_consumer.ps1
```

Terminal 2 - producer Rekrute :

```powershell
.\scripts\run_rekrute_stream.ps1 -Pages 1 -Keyword python -IntervalSeconds 60
```

Terminal 3 - producer MarocAnnonces :

```powershell
.\scripts\run_maroc_annonces_stream.ps1 -Pages 2 -IntervalSeconds 120
```

Alternative recommandee - supervisor multi-sources :

```powershell
.\scripts\run_streaming_supervisor.ps1 -RekrutePages 1 -RekruteKeyword python -RekruteIntervalSeconds 60 -MarocAnnoncesPages 2 -MarocAnnoncesIntervalSeconds 120
```

Avec import LinkedIn periodique :

```powershell
.\scripts\run_streaming_supervisor.ps1 -IncludeLinkedIn -LinkedInIntervalSeconds 300
```

Demarrer les services locaux :

```bash
docker compose up -d postgres kafka schema-registry
```

Creer le topic Kafka :

```bash
python create_kafka_topics.py
```

Appliquer le schema PostgreSQL :

```powershell
Get-Content .\sql\schema.sql | docker compose exec -T postgres psql -U emploi -d emploi_maroc
```

Lancer le consumer dans un terminal :

```bash
python -m src.streaming.consumer
```

Publier une collecte Rekrute dans un deuxieme terminal :

```bash
python -m src.streaming.producer --source rekrute --pages 1 --keyword python
```

Publier en boucle toutes les 60 secondes :

```bash
python -m src.streaming.producer --source rekrute --pages 1 --keyword python --loop --interval-seconds 60
```

Publier MarocAnnonces :

```bash
python -m src.streaming.producer --source maroc_annonces --pages 2
```

Les donnees streaming sont ecrites dans :

- PostgreSQL : `jobs_clean_stream`, `job_skills_stream`
- Parquet : `data/lake/silver/jobs/date=.../hour=.../`

Le pipeline batch `run_pipeline.py` reste disponible pour les backfills et les reconstructions completes.

## Redemarrage local apres arret

Quand Docker Desktop ou les terminaux ont ete fermes :

1. Ouvrir Docker Desktop et attendre qu'il soit pret.
2. Ouvrir un terminal PowerShell dans le projet.
3. Activer l'environnement virtuel :

```powershell
.\venv\Scripts\activate
```

4. Demarrer les services et verifier le schema/topic :

```powershell
.\scripts\start_streaming_stack.ps1
```

5. Terminal 1 - lancer le consumer :

```powershell
.\scripts\run_consumer.ps1
```

6. Terminal 2 - lancer le supervisor multi-sources :

```powershell
.\scripts\run_streaming_supervisor.ps1
```

7. Ouvrir Superset :

```text
http://localhost:8089
```

8. Rafraichir le dashboard streaming.

Pour arreter proprement les producteurs/consumer, utiliser `Ctrl+C` dans leurs terminaux.
Pour arreter les conteneurs sans supprimer les donnees :

```powershell
docker compose stop
```

Eviter sauf besoin explicite :

```powershell
docker compose down -v
```

car `-v` supprime les volumes PostgreSQL et Superset.

## Docker

Demarrer PostgreSQL, MinIO et Superset :

```bash
docker compose up -d
```

Services par defaut :

- PostgreSQL : `localhost:5432`
- MinIO console : `http://localhost:9001`
- Superset : `http://localhost:8089`
- Airflow : `http://localhost:8080` (`admin` / `admin`)

## Airflow

Les DAGs sont montes depuis `dags/` :

- `daily_scraping_batch` : setup MinIO, scraping Rekrute, scraping MarocAnnonces, import LinkedIn CSV si present.
- `medallion_transform_load` : Bronze vers Silver/Gold, chargement PostgreSQL, resume qualite batch.
- `data_quality_checks` : validations Great Expectations batch et streaming.

Chaque tache appelle les scripts existants du projet depuis `/opt/airflow/project`, pour eviter de dupliquer la logique metier dans les DAGs.
