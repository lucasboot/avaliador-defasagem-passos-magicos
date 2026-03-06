(function () {
    const studentText = document.getElementById("student-text");
    const classifyBtn = document.getElementById("classify-btn");
    const loading = document.getElementById("loading");
    const resultSection = document.getElementById("result-section");
    const errorSection = document.getElementById("error-section");
    const predictionEl = document.getElementById("prediction");
    const rawOutputEl = document.getElementById("raw-output");
    const errorMessageEl = document.getElementById("error-message");

    function toTitleCase(value) {
        return value
            .split(" ")
            .filter(Boolean)
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }

    function normalizePrediction(prediction) {
        return String(prediction || "")
            .trim()
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^\w\s]/g, "")
            .replace(/\s+/g, "_");
    }

    function formatPredictionLabel(prediction) {
        const normalized = normalizePrediction(prediction);

        if (normalized.includes("severa")) {
            return "Severa";
        }

        if (normalized.includes("moderada")) {
            return "Moderada";
        }

        if (normalized.includes("em_fase")) {
            return "Em Fase";
        }

        return toTitleCase(normalized.replace(/_/g, " "));
    }

    function getPredictionTone(prediction) {
        const normalized = normalizePrediction(prediction);

        if (normalized.includes("severa")) {
            return "error";
        }

        if (normalized.includes("moderada")) {
            return "warning";
        }

        if (normalized.includes("em_fase")) {
            return "success";
        }

        return "neutral";
    }

    function hideAll() {
        loading.classList.add("hidden");
        resultSection.classList.add("hidden");
        errorSection.classList.add("hidden");
    }

    function showLoading() {
        hideAll();
        loading.classList.remove("hidden");
    }

    function showResult(prediction, rawOutput, explanation) {
        hideAll();
        predictionEl.textContent = formatPredictionLabel(prediction);
        predictionEl.classList.remove("prediction--success", "prediction--warning", "prediction--error", "prediction--neutral");
        predictionEl.classList.add(`prediction--${getPredictionTone(prediction)}`);
        rawOutputEl.textContent = rawOutput || "(vazio)";
        const explanationEl = document.getElementById("explanation");
        if (explanation && explanation.trim()) {
            explanationEl.textContent = explanation;
            explanationEl.classList.remove("hidden");
        } else {
            explanationEl.textContent = "";
            explanationEl.classList.add("hidden");
        }
        resultSection.classList.remove("hidden");
    }

    function showError(message) {
        hideAll();
        errorMessageEl.textContent = message;
        errorSection.classList.remove("hidden");
    }

    classifyBtn.addEventListener("click", async function () {
        const text = studentText.value.trim();
        if (!text) {
            showError("Por favor, digite o caso do aluno.");
            return;
        }

        showLoading();
        classifyBtn.disabled = true;

        try {
            const res = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ student_text: text }),
            });

            const data = await res.json();

            if (!res.ok) {
                const detail = data.detail || (typeof data.detail === "string" ? data.detail : "Erro desconhecido");
                const msg = typeof detail === "string"
                    ? detail
                    : (detail.msg || JSON.stringify(detail));
                const rawInfo = data.raw_output ? ` Resposta bruta: "${data.raw_output}"` : "";
                showError(msg + rawInfo);
                return;
            }

            showResult(data.prediction, data.raw_output, data.explanation);
        } catch (err) {
            showError("Falha ao conectar com a API: " + (err.message || "Erro de rede"));
        } finally {
            classifyBtn.disabled = false;
        }
    });
})();
