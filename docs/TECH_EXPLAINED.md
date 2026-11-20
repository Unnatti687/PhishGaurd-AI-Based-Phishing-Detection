# PhishGuard - Technical Architecture, Methodology & Viva Guide

> **Project:** AI-Based Phishing Website Detection  
> **Authors:** Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)  
> **Institution:** SRM Institute of Science and Technology  

---

## 1. Libraries and Frameworks Explained

### 1.1 Scikit-Learn (`sklearn`)
* **What it is:** The standard, battle-tested Python machine learning library providing efficient tools for predictive data analysis.
* **How it is used in this project:**
  - Implements `train_test_split` with stratification to preserve class balance.
  - Implements `StandardScaler` inside `Pipeline` objects to prevent data leakage.
  - Implements `LogisticRegression`, `DecisionTreeClassifier`, `RandomForestClassifier`, and `SVC`.
  - Performs 5-fold cross-validation and hyperparameter search via `GridSearchCV`.
  - Calculates evaluation metrics: `accuracy_score`, `precision_score`, `recall_score`, `f1_score`, `roc_auc_score`, and `confusion_matrix`.
* **Why chosen:** Highly optimized in C/Cython, standardized API across all algorithms, and supports reproducible random seeds.

### 1.2 Pandas (`pandas`)
* **What it is:** A high-performance data manipulation and analysis library built on DataFrame structures.
* **How it is used in this project:** Loads `dataset_phishing.csv`, inspects null values and duplicates, handles label encoding, manages feature matrices, and writes `metrics.csv` and `error_analysis.csv`.
* **Why chosen:** Vectorized tabular operations and seamless interoperability with Scikit-Learn.

### 1.3 NumPy (`numpy`)
* **What it is:** The fundamental package for scientific computing with multi-dimensional array operations.
* **How it is used in this project:** Matrix manipulation, probability slicing (`[:, 1]`), and numeric calculations.
* **Why chosen:** Low-level C execution speed and memory efficiency.

### 1.4 Matplotlib (`matplotlib`)
* **What it is:** A comprehensive plotting and visualization library.
* **How it is used in this project:** Generates high-resolution PNG charts:
  - 2x2 grid of confusion matrices (`confusion_matrices.png`)
  - Multi-classifier ROC curves (`roc_curves.png`)
  - Top 15 feature importances and linear coefficients (`feature_importance.png`)
  - Grouped metric comparison bar chart (`model_comparison_bar.png`)
* **Why chosen:** Full programmatic control over dpi, labels, color schemes, and layout geometry.

### 1.5 Joblib (`joblib`)
* **What it is:** A serialization library optimized for persisting Python objects containing large NumPy arrays.
* **How it is used in this project:** Saves the trained Random Forest champion model (`best_model.joblib`) and feature column names list.
* **Why chosen:** Much faster and more compact than standard `pickle` for trained ML pipelines.

### 1.6 Flask & Flask-CORS (`flask`, `flask_cors`)
* **What it is:** A lightweight, unopinionated WSGI web application microframework.
* **How it is used in this project:**
  - Implements the REST API endpoints: `GET /api/health`, `POST /api/predict`, `POST /api/bulk-predict`, `GET /api/metrics`.
  - Serves static assets for the single-page frontend.
  - Enables Cross-Origin Resource Sharing (CORS).
* **Why chosen:** Simple, clean, fast startup, minimal overhead, perfect for ML model serving without complex container/Kubernetes overhead.

### 1.7 Pytest (`pytest`)
* **What it is:** A robust test runner and assertions framework for Python.
* **How it is used in this project:** Automated unit testing for feature extraction (`test_feature_extractor.py`) and API endpoint integration (`test_api.py`).
* **Why chosen:** Readable assertions, detailed failure reporting, and fixtures support.

---

## 2. Machine Learning Techniques & Methodology

### 2.1 URL-Only Feature Extraction (42 Features)
In accordance with our SRM IST presentation scope (Slide 2 & 7), the classifier operates strictly on lexical and structural attributes of the URL string:
1. **Length Dimensions:** Total URL length, hostname length, path length, query length. Phishing URLs tend to be substantially longer to accommodate obfuscation.
2. **Special Character Counts:** Frequencies of `.`, `-`, `@`, `?`, `&`, `=`, `_`, `~`, `%`, `/`, `:`, `,`, `;`, `$`, space, and `//`.
3. **Information Theory (Shannon Entropy):**
   $$H(X) = -\sum_{i=1}^n P(x_i) \log_2 P(x_i)$$
   Measures string randomness. Algorithmic phishing URLs or hex-obfuscated tokens exhibit significantly higher entropy than natural human-readable domain names.
4. **Security Flags:** Raw IPv4/IPv6 address hostname, known URL shorteners (`bit.ly`, `tinyurl`), non-standard ports, insecure HTTP scheme, nested subdomain count, and hyphen brand mimicry (`paypal-secure`).
5. **Security Lure Keywords:** Matches words like `login`, `verify`, `banking`, `account`, `signin`, `update`.

### 2.2 Data Preprocessing & Splitting Protocol
- **Duplicate Removal:** Checked for duplicate URLs before splitting. Dropped 1 duplicate to ensure the exact same URL cannot exist in both the train and test partitions.
- **Stratified 80/20 Holdout Split:** 9,143 training samples and 2,286 testing samples. Stratification ensures the 50/50 legitimate/phishing class ratio is precisely preserved in both sets.
- **Data Leakage Prevention:** Feature scaling (`StandardScaler`) is fitted strictly on `X_train` within a `Pipeline`. `X_test` is transformed using the training parameters and remains completely untouched until final evaluation.

### 2.3 Evaluated Classifiers
1. **Logistic Regression:** Linear baseline maximizing log-likelihood with L2 regularization. Provides interpretable coefficients indicating which features push odds towards phishing.
2. **Decision Tree:** Non-linear recursive binary partitioning. Constrained with `max_depth=14` and `min_samples_split=5` to prevent overfitting.
3. **Random Forest:** Ensemble bagging of 100 decorrelated decision trees with feature subsampling ($\sqrt{p}$). Yields the best generalization performance.
4. **Support Vector Machine (SVM):** Finds the optimal maximum-margin hyperplane in kernel space (RBF kernel, $C=2.0$).

---

## 3. 15 Essential Viva Questions & Model Answers

### Q1: Why did you choose a URL-only approach instead of analyzing the HTML page content or screenshots?
**Answer:** URL-only detection offers three critical security advantages:
1. **Zero Runtime Latency:** URL features extract in <0.1 ms, allowing real-time blocking before a browser even opens a TCP socket to the server.
2. **User Privacy & Safety:** Loading malicious pages exposes the client to drive-by downloads, malware injection, and tracking.
3. **Transient Attack Lifecycles:** Phishing sites stay online for very short periods (63% last <2 hours). Many cloak against crawlers by serving 404s to scanners but showing the phish to humans. URL features cannot be cloaked.

### Q2: What benchmark dataset was used, and what are its characteristics?
**Answer:** We used the official Hannousse & Yahiouche (2021) benchmark dataset (`dataset_phishing.csv`). It consists of 11,430 URLs, balanced evenly (5,715 legitimate and 5,715 phishing). We extracted our own 42 URL-only features directly from the raw URL column.

### Q3: How did you ensure your models were not overfitting?
**Answer:** We applied three defenses:
1. **Stratified 5-Fold Cross-Validation:** Models were tuned and verified across 5 distinct training folds.
2. **Structural Regularization:** We constrained Decision Tree depth (`max_depth=14`), pruned tree leaves (`min_samples_split=5`), and applied L2 regularization in Logistic Regression ($C=1.0$).
3. **Ensemble Averaging:** Random Forest averages predictions across 100 decorrelated trees, substantially reducing variance.

### Q4: Why is scaling only applied to Logistic Regression and SVM, but not Decision Tree or Random Forest?
**Answer:** Distance-based and gradient-based algorithms (LR and SVM) calculate margins and inner products; unscaled features with large ranges (e.g. `url_length` in hundreds vs `nb_at` in ones) would dominate the loss function. In contrast, tree-based models make orthogonal splits based on monotonic ordering, making them completely invariant to feature scaling.

### Q5: How did you prevent data leakage during scaling?
**Answer:** We encapsulated `StandardScaler` inside a Scikit-Learn `Pipeline`. The mean and variance parameters ($\mu, \sigma$) are computed solely on the training fold during `.fit()`. The held-out test data is strictly transformed using the frozen training statistics.

### Q6: Which model did you select as the champion and why?
**Answer:** We selected **Random Forest**. It achieved the highest Test F1-Score (**0.8949**), highest ROC-AUC (**0.9620**), and critically the highest Recall on phishing (**89.41%**), producing only 121 False Negatives out of 1,143 attacks while running at 0.018 ms per URL.

### Q7: Why is Recall on phishing more critical than Precision in this domain?
**Answer:** A False Negative means an active phishing attack slips past the filter, resulting in credential theft, financial fraud, or corporate breach. A False Positive simply results in a user caution warning. While both should be minimized, minimizing False Negatives (maximizing Recall) is the primary security imperative.

### Q8: What does Shannon Character Entropy measure in a URL?
**Answer:** It quantifies the information density and randomness of character distributions:
$$H = -\sum p_i \log_2(p_i)$$
Legitimate URLs use predictable dictionary words (low entropy ~2.5 to 3.5 bits). Attackers using Domain Generation Algorithms (DGAs), random tokens, or hex padding generate elevated entropy (>4.2 bits).

### Q9: What is the significance of the `@` symbol in phishing URLs?
**Answer:** In the standard URL specification (RFC 3986), characters before an `@` symbol represent HTTP Basic Authentication username/password tokens, and the browser ignores them for routing, directing the user to the host *after* the `@`. Attackers exploit this to display `http://google.com@attacker-controlled-site.com`.

### Q10: What were the findings from your Error Analysis?
**Answer:**
- **False Positives (119 URLs):** Legitimate academic, news, or government URLs containing lengthy directory paths, hyphens, or deep subdomains.
- **False Negatives (121 URLs):** Highly polished phishing attacks that registered short, clean, newly acquired domain names without special characters or overt lure words. Detecting these requires future page-content or domain-age signals.

### Q11: How does the system explain its predictions to the end user?
**Answer:** In the Flask backend (`/api/predict`), we inspect the extracted feature vector against high-risk thresholds (e.g. raw IP address, URL shortener, lure keyword count, abnormal subdomains) and return structured, human-readable risk factors ranked by severity.

### Q12: Why does a "Legitimate" prediction not guarantee that a website is safe?
**Answer:** An attacker may compromise a legitimate high-reputation website (e.g., an unpatched WordPress site) or abuse open redirects and cloud storage buckets. The URL structure appears clean and legitimate, but the hosted content is malicious.

### Q13: What is the difference between Gini Importance and Logistic Regression coefficients?
**Answer:** Gini Importance (Mean Decrease in Impurity) measures the total reduction in node impurity brought by a feature across all trees in Random Forest; it is always non-negative. Logistic Regression coefficients indicate both the magnitude and *directional sign* (+ pushing toward phishing, - pushing toward legitimate).

### Q14: How does the system handle bulk scanning safely?
**Answer:** The `POST /api/bulk-predict` endpoint accepts up to 50 URLs per request. It runs vectorized inference in memory, aggregating counts for safe, suspicious, and phishing URLs while returning individual verdicts within 5 milliseconds.

### Q15: What are the primary future improvements planned for PhishGuard?
**Answer:** As outlined in Slide 10 of our deck:
1. Incorporating lightweight runtime page metadata (form `action` targets and external favicon links).
2. Deep learning character embeddings (URLNet / 1D-CNNs).
3. Online streaming retraining on live feeds (PhishTank/OpenPhish) to combat concept drift.
4. Packaging into a client-side WebExtension for real-time browser warning popups.
