"""
PhishGuard - URL-Only Feature Extraction Module
================================================
Extracts 42 lexical, structural, and information-theoretic features directly from
a raw URL string. Operates strictly offline with zero network/WHOIS/page lookups,
conforming to the SRM IST Project scope ("URL features only").

Authors: Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)
"""

import math
import re
import ipaddress
from urllib.parse import urlparse

# Common URL shortening services
SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "t.co", "ow.ly", "is.gd", "buff.ly",
    "adf.ly", "bit.do", "mcaf.ee", "rebrand.ly", "tiny.cc", "cutt.ly",
    "shorte.st", "trib.al", "lnkd.in", "db.tt", "qr.ae", "t.ly", "sur.ly"
}

# Suspicious keywords strongly associated with phishing lures
SUSPICIOUS_KEYWORDS = [
    "login", "verify", "update", "banking", "secure", "account",
    "signin", "confirm", "password", "paypal", "apple", "ebay",
    "wallet", "security", "billing", "support", "auth", "recover",
    "client", "webscr", "checkout", "alert", "service", "payment"
]


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string (measures randomness/obfuscation)."""
    if not text:
        return 0.0
    length = len(text)
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return float(entropy)


def is_ip_address(hostname: str) -> int:
    """Return 1 if hostname is a valid IPv4 or IPv6 address, else 0."""
    if not hostname:
        return 0
    clean_host = hostname.split(":")[0].strip("[]")
    try:
        ipaddress.ip_address(clean_host)
        return 1
    except ValueError:
        pass
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, clean_host):
        return 1
    return 0


def get_subdomain_count(hostname: str) -> int:
    """Return the number of subdomains in hostname."""
    if not hostname or is_ip_address(hostname):
        return 0
    parts = [p for p in hostname.split(".") if p]
    two_part_tlds = {"co.uk", "com.au", "co.nz", "co.jp", "com.br", "gov.uk", "ac.uk", "edu.au"}
    if len(parts) >= 2 and f"{parts[-2]}.{parts[-1]}".lower() in two_part_tlds:
        return max(0, len(parts) - 3)
    return max(0, len(parts) - 2)


def get_tld_length(hostname: str) -> int:
    """Extract length of the top-level domain."""
    if not hostname or is_ip_address(hostname):
        return 0
    parts = [p for p in hostname.split(".") if p]
    if not parts:
        return 0
    return len(parts[-1])


def max_char_repeat(text: str) -> int:
    """Calculate the maximum consecutive repetition count of any character."""
    if not text:
        return 0
    max_rep = 1
    cur_rep = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            cur_rep += 1
            if cur_rep > max_rep:
                max_rep = cur_rep
        else:
            cur_rep = 1
    return max_rep


def extract_url_features(raw_url: str) -> dict:
    """
    Extract 42 purely URL-based lexical and structural features from raw_url.
    Returns a dictionary mapping feature name to numeric value (float/int).
    """
    url = str(raw_url).strip()
    if not url:
        url = "http://empty-url.local"

    # Ensure URL has a scheme for reliable urlparse parsing
    parse_target = url
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        parse_target = "http://" + url

    try:
        parsed = urlparse(parse_target)
    except Exception:
        parsed = urlparse("http://malformed-url.local")

    hostname = parsed.netloc.lower()
    path = parsed.path
    query = parsed.query
    url_lower = url.lower()

    # Raw lengths
    url_len = len(url)
    host_len = len(hostname)
    path_len = len(path)
    query_len = len(query)

    # Character counts
    nb_dots = url.count(".")
    nb_hyphens = url.count("-")
    nb_at = url.count("@")
    nb_qm = url.count("?")
    nb_and = url.count("&")
    nb_or = url.count("|")
    nb_eq = url.count("=")
    nb_underscore = url.count("_")
    nb_tilde = url.count("~")
    nb_percent = url.count("%")
    nb_slash = url.count("/")
    nb_star = url.count("*")
    nb_colon = url.count(":")
    nb_comma = url.count(",")
    nb_semicolon = url.count(";")
    nb_dollar = url.count("$")
    nb_space = url.count(" ") + url.count("%20")
    nb_www = url_lower.count("www")
    nb_com = url_lower.count(".com") + url_lower.count("com")

    # Extra double slashes in path
    extra_dslash = max(0, url.count("//") - (1 if "://" in url else 0))

    # Token / presence flags
    http_in_path = 1 if ("http:" in path.lower() or "https:" in path.lower() or "http" in query.lower()) else 0
    has_https = 1 if parsed.scheme.lower() == "https" else 0
    https_in_domain = 1 if ("https" in hostname and parsed.scheme.lower() != "https") else 0

    # Digit ratios
    digits_url = sum(c.isdigit() for c in url)
    digits_host = sum(c.isdigit() for c in hostname)
    ratio_digits_url = float(digits_url / max(url_len, 1))
    ratio_digits_host = float(digits_host / max(host_len, 1))

    # Network / domain structure
    punycode = 1 if "xn--" in hostname else 0
    has_port = 1 if parsed.port is not None else 0
    has_ip = is_ip_address(hostname)
    nb_subdomains = get_subdomain_count(hostname)
    prefix_suffix = 1 if ("-" in hostname) else 0
    tld_len = get_tld_length(hostname)

    # Shortener check
    host_no_port = hostname.split(":")[0]
    is_shortener = 1 if any(shortener in host_no_port for shortener in SHORTENERS) else 0

    # Entropy
    char_entropy = calculate_entropy(url)

    # Suspicious keywords count
    suspicious_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in url_lower)

    # Word tokens
    words = [w for w in re.split(r"[^a-zA-Z0-9]+", url) if w]
    longest_word_len = max((len(w) for w in words), default=0)
    shortest_word_len = min((len(w) for w in words), default=0)
    avg_word_len = float(sum(len(w) for w in words) / max(len(words), 1))

    repeat_char_max = max_char_repeat(url)

    return {
        "url_length": url_len,
        "hostname_length": host_len,
        "path_length": path_len,
        "query_length": query_len,
        "nb_dots": nb_dots,
        "nb_hyphens": nb_hyphens,
        "nb_at": nb_at,
        "nb_qm": nb_qm,
        "nb_and": nb_and,
        "nb_or": nb_or,
        "nb_eq": nb_eq,
        "nb_underscore": nb_underscore,
        "nb_tilde": nb_tilde,
        "nb_percent": nb_percent,
        "nb_slash": nb_slash,
        "nb_star": nb_star,
        "nb_colon": nb_colon,
        "nb_comma": nb_comma,
        "nb_semicolon": nb_semicolon,
        "nb_dollar": nb_dollar,
        "nb_space": nb_space,
        "nb_www": nb_www,
        "nb_com": nb_com,
        "nb_dslash": extra_dslash,
        "http_in_path": http_in_path,
        "has_https": has_https,
        "https_in_domain": https_in_domain,
        "ratio_digits_url": ratio_digits_url,
        "ratio_digits_host": ratio_digits_host,
        "punycode": punycode,
        "has_port": has_port,
        "has_ip": has_ip,
        "nb_subdomains": nb_subdomains,
        "prefix_suffix": prefix_suffix,
        "is_shortener": is_shortener,
        "char_entropy": char_entropy,
        "suspicious_keywords_count": suspicious_count,
        "longest_word_len": longest_word_len,
        "shortest_word_len": shortest_word_len,
        "avg_word_len": avg_word_len,
        "char_repeat_max": repeat_char_max,
        "tld_length": tld_len,
    }


FEATURE_NAMES = list(extract_url_features("http://example.com").keys())
