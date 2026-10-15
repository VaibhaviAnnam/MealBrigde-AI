// components/DonationCard.jsx
import StatusBadge from "./StatusBadge";
import FoodSafetyWarning from "./FoodSafetyWarning";

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function DonationCard({ donation, actions }) {
  const {
    food_name, food_category, donor_name, donor_type,
    quantity_servings, allergens, storage_conditions,
    donor_confirms_suitability, preparation_time,
    collection_deadline, address, status, description,
  } = donation;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">{food_name}</div>
          <div className="card-meta">
            {donor_name} &middot; {donor_type}
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
        <span className="badge badge-available" style={{ background: "#f3f4f6", color: "#374151" }}>
          {food_category}
        </span>
        <span style={{ marginLeft: 8, color: "var(--text)", fontWeight: 600 }}>
          {quantity_servings} servings
        </span>
      </div>

      {description && (
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: 8 }}>
          {description}
        </p>
      )}

      <div className="card-meta">
        <div>Prepared: {formatDate(preparation_time)}</div>
        <div>Deadline: {formatDate(collection_deadline)}</div>
        {address && <div>Location: {address}</div>}
      </div>

      <FoodSafetyWarning
        confirmed={donor_confirms_suitability}
        allergens={allergens}
        storageConditions={storage_conditions}
      />

      {actions && <div style={{ marginTop: 12 }}>{actions}</div>}
    </div>
  );
}
