"""
PhishGuard - Flask REST API Backend
====================================
Serves phishing detection predictions, feature extractions, risk factor
explanations, bulk scanning, and the single-page dashboard frontend.

Endpoints:
- GET  /                     -> Serves frontend dashboard (index.html)
- GET  /api/health           -> Backend status, active model, feature count
- POST /api/predict          -> Classify single URL with feature breakdown and reasons
- POST /api/bulk-predict     -> Batch scan up to 50 URLs
- GET  /api/metrics          -> Returns test performance metrics and confusion data

Authors: Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)
SRM Institute of Science and Technology
"""

import os
import sys
import json
import joblib
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add src to sys.path so we can import feature extractor
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
RESULTS_DIR = PROJECT_ROOT / "results"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from feature_extractor import extract_url_features, FEATURE_NAMES

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)

# Global variables for model and metadata
model = None
feature_names = None
metrics_cache = None


def load_model_and_metadata():
    """Load the trained model and feature list into memory on startup."""
    global model, feature_names, metrics_cache
    model_path = RESULTS_DIR / "best_model.joblib"
    feature_path = RESULTS_DIR / "feature_names.json"
    metrics_path = RESULTS_DIR / "metrics.csv"

    if model_path.exists():
        model = joblib.load(model_path)
        print(f"[+] Loaded model from: {model_path}")
    else:
        print("[-] Warning: Model not found at", model_path)

    if feature_path.exists():
        with open(feature_path, "r") as f:
            feature_names = json.load(f)
        print(f"[+] Loaded {len(feature_names)} feature column definitions.")
    else:
        feature_names = FEATURE_NAMES

    if metrics_path.exists():
        try:
            m_df = pd.read_csv(metrics_path)
            metrics_cache = m_df.to_dict(orient="records")
        except Exception:
            metrics_cache = []


# Initial load
load_model_and_metadata()


def generate_top_reasons(features: dict, prob: float) -> list:
    """
    Generate human-readable risk explanation reasons based on feature values.
    Conforms to project explainability objectives.
    """
    reasons = []

    if features.get("has_ip", 0) == 1:
        reasons.append({
            "factor": "IP Address Hostname",
            "description": "The URL uses a raw IP address instead of a registered domain name, a hallmark of evasion.",
            "severity": "high"
        })

    if features.get("is_shortener", 0) == 1:
        reasons.append({
            "factor": "URL Shortener Service",
            "description": "Uses a known URL shortening redirector (e.g., bit.ly, tinyurl) which conceals final destination.",
            "severity": "medium"
        })

    kw_count = features.get("suspicious_keywords_count", 0)
    if kw_count > 0:
        reasons.append({
            "factor": "Suspicious Security Keywords",
            "description": f"URL contains {kw_count} credential or security lure keywords (e.g., 'login', 'verify', 'update').",
            "severity": "high" if kw_count >= 2 else "medium"
        })

    if features.get("nb_at", 0) > 0:
        reasons.append({
            "factor": "@ Character in URL",
            "description": "Contains '@' character which discards prior tokens and tricks browser authentication handling.",
            "severity": "high"
        })

    if features.get("prefix_suffix", 0) == 1:
        reasons.append({
            "factor": "Hyphenated Brand Mimicry",
            "description": "Domain contains hyphens (-) typically used to construct spoofed brand domains (e.g. 'paypal-security').",
            "severity": "medium"
        })

    sub_count = features.get("nb_subdomains", 0)
    if sub_count >= 2:
        reasons.append({
            "factor": "Deep Subdomain Nesting",
            "description": f"Detected {sub_count} nested subdomains, frequently used to obscure malicious host infrastructure.",
            "severity": "medium"
        })

    if features.get("url_length", 0) > 75:
        reasons.append({
            "factor": "Excessive URL Length",
            "description": f"Total length is {features.get('url_length')} characters, significantly higher than benign averages.",
            "severity": "low"
        })

    if features.get("ratio_digits_url", 0) > 0.15:
        reasons.append({
            "factor": "High Numeric Digit Ratio",
            "description": f"Digits comprise {features.get('ratio_digits_url') * 100:.1f}% of the URL, indicating hex tokens or random IDs.",
            "severity": "medium"
        })

    if features.get("char_entropy", 0) > 4.2:
        reasons.append({
            "factor": "High Character Entropy",
            "description": f"Shannon character entropy is elevated ({features.get('char_entropy'):.2f} bits), suggesting randomized strings.",
            "severity": "low"
        })

    if features.get("has_https", 0) == 0:
        reasons.append({
            "factor": "Insecure HTTP Scheme",
            "description": "Website operates over unencrypted HTTP protocol without SSL/TLS encryption.",
            "severity": "low"
        })

    # If few or no adverse indicators found and probability is low
    if not reasons and prob < 0.40:
        reasons.append({
            "factor": "Standard Clean URL Structure",
            "description": "Domain name length, character entropy, and keyword distribution conform to standard legitimate websites.",
            "severity": "info"
        })

    return reasons[:5]


@app.route("/")
def index():
    """Serve the single-page frontend application."""
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/results/<path:filename>")
def serve_results(filename):
    """Serve generated visualization plots and artifacts from results directory."""
    return send_from_directory(str(RESULTS_DIR), filename)


@app.route("/<path:path>")
def static_files(path):
    """Serve static frontend assets."""
    return send_from_directory(str(FRONTEND_DIR), path)


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint indicating model state and version."""
    return jsonify({
        "status": "online",
        "service": "PhishGuard Phishing Detection API",
        "authors": "Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)",
        "institution": "SRM Institute of Science and Technology",
        "model_loaded": model is not None,
        "features_count": len(feature_names) if feature_names else 0,
        "version": "1.0.0"
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Predict phishing probability for a single URL.
    Payload: {"url": "https://example.com"}
    """
    global model, feature_names
    if model is None:
        load_model_and_metadata()
        if model is None:
            return jsonify({"error": "Model not trained or not found on server."}), 503

    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "Invalid request body. JSON with key 'url' is required."}), 400

    raw_url = str(data["url"]).strip()
    if not raw_url:
        return jsonify({"error": "Empty URL provided."}), 400

    # Extract features
    features = extract_url_features(raw_url)
    feat_vector = pd.DataFrame([features])[feature_names]

    # Predict probability
    if hasattr(model, "predict_proba"):
        prob_phish = float(model.predict_proba(feat_vector)[0][1])
    else:
        # Decision function fallback
        score = float(model.decision_function(feat_vector)[0])
        prob_phish = 1.0 / (1.0 + (2.71828 ** (-score)))

    # Determine verdict and risk level
    if prob_phish >= 0.70:
        verdict = "Phishing"
        risk_level = "High"
    elif prob_phish >= 0.35:
        verdict = "Suspicious"
        risk_level = "Medium"
    else:
        verdict = "Safe"
        risk_level = "Low"

    top_reasons = generate_top_reasons(features, prob_phish)

    return jsonify({
        "url": raw_url,
        "verdict": verdict,
        "is_phishing": bool(prob_phish >= 0.50),
        "phishing_probability": round(prob_phish, 4),
        "confidence_percentage": round(prob_phish * 100 if prob_phish >= 0.5 else (1 - prob_phish) * 100, 1),
        "risk_level": risk_level,
        "top_reasons": top_reasons,
        "features": features
    })


@app.route("/api/bulk-predict", methods=["POST"])
def bulk_predict():
    """
    Batch classify a list of URLs (max 50).
    Payload: {"urls": ["http://url1.com", "http://url2.com", ...]}
    """
    global model, feature_names
    if model is None:
        load_model_and_metadata()
        if model is None:
            return jsonify({"error": "Model not loaded."}), 503

    data = request.get_json(silent=True)
    if not data or "urls" not in data or not isinstance(data["urls"], list):
        return jsonify({"error": "Invalid payload. JSON array of 'urls' required."}), 400

    url_list = data["urls"]
    if len(url_list) == 0:
        return jsonify({"error": "List of URLs cannot be empty."}), 400
    if len(url_list) > 50:
        return jsonify({"error": "Bulk scanning is capped at 50 URLs per request."}), 400

    results = []
    phishing_count = 0
    safe_count = 0
    suspicious_count = 0

    for u in url_list:
        raw_url = str(u).strip()
        if not raw_url:
            continue
        feats = extract_url_features(raw_url)
        vector = pd.DataFrame([feats])[feature_names]

        if hasattr(model, "predict_proba"):
            prob = float(model.predict_proba(vector)[0][1])
        else:
            score = float(model.decision_function(vector)[0])
            prob = 1.0 / (1.0 + (2.71828 ** (-score)))

        if prob >= 0.70:
            verdict = "Phishing"
            risk_level = "High"
            phishing_count += 1
        elif prob >= 0.35:
            verdict = "Suspicious"
            risk_level = "Medium"
            suspicious_count += 1
        else:
            verdict = "Safe"
            risk_level = "Low"
            safe_count += 1

        reasons = generate_top_reasons(feats, prob)

        results.append({
            "url": raw_url,
            "verdict": verdict,
            "phishing_probability": round(prob, 4),
            "risk_level": risk_level,
            "top_reason": reasons[0]["factor"] if reasons else "Clean URL structure"
        })

    return jsonify({
        "total_scanned": len(results),
        "phishing_count": phishing_count,
        "suspicious_count": suspicious_count,
        "safe_count": safe_count,
        "results": results
    })


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Return trained model performance metrics."""
    global metrics_cache
    if metrics_cache is None:
        load_model_and_metadata()
    return jsonify({
        "metrics": metrics_cache or []
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting PhishGuard Flask server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
