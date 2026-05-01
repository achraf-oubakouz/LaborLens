# Plateforme d'Analyse du Marche de l'Emploi au Maroc

Ce projet construit un pipeline data pour collecter, nettoyer et analyser les offres d'emploi publiees au Maroc.

L'objectif est de repondre a des questions concretes :

- Quels metiers sont les plus demandes ?
- Quelles competences reviennent le plus souvent ?
- Quelles villes concentrent les opportunites ?
- Quels secteurs et types de contrats recrutent le plus ?

## Architecture

```text
Sources web
  -> scraping Python
  -> data lake local bronze/silver/gold
  -> tables analytiques
  -> PostgreSQL / Superset
```

Version cible :

```text
Scraping -> Kafka -> MinIO Bronze -> Transformations Silver/Gold -> PostgreSQL -> Superset
                                      -> Great Expectations
                                      -> Airflow
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
|-- quality/
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

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

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

Option avec mot-cle :

```bash
python run_pipeline.py --source rekrute --pages 2 --keyword python
```

Pour charger les tables Gold dans PostgreSQL :

```bash
docker compose up -d postgres
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

- `data/bronze/` : offres brutes
- `data/silver/` : offres nettoyees
- `data/gold/` : agregats pour dashboard

## Docker

Demarrer PostgreSQL, MinIO et Superset :

```bash
docker compose up -d
```

Services par defaut :

- PostgreSQL : `localhost:5432`
- MinIO console : `http://localhost:9001`
- Superset : `http://localhost:8088`

## Prochaines etapes

1. Ajouter un scraper reel pour Rekrute ou Emploi.ma.
2. Connecter Superset a PostgreSQL.
3. Ajouter Airflow pour orchestrer le scraping quotidien.
4. Ajouter Great Expectations pour formaliser la qualite.
