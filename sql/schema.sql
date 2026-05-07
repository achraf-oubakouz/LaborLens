CREATE TABLE IF NOT EXISTS offres_clean (
    source VARCHAR(50),
    title TEXT NOT NULL,
    company TEXT,
    city VARCHAR(150),
    sector VARCHAR(150),
    description TEXT,
    experience_level VARCHAR(150),
    contract_type VARCHAR(100),
    published_at DATE,
    url TEXT,
    content_length INTEGER,
    skills TEXT
);

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
