# 🛡️ PhishGuard – AI-Based Phishing Website Detection

**Developed by:**
- **Unnatti Dixit** – RA2411003030009
- **Daksh Jaiswal** – RA2411003030048

**Institution:** SRM Institute of Science and Technology  
**Department:** Computer Science and Engineering

<p align="center">
  <a href="https://phishgaurd-ai-based-phishing-detection-1.onrender.com"><strong>🌐 LIVE DEMO – Try PhishGuard</strong></a>
</p>

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![Machine Learning](https://img.shields.io/badge/Domain-Machine%20Learning-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Deployment](https://img.shields.io/badge/Deployed%20on-Render-purple)

## 📌 Project Overview

PhishGuard is an end-to-end Machine Learning application designed to detect phishing websites by analyzing URL-based lexical and structural features.

It uses trained Machine Learning models to classify URLs as legitimate or phishing and provides phishing probability, risk levels, and human-readable explanations.

The application is built using Python and Flask with an interactive frontend dashboard and is publicly deployed through **Render**.

## 🌐 Live Application

**Live Website:** https://phishgaurd-ai-based-phishing-detection-1.onrender.com

**Deployment Platform:** Render

## ✨ Key Features

- URL-based phishing detection using lexical and structural features.
- Machine Learning classification using multiple algorithms.
- Random Forest, Decision Tree, Logistic Regression and SVM models.
- Phishing probability and risk-level assessment.
- Explainable predictions with human-readable risk indicators.
- Bulk URL scanning for up to 50 URLs.
- Model performance metrics.
- Interactive web dashboard.
- Privacy-focused URL analysis without webpage DOM scraping or runtime WHOIS/DNS queries.

## 🏗️ System Architecture

1. **Frontend:** Interactive phishing detection dashboard.
2. **Backend:** Flask API for handling requests.
3. **Feature Extraction:** Extraction of 42 URL-based features.
4. **ML Classification:** Trained models classify URLs.
5. **Prediction & Explainability:** Generates verdicts, probabilities and risk explanations.
6. **Deployment:** Publicly hosted using Render.

## 🤖 Machine Learning Models

Four classification algorithms were implemented and evaluated:

- Random Forest
- Support Vector Machine (SVM)
- Decision Tree
- Logistic Regression

### Model Performance

Evaluation performed on an untouched, stratified 20% test dataset containing 2,286 URLs.

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Random Forest | 89.50% | 89.57% | 89.41% | 0.8949 | 0.9620 |
| SVM | 88.28% | 88.08% | 88.54% | 0.8831 | 0.9563 |
| Decision Tree | 85.65% | 87.98% | 82.59% | 0.8520 | 0.8842 |
| Logistic Regression | 83.86% | 84.62% | 82.76% | 0.8368 | 0.9216 |

**Selected Model: Random Forest**

Random Forest achieved the highest test accuracy and ROC-AUC among the evaluated models.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask, Flask-CORS |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib |
| Frontend | HTML, CSS, JavaScript |
| Testing | Pytest |
| Deployment | Render |
| Version Control | Git, GitHub |

## 📂 Project Structure

```text
PhishGaurd/
│
├── backend/
│   └── app.py
├── frontend/
├── data/
├── docs/
├── notebooks/
├── results/
│   ├── best_model.joblib
│   ├── random_forest.joblib
│   ├── decision_tree.joblib
│   ├── logistic_regression.joblib
│   └── support_vector_machine.joblib
├── src/
│   ├── feature_extractor.py
│   ├── data_loader.py
│   ├── train.py
│   └── generate_plots.py
├── tests/
├── requirements.txt
├── README.md
└── LICENSE
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Unnatti687/PhishGaurd-AI-Based-Phishing-Detection.git
cd PhishGaurd-AI-Based-Phishing-Detection
```

### 2. Create a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python backend/app.py
```

### 5. Open in browser

```text
http://127.0.0.1:5000
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Opens the frontend dashboard |
| GET | `/api/health` | Checks application and model status |
| POST | `/api/predict` | Analyzes a single URL |
| POST | `/api/bulk-predict` | Analyzes multiple URLs |
| GET | `/api/metrics` | Retrieves model performance metrics |

## ⚠️ Limitations

- Detection is based exclusively on URL characteristics.
- Sophisticated phishing websites hosted on compromised legitimate domains may evade detection.
- A safe prediction does not guarantee that a website is completely trustworthy.
- Model performance depends on the training dataset and evolving phishing techniques.
- Periodic model retraining is recommended.

## 🔮 Future Enhancements

- Character-level Deep Learning models such as CNNs and Transformers.
- Additional webpage-content analysis.
- Automated model retraining using updated phishing datasets.
- Browser extension integration.
- Enhanced real-time threat intelligence.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>PhishGuard – Making the Web Safer Through Machine Learning.</strong>
</p>
