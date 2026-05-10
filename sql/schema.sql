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
    skills TEXT,
    silver_transform_version VARCHAR(80),
    skills_extraction_version VARCHAR(80)
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

CREATE TABLE IF NOT EXISTS offer_skills (
    source VARCHAR(50),
    title TEXT,
    company TEXT,
    city VARCHAR(150),
    contract_type VARCHAR(100),
    published_at DATE,
    url TEXT,
    skill VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS jobs_clean_stream (
    job_id TEXT PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
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
    skills TEXT,
    scraped_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_skills_stream (
    job_id TEXT NOT NULL,
    source VARCHAR(50),
    title TEXT,
    company TEXT,
    city VARCHAR(150),
    contract_type VARCHAR(100),
    published_at DATE,
    url TEXT,
    skill VARCHAR(100),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (job_id, skill)
);

CREATE TABLE IF NOT EXISTS stream_producer_runs (
    run_id TEXT PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    keyword TEXT,
    pages INTEGER,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    rows_published INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS stream_consumer_batches (
    batch_id TEXT PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    rows_processed INTEGER DEFAULT 0,
    skills_processed INTEGER DEFAULT 0,
    parquet_path TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS stream_dead_letter_jobs (
    dead_letter_id TEXT PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    source VARCHAR(50),
    url TEXT,
    title TEXT,
    reason TEXT NOT NULL,
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_quality_results (
    quality_result_id BIGSERIAL PRIMARY KEY,
    run_at TIMESTAMP NOT NULL,
    target VARCHAR(100) NOT NULL,
    check_name VARCHAR(150) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    failed_count INTEGER NOT NULL,
    total_count INTEGER NOT NULL,
    details TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_run_metadata (
    run_id TEXT PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    bronze_paths TEXT,
    silver_path TEXT,
    gold_paths TEXT,
    silver_transform_version VARCHAR(80),
    skills_extraction_version VARCHAR(80),
    error_message TEXT
);
