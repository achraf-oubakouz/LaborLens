from datetime import date


def scrape_sample_jobs() -> list[dict[str, str]]:
    today = date.today().isoformat()

    return [
        {
            "source": "sample",
            "title": "Data Analyst Junior",
            "company": "Atlas Analytics",
            "city": "Casablanca",
            "sector": "Informatique",
            "description": "Analyse de donnees, dashboards Power BI, SQL, Excel et communication avec les equipes metier.",
            "experience_level": "Debutant",
            "contract_type": "CDI",
            "published_at": today,
            "url": "https://example.com/jobs/data-analyst-junior",
        },
        {
            "source": "sample",
            "title": "Developpeur Python",
            "company": "Rabat Tech",
            "city": "Rabat",
            "sector": "Technologie",
            "description": "Developpement backend avec Python, Docker, Git, SQL et bonnes pratiques Linux.",
            "experience_level": "2 ans",
            "contract_type": "CDI",
            "published_at": today,
            "url": "https://example.com/jobs/developpeur-python",
        },
        {
            "source": "sample",
            "title": "Stagiaire Business Intelligence",
            "company": "Marrakech Services",
            "city": "Marrakech",
            "sector": "Services",
            "description": "Stage BI avec Excel, Power BI, SQL, analyse de donnees et presentation des resultats.",
            "experience_level": "Stage",
            "contract_type": "Stage",
            "published_at": today,
            "url": "https://example.com/jobs/stage-bi",
        },
        {
            "source": "sample",
            "title": "Ingenieur DevOps",
            "company": "Casa Cloud",
            "city": "Casa",
            "sector": "Cloud",
            "description": "Mise en place CI/CD avec Docker, Kubernetes, Linux, Git, AWS et supervision.",
            "experience_level": "3 ans",
            "contract_type": "CDI",
            "published_at": today,
            "url": "https://example.com/jobs/ingenieur-devops",
        },
    ]
