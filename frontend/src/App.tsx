/**
 * Milestone 1 UI: one button that proves React -> FastAPI -> PostgreSQL -> React.
 *
 * It models the three states every async call in this app will have:
 * idle/loading, success, and error. The chat UI in Milestone 5 uses exactly
 * this shape - which is the point of building it here first.
 */

import { useState } from 'react';
import { getHealth, type HealthResponse } from './services/healthApi';
import { ApiError } from './services/api';
import './App.css';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function checkHealth() {
    setLoading(true);
    setError(null);
    setHealth(null);

    try {
      const result = await getHealth();
      setHealth(result);
    } catch (err) {
      // ApiError is ours and carries a status; anything else is a real bug.
      setError(err instanceof ApiError ? err.message : 'Something went wrong.');
    } finally {
      // finally, not inside try - the spinner must stop on failure too.
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>AI Assistant</h1>
      <p className="subtitle">Milestone 1 &mdash; project setup</p>

      <button onClick={checkHealth} disabled={loading}>
        {loading ? 'Checking\u2026' : 'Check backend health'}
      </button>

      {health && (
        <div className="card success">
          <div>
            API status: <strong>{health.status}</strong>
          </div>
          <div>
            Database: <strong>{health.database}</strong>
          </div>
          <div>
            Version: <strong>{health.version}</strong>
          </div>
        </div>
      )}

      {error && (
        <div className="card error">
          <strong>Error:</strong> {error}
        </div>
      )}
    </main>
  );
}

export default App;
