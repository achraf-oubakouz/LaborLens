import re
import unicodedata


CITY_ALIASES = {
    "agadir": "Agadir",
    "ait melloul": "Ait Melloul",
    "ain atiq": "Ain Atiq",
    "akdz": "Agdz",
    "agdz": "Agdz",
    "al aaroui": "Al Aaroui",
    "al hoceima": "Al Hoceima",
    "amizmiz": "Amizmiz",
    "beni mellal": "Beni Mellal",
    "beni mellal-khenifra": "Beni Mellal-Khenifra",
    "ben guerir": "Benguerir",
    "benguerir": "Benguerir",
    "benslimane": "Benslimane",
    "berrechid": "Berrechid",
    "bir jedid": "Bir Jdid",
    "bir jdid": "Bir Jdid",
    "bouarfa": "Bouarfa",
    "bouskoura": "Bouskoura",
    "bouznika": "Bouznika",
    "casa": "Casablanca",
    "casablanca": "Casablanca",
    "casablanca et peripherie": "Casablanca",
    "casablanca et rabat": "Casablanca",
    "casablanca maarif": "Casablanca",
    "casablanca-settat": "Casablanca-Settat",
    "casablanca settat": "Casablanca-Settat",
    "cdi formation remuneree rabat": "Rabat",
    "cdi primes deplafonnees rabat": "Rabat",
    "dakhla": "Dakhla",
    "dcheira": "Dcheira",
    "deroua": "Deroua",
    "el jadida": "El Jadida",
    "errachidia": "Errachidia",
    "fes": "Fes",
    "fès": "Fes",
    "guelmim": "Guelmim",
    "inezgane": "Inezgane",
    "international": "International",
    "kenitra": "Kenitra",
    "kénitra": "Kenitra",
    "khouribga": "Khouribga",
    "laayoune": "Laayoune",
    "maroc": "Tout Le Maroc",
    "marrakech": "Marrakech",
    "marrakech-safi": "Marrakech-Safi",
    "marrakesh": "Marrakech",
    "meknes": "Meknes",
    "meknès": "Meknes",
    "mohammedia": "Mohammedia",
    "nador": "Nador",
    "non renseigne": "Non renseigne",
    "nouaceur": "Nouaceur",
    "oujda": "Oujda",
    "rabat": "Rabat",
    "rabat casa": "Rabat",
    "rabat-sale-kenitra": "Rabat-Sale-Kenitra",
    "safi": "Safi",
    "sala al jadida": "Sala Al Jadida",
    "sale": "Sale",
    "salé": "Sale",
    "settat": "Settat",
    "taliouine": "Taliouine",
    "tanger": "Tanger",
    "tanger med": "Tanger",
    "tanger-tetouan-al hoceima": "Tanger-Tetouan-Al Hoceima",
    "temara": "Temara",
    "tetouan": "Tetouan",
    "tiflet": "Tiflet",
    "tout le maroc": "Tout Le Maroc",
}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return normalized.encode("ascii", "ignore").decode("ascii")


def normalize_location_text(value: str) -> str:
    cleaned = strip_accents(value).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_city(value: str) -> str:
    raw_value = str(value or "").strip()
    if not raw_value or raw_value.lower() in {"nan", "none", "n/a", "na"}:
        return "Non renseigne"

    cleaned = normalize_location_text(raw_value)
    if cleaned in CITY_ALIASES:
        return CITY_ALIASES[cleaned]

    for pattern in sorted(CITY_ALIASES, key=len, reverse=True):
        normalized_pattern = normalize_location_text(pattern)
        if re.search(rf"\b{re.escape(normalized_pattern)}\b", cleaned):
            return CITY_ALIASES[pattern]

    return "Non renseigne" if len(cleaned.split()) > 4 else strip_accents(raw_value).title()


def known_city_values() -> set[str]:
    return set(CITY_ALIASES.values()) | {"Non renseigne"}
