let datasetId = null;
let datasetColumns = [];

const $ = (id) => document.getElementById(id);

function toast(message) {
    const toastBox = $("toast");

    if (!toastBox) {
        alert(message);
        return;
    }

    toastBox.textContent = message;
    toastBox.classList.add("show");

    setTimeout(() => {
        toastBox.classList.remove("show");
    }, 3000);
}

function setStatus(text, cls = "working") {
    const badge = $("statusBadge");
    if (!badge) return;

    badge.className = `status ${cls}`;
    badge.textContent = text;
}

function setProgress(value) {
    const bar = $("progressBar");
    if (!bar) return;

    bar.style.width = `${value}%`;
}

async function parseResponse(response) {
    const text = await response.text();
    let data;

    try {
        data = text ? JSON.parse(text) : {};
    } catch {
        console.error(text);
        throw new Error("Invalid JSON response from server.");
    }

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed");
    }

    return data;
}

async function api(url, payload = {}) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify(payload)
    });

    return parseResponse(response);
}

function escapeHtml(text) {
    return String(text ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function renderObject(id, obj) {
    const el = $(id);
    if (!el) return;

    if (!obj) {
        el.innerHTML = "<div>No Data Available</div>";
        return;
    }

    el.innerHTML = Object.entries(obj)
        .map(([k, v]) => {
            const value = typeof v === "object" ? JSON.stringify(v) : v;

            return `
                <div class="profile-row">
                    <strong>${escapeHtml(k)}</strong>
                    <span>${escapeHtml(value)}</span>
                </div>
            `;
        })
        .join("");
}

function renderMetrics(profile) {
    const grid = $("metricGrid");
    if (!grid || !profile) return;

    const metrics = [
        ["Rows", profile.rows],
        ["Columns", profile.columns],
        ["Missing Values", profile.missing_values],
        ["Duplicate Rows", profile.duplicate_rows]
    ];

    grid.innerHTML = metrics
        .map(([label, value]) => `
            <div class="metric-card">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
            </div>
        `)
        .join("");
}

function renderColumns(cols, numericCols = []) {
    datasetColumns = cols || [];

    const targetCols = numericCols.length ? numericCols : datasetColumns;

    $("yCol").innerHTML = targetCols
        .map(col => `<option value="${escapeHtml(col)}">${escapeHtml(col)}</option>`)
        .join("");

    $("xCols").innerHTML = datasetColumns
        .map(col => `
            <label>
                <input type="checkbox" value="${escapeHtml(col)}">
                ${escapeHtml(col)}
            </label>
        `)
        .join("");

    autoSelectX();
}

function selectedX() {
    const y = $("yCol").value;

    return [...document.querySelectorAll("#xCols input:checked")]
        .map(el => el.value)
        .filter(v => v !== y);
}

function updateFeatureCount() {
    $("featureCount").textContent = `${selectedX().length} selected`;
}

function autoSelectX() {
    const y = $("yCol").value;

    document.querySelectorAll("#xCols input").forEach((box, i) => {
        box.checked = box.value !== y && i < 5;
    });

    updateFeatureCount();
}

function selectAllX() {
    const y = $("yCol").value;

    document.querySelectorAll("#xCols input").forEach(box => {
        box.checked = box.value !== y;
    });

    updateFeatureCount();
}

function clearX() {
    document.querySelectorAll("#xCols input").forEach(box => {
        box.checked = false;
    });

    updateFeatureCount();
}

async function uploadCSV() {
    const file = $("csvFile").files[0];

    if (!file) {
        toast("Select CSV file first");
        return;
    }

    try {
        setStatus("Uploading");
        setProgress(15);

        const fd = new FormData();
        fd.append("file", file);

        const response = await fetch("/api/upload", {
            method: "POST",
            body: fd
        });

        const data = await parseResponse(response);

        datasetId = data.dataset_id;
        renderColumns(data.columns, data.numeric_columns);
        renderObject("profile", data.profile);
        renderMetrics(data.profile);

        $("datasetTitle").textContent = file.name;

        setStatus("Uploaded", "ready");
        setProgress(30);
        toast("Dataset uploaded");
    } catch (err) {
        toast(err.message);
        console.error(err);
    }
}

async function preprocess() {
    if (!datasetId) {
        toast("Upload dataset first");
        return;
    }

    try {
        setStatus("Cleaning");
        setProgress(50);

        const data = await api("/api/preprocess", {
            dataset_id: datasetId
        });

        renderObject("preprocessResult", data.profile);
        renderColumns(data.columns, data.numeric_columns || data.columns);

        setStatus("Ready", "ready");
        setProgress(60);
    } catch (err) {
        toast(err.message);
    }
}

async function makeCharts() {
    if (!datasetId) {
        toast("Upload dataset first");
        return;
    }

    try {
        setStatus("Generating Charts");
        setProgress(75);

        const data = await api("/api/charts", {
            dataset_id: datasetId,
            y_col: $("yCol").value
        });

        $("insights").innerHTML = (data.insights || [])
            .map(i => `<div class="pill">${escapeHtml(i)}</div>`)
            .join("");

        const charts = $("charts");
        charts.innerHTML = "";

        (data.charts || []).forEach((chart, index) => {
            const card = document.createElement("div");
            const container = document.createElement("div");

            card.className = "chart-card";
            container.id = `chart${index}`;
            container.style.height = "500px";

            card.appendChild(container);
            charts.appendChild(card);

            const fig = JSON.parse(chart.json);

            Plotly.newPlot(container.id, fig.data, fig.layout, {
                responsive: true
            });
        });

        setStatus("Charts Ready", "ready");
    } catch (err) {
        toast(err.message);
    }
}

function renderModel(result) {
    if (!result) return;

    const best = result.best_model || {};

    $("modelSummary").innerHTML = `
        <div class="tiny">Best Model</div>
        <h2>${escapeHtml(best.model)}</h2>
        <div class="score">${escapeHtml(best.score)}</div>
        <p>${escapeHtml(result.problem_type)}</p>
    `;

    $("modelResult").innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                ${(result.models || []).map(m => `
                    <tr>
                        <td>${escapeHtml(m.model)}</td>
                        <td>${escapeHtml(m.score)}</td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
}

async function trainModel() {
    if (!datasetId) {
        toast("Upload dataset first");
        return;
    }

    try {
        setStatus("Training");

        const data = await api("/api/train", {
            dataset_id: datasetId,
            x_cols: selectedX(),
            y_col: $("yCol").value
        });

        renderModel(data.result);

        $("suggestions").innerHTML = (data.suggestions || [])
            .map(s => `<div class="warn">${escapeHtml(s)}</div>`)
            .join("");

        setStatus("Model Ready", "ready");
        setProgress(100);
    } catch (err) {
        toast(err.message);
    }
}

function formatBusinessAI(text) {
    return escapeHtml(text || "")
        .replace(/\*\*/g, "")
        .replace(/\|/g, "")
        .replace(/---/g, "")
        .replace(/\n/g, "<br>");
}

async function summary() {
    if (!datasetId) {
        toast("Upload dataset first");
        return;
    }

    try {
        const data = await api("/api/summary", {
            dataset_id: datasetId
        });

        $("summary").innerHTML = formatBusinessAI(data.summary);
    } catch (err) {
        toast(err.message);
    }
}

async function ask() {
    if (!datasetId) {
        toast("Upload dataset first");
        return;
    }

    const question = $("question").value.trim();

    if (!question) {
        toast("Enter question");
        return;
    }

    try {
        const data = await api("/api/ask", {
            dataset_id: datasetId,
            question
        });

        $("answer").innerHTML = formatBusinessAI(data.answer);
    } catch (err) {
        toast(err.message);
    }
}

function resetApp() {
    location.reload();
}

document.addEventListener("DOMContentLoaded", () => {
    $("csvFile")?.addEventListener("change", e => {
        const file = e.target.files[0];
        if (file) {
            $("fileName").textContent = file.name;
        }
    });

    $("yCol")?.addEventListener("change", autoSelectX);

    document.addEventListener("change", e => {
        if (e.target.matches("#xCols input")) {
            updateFeatureCount();
        }
    });

    window.uploadCSV = uploadCSV;
    window.preprocess = preprocess;
    window.makeCharts = makeCharts;
    window.trainModel = trainModel;
    window.summary = summary;
    window.ask = ask;
    window.selectAllX = selectAllX;
    window.clearX = clearX;
    window.autoSelectX = autoSelectX;
    window.resetApp = resetApp;
});
