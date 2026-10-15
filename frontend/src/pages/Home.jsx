// pages/Home.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getImpact } from "../services/api";

export default function Home() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    getImpact()
      .then((r) => setSummary(r.data.summary))
      .catch(() => {}); // fail silently on home page
  }, []);

  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <div className="hero">
        <h1>Bridge Surplus Food to Those Who Need It</h1>
        <p>
          MealBridge AI connects restaurants, canteens, bakeries and events
          that have surplus food with NGOs ready to collect and distribute it —
          reducing food waste and feeding communities.
        </p>
        <div className="hero-actions">
          <button className="btn-hero-primary" onClick={() => navigate("/donor")}>
            Post a Donation
          </button>
          <button className="btn-hero-secondary" onClick={() => navigate("/ngo")}>
            Find Food for Your NGO
          </button>
        </div>
      </div>

      {/* ── Live stats teaser ─────────────────────────────────────── */}
      {summary && (
        <div className="section">
          <div style={{ maxWidth: 1100, margin: "0 auto" }}>
            <h2 className="section-title">Live Platform Activity</h2>
            <p className="section-sub">Updated in real time from the database</p>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">{summary.total_donations_posted}</div>
                <div className="stat-label">Donations Posted</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{summary.total_donations_available}</div>
                <div className="stat-label">Available Now</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{summary.total_donations_completed}</div>
                <div className="stat-label">Completed</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{summary.estimated_meals_distributed}</div>
                <div className="stat-label">Meals Distributed</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{summary.estimated_kg_food_saved} kg</div>
                <div className="stat-label">Food Waste Prevented</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── How it works ─────────────────────────────────────────── */}
      <div className="section section-alt">
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <h2 className="section-title">How It Works</h2>
          <p className="section-sub">Three steps from surplus food to full plates</p>
          <div className="card-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
            {[
              {
                step: "1",
                title: "Donor posts surplus",
                body: "Restaurants, canteens, bakeries and event organisers post details of surplus food — quantity, allergens, storage conditions and collection deadline.",
              },
              {
                step: "2",
                title: "Smart matching",
                body: "Our rule-based engine scores each available donation for nearby NGOs based on distance, urgency and quantity fit — with full allergen filtering.",
              },
              {
                step: "3",
                title: "NGO collects & distributes",
                body: "NGOs browse matched donations, accept the ones they can handle, and update the status once food is collected and distributed.",
              },
            ].map(({ step, title, body }) => (
              <div className="card" key={step}>
                <div style={{
                  width: 36, height: 36, background: "var(--accent)",
                  color: "#fff", borderRadius: "50%", display: "flex",
                  alignItems: "center", justifyContent: "center",
                  fontWeight: 700, fontSize: "1rem", marginBottom: 12,
                }}>
                  {step}
                </div>
                <div className="card-title" style={{ marginBottom: 6 }}>{title}</div>
                <p style={{ fontSize: "0.875rem", color: "var(--muted)" }}>{body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Food safety note ──────────────────────────────────────── */}
      <div className="section">
        <div style={{ maxWidth: 760, margin: "0 auto" }}>
          <h2 className="section-title">Food Safety First</h2>
          <p className="section-sub">We do not automatically certify food as safe</p>
          <div className="safety-warning" style={{ fontSize: "0.9rem", lineHeight: 1.7 }}>
            <strong>Important:</strong> MealBridge AI requires donors to explicitly confirm
            food suitability before a donation is listed as safe to collect. All donations
            display allergen information and storage requirements. NGOs must review this
            information carefully and perform their own safety checks before distribution.
            Food marked "unconfirmed" must not be collected until the donor confirms suitability.
          </div>
        </div>
      </div>
    </>
  );
}
