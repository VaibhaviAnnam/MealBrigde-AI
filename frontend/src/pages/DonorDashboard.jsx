// pages/DonorDashboard.jsx
import { useState, useEffect, useCallback } from "react";
import { getDonations, createDonation, deleteDonation } from "../services/api";
import DonationCard from "../components/DonationCard";

// ── Helpers ────────────────────────────────────────────────────────────────

function toLocalIso(dateStr) {
  // Convert a datetime-local input value to ISO string with timezone offset
  if (!dateStr) return "";
  return new Date(dateStr).toISOString();
}

const EMPTY_FORM = {
  donor_name: "",
  donor_type: "restaurant",
  donor_email: "",
  donor_phone: "",
  food_name: "",
  food_category: "cooked",
  quantity_servings: "",
  description: "",
  allergens: "none",
  storage_conditions: "",
  preparation_time: "",
  collection_deadline: "",
  latitude: "",
  longitude: "",
  address: "",
  donor_confirms_suitability: false,
};

// ── DonationForm ───────────────────────────────────────────────────────────

function DonationForm({ onCreated }) {
  const [form, setForm]       = useState(EMPTY_FORM);
  const [errors, setErrors]   = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const set = (field) => (e) => {
    const val = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [field]: val }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSuccess(false);

    // Client-side quick checks
    const clientErrors = [];
    if (!form.donor_name.trim())         clientErrors.push("Donor name is required.");
    if (!form.donor_email.trim())        clientErrors.push("Donor email is required.");
    if (!form.food_name.trim())          clientErrors.push("Food name is required.");
    if (!form.storage_conditions.trim()) clientErrors.push("Storage conditions are required.");
    if (!form.preparation_time)          clientErrors.push("Preparation time is required.");
    if (!form.collection_deadline)       clientErrors.push("Collection deadline is required.");
    if (!form.latitude || !form.longitude) clientErrors.push("Latitude and longitude are required.");
    if (!form.donor_confirms_suitability)
      clientErrors.push("You must confirm food suitability before posting.");

    if (clientErrors.length) { setErrors(clientErrors); return; }

    setSubmitting(true);
    try {
      const payload = {
        ...form,
        quantity_servings: Number(form.quantity_servings),
        latitude:          Number(form.latitude),
        longitude:         Number(form.longitude),
        preparation_time:  toLocalIso(form.preparation_time),
        collection_deadline: toLocalIso(form.collection_deadline),
      };
      await createDonation(payload);
      setSuccess(true);
      setForm(EMPTY_FORM);
      onCreated();
    } catch (err) {
      const data = err.response?.data;
      if (data?.errors) setErrors(data.errors);
      else setErrors([data?.error || "An unexpected error occurred."]);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 16 }}>
        Post New Donation
      </h2>

      {success && (
        <div className="alert alert-success">
          Donation posted successfully!
        </div>
      )}

      {errors.length > 0 && (
        <div className="alert alert-error">
          <strong>Please fix the following:</strong>
          <ul style={{ marginTop: 6, paddingLeft: 18 }}>
            {errors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <h3 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: 12, color: "var(--muted)", textTransform: "uppercase" }}>
          Donor Information
        </h3>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Donor / Organisation Name <span className="required">*</span></label>
            <input className="form-control" value={form.donor_name} onChange={set("donor_name")} placeholder="e.g. The Grand Hotel" />
          </div>
          <div className="form-group">
            <label className="form-label">Donor Type <span className="required">*</span></label>
            <select className="form-control" value={form.donor_type} onChange={set("donor_type")}>
              {["restaurant","canteen","bakery","event","other"].map(t => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Contact Email <span className="required">*</span></label>
            <input className="form-control" type="email" value={form.donor_email} onChange={set("donor_email")} placeholder="contact@example.com" />
          </div>
          <div className="form-group">
            <label className="form-label">Contact Phone</label>
            <input className="form-control" value={form.donor_phone} onChange={set("donor_phone")} placeholder="+91-98000-00000" />
          </div>
        </div>

        <hr className="divider" />
        <h3 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: 12, color: "var(--muted)", textTransform: "uppercase" }}>
          Food Details
        </h3>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Food Name <span className="required">*</span></label>
            <input className="form-control" value={form.food_name} onChange={set("food_name")} placeholder="e.g. Vegetable Biryani" />
          </div>
          <div className="form-group">
            <label className="form-label">Food Category <span className="required">*</span></label>
            <select className="form-control" value={form.food_category} onChange={set("food_category")}>
              {["cooked","raw","baked","packaged","other"].map(c => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Quantity (servings) <span className="required">*</span></label>
            <input className="form-control" type="number" min="1" value={form.quantity_servings} onChange={set("quantity_servings")} placeholder="e.g. 50" />
          </div>
          <div className="form-group">
            <label className="form-label">Allergens</label>
            <input className="form-control" value={form.allergens} onChange={set("allergens")} placeholder="e.g. nuts, dairy, gluten (or 'none')" />
            <div className="form-hint">List all allergens present. Write "none" if there are none.</div>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea className="form-control" rows={2} value={form.description} onChange={set("description")} placeholder="Any extra details about the food..." />
        </div>

        <hr className="divider" />
        <h3 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: 12, color: "var(--muted)", textTransform: "uppercase" }}>
          Food Safety
        </h3>
        <div className="form-group">
          <label className="form-label">Storage Conditions <span className="required">*</span></label>
          <input className="form-control" value={form.storage_conditions} onChange={set("storage_conditions")} placeholder="e.g. Keep refrigerated below 4°C" />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Preparation Time <span className="required">*</span></label>
            <input className="form-control" type="datetime-local" value={form.preparation_time} onChange={set("preparation_time")} />
          </div>
          <div className="form-group">
            <label className="form-label">Collection Deadline <span className="required">*</span></label>
            <input className="form-control" type="datetime-local" value={form.collection_deadline} onChange={set("collection_deadline")} />
          </div>
        </div>
        <div className="form-group">
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={form.donor_confirms_suitability}
              onChange={set("donor_confirms_suitability")}
              style={{ width: 16, height: 16 }}
            />
            <span>
              <strong>I confirm this food is suitable for donation.</strong> It has been prepared
              safely, stored correctly, and the allergen information above is accurate.
              <span className="required"> *</span>
            </span>
          </label>
        </div>

        <hr className="divider" />
        <h3 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: 12, color: "var(--muted)", textTransform: "uppercase" }}>
          Collection Location
        </h3>
        <div className="form-group">
          <label className="form-label">Address</label>
          <input className="form-control" value={form.address} onChange={set("address")} placeholder="Street address" />
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

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Posting…" : "Post Donation"}
        </button>
      </form>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function DonorDashboard() {
  const [tab,       setTab]       = useState("list");   // "list" | "post"
  const [donations, setDonations] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [filterEmail, setFilterEmail] = useState("");
  const [error,     setError]     = useState(null);

  const loadDonations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = filterEmail ? { donor_email: filterEmail } : {};
      const r = await getDonations(params);
      setDonations(r.data);
    } catch {
      setError("Could not load donations. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [filterEmail]);

  useEffect(() => { loadDonations(); }, [loadDonations]);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this donation?")) return;
    try {
      await deleteDonation(id);
      loadDonations();
    } catch (err) {
      alert(err.response?.data?.error || "Could not delete donation.");
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">Donor Dashboard</h1>
      <p className="page-subtitle">
        Post surplus food donations and track their status.
      </p>

      <div className="tabs">
        <button className={`tab-btn ${tab === "list" ? "active" : ""}`} onClick={() => setTab("list")}>
          All Donations
        </button>
        <button className={`tab-btn ${tab === "post" ? "active" : ""}`} onClick={() => setTab("post")}>
          + Post New
        </button>
      </div>

      {tab === "post" && (
        <DonationForm onCreated={() => { setTab("list"); loadDonations(); }} />
      )}

      {tab === "list" && (
        <>
          <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center" }}>
            <input
              className="form-control"
              style={{ maxWidth: 280 }}
              placeholder="Filter by donor email…"
              value={filterEmail}
              onChange={(e) => setFilterEmail(e.target.value)}
            />
            {filterEmail && (
              <button className="btn btn-outline btn-sm" onClick={() => setFilterEmail("")}>
                Clear
              </button>
            )}
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {loading && <div className="spinner-wrap">Loading donations…</div>}

          {!loading && donations.length === 0 && (
            <div className="alert alert-info">
              No donations found.{" "}
              <button
                className="btn btn-outline btn-sm"
                style={{ marginLeft: 8 }}
                onClick={() => setTab("post")}
              >
                Post one now
              </button>
            </div>
          )}

          <div className="card-grid">
            {donations.map((d) => (
              <DonationCard
                key={d.id}
                donation={d}
                actions={
                  d.status === "available" ? (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(d.id)}
                    >
                      Delete
                    </button>
                  ) : null
                }
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
