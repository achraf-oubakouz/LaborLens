CREATE TABLE IF NOT EXISTS offres_par_jour (
    date DATE PRIMARY KEY,
    nb_offres INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS offres_par_ville (
    city VARCHAR(100) PRIMARY KEY,
    nb_offres INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS offres_par_secteur (
    sector VARCHAR(150) PRIMARY KEY,
    nb_offres INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS offres_par_contrat (
    contract_type VARCHAR(50) PRIMARY KEY,
    nb_offres INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS top_competences (
    skill VARCHAR(100) PRIMARY KEY,
    nb_mentions INTEGER NOT NULL
);
