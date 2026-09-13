import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runWorkflow = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      // Backend expects the query in the JSON body
      const response = await fetch(`${API_URL}/api/tasks/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail
            ? typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail)
            : "Workflow request failed"
        );
      }

      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {/* HERO */}
      <header className="hero-section">
        <h1>
          Intelligence that stays <span>on</span>
          <br />
          your infrastructure.
        </h1>

        <p>
          Execute confidential enterprise workloads through a multi-agent AI
          system with privacy controls and capability-based orchestration.
        </p>
      </header>

      {/* WORKSPACE */}
      <main className="workspace">
        {/* LEFT PANEL */}
        <section className="panel">
          <div className="panel-title">ASK KERNEL</div>

          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.ctrlKey && e.key === "Enter") {
                runWorkflow();
              }
            }}
            placeholder="Enter your task..."
            disabled={loading}
          />

          <button
            onClick={runWorkflow}
            disabled={loading || !query.trim()}
          >
            {loading ? "RUNNING WORKFLOW..." : "RUN WORKFLOW →"}
          </button>

          <div className="shortcut">
            CTRL + ENTER TO RUN
          </div>
        </section>

        {/* RIGHT PANEL */}
        <section className="panel output-panel">
          <div className="output-header">
            <span>WORKFLOW OUTPUT</span>

            <span className="live">
              <span className="live-dot">●</span> LIVE
            </span>
          </div>

          {/* LOADING */}
          {loading && (
            <div className="status">
              <div className="spinner"></div>

              <h3>Kernel is processing...</h3>

              <p>
                Planning agents, evaluating privacy policies,
                and executing the workflow.
              </p>
            </div>
          )}

          {/* ERROR */}
          {!loading && error && (
            <div className="error">
              <h3>Workflow Error</h3>

              <pre>{error}</pre>

              <button
                className="retry"
                onClick={runWorkflow}
              >
                RETRY →
              </button>
            </div>
          )}

          {/* SUCCESS */}
          {!loading && !error && result && (
            <div className="result">
              <div className="success-label">
                ● WORKFLOW COMPLETED
              </div>

              <h3>Response</h3>

              <div className="answer">
                {result.final_answer ||
                  result.current_answer ||
                  result.result ||
                  result.response ||
                  "Workflow completed, but no final answer was returned."}
              </div>

              {/* Workflow details */}
              <details>
                <summary>
                  View workflow details
                </summary>

                <pre>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            </div>
          )}

          {/* EMPTY */}
          {!loading && !error && !result && (
            <div className="empty">
              <div className="kernel-symbol">⌁</div>

              <p>
                Workflow results will appear here.
              </p>

              <span>
                Submit a task to begin.
              </span>
            </div>
          )}
        </section>
      </main>

      {/* FOOTER */}
      <footer>
        <div>
          <strong>KERNEL</strong>
          <span> SOVEREIGN AI WORKBENCH</span>
        </div>

        <div>
          ON-PREMISE • PRIVACY-FIRST • AGENTIC
        </div>
      </footer>
    </div>
  );
}

export default App;