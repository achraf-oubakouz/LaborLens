import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin


BASE_URL = "https://www.emploi.ma"
LISTING_URL = f"{BASE_URL}/recherche-jobs-maroc"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _parse_french_date(value: str) -> str:
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", value or "")
    if not match:
        return ""
    return datetime.strptime(match.group(1), "%d.%m.%Y").date().isoformat()


def _listing_url(keyword: str) -> str:
    return LISTING_URL


def _matches_keyword(job: dict[str, str], keyword: str) -> bool:
    if not keyword:
        return True

    haystack = " ".join(
        [
            job.get("title", ""),
            job.get("company", ""),
            job.get("city", ""),
            job.get("description", ""),
            job.get("contract_type", ""),
            job.get("experience_level", ""),
        ]
    ).lower()
    return keyword.lower() in haystack


def _get_listing_html(url: str, params: dict[str, int] | None) -> str:
    try:
        from curl_cffi import requests as browser_requests

        response = browser_requests.get(
            url,
            params=params,
            headers=HEADERS,
            impersonate="chrome",
            timeout=30,
        )
        response.raise_for_status()
        return response.text
    except ModuleNotFoundError:
        import requests

        response = requests.get(url, params=params, headers=HEADERS, timeout=(10, 30))
        response.raise_for_status()
        return response.text


def _extract_field(text: str, label: str) -> str:
    labels = (
        "Niveau d.etudes requis|Niveau d.experience|Contrat propose|"
        "Region de|Competences cles|Langues exigees"
    )
    normalized_text = (
        text.replace("´", "'")
        .replace("’", "'")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
        .replace("É", "E")
        .replace("Région", "Region")
        .replace("Compétences", "Competences")
    )
    normalized_label = (
        label.replace("´", "'")
        .replace("’", "'")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
    )
    pattern = rf"{re.escape(normalized_label)}\s*:\s*(.*?)(?=\s+(?:{labels})\s*:|$)"
    match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
    return _clean_text(match.group(1)) if match else ""


def _candidate_blocks(soup: Any) -> list[Any]:
    blocks = []
    seen = set()
    for link in soup.find_all("a", href=True):
        if "/offre-emploi-maroc/" not in link["href"]:
            continue
        heading = link.find_parent(["h2", "h3", "h4"]) or link
        block = heading
        for parent in heading.parents:
            text = _clean_text(parent.get_text(" "))
            if "Contrat propose" in text or "Contrat proposé" in text:
                block = parent
                break
        key = id(block)
        if key not in seen:
            blocks.append(block)
            seen.add(key)
    return blocks


def _parse_job_block(block: Any) -> dict[str, str] | None:
    link = block.find("a", href=lambda href: href and "/offre-emploi-maroc/" in href)
    if link is None:
        return None

    title = _clean_text(link.get_text(" "))
    if not title:
        return None

    url = urljoin(BASE_URL, link["href"])
    full_text = _clean_text(block.get_text(" "))
    company = ""
    company_link = link.find_next("a")
    if company_link and "/offre-emploi-maroc/" not in company_link.get("href", ""):
        company = _clean_text(company_link.get_text(" "))

    experience = _extract_field(full_text, "Niveau d'experience")
    contract = _extract_field(full_text, "Contrat propose")
    region = _extract_field(full_text, "Region de")
    skills = _extract_field(full_text, "Competences cles")
    published_at = _parse_french_date(full_text)

    description = full_text.replace(title, "", 1)
    if company:
        description = description.replace(company, "", 1)

    return {
        "source": "emploi_ma",
        "title": title,
        "company": company,
        "city": region,
        "sector": "Non renseigne",
        "description": _clean_text(f"{description} {skills}"),
        "experience_level": experience,
        "contract_type": contract,
        "published_at": published_at,
        "url": url,
    }


def scrape_emploi_ma_jobs(max_pages: int = 1, keyword: str = "") -> list[dict[str, str]]:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Dependances manquantes pour scraper Emploi.ma. "
            "Installez-les avec: pip install -r requirements.txt"
        ) from exc

    jobs: list[dict[str, str]] = []
    seen = set()

    for page in range(max_pages):
        try:
            html = _get_listing_html(
                _listing_url(keyword),
                params={"page": page} if page else None,
            )
        except Exception as exc:
            print(
                f"WARNING: Emploi.ma indisponible pour keyword='{keyword or 'all'}', "
                f"page={page + 1}. Les pages suivantes de ce mot-cle sont ignorees. Detail: {exc}"
            )
            break

        soup = BeautifulSoup(html, "html.parser")
        blocks = _candidate_blocks(soup)

        for block in blocks:
            job = _parse_job_block(block)
            if not job:
                continue
            if not _matches_keyword(job, keyword):
                continue
            dedupe_key = job["url"] or f"{job['title']}|{job['company']}|{job['published_at']}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            jobs.append(job)

    return jobs
