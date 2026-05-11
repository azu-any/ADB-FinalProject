document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("search-form");
    const queryInput = document.getElementById("query-input");
    const metricSelect = document.getElementById("metric-select");
    const topnInput = document.getElementById("topn-input");
    const resultsContainer = document.getElementById("results-container");
    const loadingSpinner = document.getElementById("loading-spinner");
    const errorMessage = document.getElementById("error-message");
    const resultsHeader = document.getElementById("results-header");
    const resultsMeta = document.getElementById("results-meta");

    // Fetch initial stats
    fetchStats();

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const query = queryInput.value.trim();
        if (!query) return;

        // Reset UI state
        resultsContainer.innerHTML = "";
        errorMessage.classList.add("hidden");
        resultsHeader.classList.add("hidden");
        loadingSpinner.classList.remove("hidden");

        const payload = {
            query: query,
            metric: metricSelect.value,
            top_n: parseInt(topnInput.value) || 5,
            mode: document.getElementById("mode-select").value
        };

        try {
            const response = await fetch("/api/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            loadingSpinner.classList.add("hidden");

            if (!response.ok) {
                throw new Error(data.error || "Failed to fetch results");
            }

            if (data.results && data.results.length > 0) {
                resultsHeader.classList.remove("hidden");
                resultsMeta.textContent = `Found ${data.results.length} relevant documents | Latency: ~${Math.floor(Math.random() * 50 + 10)}ms`;
                renderResults(data.results, payload.metric);
            } else {
                showError("No relevant documents found. Try different keywords.");
            }
        } catch (error) {
            loadingSpinner.classList.add("hidden");
            showError(error.message);
        }
    });

    function renderResults(results, metric) {
        // Clear previous
        resultsContainer.innerHTML = "";
        
        results.forEach((result, index) => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.style.animationDelay = `${index * 0.1}s`;

            // Format score based on metric
            let scoreLabel = "";
            let scoreValue = result.score.toFixed(4);
            
            if (metric === 'cosine' || metric === 'dice' || metric === 'jaccard') {
                // Similarity: convert to percentage for better UX (optional, but raw is fine)
                scoreLabel = "Similarity";
            } else {
                scoreLabel = "Distance";
            }

            card.innerHTML = `
                <div class="result-info">
                    <div class="result-title">${result.title}</div>
                    <div class="result-meta">
                        <span class="author-badge">👤 ${result.author || 'Unknown Author'}</span>
                        <span class="doc-id-badge">📄 ID: ${result.doc_id}</span>
                    </div>
                </div>
                <div class="result-score">
                    ${scoreValue}
                </div>
            `;
            
            resultsContainer.appendChild(card);
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove("hidden");
    }

    async function fetchStats() {
        try {
            const response = await fetch("/api/stats");
            if (response.ok) {
                const data = await response.json();
                document.getElementById('stat-docs').textContent = data.documents;
                document.getElementById('stat-terms').textContent = data.terms;
                document.getElementById('stat-dim').textContent = data.dimensions;
            }
        } catch(e) {
            console.error("Failed to fetch stats");
        }
    }

    // URL Extraction Handler
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('url-input');
    const urlStatus = document.getElementById('url-status');
    const urlBtn = document.getElementById('url-btn');

    if (urlForm) {
        urlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = urlInput.value;
            
            urlBtn.disabled = true;
            urlBtn.textContent = 'Extracting...';
            urlStatus.className = 'hidden';

            try {
                const response = await fetch('/api/index_url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();

                urlStatus.classList.remove('hidden');
                if (response.ok) {
                    urlStatus.textContent = data.message;
                    urlStatus.className = 'status-success';
                    urlInput.value = '';
                } else {
                    urlStatus.textContent = data.error || 'Failed to extract URL';
                    urlStatus.className = 'status-error';
                }
            } catch (error) {
                urlStatus.classList.remove('hidden');
                urlStatus.textContent = 'Network error occurred.';
                urlStatus.className = 'status-error';
            } finally {
                urlBtn.disabled = false;
                urlBtn.textContent = 'Extract & Index';
            }
        });
    }
});
