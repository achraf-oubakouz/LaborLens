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

- `data/bronze/` : offres brutes
- `data/silver/` : offres nettoyees
- `data/gold/` : agregats pour dashboard

## Superset

Ajouter les datasets suivants depuis PostgreSQL :

- `offres_clean` : table detaillee pour filtres, KPI et exploration.
- `offres_par_jour` : evolution du nombre d'offres.
- `offres_par_ville` : offres par ville ou region.
- `offres_par_secteur` : offres par secteur.
- `offres_par_contrat` : offres par type de contrat.
- `top_competences` : competences les plus mentionnees.

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

1. Ajouter des KPI et filtres Superset par source, region, secteur et contrat.
2. Ajouter Airflow pour orchestrer le scraping quotidien.
3. Ajouter Great Expectations pour formaliser la qualite.
