# Experimental Results Summary

> **Project:** AI-Based Phishing Website Detection  
> **Institution:** SRM Institute of Science and Technology  
> **Authors:** Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)  
> **Dataset:** Hannousse & Yahiouche Benchmark (11,430 URLs; 5,715 Legitimate, 5,715 Phishing)  
> **Evaluation Protocol:** Stratified 80/20 train/test split (Untouched test set: 2,286 URLs: 1,143 Legitimate, 1,143 Phishing)  
> **Features:** 42 Pure URL-Only Features (0 DOM / 0 network lookups)

---

## 1. Model Performance Comparison Table (Held-Out Test Set)

| Classifier Algorithm | 5-Fold CV F1 | Test Accuracy | Test Precision | Test Recall | Test F1-Score | ROC-AUC | False Negatives (Missed Phish) | False Positives (False Alarms) | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest (Best)** | **0.8936** | **89.50%** | **89.57%** | **89.41%** | **0.8949** | **0.9620** | **121** | **119** | **0.018 ms/URL** |
| **Support Vector Machine (SVM)** | 0.8810 | 88.28% | 88.08% | 88.54% | 0.8831 | 0.9563 | 131 | 137 | 0.287 ms/URL |
| **Decision Tree** | 0.8452 | 85.65% | 87.98% | 82.59% | 0.8520 | 0.8842 | 199 | 129 | <0.001 ms/URL |
| **Logistic Regression** | 0.8302 | 83.86% | 84.62% | 82.76% | 0.8368 | 0.9216 | 197 | 172 | 0.001 ms/URL |

---

## 2. Best Model Selection & Viva Justification

### Selected Model: **Random Forest Classifier**
* **Hyperparameters:** `n_estimators=100`, `max_depth=16`, `min_samples_split=5`

### Justification Points (for Viva):
1. **Critical Recall on Phishing (89.41%):** In cybersecurity defense, False Negatives (missing an active phishing attack) carry severe financial and credential loss consequences. Random Forest yielded the fewest False Negatives (121 out of 1,143 test phishing URLs), outperforming SVM (131), LR (197), and Decision Tree (199).
2. **Superior ROC-AUC (0.9620):** Demonstrates exceptional discriminative capability across all confidence thresholds, minimizing false alarms while maximizing threat capture.
3. **Sub-Millisecond Inference (0.018 ms/URL):** Over 15x faster than SVM (0.287 ms), enabling wire-speed packet inspection (>50,000 URLs/second) suitable for real-time proxies and browser extensions.
4. **Ensemble Variance Reduction:** Bagging across 100 decorrelated decision trees significantly reduces variance compared to the single Decision Tree (which overfit deeper branches with an F1 of only 0.8520).

---

## 3. Top 10 Most Discriminative URL Features

Based on Random Forest Gini Importance (Mean Decrease in Impurity):
1. `nb_www` (0.1028): Presence of the canonical `www` prefix is overwhelmingly typical in legitimate domains; phishing domains frequently omit or misplace it.
2. `char_entropy` (0.0713): High character randomness indicates randomly generated strings, hex-encoded hashes, or Domain Generation Algorithms (DGAs).
3. `ratio_digits_url` (0.0667): Phishing URLs heavily utilize long hexadecimal strings, session IDs, and port markers.
4. `char_repeat_max` (0.0660): Consecutive repeated characters used in obfuscated redirects and padding.
5. `longest_word_len` (0.0637): Attackers assemble protracted brand compounds (e.g. `update-security-account-verification`).
6. `suspicious_keywords_count` (0.0628): Presence of credential lure words (`login`, `verify`, `account`, `banking`, `appleid`, `secure`).
7. `path_length` (0.0571): Phishing campaigns frequently deploy deep multi-level directories on free web hosts.
8. `hostname_length` (0.0508): Longer hostnames reflect brand spoofing subdomains.
9. `url_length` (0.0504): Total string length is significantly longer for phishing URLs.
10. `nb_slash` (0.0503): Nested directory hierarchies.

---

## 4. Error Analysis Summary (Test Set)

From the 2,286 held-out test URLs:
- **Total False Positives:** 119 legitimate URLs misclassified as phishing.
  - *Root Cause:* Legitimate educational, news, and specialized portals with protracted URLs, hyphens, or deep paths (e.g. `http://iwanarif.lecturer.pens.ac.id/2.%20network%20protocols.pdf`, `http://z80-heaven.wikidot.com`).
- **Total False Negatives:** 121 phishing URLs misclassified as legitimate.
  - *Root Cause:* Clean, short domain names without overt keywords or nested subdomains (e.g. `http://bolkyaresha.in`, `http://www.mazzoli.com/stand/otp.php`), where malicious intent resides strictly in runtime page content.

---

## 5. Key Limitations (Matching Deck Slide 2 & 6)

1. **URL-Only Boundary:** Phishing pages hosted on compromised top-level domains that use short, clean URL structures cannot be identified through lexical analysis alone without page-content inspection.
2. **"Legitimate" $\neq$ Safe:** A "Legitimate" classification strictly indicates the absence of malicious URL structural patterns; it does not guarantee the server has not been breached or compromised.
3. **Offline Benchmark Evaluation:** Real-world adversarial attackers continuously adapt to feature signatures (concept drift). Periodic retraining on live threat feeds is mandatory.
