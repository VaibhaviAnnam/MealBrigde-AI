// pages/NgoDashboard.jsx
import { useState, useEffect, useCallback } from "react";
import { getNGOs, createNGO, getMatches, createClaim, getClaims, updateClaimStatus } from "../services/api";
import DonationCard from "../components/DonationCard";
import StatusBadge from "../components/StatusBadge";

// ── ScoreBar ───────────────────────────────────────────────────────────────

function ScoreBar({ score }) {
  return (
    <div className="score-bar-wrap">
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--muted)", marginBottom: 2 }}>
        <span>Match score</span>
        <span style={{ fontWeight: 700, color: "var(--accent)" }}>{(score * 100).toFixed(1)}%</span>
      </div>
      <div className="score-bar-bg">
        <div className="score-bar-fill" style={{ width: `${Math.min(score * 100, 100)}%` }} />
      </div>
    </div>
  );
}

// ── NGO selector / register ────────────────────────────────────────────────

function NGOSelector({ ngos, selectedId, onSelect, onRegister }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", contact_email: "", phone: "",
    latitude: "", longitude: "", max_capacity: 100,
    allergen_restrictions: "",
  });
  const [errors, setErrors] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const set = (f) => (e) => setForm((s) => ({ ...s, [f]: e.target.value }));

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrors([]);
    const errs = [];
    if (!form.name.trim())          errs.push("Name is required.");
    if (!form.contact_email.trim()) errs.push("Contact email is required.");
    if (!form.latitude || !form.longitude) errs.push("Latitude and longitude are required.");
    if (errs.length) { setErrors(errs); return; }

    setSubmitting(true);
    try {
      const r = await createNGO({
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        max_capacity: Number(form.max_capacity),
      });
      onRegister(r.data);
      setShowForm(false);
      setForm({ name: "", contact_email: "", phone: "", latitude: "", longitude: "", max_capacity: 100, allergen_restrictions: "" });
    } catch (err) {
      const data = err.response?.data;
      if (data?.errors) setErrors(data.errors);
      else setErrors([data?.error || "Registration failed."]);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Select Your NGO</h2>
        <button className="btn btn-outline btn-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ Register NGO"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleRegister} noValidate style={{ marginBottom: 16, paddingBottom: 16, borderBottom: "1px solid var(--border)" }}>
          {errors.length > 0 && (
            <div className="alert alert-error">
              {errors.map((e, i) => <div key={i}>{e}</div>)}
            </div>
          )}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">NGO Name <span className="required">*</span></label>
              <input className="form-control" value={form.name} onChange={set("name")} placeholder="Organisation name" />
            </div>
            <div className="form-group">
              <label className="form-label">Contact Email <span className="required">*</span></label>
              <input className="form-control" type="email" value={form.contact_email} onChange={set("contact_email")} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Latitude <span className="required">*</span></label>
              <input className="form-control" type="number" step="any" value={form.latitude} onChange={set("latitude")} placeholder="e.g. 12.9716" />
            </div>
            <div className="form-group">
              <label className="form-label">Longitude <span className="required">*</span></label>
              <input className="form-control" type="number" step="any" value={form.longitude} onChange={set("longitude")} placeholder="e.g. 77.5946" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Capacity (servings)</label>
              <input className="form-control" type="number" value={form.max_capacity} onChange={set("max_capacity")} />
            </div>
            <div className="form-group">
              <label className="form-label">Allergen Restrictions</label>
              <input className="form-control" value={form.allergen_restrictions} onChange={set("allergen_restrictions")} placeholder="e.g. nuts, gluten" />
              <div className="form-hint">Allergens your organisation cannot accept.</div>
            </div>
          </div>
          <button type="submit" className="btn btn-primary btn-sm" disabled={submitting}>
            {submitting ? "Registering…" : "Register"}
          </button>
        </form>
      )}

      {ngos.length === 0 ? (
        <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>
          No NGOs registered yet. Register one above to get started.
        </p>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {ngos.map((n) => (
            <button
              key={n.id}
              className={`btn ${selectedId === n.id ? "btn-primary" : "btn-outline"}`}
              onClick={() => onSelect(n.id)}
            >
              {n.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function NgoDashboard() {
  const [ngos,       setNgos]       = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tab,        setTab]        = useState("matches");  // "matches" | "claims"
  const [matches,    setMatches]    = useState([]);
  const [claims,     setClaims]     = useState([]);
  const [loading,    setLoading]    = useState(false);
  const [claimingId, setClaimingId] = useState(null);
  const [error,      setError]      = useState(null);
  const [maxDist,    setMaxDist]    = useState(50);

  // Load NGOs on mount
  useEffect(() => {
    getNGOs()
      .then((r) => {
        setNgos(r.data);
        if (r.data.length > 0) setSelectedId(r.data[0].id);
      })
      .catch(() => setError("Could not load NGOs. Is the backend running?"));
  }, []);

  // Load matches when NGO or distance changes
  const loadMatches = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true); setError(null);
    try {
      const r = await getMatches(selectedId, { max_distance_km: maxDist });
      setMatches(r.data.matches);
    } catch {
      setError("Could not load matches.");
    } finally {
      setLoading(false);
    }
  }, [selectedId, maxDist]);

  // Load claims for selected NGO
  const loadClaims = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true); setError(null);
    try {
      const r = await getClaims({ ngo_id: selectedId });
      setClaims(r.data);
    } catch {
      setError("Could not load claims.");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => { if (tab === "matches") loadMatches(); }, [tab, loadMatches]);
  useEffect(() => { if (tab === "claims")  loadClaims();  }, [tab, loadClaims]);

  const handleClaim = async (donationId) => {
    setClaimingId(donationId);
    try {
      await createClaim({ ngo_id: selectedId, donation_id: donationId });
      loadMatches();
    } catch (err) {
      alert(err.response?.data?.error || "Could not claim donation.");
    } finally {
      setClaimingId(null);
    }
  };

  const handleUpdateClaim = async (claimId, status) => {
    try {
      await updateClaimStatus(claimId, status);
      loadClaims();
    } catch (err) {
      alert(err.response?.data?.error || "Could not update claim.");
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">NGO Dashboard</h1>
      <p className="page-subtitle">
        Browse matched donations and track your claims.
      </p>

      <NGOSelector
        ngos={ngos}
        selectedId={selectedId}
        onSelect={(id) => { setSelectedId(id); setTab("matches"); }}
        onRegister={(ngo) => {
          setNgos((prev) => [...prev, ngo]);
          setSelectedId(ngo.id);
        }}
      />

      {selectedId && (
        <>
          <div className="tabs">
            <button className={`tab-btn ${tab === "matches" ? "active" : ""}`} onClick={() => setTab("matches")}>
              Matched Donations
            </button>
            <button className={`tab-btn ${tab === "claims" ? "active" : ""}`} onClick={() => setTab("claims")}>
              My Claims
            </button>
          </div>

          {tab === "matches" && (
            <>
              <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
                <label style={{ fontSize: "0.875rem", fontWeight: 600 }}>
                  Max distance (km):
                  <input
                    type="number"
                    min="1" max="500"
                    value={maxDist}
                    onChange={(e) => setMaxDist(Number(e.target.value))}
                    className="form-control"
                    style={{ width: 80, display: "inline-block", marginLeft: 8 }}
                  />
                </label>
                <button className="btn btn-outline btn-sm" onClick={loadMatches}>Refresh</button>
              </div>

              {error  && <div className="alert alert-error">{error}</div>}
              {loading && <div className="spinner-wrap">Finding matches…</div>}

              {!loading && matches.length === 0 && (
                <div className="alert alert-info">
                  No available donations match your NGO's location and requirements within {maxDist} km.
                </div>
              )}

              <div className="card-grid">
                {matches.map((m) => (
                  <DonationCard
                    key={m.id}
                    donation={m}
                    actions={
                      <div>
                        <ScoreBar score={m.match.score} />
                        <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 4 }}>
                          {m.match.distance_km} km away &middot; {m.match.hours_remaining}h remaining
                        </div>
                        <div style={{ marginTop: 8 }}>
                          <button
                            className="btn btn-success btn-sm"
                            disabled={claimingId === m.id}
                            onClick={() => handleClaim(m.id)}
                          >
                            {claimingId === m.id ? "Claiming…" : "Accept Donation"}
                          </button>
                        </div>
                      </div>
                    }
                  />
                ))}
              </div>
            </>
          )}

          {tab === "claims" && (
            <>
              <button className="btn btn-outline btn-sm" style={{ marginBottom: 16 }} onClick={loadClaims}>
                Refresh
              </button>

              {error  && <div className="alert alert-error">{error}</div>}
              {loading && <div className="spinner-wrap">Loading claims…</div>}

              {!loading && claims.length === 0 && (
                <div className="alert alert-info">No claims yet for this NGO.</div>
              )}

              <div className="card-grid">
                {claims.map((c) => (
                  <div key={c.id} className="card">
                    <div className="card-header">
                      <div>
                        <div className="card-title">Claim #{c.id}</div>
                        <div className="card-meta">Donation #{c.donation_id}</div>
                      </div>
                      <StatusBadge status={c.status} />
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      Claimed: {new Date(c.claimed_at).toLocaleString()}
                    </div>
                    {c.notes && <div style={{ marginTop: 6, fontSize: "0.85rem" }}>{c.notes}</div>}
                    <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {c.status === "pending" && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleUpdateClaim(c.id, "confirmed")}
                        >
                          Confirm
                        </button>
                      )}
                      {(c.status === "confirmed") && (
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleUpdateClaim(c.id, "collected")}
                        >
                          Mark Collected
                        </button>
                      )}
                      {(c.status === "pending" || c.status === "confirmed") && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleUpdateClaim(c.id, "cancelled")}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
