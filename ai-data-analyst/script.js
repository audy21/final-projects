var API_URL = "http://localhost:8004";
var TOKEN_KEY = "analis_token";

var viewLogin = document.getElementById("view-login");
var viewApp = document.getElementById("view-app");

function api(path, options) {
  options = options || {};
  options.headers = options.headers || {};
  options.headers["Content-Type"] = "application/json";
  var token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    options.headers["Authorization"] = "Bearer " + token;
  }
  return fetch(API_URL + path, options).then(function (response) {
    if (response.status === 401) {
      logout();
      throw new Error("Sesi berakhir. Silakan masuk kembali.");
    }
    return response.json();
  });
}

function showLogin() {
  viewLogin.hidden = false;
  viewApp.hidden = true;
}

function showApp() {
  viewLogin.hidden = true;
  viewApp.hidden = false;
  loadHistory();
  loadDbCurrent();
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  showLogin();
}

/* ===== Login ===== */

var loginForm = document.getElementById("login-form");
var loginError = document.getElementById("login-error");

loginForm.addEventListener("submit", function (event) {
  event.preventDefault();
  var username = document.getElementById("login-username").value.trim();
  var password = document.getElementById("login-password").value;

  fetch(API_URL + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, password: password })
  })
    .then(function (response) {
      if (response.status === 401) {
        loginError.textContent = "Username atau password salah.";
        loginError.hidden = false;
        throw new Error("unauthorized");
      }
      return response.json();
    })
    .then(function (data) {
      localStorage.setItem(TOKEN_KEY, data.token);
      loginError.hidden = true;
      document.getElementById("login-password").value = "";
      showApp();
    })
    .catch(function (err) {
      if (err.message !== "unauthorized") {
        loginError.textContent = "Tidak dapat terhubung ke server. Pastikan backend berjalan di port 8004.";
        loginError.hidden = false;
      }
    });
});

document.getElementById("btn-logout").addEventListener("click", logout);

/* ===== Tab ===== */

var tabs = document.querySelectorAll(".tab");
var panelQuery = document.getElementById("panel-query");
var panelSettings = document.getElementById("panel-settings");

tabs.forEach(function (tab) {
  tab.addEventListener("click", function () {
    tabs.forEach(function (t) { t.classList.remove("active"); });
    tab.classList.add("active");
    var view = tab.getAttribute("data-view");
    panelQuery.hidden = view !== "query";
    panelSettings.hidden = view !== "settings";
  });
});

/* ===== Kueri ===== */

var queryForm = document.getElementById("query-form");
var queryInput = document.getElementById("query-input");
var stateInitial = document.getElementById("state-initial");
var stateLoading = document.getElementById("state-loading");
var stateSuccess = document.getElementById("state-success");
var stateError = document.getElementById("state-error");
var errorMessage = document.getElementById("error-message");
var resultQuery = document.getElementById("result-query");
var resultCount = document.getElementById("result-count");
var resultTable = document.getElementById("result-table");
var summaryBlocks = document.getElementById("summary-blocks");
var chartWrap = document.getElementById("chart-wrap");
var btnDownloadChart = document.getElementById("btn-download-chart");
var sqlBox = document.getElementById("sql-box");
var sqlText = document.getElementById("sql-text");
var emptyResult = document.getElementById("empty-result");
var tableWrap = document.getElementById("table-wrap");
var btnDownload = document.getElementById("btn-download");

var activeChart = null;

function showQueryState(el) {
  stateInitial.hidden = true;
  stateLoading.hidden = true;
  stateSuccess.hidden = true;
  stateError.hidden = true;
  el.hidden = false;
}

function renderTable(columns, rows) {
  var thead = resultTable.querySelector("thead");
  var tbody = resultTable.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  var headRow = document.createElement("tr");
  columns.forEach(function (column) {
    var th = document.createElement("th");
    th.textContent = column;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);

  rows.forEach(function (row) {
    var tr = document.createElement("tr");
    row.forEach(function (cell) {
      var td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function formatNumber(value) {
  return Number(value).toLocaleString("id-ID");
}

function renderSummary(columns, rows) {
  summaryBlocks.innerHTML = "";
  var hasContent = false;

  var totalBlock = document.createElement("div");
  totalBlock.className = "summary-block";
  var totalLabel = document.createElement("span");
  totalLabel.className = "summary-label";
  totalLabel.textContent = "Total baris";
  var totalValue = document.createElement("span");
  totalValue.className = "summary-value";
  totalValue.textContent = formatNumber(rows.length);
  totalBlock.appendChild(totalLabel);
  totalBlock.appendChild(totalValue);
  summaryBlocks.appendChild(totalBlock);
  hasContent = true;

  columns.forEach(function (column, i) {
    if (column.toLowerCase() === "id") return;
    var values = rows.map(function (r) { return r[i]; });
    var allNumeric = values.length > 0 && values.every(function (v) {
      return v !== null && v !== "" && !isNaN(Number(v));
    });
    if (!allNumeric) return;

    var sum = values.reduce(function (acc, v) { return acc + Number(v); }, 0);
    var block = document.createElement("div");
    block.className = "summary-block";
    var label = document.createElement("span");
    label.className = "summary-label";
    var upper = column.toUpperCase();
    label.textContent = upper.indexOf("COUNT") !== -1 ? "Total hasil" : "Total " + column;
    var value = document.createElement("span");
    value.className = "summary-value";
    value.textContent = formatNumber(sum);
    block.appendChild(label);
    block.appendChild(value);
    summaryBlocks.appendChild(block);
    hasContent = true;
  });

  summaryBlocks.hidden = !hasContent;
}

function detectChart(columns, rows) {
  var dateIndex = -1;
  var numericIndex = -1;
  var textIndex = -1;

  columns.forEach(function (column, i) {
    if (column.toLowerCase() === "id") return;
    var values = rows.map(function (r) { return r[i]; }).filter(function (v) {
      return v !== null && v !== "";
    });
    if (values.length === 0) return;

    var allNumeric = values.every(function (v) { return !isNaN(Number(v)); });
    var allDates = values.every(function (v) {
      return /^\d{4}-\d{2}-\d{2}/.test(String(v));
    });

    if (allNumeric && numericIndex === -1) {
      numericIndex = i;
    } else if (allDates && dateIndex === -1) {
      dateIndex = i;
    } else if (!allNumeric && textIndex === -1) {
      textIndex = i;
    }
  });

  if (dateIndex !== -1 && numericIndex !== -1) {
    return { type: "line", labelIndex: dateIndex, valueIndex: numericIndex };
  }
  if (textIndex !== -1 && numericIndex !== -1) {
    return { type: "bar", labelIndex: textIndex, valueIndex: numericIndex };
  }
  return null;
}

function renderChart(columns, rows) {
  if (activeChart) {
    activeChart.destroy();
    activeChart = null;
  }

  var spec = detectChart(columns, rows);
  if (!spec) {
    chartWrap.hidden = true;
    btnDownloadChart.hidden = true;
    return;
  }

  var labels = rows.map(function (r) {
    var label = String(r[spec.labelIndex]);
    return label.length > 20 ? label.slice(0, 20) + "…" : label;
  });
  var values = rows.map(function (r) { return Number(r[spec.valueIndex]); });

  activeChart = new Chart(document.getElementById("result-chart"), {
    type: spec.type,
    data: {
      labels: labels,
      datasets: [{
        label: columns[spec.valueIndex],
        data: values,
        backgroundColor: "#1a56db",
        borderColor: "#1a56db",
        borderWidth: spec.type === "line" ? 2 : 0
      }]
    },
    options: {
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  chartWrap.hidden = false;
  btnDownloadChart.hidden = false;
}

function runQuery(text) {
  showQueryState(stateLoading);

  api("/query", {
    method: "POST",
    body: JSON.stringify({ text: text })
  })
    .then(function (data) {
      if (data.error) {
        errorMessage.textContent = data.error;
        showQueryState(stateError);
        return;
      }

      sqlText.textContent = data.sql || "";
      sqlBox.hidden = !data.sql;

      if (data.rows.length === 0) {
        renderSummary(data.columns, data.rows);
        chartWrap.hidden = true;
        btnDownloadChart.hidden = true;
        tableWrap.hidden = true;
        emptyResult.hidden = false;
        btnDownload.hidden = true;
      } else {
        renderTable(data.columns, data.rows);
        renderSummary(data.columns, data.rows);
        renderChart(data.columns, data.rows);
        tableWrap.hidden = false;
        emptyResult.hidden = true;
        btnDownload.hidden = false;
      }

      resultQuery.textContent = text;
      resultCount.textContent = data.rows.length;
      showQueryState(stateSuccess);
      loadHistory();
    })
    .catch(function (err) {
      errorMessage.textContent = err.message || "Kueri gagal. Coba lagi.";
      showQueryState(stateError);
    });
}

queryForm.addEventListener("submit", function (event) {
  event.preventDefault();
  var text = queryInput.value.trim();
  if (text === "") {
    errorMessage.textContent = "Pertanyaan tidak boleh kosong.";
    showQueryState(stateError);
    return;
  }
  runQuery(text);
});

queryInput.addEventListener("keydown", function (event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    queryForm.requestSubmit();
  }
});

document.querySelectorAll(".example-chip").forEach(function (chip) {
  chip.addEventListener("click", function () {
    queryInput.value = chip.textContent;
    queryForm.requestSubmit();
  });
});

document.querySelectorAll("[data-reset]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    queryInput.value = "";
    showQueryState(stateInitial);
    queryInput.focus();
  });
});

/* ===== Unduh ===== */

document.getElementById("btn-download").addEventListener("click", function () {
  var rows = [];
  resultTable.querySelectorAll("tr").forEach(function (tr) {
    var cells = [];
    tr.querySelectorAll("th, td").forEach(function (cell) {
      cells.push("\"" + cell.textContent.trim() + "\"");
    });
    rows.push(cells.join(","));
  });
  var csv = rows.join("\n");
  var blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  var link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "hasil-kueri.csv";
  link.click();
});

btnDownloadChart.addEventListener("click", function () {
  var canvas = document.getElementById("result-chart");
  var link = document.createElement("a");
  link.href = canvas.toDataURL("image/png");
  link.download = "grafik.png";
  link.click();
});

/* ===== Riwayat ===== */

var historyList = document.getElementById("history-list");
var historyEmpty = document.getElementById("history-empty");

function loadHistory() {
  api("/history")
    .then(function (data) {
      historyList.innerHTML = "";
      var items = data.history || [];
      historyEmpty.hidden = items.length > 0;
      items.forEach(function (item) {
        var li = document.createElement("li");
        li.textContent = item.text;
        li.title = item.text + " — " + item.ts;
        li.addEventListener("click", function () {
          queryInput.value = item.text;
          runQuery(item.text);
        });
        historyList.appendChild(li);
      });
    })
    .catch(function () {});
}

/* ===== Pengaturan Database ===== */

var dbForm = document.getElementById("db-form");
var dbResult = document.getElementById("db-result");
var dbStatus = document.getElementById("db-status");
var dbTables = document.getElementById("db-tables");

dbForm.addEventListener("submit", function (event) {
  event.preventDefault();

  var config = {
    host: document.getElementById("db-host").value.trim(),
    port: document.getElementById("db-port").value.trim(),
    dbname: document.getElementById("db-name").value.trim(),
    username: document.getElementById("db-username").value.trim(),
    password: document.getElementById("db-password").value
  };

  api("/db/connect", {
    method: "POST",
    body: JSON.stringify(config)
  })
    .then(function (data) {
      dbResult.hidden = false;
      dbTables.innerHTML = "";
      if (data.status === "connected") {
        dbStatus.textContent = "Terhubung (" + data.engine + ")";
        dbStatus.className = "db-status ok";
        data.tables.forEach(function (t) {
          var li = document.createElement("li");
          li.textContent = t;
          dbTables.appendChild(li);
        });
      } else {
        dbStatus.textContent = data.error || "Koneksi gagal.";
        dbStatus.className = "db-status failed";
      }
    })
    .catch(function (err) {
      dbResult.hidden = false;
      dbStatus.textContent = err.message || "Koneksi gagal.";
      dbStatus.className = "db-status failed";
      dbTables.innerHTML = "";
    });
});

function loadDbCurrent() {
  api("/db/current")
    .then(function (data) {
      if (!data.schema || data.schema.length === 0) return;
      dbResult.hidden = false;
      dbStatus.textContent = "Aktif: " + data.engine;
      dbStatus.className = "db-status ok";
      dbTables.innerHTML = "";
      data.schema.forEach(function (t) {
        var li = document.createElement("li");
        li.textContent = t.table;
        dbTables.appendChild(li);
      });
    })
    .catch(function () {});
}

/* ===== Inisialisasi ===== */

if (localStorage.getItem(TOKEN_KEY)) {
  showApp();
} else {
  showLogin();
}
