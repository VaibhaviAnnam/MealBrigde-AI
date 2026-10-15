"""
routes/donations.py – CRUD endpoints for Donation objects.

Endpoints
---------
POST   /api/donations            – create a new donation
GET    /api/donations            – list donations (optional ?status= filter)
GET    /api/donations/<id>       – get one donation
PATCH  /api/donations/<id>       – update status
DELETE /api/donations/<id>       – cancel / remove a donation
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from app_factory import db
from models import Donation

donations_bp = Blueprint("donations", __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_DONOR_TYPES   = {"restaurant", "canteen", "bakery", "event", "other"}
VALID_FOOD_CATS     = {"cooked", "raw", "baked", "packaged", "other"}
VALID_STATUSES      = {"available", "claimed", "collected", "completed", "expired", "cancelled"}


def _parse_dt(value, field_name):
    """Parse an ISO-8601 datetime string; raise ValueError with a clear message on failure."""
    if not value:
        raise ValueError(f"'{field_name}' is required.")
    try:
        dt = datetime.fromisoformat(str(value))
        # Make timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        raise ValueError(f"'{field_name}' must be a valid ISO-8601 datetime string (e.g. 2024-06-01T14:00:00).")


def _validate_donation_payload(data):
    """
    Validate required fields in a donation POST/PATCH body.
    Returns a list of error strings; empty list = valid.
    """
    errors = []

    required_strings = [
        ("donor_name",        "Donor name"),
        ("donor_email",       "Donor email"),
        ("food_name",         "Food name"),
        ("storage_conditions","Storage conditions"),
    ]
    for field, label in required_strings:
        if not data.get(field, "").strip():
            errors.append(f"{label} is required.")

    # Enum checks
    donor_type = data.get("donor_type", "")
    if donor_type not in VALID_DONOR_TYPES:
        errors.append(f"'donor_type' must be one of: {', '.join(sorted(VALID_DONOR_TYPES))}.")

    food_category = data.get("food_category", "")
    if food_category not in VALID_FOOD_CATS:
        errors.append(f"'food_category' must be one of: {', '.join(sorted(VALID_FOOD_CATS))}.")

    # Quantity
    try:
        qty = int(data.get("quantity_servings", 0))
        if qty <= 0:
            errors.append("'quantity_servings' must be a positive integer.")
    except (TypeError, ValueError):
        errors.append("'quantity_servings' must be a positive integer.")

    # Coordinates
    for coord in ("latitude", "longitude"):
        try:
            float(data[coord])
        except (KeyError, TypeError, ValueError):
            errors.append(f"'{coord}' must be a valid number.")

    # Datetime fields (only check format here; logical checks below)
    prep_dt = coll_dt = None
    try:
        prep_dt = _parse_dt(data.get("preparation_time"), "preparation_time")
    except ValueError as e:
        errors.append(str(e))

    try:
        coll_dt = _parse_dt(data.get("collection_deadline"), "collection_deadline")
    except ValueError as e:
        errors.append(str(e))

    if prep_dt and coll_dt and coll_dt <= prep_dt:
        errors.append("'collection_deadline' must be after 'preparation_time'.")

    # Food-safety suitability confirmation
    confirms = data.get("donor_confirms_suitability")
    if not isinstance(confirms, bool):
        errors.append("'donor_confirms_suitability' must be a boolean (true/false).")

    return errors, prep_dt, coll_dt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@donations_bp.route("/donations", methods=["POST"])
def create_donation():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON."}), 400

    errors, prep_dt, coll_dt = _validate_donation_payload(data)
    if errors:
        return jsonify({"errors": errors}), 422

    donation = Donation(
        donor_name               = data["donor_name"].strip(),
        donor_type               = data["donor_type"],
        donor_email              = data["donor_email"].strip(),
        donor_phone              = data.get("donor_phone", "").strip(),
        food_name                = data["food_name"].strip(),
        food_category            = data["food_category"],
        quantity_servings        = int(data["quantity_servings"]),
        description              = data.get("description", "").strip(),
        allergens                = data.get("allergens", "none").strip(),
        storage_conditions       = data["storage_conditions"].strip(),
        preparation_time         = prep_dt,
        donor_confirms_suitability = data["donor_confirms_suitability"],
        latitude                 = float(data["latitude"]),
        longitude                = float(data["longitude"]),
        address                  = data.get("address", "").strip(),
        collection_deadline      = coll_dt,
        status                   = "available",
    )
    db.session.add(donation)
    db.session.commit()
    return jsonify(donation.to_dict()), 201


@donations_bp.route("/donations", methods=["GET"])
def list_donations():
    status_filter = request.args.get("status")
    donor_email   = request.args.get("donor_email")

    query = Donation.query
    if status_filter:
        if status_filter not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status filter. Valid values: {', '.join(sorted(VALID_STATUSES))}"}), 400
        query = query.filter_by(status=status_filter)
    if donor_email:
        query = query.filter_by(donor_email=donor_email.strip())

    donations = query.order_by(Donation.collection_deadline.asc()).all()
    return jsonify([d.to_dict() for d in donations]), 200


@donations_bp.route("/donations/<int:donation_id>", methods=["GET"])
def get_donation(donation_id):
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404
    return jsonify(donation.to_dict()), 200


@donations_bp.route("/donations/<int:donation_id>", methods=["PATCH"])
def update_donation_status(donation_id):
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status:
        if new_status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status. Valid values: {', '.join(sorted(VALID_STATUSES))}"}), 422
        donation.status = new_status

    db.session.commit()
    return jsonify(donation.to_dict()), 200


@donations_bp.route("/donations/<int:donation_id>", methods=["DELETE"])
def delete_donation(donation_id):
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    if donation.status not in {"available", "cancelled"}:
        return jsonify({"error": "Only 'available' or 'cancelled' donations can be deleted."}), 409

    db.session.delete(donation)
    db.session.commit()
    return jsonify({"message": "Donation deleted."}), 200
