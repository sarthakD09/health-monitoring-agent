"use client";

import { useEffect, useRef, useState } from "react";
import type { MonitoringResult, Observation } from "./types";

type Mode = "demo" | "live";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const WS_URL = API_URL.replace(/^http/, "ws");
const SUBJECT_ID = "dashboard-demo-subject";

type WebSocketStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

const demoVitals = {
  heartRate: 72,
  spo2: 98,
  temperature: 36.7,
  signalQuality: 0.95,
};

function makeObservation(): Observation {
  return {
    timestamp: new Date().toISOString(),
    subject_id: "dashboard-demo-subject",
    source: "scenario",
    heart_rate: 72,
    spo2: 98,
    temperature: 36.7,
    activity: "resting",
    signal_quality: 0.95,
  };
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("demo");
  const [backendStatus, setBackendStatus] = useState("Not checked");
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");
  const [result, setResult] = useState<MonitoringResult | null>(null);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>("disconnected");
  const [wsError, setWsError] = useState("");
  const [wsSending, setWsSending] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    return () => {
      const socket = wsRef.current;

      if (socket) {
        wsRef.current = null;

        // Prevent callbacks from updating state after unmount.
        socket.onopen = null;
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;

        socket.close();
      }
    };
  }, []);
  async function checkBackend() {
    setChecking(true);
    setApiError("");

    try {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) throw new Error(`Health check returned ${response.status}`);

      const data: { status: string } = await response.json();
      setBackendStatus(data.status === "ok" ? "Connected" : "Unexpected response");
    } catch {
      setBackendStatus("Disconnected");
      setApiError("Could not reach FastAPI. Confirm that the backend is running on port 8000.");
    } finally {
      setChecking(false);
    }
  }

  async function submitObservation() {
    setSubmitting(true);
    setApiError("");

    try {
      const observation = makeObservation();
      const response = await fetch(`${API_URL}/observations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(observation),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`API returned ${response.status}: ${detail}`);
      }

      const data: MonitoringResult = await response.json();
      setResult(data);
      setBackendStatus("Connected");
    } catch (error) {
      setApiError(
        error instanceof Error
          ? error.message
          : "Could not submit the observation.",
      );
    } finally {
      setSubmitting(false);
    }
  }
  function connectWebSocket() {
  const current = wsRef.current;

  if (
    current &&
    (current.readyState === WebSocket.OPEN ||
      current.readyState === WebSocket.CONNECTING)
  ) {
    return;
  }

  setWsError("");
  setWsStatus("connecting");

  try {
    const socket = new WebSocket(
      `${WS_URL}/ws/monitor/${encodeURIComponent(SUBJECT_ID)}`,
    );

    wsRef.current = socket;

    socket.onopen = () => {
      setWsStatus("connected");
      setWsError("");
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      setWsSending(false);

      try {
        const payload: unknown = JSON.parse(event.data);

        if (
          typeof payload === "object" &&
          payload !== null &&
          "error" in payload
        ) {
          const message = String(payload.error);
          setWsError(message);
          return;
        }

        // The backend returns a MonitoringResult for valid observations.
        setResult(payload as MonitoringResult);
        setMode("live");
        setBackendStatus("Connected");
        setWsError("");
      } catch {
        setWsError("Received an invalid message from the WebSocket.");
      }
    };

    socket.onerror = () => {
      setWsStatus("error");
      setWsError(
        "WebSocket connection failed. Check that FastAPI is running.",
      );
      setWsSending(false);
    };

    socket.onclose = () => {
      if (wsRef.current === socket) {
        wsRef.current = null;
        setWsStatus("disconnected");
        setWsSending(false);
      }
    };
  } catch {
    setWsStatus("error");
    setWsError("Could not create the WebSocket connection.");
  }
}

function disconnectWebSocket() {
  const socket = wsRef.current;
  wsRef.current = null;

  if (socket) {
    socket.close();
  }

  setWsStatus("disconnected");
  setWsSending(false);
}

function sendSampleOverWebSocket() {
  const socket = wsRef.current;

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setWsError("Connect the WebSocket before sending a sample.");
    return;
  }

  setWsError("");
  setWsSending(true);

  try {
    socket.send(JSON.stringify(makeObservation()));
  } catch {
    setWsSending(false);
    setWsError("Could not send the sample observation.");
  }
}
  const liveResult = mode === "live" ? result : null;
  const vitals = liveResult
    ? {
        heartRate: liveResult.observation.heart_rate,
        spo2: liveResult.observation.spo2,
        temperature: liveResult.observation.temperature,
        signalQuality: liveResult.signal_quality.score,
      }
    : demoVitals;

  const action = liveResult?.decision.action;
  const severity = liveResult?.anomaly.severity;

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">+</div>
          <div>
            <strong>Pulsewise</strong>
            <span>HEALTH INTELLIGENCE</span>
          </div>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active"><span>◫</span> Overview</div>
        <div className="nav-item"><span>⌁</span> Live monitoring</div>
        <div className="nav-item"><span>◷</span> History &amp; trends</div>
        <div className="nav-item"><span>◎</span> Experiments</div>
        <div className="sidebar-bottom">
          <div className="prototype-badge"><span /> RESEARCH PROTOTYPE</div>
          <p>For research and demonstration only. Not a medical device.</p>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">HEALTH MONITORING AGENT / OVERVIEW</div>
            <h1>Monitoring overview</h1>
            <p className="subtitle">Personalized physiological monitoring and alert assessment.</p>
          </div>
          <div className="mode-switch">
            <button className={mode === "demo" ? "selected" : ""} onClick={() => setMode("demo")}>Demo mode</button>
            <button className={mode === "live" ? "selected" : ""} onClick={() => setMode("live")}>API test mode</button>
          </div>
        </header>

        <div className="notice">
          <span className="notice-icon">i</span>
          <div>
            <strong>{mode === "demo" ? "Demonstration data" : "Backend API test mode"}</strong>
            <p>{mode === "demo"
              ? "These values are illustrative and are not real patient measurements."
              : "Submit a sample observation to display the actual backend response. This is not a live sensor stream."}</p>
          </div>
          <span className="notice-tag">{mode === "demo" ? "SIMULATED" : "API TEST"}</span>
        </div>

        <div className="section-heading">
          <div>
            <h2>Physiological signals</h2>
            <p>{liveResult ? "Values returned by the monitoring API" : "Illustrative sample observation"}</p>
          </div>
          <span className="timestamp">{liveResult ? liveResult.observation.timestamp : "DEMO SESSION · SAMPLE 001"}</span>
        </div>

        <div className="vitals-grid">
          <article className="metric-card">
            <div className="metric-top"><span>Heart rate</span><span className="metric-icon coral">♥</span></div>
            <div className="metric-value">{vitals.heartRate ?? "—"}<small> bpm</small></div>
            <div className="metric-foot"><span className="dot coral-bg" /> {liveResult ? "API response" : "Illustrative value"}</div>
            <div className="sparkline coral-line"><svg viewBox="0 0 240 44" preserveAspectRatio="none"><path d="M0 27 L18 25 L31 30 L46 18 L60 23 L77 13 L92 21 L108 17 L124 27 L141 22 L156 25 L171 11 L185 20 L202 16 L220 22 L240 13" /></svg></div>
          </article>
          <article className="metric-card">
            <div className="metric-top"><span>Oxygen saturation</span><span className="metric-icon blue">◉</span></div>
            <div className="metric-value">{vitals.spo2 ?? "—"}<small>%</small></div>
            <div className="metric-foot"><span className="dot blue-bg" /> {liveResult ? "API response" : "Illustrative value"}</div>
            <div className="sparkline blue-line"><svg viewBox="0 0 240 44" preserveAspectRatio="none"><path d="M0 23 L20 22 L40 25 L60 19 L80 22 L100 18 L120 23 L140 21 L160 24 L180 19 L200 22 L220 18 L240 20" /></svg></div>
          </article>
          <article className="metric-card">
            <div className="metric-top"><span>Temperature</span><span className="metric-icon amber">♨</span></div>
            <div className="metric-value">{vitals.temperature ?? "—"}<small> °C</small></div>
            <div className="metric-foot"><span className="dot amber-bg" /> {liveResult ? "API response" : "Illustrative value"}</div>
            <div className="sparkline amber-line"><svg viewBox="0 0 240 44" preserveAspectRatio="none"><path d="M0 29 L20 27 L40 28 L60 23 L80 25 L100 21 L120 24 L140 20 L160 22 L180 19 L200 22 L220 18 L240 20" /></svg></div>
          </article>
        </div>

        <div className="content-grid">
          <article className="panel">
            <div className="panel-header">
              <div><h2>Monitoring assessment</h2><p>{liveResult ? "Actual MonitoringService result" : "Illustrative warm-up state"}</p></div>
              <span className="pill neutral">{liveResult ? "API RESULT" : "DEMO"}</span>
            </div>
            <div className="assessment-row">
              <div className="assessment-icon green">✓</div>
              <div className="assessment-copy"><strong>Signal quality</strong><span>{liveResult ? `${liveResult.signal_quality.status} · score ${liveResult.signal_quality.score?.toFixed(2) ?? "unavailable"}` : `Illustrative score ${demoVitals.signalQuality.toFixed(2)}`}</span></div>
              <span className={`pill ${liveResult?.signal_quality.status === "trustworthy" || !liveResult ? "good" : "warning"}`}>{liveResult ? liveResult.signal_quality.status.toUpperCase() : "DEMO"}</span>
            </div>
            <div className="assessment-row">
              <div className="assessment-icon amber">◷</div>
              <div className="assessment-copy"><strong>Personal baseline</strong><span>{liveResult?.baseline ? `${liveResult.baseline.metric}: center ${liveResult.baseline.center.toFixed(2)}, scale ${liveResult.baseline.scale.toFixed(2)}, samples ${liveResult.baseline.window_size}` : "Baseline not initialized or not returned"}</span></div>
              <span className="pill warning">{liveResult?.baseline ? "AVAILABLE" : "WARM-UP"}</span>
            </div>
            <div className="assessment-row">
              <div className="assessment-icon slate">?</div>
              <div className="assessment-copy"><strong>Anomaly assessment</strong><span>{liveResult ? liveResult.anomaly.reasons.join("; ") : "No live assessment submitted"}</span></div>
              <span className="pill neutral">{(severity ?? "unknown").toUpperCase()}</span>
            </div>
            <div className="assessment-row last">
              <div className="assessment-icon amber">↻</div>
              <div className="assessment-copy"><strong>Recommended action</strong><span>{liveResult ? liveResult.decision.reasons.join("; ") : "Submit an observation to see the backend decision"}</span></div>
              <span className={`pill ${action === "monitor" ? "good" : "warning"}`}>{(action ?? "recheck").toUpperCase()}</span>
            </div>
          </article>

          <article className="panel system-panel">
            <div className="panel-header"><div><h2>System status</h2><p>Development environment</p></div><span className="status-ring" /></div>
            <div className="system-row"><span>Backend API</span><strong className={backendStatus === "Connected" ? "text-good" : ""}>{backendStatus}</strong></div>
            <div className="system-row"><span>REST endpoint</span><code>/observations</code></div>
            <div className="system-row"><span>Live stream</span><code>/ws/monitor/…</code></div>
            <div className="system-row"><span>Decision engine</span><strong>Deterministic policy</strong></div>
            <button className="primary-button" onClick={checkBackend} disabled={checking}>{checking ? "Checking…" : "Check backend connection"} <span>↗</span></button>
            <button className="primary-button" onClick={() => { setMode("live"); void submitObservation(); }} disabled={submitting}>{submitting ? "Submitting…" : "Submit sample observation"} <span>→</span></button>
            <div className="system-row">
              <span>WebSocket status</span>
              <strong
                className={
                  wsStatus === "connected" ? "text-good" : ""
                }
              >
                {wsStatus}
              </strong>
            </div>

            <div className="system-row">
              <span>WebSocket endpoint</span>
              <code>/ws/monitor/…</code>
            </div>

            <button
              className="primary-button"
              onClick={connectWebSocket}
              disabled={wsStatus === "connecting" || wsStatus === "connected"}
            >
              {wsStatus === "connecting" ? "Connecting…" : "Connect live channel"}
            </button>

            <button
              className="primary-button"
              onClick={sendSampleOverWebSocket}
              disabled={wsStatus !== "connected" || wsSending}
            >
              {wsSending ? "Waiting for response…" : "Send WebSocket sample"}
            </button>

            <button
              className="primary-button"
              onClick={disconnectWebSocket}
              disabled={wsStatus === "disconnected"}
            >
              Disconnect live channel
            </button>

            {wsError && (
              <p role="alert" className="system-note">
                {wsError}
              </p>
            )}
            {apiError && <p role="alert" className="system-note">{apiError}</p>}
            <p className="system-note">Keep FastAPI running on port 8000. This sample does not represent a real patient.</p>
          </article>
        </div>

        {liveResult && (
          <article className="panel" style={{ marginTop: 16 }}>
            <div className="panel-header"><div><h2>Backend response details</h2><p>Raw evidence summaries returned by the API</p></div></div>
            <p><strong>Risk score:</strong> {liveResult.risk.score.toFixed(2)} · <strong>Risk severity:</strong> {liveResult.risk.severity}</p>
            <p><strong>Context:</strong> {liveResult.context.activity ?? "Unavailable"} · Missing fields: {liveResult.context.missing_fields.join(", ") || "none"}</p>
            <p><strong>Risk reasons:</strong> {liveResult.risk.reasons.join("; ") || "none"}</p>
          </article>
        )}

        <footer className="footer">
          <span>HEALTH MONITORING AGENT <span className="footer-separator">/</span> DEVELOPMENT BUILD</span>
          <span>Research prototype · Not for clinical decisions</span>
        </footer>
      </section>
    </main>
  );
}