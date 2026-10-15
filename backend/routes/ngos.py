"""
routes/ngos.py – NGO registration and claim management endpoints.

Endpoints
---------
POST  /api/ngos                        – register an NGO
GET   /api/ngos                        – list all NGOs
GET   /api/ngos/<id>                   – get one NGO

POST  /api/claims                      – NGO accepts a donation
GET   /api/claims?ngo_id=&donation_id= – query claims
PATCH /api/claims/<id>/status          – update claim status
"""

from flask import Blueprint, jsonify, request
from app_factory import db
from models import NGO, Donation, Claim

ngos_bp = Blueprint("ngos", __name__)

VALID_CLAIM_STATUSES = {"pending", "confirmed", "collected", "cancelled"}


# ---------------------------------------------------------------------------
# NGO CRUD
# ---------------------------------------------------------------------------

@ngos_bp.route("/ngos", methods=["POST"])
def create_ngo():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    errors = []
    for field, label in [("name", "Name"), ("contact_email", "Contact email")]:
        if not data.get(field, "").strip():
            errors.append(f"{label} is required.")

    try:
        lat = float(data["latitude"])
        lon = float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        errors.append("Valid 'latitude' and 'longitude' are required.")
        lat = lon = 0.0

    if errors:
        return jsonify({"errors": errors}), 422

    # Check duplicate email
    existing = NGO.query.filter_by(contact_email=data["contact_email"].strip()).first()
    if existing:
        return jsonify({"error": "An NGO with this email already exists."}), 409

    ngo = NGO(
        name                  = data["name"].strip(),
        contact_email         = data["contact_email"].strip(),
        phone                 = data.get("phone", "").strip(),
        latitude              = lat,
        longitude             = lon,
        max_capacity          = int(data.get("max_capacity", 100)),
        allergen_restrictions = data.get("allergen_restrictions", "").strip(),
    )
    db.session.add(ngo)
    db.session.commit()
    return jsonify(ngo.to_dict()), 201


@ngos_bp.route("/ngos", methods=["GET"])
def list_ngos():
    ngos = NGO.query.order_by(NGO.name.asc()).all()
    return jsonify([n.to_dict() for n in ngos]), 200


@ngos_bp.route("/ngos/<int:ngo_id>", methods=["GET"])
def get_ngo(ngo_id):
    ngo = db.session.get(NGO, ngo_id)
    if not ngo:
        return jsonify({"error": "NGO not found."}), 404
    return jsonify(ngo.to_dict()), 200


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------

@ngos_bp.route("/claims", methods=["POST"])
def create_claim():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    ngo_id      = data.get("ngo_id")
    donation_id = data.get("donation_id")

    if not ngo_id or not donation_id:
        return jsonify({"error": "'ngo_id' and 'donation_id' are required."}), 422

    ngo      = db.session.get(NGO, ngo_id)
    donation = db.session.get(Donation, donation_id)

    if not ngo:
        return jsonify({"error": "NGO not found."}), 404
    if not donation:
        return jsonify({"error": "Donation not found."}), 404
    if donation.status != "available":
        return jsonify({"error": f"Donation is not available (current status: {donation.status})."}), 409

    # Prevent duplicate active claims from same NGO
    existing = Claim.query.filter_by(
        ngo_id=ngo_id, donation_id=donation_id
    ).filter(Claim.status != "cancelled").first()
    if existing:
        return jsonify({"error": "Your organisation has already claimed this donation."}), 409

    claim = Claim(
        donation_id = donation_id,
        ngo_id      = ngo_id,
        status      = "pending",
        notes       = data.get("notes", "").strip(),
    )
    donation.status = "claimed"

    db.session.add(claim)
    db.session.commit()
    return jsonify(claim.to_dict()), 201


@ngos_bp.route("/claims", methods=["GET"])
def list_claims():
    ngo_id      = request.args.get("ngo_id", type=int)
    donation_id = request.args.get("donation_id", type=int)

    query = Claim.query
    if ngo_id:
        query = query.filter_by(ngo_id=ngo_id)
    if donation_id:
        query = query.filter_by(donation_id=donation_id)

    claims = query.order_by(Claim.claimed_at.desc()).all()
    return jsonify([c.to_dict() for c in claims]), 200


@ngos_bp.route("/claims/<int:claim_id>/status", methods=["PATCH"])
def update_claim_status(claim_id):
    claim = db.session.get(Claim, claim_id)
    if not claim:
        return jsonify({"error": "Claim not found."}), 404

    data       = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if not new_status or new_status not in VALID_CLAIM_STATUSES:
        return jsonify({"error": f"'status' must be one of: {', '.join(sorted(VALID_CLAIM_STATUSES))}."}), 422

    old_status = claim.status
    claim.status = new_status

    # Keep donation status in sync
    donation = claim.donation
    if new_status == "collected":
        donation.status = "completed"
    elif new_status == "cancelled" and old_status != "cancelled":
        # Only revert donation if no other active claim exists
        other_active = Claim.query.filter(
            Claim.donation_id == donation.id,
            Claim.id          != claim_id,
            Claim.status      != "cancelled",
        ).first()
        if not other_active:
            donation.status = "available"

    db.session.commit()
    return jsonify(claim.to_dict()), 200
