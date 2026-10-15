// pages/ImpactDashboard.jsx
import { useState, useEffect } from "react";
import { getImpact } from "../services/api";

function StatCard({ number, label }) {
  return (
    <div className="stat-card">
      <div className="stat-number">{number}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function ImpactDashboard() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    getImpact()
      .then((r) => setData(r.data))
      .catch(() => setError("Could not load impact data. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner-wrap">Loading impact data…</div>;
  if (error)   return <div className="page-container"><div className="alert alert-error">{error}</div></div>;

  const { summary, per_donor_type, recent_completions } = data;

  return (
    <div className="page-container">
      <h1 className="page-title">Impact Dashboard</h1>
      <p className="page-subtitle">
        Platform-wide statistics on food rescued and communities served.
      </p>

      {/* ── Key Numbers ─────────────────────────────────────────── */}
      <div className="stats-grid">
        <StatCard number={summary.total_donations_posted}    label="Donations Posted" />
        <StatCard number={summary.total_donations_available} label="Available Now" />
        <StatCard number={summary.total_donations_claimed}   label="Claimed" />
        <StatCard number={summary.total_donations_completed} label="Completed" />
        <StatCard number={summary.total_donations_cancelled} label="Cancelled / Expired" />
        <StatCard number={summary.total_claims}              label="Total Claims" />
      </div>

      {/* ── Food impact ──────────────────────────────────────────── */}
      <div className="card-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", marginBottom: 32 }}>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2.8rem", fontWeight: 800, color: "var(--success)" }}>
            {summary.estimated_meals_distributed.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.9rem", color: "var(--muted)", marginTop: 4 }}>
            Estimated meals distributed
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 4 }}>
            (from completed donations)
          </div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2.8rem", fontWeight: 800, color: "var(--accent)" }}>
            {summary.estimated_kg_food_saved.toLocaleString()} kg
          </div>
          <div style={{ fontSize: "0.9rem", color: "var(--muted)", marginTop: 4 }}>
            Estimated food waste prevented
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 4 }}>
            (approx. 0.4 kg per serving)
          </div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2.8rem", fontWeight: 800, color: "#7c3aed" }}>
            {summary.total_servings_in_system.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.9rem", color: "var(--muted)", marginTop: 4 }}>
            Total servings in system
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 4 }}>
            (all statuses)
          </div>
        </div>
      </div>

      {/* ── Per donor type ───────────────────────────────────────── */}
      {per_donor_type.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 16 }}>
            Breakdown by Donor Type
          </h2>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>Donor Type</th>
                  <th style={{ padding: "8px 12px" }}>Donations Posted</th>
                  <th style={{ padding: "8px 12px" }}>Total Servings</th>
                  <th style={{ padding: "8px 12px" }}>Est. kg Saved</th>
                </tr>
              </thead>
              <tbody>
                {per_donor_type.map((row) => (
                  <tr key={row.donor_type} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "8px 12px", textTransform: "capitalize", fontWeight: 600 }}>
                      {row.donor_type}
                    </td>
                    <td style={{ padding: "8px 12px" }}>{row.donations_posted}</td>
                    <td style={{ padding: "8px 12px" }}>{row.total_servings}</td>
                    <td style={{ padding: "8px 12px" }}>
                      {(row.total_servings * 0.4).toFixed(1)} kg
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Recent completions ───────────────────────────────────── */}
      {recent_completions.length > 0 && (
        <div>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 16 }}>
            Recent Completed Donations
          </h2>
          <div className="card-grid">
            {recent_completions.map((d) => (
              <div key={d.id} className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">{d.food_name}</div>
                    <div className="card-meta">{d.donor_name} &middot; {d.donor_type}</div>
                  </div>
                  <span className="badge badge-completed">completed</span>
                </div>
                <div style={{ fontSize: "0.85rem", marginTop: 4 }}>
                  <strong>{d.quantity_servings}</strong> servings &middot; ≈{(d.quantity_servings * 0.4).toFixed(1)} kg saved
                </div>
                {d.address && (
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginTop: 4 }}>
                    {d.address}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Methodology note ─────────────────────────────────────── */}
      <div className="alert alert-info" style={{ marginTop: 32 }}>
        <strong>Methodology:</strong> Meal counts equal the sum of servings from completed donations.
        Food waste estimates use a fixed factor of 0.4 kg per serving, which is an approximation.
        These figures do not account for post-collection spoilage or distribution losses.
      </div>
    </div>
  );
}
