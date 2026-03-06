(function () {
    const studentText = document.getElementById("student-text");
    const classifyBtn = document.getElementById("classify-btn");
    const loading = document.getElementById("loading");
    const resultSection = document.getElementById("result-section");
    const errorSection = document.getElementById("error-section");
    const predictionEl = document.getElementById("prediction");
    const rawOutputEl = document.getElementById("raw-output");
    const errorMessageEl = document.getElementById("error-message");

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
        predictionEl.textContent = prediction;
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
