"""
Unit Tests for URL-Only Feature Extraction
==========================================
Tests the 42 lexical, structural, and information-theoretic features
to guarantee deterministic and bug-free extraction across legitimate,
IP-based, and phishing URL patterns.

Authors: Daksh Jaiswal & Unnatti Dixit
"""

import pytest
import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from feature_extractor import (
    extract_url_features,
    calculate_entropy,
    is_ip_address,
    get_subdomain_count,
    FEATURE_NAMES
)


def test_feature_count_and_keys():
    """Verify that feature extraction yields the exact declared feature keys."""
    feats = extract_url_features("https://www.google.com")
    assert isinstance(feats, dict)
    assert len(feats) == len(FEATURE_NAMES)
    for key in FEATURE_NAMES:
        assert key in feats
        assert isinstance(feats[key], (int, float))


def test_ip_address_detection():
    """Verify raw IP address recognition in URLs."""
    feats_ip = extract_url_features("http://192.168.1.1/login.php")
    assert feats_ip["has_ip"] == 1
    assert feats_ip["hostname_length"] > 0

    feats_domain = extract_url_features("https://www.srmist.edu.in")
    assert feats_domain["has_ip"] == 0


def test_https_and_credentials():
    """Verify HTTPS flag and '@' symbol detection."""
    feats_https = extract_url_features("https://secure.bank.com/portal")
    assert feats_https["has_https"] == 1
    assert feats_https["nb_at"] == 0

    feats_at = extract_url_features("http://bank.com:account@attacker.com/steal")
    assert feats_at["nb_at"] == 1
    assert feats_at["has_https"] == 0


def test_suspicious_keywords_and_subdomains():
    """Verify keyword counter and subdomain nesting."""
    url = "http://verify.update.account.paypal-security.com/signin"
    feats = extract_url_features(url)
    assert feats["suspicious_keywords_count"] >= 3  # verify, update, account, signin
    assert feats["nb_subdomains"] >= 2
    assert feats["prefix_suffix"] == 1  # paypal-security has hyphen


def test_url_shortener_detection():
    """Verify detection of URL shortening redirection services."""
    feats_short = extract_url_features("http://bit.ly/3xY81z")
    assert feats_short["is_shortener"] == 1

    feats_normal = extract_url_features("https://www.github.com/torvalds")
    assert feats_normal["is_shortener"] == 0


def test_entropy_computation():
    """Verify Shannon character entropy calculation."""
    # Repetitive string should have low entropy
    low_ent = calculate_entropy("aaaaaaa")
    assert low_ent == 0.0

    # Diverse string should have high entropy
    high_ent = calculate_entropy("aB3$9!zK#1qL")
    assert high_ent > 3.0


def test_empty_and_malformed_url():
    """Verify graceful handling of malformed or empty inputs without exceptions."""
    f_empty = extract_url_features("")
    assert isinstance(f_empty, dict)
    assert f_empty["url_length"] > 0

    f_none = extract_url_features(None)
    assert isinstance(f_none, dict)
