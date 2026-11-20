"""
Integration Tests for PhishGuard Flask API
==========================================
Validates /api/health, /api/predict, /api/bulk-predict, and /api/metrics.

Authors: Daksh Jaiswal & Unnatti Dixit
"""

import pytest
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Ensure health endpoint returns online status and author metadata."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert "Daksh Jaiswal" in data["authors"]
    assert "Unnatti Dixit" in data["authors"]
    assert "SRM Institute" in data["institution"]


def test_predict_endpoint_valid_url(client):
    """Test single URL prediction with complete response schema."""
    payload = {"url": "http://secure-login.paypa1-verify.com/update@id"}
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "verdict" in data
    assert data["verdict"] in ["Phishing", "Suspicious", "Safe"]
    assert "phishing_probability" in data
    assert 0.0 <= data["phishing_probability"] <= 1.0
    assert "features" in data
    assert "top_reasons" in data
    assert isinstance(data["top_reasons"], list)


def test_predict_endpoint_invalid_input(client):
    """Test validation when URL is missing or empty."""
    res_empty = client.post("/api/predict", json={"url": "   "})
    assert res_empty.status_code == 400

    res_missing = client.post("/api/predict", json={"invalid_key": 123})
    assert res_missing.status_code == 400


def test_bulk_predict_endpoint(client):
    """Test batch prediction for up to 50 URLs."""
    urls = [
        "https://www.srmist.edu.in",
        "https://github.com",
        "http://appleid.apple.com-app.es/"
    ]
    res = client.post("/api/bulk-predict", json={"urls": urls})
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_scanned"] == 3
    assert len(data["results"]) == 3
    assert "phishing_count" in data
    assert "safe_count" in data


def test_bulk_predict_limit_exceeded(client):
    """Verify error when bulk URL list exceeds 50."""
    too_many = [f"http://example{i}.com" for i in range(55)]
    res = client.post("/api/bulk-predict", json={"urls": too_many})
    assert res.status_code == 400
