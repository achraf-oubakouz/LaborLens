import re
from datetime import date
from typing import Any
from urllib.parse import urljoin

from src.common.locations import extract_city


BASE_URL = "https://www.marocannonces.com"
LISTING_URL = f"{BASE_URL}/recrutement-emploi"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _listing_params(page: int) -> dict[str, int] | None:
    return {"pge": page} if page > 1 else None


def _extract_city(title: str) -> str:
    return extract_city(title)


def _clean_title(title: str, city: str) -> str:
    if not city:
        return title
    return _clean_text(re.sub(rf"\b{re.escape(city)}\b", "", title, flags=re.IGNORECASE))


def _matches_keyword(job: dict[str, str], keyword: str) -> bool:
    if not keyword:
        return True
    haystack = " ".join([job.get("title", ""), job.get("city", ""), job.get("description", "")]).lower()
    return keyword.lower() in haystack


def _candidate_links(soup: Any) -> list[Any]:
    links = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = _clean_text(link.get_text(" "))
        if "/annonce/" not in href or not text:
            continue
        key = href
        if key in seen:
            continue
        seen.add(key)
        links.append(link)
    return links


def _parse_job_link(link: Any) -> dict[str, str] | None:
    raw_title = _clean_text(link.get_text(" "))
    if not raw_title:
        return None

    city = _extract_city(raw_title)
    title = _clean_title(raw_title, city)
    url = urljoin(BASE_URL, link["href"])

    return {
        "source": "maroc_annonces",
        "title": title,
        "company": "Non renseigne",
        "city": city,
        "sector": "Non renseigne",
        "description": raw_title,
        "experience_level": "",
        "contract_type": "Non renseigne",
        "published_at": date.today().isoformat(),
        "url": url,
    }


def scrape_maroc_annonces_jobs(max_pages: int = 1, keyword: str = "") -> list[dict[str, str]]:
    try:
        import requests
        from bs4 import BeautifulSoup
        from requests import RequestException
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Dependances manquantes pour scraper MarocAnnonces. "
            "Installez-les avec: pip install -r requirements.txt"
        ) from exc

    jobs: list[dict[str, str]] = []
    seen = set()

    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                LISTING_URL,
                params=_listing_params(page),
                headers=HEADERS,
                timeout=(10, 30),
            )
            response.raise_for_status()
        except RequestException as exc:
            print(
                f"WARNING: MarocAnnonces indisponible pour keyword='{keyword or 'all'}', "
                f"page={page}. Les pages suivantes de ce mot-cle sont ignorees. Detail: {exc}"
            )
            break

        soup = BeautifulSoup(response.text, "html.parser")
        for link in _candidate_links(soup):
            job = _parse_job_link(link)
            if not job or not _matches_keyword(job, keyword):
                continue
            dedupe_key = job["url"]
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            jobs.append(job)

    return jobs

