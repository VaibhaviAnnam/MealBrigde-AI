// components/FoodSafetyWarning.jsx
export default function FoodSafetyWarning({ confirmed, allergens, storageConditions }) {
  return (
    <div className={confirmed ? "safety-confirmed" : "safety-warning"}>
      {confirmed ? (
        <strong>Food safety confirmed by donor.</strong>
      ) : (
        <strong>
          Food safety NOT yet confirmed by donor — verify suitability before collection.
        </strong>
      )}
      {allergens && allergens !== "none" && (
        <div style={{ marginTop: 4 }}>
          <strong>Allergens:</strong> {allergens}
        </div>
      )}
      {storageConditions && (
        <div style={{ marginTop: 4 }}>
          <strong>Storage:</strong> {storageConditions}
        </div>
      )}
    </div>
  );
}
