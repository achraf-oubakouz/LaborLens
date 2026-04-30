import re
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import urljoin



BASE_URL = "https://www.rekrute.com"
LISTING_URL = f"{BASE_URL}/offres.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _parse_french_date(value: str) -> str:
    match = re.search(r"(\d{2}/\d{2}/\d{4})", value or "")
    if not match:
        return ""
    return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return normalized.encode("ascii", "ignore").decode("ascii")


def _extract_field(text: str, label: str) -> str:
    normalized_text = _strip_accents(text)
    normalized_label = _strip_accents(label)
    next_labels = (
        "Secteur d'activite|Fonction|Experience requise|"
        "Niveau d'etude demande|Type de contrat propose|Teletravail"
    )
    pattern = rf"{re.escape(normalized_label)}\s*:\s*(.*?)(?=\s+(?:{next_labels})\s*:|$)"
    match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
    return _clean_text(match.group(1)) if match else ""


def _extract_title_city(heading: str) -> tuple[str, str]:
    if "|" not in heading:
        return _clean_text(heading), ""

    title, location = heading.split("|", 1)
    location = re.sub(r"\(.*?\)", "", location)
    city = location.split(",")[0].strip()
    return _clean_text(title), _clean_text(city)


def _candidate_blocks(soup: Any) -> list[Any]:
    headings = []
    for tag_name in ("h2", "h3"):
        headings.extend(soup.find_all(tag_name))

    blocks = []
    seen = set()
    for heading in headings:
        heading_text = _clean_text(heading.get_text(" "))
        if "|" not in heading_text:
            continue

        block = heading
        for parent in heading.parents:
            text = _clean_text(parent.get_text(" "))
            if "Publication :" in text and len(text) > len(heading_text):
                block = parent
                break

        key = id(block)
        if key not in seen:
            blocks.append(block)
            seen.add(key)

    return blocks


def _parse_job_block(block: Any) -> dict[str, str] | None:
    heading = block.find(["h2", "h3"])
    if heading is None:
        return None

    heading_text = _clean_text(heading.get_text(" "))
    title, city = _extract_title_city(heading_text)
    if not title:
        return None

    link = heading.find("a") or block.find("a", href=True)
    url = urljoin(BASE_URL, link["href"]) if link and link.has_attr("href") else ""
    full_text = _clean_text(block.get_text(" "))

    sector = _extract_field(full_text, "Secteur d'activite")
    experience = _extract_field(full_text, "Experience requise")
    contract = _extract_field(full_text, "Type de contrat propose")
    published_at = _parse_french_date(full_text)

    description = full_text
    if "Publication :" in description:
        description = description.split("Publication :", 1)[0]
    description = description.replace(heading_text, "", 1)

    return {
        "source": "rekrute",
        "title": title,
        "company": "",
        "city": city,
        "sector": sector or "Non renseigne",
        "description": _clean_text(description),
        "experience_level": experience,
        "contract_type": contract.split("-")[0].strip() if contract else "",
        "published_at": published_at,
        "url": url,
    }


def scrape_rekrute_jobs(max_pages: int = 1, keyword: str = "") -> list[dict[str, str]]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Dependances manquantes pour scraper Rekrute. "
            "Installez-les avec: pip install -r requirements.txt"
        ) from exc

    jobs: list[dict[str, str]] = []
    seen = set()

    for page in range(1, max_pages + 1):
        response = requests.get(
            LISTING_URL,
            params={"s": "3", "p": page, "o": 1, "query": keyword},
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        blocks = _candidate_blocks(soup)

        for block in blocks:
            job = _parse_job_block(block)
            if not job:
                continue
            dedupe_key = job["url"] or f"{job['title']}|{job['city']}|{job['published_at']}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            jobs.append(job)

    return jobs


