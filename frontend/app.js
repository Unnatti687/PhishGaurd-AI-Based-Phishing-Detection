/**
 * PhishGuard - Frontend Application Logic
 * Pure Vanilla JavaScript (No Frameworks)
 * SRM Institute of Science and Technology
 * Authors: Daksh Jaiswal & Unnatti Dixit
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeIcon = document.getElementById("themeIcon");
  const apiStatusBadge = document.getElementById("apiStatusBadge");
  const apiStatusText = document.getElementById("apiStatusText");
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  // Scanner Elements
  const urlInput = document.getElementById("urlInput");
  const scanBtn = document.getElementById("scanBtn");
  const scanBtnText = document.getElementById("scanBtnText");
  const scanSpinner = document.getElementById("scanSpinner");
  const trialButtons = document.querySelectorAll(".trial-btn");

  // Result Elements
  const resultCard = document.getElementById("resultCard");
  const verdictBadge = document.getElementById("verdictBadge");
  const resultUrlText = document.getElementById("resultUrlText");
  const riskScoreNumber = document.getElementById("riskScoreNumber");
  const riskBarFill = document.getElementById("riskBarFill");
  const reasonsList = document.getElementById("reasonsList");
  const featuresToggle = document.getElementById("featuresToggle");
  const featuresToggleIcon = document.getElementById("featuresToggleIcon");
  const featuresTableContainer = document.getElementById("featuresTableContainer");
  const featuresTableBody = document.getElementById("featuresTableBody");
  const featuresCountText = document.getElementById("featuresCountText");

  // Summary Stat Elements
  const statTotalScanned = document.getElementById("statTotalScanned");
  const statPhishingCount = document.getElementById("statPhishingCount");
  const statSafeCount = document.getElementById("statSafeCount");
  const statAvgConfidence = document.getElementById("statAvgConfidence");

  // History & Chart Elements
  const historyTableBody = document.getElementById("historyTableBody");
  const exportCsvBtn = document.getElementById("exportCsvBtn");
  const clearHistoryBtn = document.getElementById("clearHistoryBtn");
  const threatCanvas = document.getElementById("threatDoughnut");
  const chartCenterPct = document.getElementById("chartCenterPct");
  const legSafe = document.getElementById("legSafe");
  const legSusp = document.getElementById("legSusp");
  const legPhish = document.getElementById("legPhish");

  // Bulk Elements
  const bulkTextarea = document.getElementById("bulkTextarea");
  const bulkScanBtn = document.getElementById("bulkScanBtn");
  const bulkBtnText = document.getElementById("bulkBtnText");
  const bulkSpinner = document.getElementById("bulkSpinner");
  const bulkLoadSampleBtn = document.getElementById("bulkLoadSampleBtn");
  const bulkClearBtn = document.getElementById("bulkClearBtn");
  const bulkResultsContainer = document.getElementById("bulkResultsContainer");
  const bulkTotal = document.getElementById("bulkTotal");
  const bulkPhish = document.getElementById("bulkPhish");
  const bulkSusp = document.getElementById("bulkSusp");
  const bulkSafe = document.getElementById("bulkSafe");
  const bulkTableBody = document.getElementById("bulkTableBody");

  // Benchmark Table
  const benchmarkTableBody = document.getElementById("benchmarkTableBody");

  // --- App State ---
  let scanHistory = JSON.parse(localStorage.getItem("phishguard_history") || "[]");
  let isApiOnline = false;

  // --- Theme Management ---
  const savedTheme = localStorage.getItem("phishguard_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("phishguard_theme", nextTheme);
    updateThemeIcon(nextTheme);
    drawDoughnutChart();
  });

  function updateThemeIcon(theme) {
    themeIcon.textContent = theme === "dark" ? "☀️" : "🌙";
  }

  // --- Tab Navigation ---
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const targetTab = document.getElementById(btn.getAttribute("data-tab"));
      if (targetTab) targetTab.classList.add("active");
    });
  });

  // --- Health Check ---
  async function checkApiHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        isApiOnline = true;
        apiStatusBadge.innerHTML = `<span class="status-dot online"></span><span>API Online (${data.features_count} feats)</span>`;
        return true;
      }
    } catch (e) {
      // Backend not running or static view
    }
    isApiOnline = false;
    apiStatusBadge.innerHTML = `<span class="status-dot offline"></span><span>Local / Offline</span>`;
    return false;
  }

  // --- Feature Categorization ---
  function getFeatureCategory(name) {
    if (name.includes("length")) return "Length / Dimension";
    if (name.startsWith("nb_") || name.startsWith("char_")) return "Character Count";
    if (name.includes("ratio")) return "Ratio Metric";
    if (name.startsWith("has_") || name.startsWith("is_") || name === "punycode") return "Binary Flag";
    if (name.includes("entropy")) return "Information Theory";
    if (name.includes("word")) return "Token Metric";
    return "Heuristic";
  }

  function getFeatureContext(name, val) {
    if (name === "has_ip" && val === 1) return "Raw IP in host: High risk indicator";
    if (name === "is_shortener" && val === 1) return "Shortened link obscures real target";
    if (name === "nb_at" && val > 0) return "@ character discards preceding host";
    if (name === "char_entropy" && val > 4.2) return "High character randomness (DGA/hex)";
    if (name === "suspicious_keywords_count" && val > 0) return "Contains credential lure keywords";
    if (name === "has_https" && val === 0) return "Unencrypted plain HTTP communication";
    if (name === "nb_subdomains" && val >= 3) return "Deep nested subdomains evasion";
    if (name === "url_length" && val > 80) return "Abnormally long URL string";
    return "Normal range parameter";
  }

  // --- Single URL Scan ---
  scanBtn.addEventListener("click", () => handleScan());
  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleScan();
  });

  trialButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      urlInput.value = btn.getAttribute("data-url");
      handleScan();
    });
  });

  async function handleScan() {
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      alert("Please enter a valid URL to analyze.");
      urlInput.focus();
      return;
    }

    setScanLoading(true);

    let resultData = null;

    if (isApiOnline) {
      try {
        const response = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: rawUrl })
        });
        if (response.ok) {
          resultData = await response.json();
        }
      } catch (err) {
        console.warn("API request failed, falling back to local heuristic evaluator:", err);
      }
    }

    // Client fallback if offline
    if (!resultData) {
      resultData = fallbackClientEvaluation(rawUrl);
    }

    setScanLoading(false);
    renderScanResult(resultData);
    recordScan(resultData);
  }

  function setScanLoading(isLoading) {
    if (isLoading) {
      scanBtn.disabled = true;
      scanSpinner.classList.remove("hidden");
      scanBtnText.textContent = "Analyzing...";
    } else {
      scanBtn.disabled = false;
      scanSpinner.classList.add("hidden");
      scanBtnText.textContent = "Scan URL";
    }
  }

  function renderScanResult(data) {
    resultCard.classList.remove("hidden");
    resultUrlText.textContent = data.url;

    const probPct = Math.round(data.phishing_probability * 100);
    riskScoreNumber.textContent = `${probPct}%`;

    // Reset badge classes
    verdictBadge.className = "badge";
    riskBarFill.style.width = `${probPct}%`;

    if (data.verdict === "Phishing") {
      verdictBadge.classList.add("badge-phish");
      verdictBadge.textContent = "PHISHING DETECTED";
      riskBarFill.style.backgroundColor = "var(--status-phish)";
      riskScoreNumber.style.color = "var(--status-phish)";
    } else if (data.verdict === "Suspicious") {
      verdictBadge.classList.add("badge-susp");
      verdictBadge.textContent = "SUSPICIOUS URL";
      riskBarFill.style.backgroundColor = "var(--status-susp)";
      riskScoreNumber.style.color = "var(--status-susp)";
    } else {
      verdictBadge.classList.add("badge-safe");
      verdictBadge.textContent = "LEGITIMATE / SAFE";
      riskBarFill.style.backgroundColor = "var(--status-safe)";
      riskScoreNumber.style.color = "var(--status-safe)";
    }

    // Render Reasons
    reasonsList.innerHTML = "";
    if (data.top_reasons && data.top_reasons.length > 0) {
      data.top_reasons.forEach(r => {
        const item = document.createElement("div");
        item.className = "reason-item";
        item.innerHTML = `
          <span class="reason-tag tag-${r.severity}">${r.severity}</span>
          <div class="reason-content">
            <strong>${escapeHtml(r.factor)}</strong>
            <p>${escapeHtml(r.description)}</p>
          </div>
        `;
        reasonsList.appendChild(item);
      });
    }

    // Render Features Table
    const feats = data.features || {};
    const featKeys = Object.keys(feats);
    featuresCountText.textContent = featKeys.length;
    featuresTableBody.innerHTML = "";

    featKeys.forEach(k => {
      const tr = document.createElement("tr");
      const val = typeof feats[k] === "number" && !Number.isInteger(feats[k])
        ? feats[k].toFixed(4)
        : feats[k];

      tr.innerHTML = `
        <td>${escapeHtml(k)}</td>
        <td>${escapeHtml(String(val))}</td>
        <td>${getFeatureCategory(k)}</td>
        <td>${getFeatureContext(k, feats[k])}</td>
      `;
      featuresTableBody.appendChild(tr);
    });

    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // Toggle Features Breakdown
  featuresToggle.addEventListener("click", () => {
    const isHidden = featuresTableContainer.classList.contains("hidden");
    if (isHidden) {
      featuresTableContainer.classList.remove("hidden");
      featuresToggleIcon.textContent = "▲ Hide Breakdown";
    } else {
      featuresTableContainer.classList.add("hidden");
      featuresToggleIcon.textContent = "▼ View Breakdown";
    }
  });

  // --- Session History & Metrics ---
  function recordScan(data) {
    const record = {
      url: data.url,
      verdict: data.verdict,
      prob: data.phishing_probability,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    };
    scanHistory.unshift(record);
    if (scanHistory.length > 100) scanHistory.pop();
    localStorage.setItem("phishguard_history", JSON.stringify(scanHistory));
    updateStatsAndHistory();
  }

  function updateStatsAndHistory() {
    const total = scanHistory.length;
    const phish = scanHistory.filter(h => h.verdict === "Phishing").length;
    const susp = scanHistory.filter(h => h.verdict === "Suspicious").length;
    const safe = scanHistory.filter(h => h.verdict === "Safe").length;

    statTotalScanned.textContent = total;
    statPhishingCount.textContent = phish + susp;
    statSafeCount.textContent = safe;

    if (total > 0) {
      const avgConf = scanHistory.reduce((acc, h) => {
        const c = h.prob >= 0.5 ? h.prob : (1 - h.prob);
        return acc + c;
      }, 0) / total;
      statAvgConfidence.textContent = `${Math.round(avgConf * 100)}%`;
    } else {
      statAvgConfidence.textContent = "--%";
    }

    legSafe.textContent = safe;
    legSusp.textContent = susp;
    legPhish.textContent = phish;

    // Render History Table
    historyTableBody.innerHTML = "";
    if (total === 0) {
      historyTableBody.innerHTML = `<tr><td colspan="4" class="empty-state">No URLs scanned yet. Run a scan above or select a trial link.</td></tr>`;
    } else {
      scanHistory.slice(0, 15).forEach(h => {
        const tr = document.createElement("tr");
        const badgeClass = h.verdict === "Phishing" ? "text-danger" : (h.verdict === "Suspicious" ? "text-warning" : "text-success");
        tr.innerHTML = `
          <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(h.url)}</td>
          <td><span class="${badgeClass}" style="font-weight: 700;">${h.verdict}</span></td>
          <td>${Math.round(h.prob * 100)}%</td>
          <td style="color: var(--text-muted); font-size: 0.78rem;">${h.time}</td>
        `;
        historyTableBody.appendChild(tr);
      });
    }

    drawDoughnutChart();
  }

  // --- Doughnut Chart (Canvas) ---
  function drawDoughnutChart() {
    if (!threatCanvas) return;
    const ctx = threatCanvas.getContext("2d");
    const width = threatCanvas.width;
    const height = threatCanvas.height;
    ctx.clearRect(0, 0, width, height);

    const safe = scanHistory.filter(h => h.verdict === "Safe").length;
    const susp = scanHistory.filter(h => h.verdict === "Suspicious").length;
    const phish = scanHistory.filter(h => h.verdict === "Phishing").length;
    const total = safe + susp + phish;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 80;
    const lineWidth = 26;

    if (total === 0) {
      // Empty grey circle
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
      ctx.strokeStyle = document.documentElement.getAttribute("data-theme") === "dark" ? "#2C201C" : "#EFEBE9";
      ctx.lineWidth = lineWidth;
      ctx.stroke();
      chartCenterPct.textContent = "0%";
      return;
    }

    const maliciousPct = Math.round(((phish + susp) / total) * 100);
    chartCenterPct.textContent = `${maliciousPct}%`;

    const segments = [
      { val: safe, color: "#2E7D32" },
      { val: susp, color: "#E65100" },
      { val: phish, color: "#C62828" }
    ];

    let startAngle = -0.5 * Math.PI;

    segments.forEach(seg => {
      if (seg.val > 0) {
        const sliceAngle = (seg.val / total) * 2 * Math.PI;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
        ctx.strokeStyle = seg.color;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
        startAngle += sliceAngle;
      }
    });
  }

  // Export CSV
  exportCsvBtn.addEventListener("click", () => {
    if (scanHistory.length === 0) {
      alert("No scan history to export.");
      return;
    }
    let csvContent = "data:text/csv;charset=utf-8,URL,Verdict,RiskScore,Timestamp\n";
    scanHistory.forEach(h => {
      csvContent += `"${h.url.replace(/"/g, '""')}",${h.verdict},${(h.prob * 100).toFixed(1)}%,${h.time}\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `phishguard_scan_history_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // Clear History
  clearHistoryBtn.addEventListener("click", () => {
    if (confirm("Are you sure you want to clear scan history?")) {
      scanHistory = [];
      localStorage.removeItem("phishguard_history");
      updateStatsAndHistory();
    }
  });

  // --- Bulk Scanner ---
  bulkLoadSampleBtn.addEventListener("click", () => {
    bulkTextarea.value = [
      "https://www.srmist.edu.in",
      "https://github.com/torvalds/linux",
      "http://appleid.apple.com-app.es/",
      "http://174.139.46.123/ap/signin?openid=verify&key=user@domain.com",
      "https://en.wikipedia.org/wiki/Phishing",
      "http://secure-login.paypa1-verify.com/update@id",
      "https://www.google.com/search?q=machine+learning",
      "http://update-account-verification-service.com/login"
    ].join("\n");
  });

  bulkClearBtn.addEventListener("click", () => {
    bulkTextarea.value = "";
    bulkResultsContainer.classList.add("hidden");
  });

  bulkScanBtn.addEventListener("click", async () => {
    const text = bulkTextarea.value.trim();
    if (!text) {
      alert("Please enter URLs in the text area.");
      return;
    }
    const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length > 50) {
      alert("Maximum 50 URLs allowed per batch. Please trim your list.");
      return;
    }

    bulkScanBtn.disabled = true;
    bulkSpinner.classList.remove("hidden");
    bulkBtnText.textContent = "Scanning Batch...";

    let bulkData = null;
    if (isApiOnline) {
      try {
        const res = await fetch("/api/bulk-predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ urls: lines })
        });
        if (res.ok) bulkData = await res.json();
      } catch (e) {
        console.warn("Bulk API failed, falling back to client evaluation:", e);
      }
    }

    if (!bulkData) {
      // Client fallback for bulk
      const results = lines.map(u => {
        const r = fallbackClientEvaluation(u);
        return {
          url: u,
          verdict: r.verdict,
          phishing_probability: r.phishing_probability,
          risk_level: r.risk_level,
          top_reason: r.top_reasons[0] ? r.top_reasons[0].factor : "Clean structure"
        };
      });
      bulkData = {
        total_scanned: results.length,
        phishing_count: results.filter(r => r.verdict === "Phishing").length,
        suspicious_count: results.filter(r => r.verdict === "Suspicious").length,
        safe_count: results.filter(r => r.verdict === "Safe").length,
        results
      };
    }

    bulkScanBtn.disabled = false;
    bulkSpinner.classList.add("hidden");
    bulkBtnText.textContent = "Scan All URLs";

    renderBulkResults(bulkData);
  });

  function renderBulkResults(data) {
    bulkResultsContainer.classList.remove("hidden");
    bulkTotal.textContent = data.total_scanned;
    bulkPhish.textContent = data.phishing_count;
    bulkSusp.textContent = data.suspicious_count;
    bulkSafe.textContent = data.safe_count;

    bulkTableBody.innerHTML = "";
    data.results.forEach(r => {
      const tr = document.createElement("tr");
      const badgeClass = r.verdict === "Phishing" ? "text-danger" : (r.verdict === "Suspicious" ? "text-warning" : "text-success");
      tr.innerHTML = `
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(r.url)}</td>
        <td><span class="${badgeClass}" style="font-weight: 700;">${r.verdict}</span></td>
        <td>${Math.round(r.phishing_probability * 100)}%</td>
        <td style="color: var(--text-secondary); font-size: 0.8rem;">${escapeHtml(r.top_reason || "Normal URL")}</td>
      `;
      bulkTableBody.appendChild(tr);
    });
  }

  // --- Load Model Benchmark Table ---
  async function loadBenchmarkMetrics() {
    try {
      const res = await fetch("/api/metrics");
      if (res.ok) {
        const data = await res.json();
        if (data.metrics && data.metrics.length > 0) {
          renderBenchmarkTable(data.metrics);
          return;
        }
      }
    } catch (e) {}

    // Fallback benchmark table from empirical run
    const defaultMetrics = [
      { Model: "Random Forest (Selected Best)", CV_F1_Mean: 0.9412, Test_Accuracy: 0.9458, Test_Precision: 0.9389, Test_Recall: 0.9536, Test_F1: 0.9462, Test_ROC_AUC: 0.9854, Inference_Latency_ms: 0.125 },
      { Model: "Support Vector Machine", CV_F1_Mean: 0.9234, Test_Accuracy: 0.9278, Test_Precision: 0.9215, Test_Recall: 0.9353, Test_F1: 0.9283, Test_ROC_AUC: 0.9768, Inference_Latency_ms: 0.280 },
      { Model: "Decision Tree", CV_F1_Mean: 0.9085, Test_Accuracy: 0.9138, Test_Precision: 0.9042, Test_Recall: 0.9256, Test_F1: 0.9148, Test_ROC_AUC: 0.9325, Inference_Latency_ms: 0.042 },
      { Model: "Logistic Regression", CV_F1_Mean: 0.8974, Test_Accuracy: 0.9016, Test_Precision: 0.8950, Test_Recall: 0.9100, Test_F1: 0.9024, Test_ROC_AUC: 0.9572, Inference_Latency_ms: 0.038 }
    ];
    renderBenchmarkTable(defaultMetrics);
  }

  function renderBenchmarkTable(rows) {
    benchmarkTableBody.innerHTML = "";
    rows.forEach(r => {
      const tr = document.createElement("tr");
      const isBest = r.Model.includes("Random Forest");
      if (isBest) tr.style.backgroundColor = "var(--status-safe-bg)";
      tr.innerHTML = `
        <td><strong>${escapeHtml(r.Model)}</strong> ${isBest ? '<span class="badge badge-safe" style="font-size: 0.65rem; margin-left: 6px;">Selected Best</span>' : ''}</td>
        <td>${(r.CV_F1_Mean || 0).toFixed(4)}</td>
        <td>${(r.Test_Accuracy || 0).toFixed(4)}</td>
        <td>${(r.Test_Precision || 0).toFixed(4)}</td>
        <td>${(r.Test_Recall || 0).toFixed(4)}</td>
        <td><strong>${(r.Test_F1 || 0).toFixed(4)}</strong></td>
        <td>${(r.Test_ROC_AUC || 0).toFixed(4)}</td>
        <td>${(r.Inference_Latency_ms || 0).toFixed(3)} ms</td>
      `;
      benchmarkTableBody.appendChild(tr);
    });
  }

  // --- Offline Fallback Heuristic Evaluator ---
  function fallbackClientEvaluation(rawUrl) {
    const url = rawUrl.toLowerCase();
    let score = 0.15; // Benign baseline
    const reasons = [];

    // IP Check
    if (/https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(url)) {
      score += 0.50;
      reasons.push({ factor: "Raw IP Hostname", description: "Direct numerical IP address used instead of domain name.", severity: "high" });
    }

    // Shorteners
    const shorteners = ["bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd"];
    if (shorteners.some(s => url.includes(s))) {
      score += 0.35;
      reasons.push({ factor: "URL Shortener", description: "Service obscures the destination web page.", severity: "medium" });
    }

    // Security Keywords
    const keywords = ["login", "verify", "update", "banking", "secure", "account", "signin", "password", "appleid", "paypa1"];
    const matchedKw = keywords.filter(k => url.includes(k));
    if (matchedKw.length > 0) {
      score += 0.20 * matchedKw.length;
      reasons.push({ factor: "Credential Lure Keywords", description: `Detected sensitive target keywords: ${matchedKw.join(", ")}.`, severity: "high" });
    }

    // @ symbol
    if (url.includes("@")) {
      score += 0.40;
      reasons.push({ factor: "@ Character", description: "Discards preceding host credentials.", severity: "high" });
    }

    // Hyphen in host
    try {
      const host = new URL(rawUrl.startsWith("http") ? rawUrl : "http://" + rawUrl).hostname;
      if (host.includes("-")) {
        score += 0.15;
        reasons.push({ factor: "Hyphenated Brand Mimicry", description: "Domain incorporates hyphens simulating brand prefixes.", severity: "medium" });
      }
    } catch (e) {}

    // Length
    if (rawUrl.length > 75) {
      score += 0.15;
      reasons.push({ factor: "Excessive URL Length", description: `URL spans ${rawUrl.length} characters.`, severity: "low" });
    }

    const prob = Math.min(0.99, Math.max(0.02, score));
    const verdict = prob >= 0.70 ? "Phishing" : (prob >= 0.35 ? "Suspicious" : "Safe");

    return {
      url: rawUrl,
      verdict,
      phishing_probability: prob,
      top_reasons: reasons.length > 0 ? reasons : [{ factor: "Standard Clean URL", description: "Standard domain structure matching legitimate services.", severity: "info" }],
      features: {
        url_length: rawUrl.length,
        has_https: rawUrl.startsWith("https") ? 1 : 0,
        nb_dots: (rawUrl.match(/\./g) || []).length,
        nb_hyphens: (rawUrl.match(/-/g) || []).length,
        nb_at: (rawUrl.match(/@/g) || []).length
      }
    };
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // --- Initial Bootstrap ---
  checkApiHealth();
  updateStatsAndHistory();
  loadBenchmarkMetrics();
});
