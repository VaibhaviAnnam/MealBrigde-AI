"""
routes/matching.py – Rule-based donation matching for NGOs.

Matching algorithm (fully transparent, no ML)
----------------------------------------------
For each available donation, a score in [0, 1] is computed as a
weighted sum of three normalised sub-scores:

    score = w_dist * S_dist + w_urgency * S_urgency + w_qty * S_qty

Where:
    S_dist    = 1 / (1 + distance_km)          proximity (higher = closer)
    S_urgency = 1 / (1 + hours_until_deadline)  urgency   (higher = sooner deadline)
    S_qty     = 1 - |qty - ngo_capacity| / max(qty, ngo_capacity)
                                                quantity fit (higher = closer match)

Weights:  w_dist=0.4  w_urgency=0.4  w_qty=0.2

Allergen filter: donations whose allergen list intersects the
NGO's allergen_restrictions are excluded entirely.

Endpoint
--------
GET /api/matches/<ngo_id>?max_distance_km=<float>&limit=<int>
"""

import math
from flask import Blueprint, jsonify, request
from app_factory import db
from models import Donation, NGO

matching_bp = Blueprint("matching", __name__)

# Score weights (must sum to 1.0)
W_DIST    = 0.4
W_URGENCY = 0.4
W_QTY     = 0.2

DEFAULT_MAX_DISTANCE_KM = 50.0
DEFAULT_LIMIT           = 20


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Return great-circle distance in kilometres between two coordinates."""
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_distance(distance_km):
    """Higher score for closer donations."""
    return 1.0 / (1.0 + distance_km)


def _score_urgency(hours_remaining):
    """Higher score for sooner deadlines (more urgent)."""
    if hours_remaining <= 0:
        return 0.0   # already expired – should have been filtered earlier
    return 1.0 / (1.0 + hours_remaining)


def _score_quantity(donation_qty, ngo_capacity):
    """Higher score when donation quantity closely matches NGO capacity."""
    if donation_qty <= 0 or ngo_capacity <= 0:
        return 0.0
    diff  = abs(donation_qty - ngo_capacity)
    denom = max(donation_qty, ngo_capacity)
    return 1.0 - (diff / denom)


def _allergen_conflict(donation_allergens_str, ngo_restrictions_str):
    """
    Return True if any allergen in the donation overlaps with
    the NGO's stated allergen restrictions.
    Comparison is case-insensitive; 'none' / empty strings are safe.
    """
    if not donation_allergens_str or donation_allergens_str.strip().lower() == "none":
        return False
    if not ngo_restrictions_str:
        return False

    donation_set  = {a.strip().lower() for a in donation_allergens_str.split(",") if a.strip()}
    restriction_set = {a.strip().lower() for a in ngo_restrictions_str.split(",") if a.strip()}
    return bool(donation_set & restriction_set)


# ---------------------------------------------------------------------------
# Matching route
# ---------------------------------------------------------------------------

@matching_bp.route("/matches/<int:ngo_id>", methods=["GET"])
def get_matches(ngo_id):
    ngo = db.session.get(NGO, ngo_id)
    if not ngo:
        return jsonify({"error": "NGO not found."}), 404

    try:
        max_distance_km = float(request.args.get("max_distance_km", DEFAULT_MAX_DISTANCE_KM))
    except ValueError:
        return jsonify({"error": "'max_distance_km' must be a number."}), 400

    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
        if limit <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "'limit' must be a positive integer."}), 400

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # Fetch all currently available donations
    available = Donation.query.filter_by(status="available").all()

    results = []
    for donation in available:
        # Skip expired donations
        deadline = donation.collection_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        hours_remaining = (deadline - now).total_seconds() / 3600.0
        if hours_remaining <= 0:
            continue

        # Skip allergen conflicts
        if _allergen_conflict(donation.allergens, ngo.allergen_restrictions):
            continue

        # Compute distance
        distance_km = haversine_km(
            ngo.latitude, ngo.longitude,
            donation.latitude, donation.longitude,
        )
        if distance_km > max_distance_km:
            continue

        # Compute sub-scores
        s_dist    = _score_distance(distance_km)
        s_urgency = _score_urgency(hours_remaining)
        s_qty     = _score_quantity(donation.quantity_servings, ngo.max_capacity)

        score = W_DIST * s_dist + W_URGENCY * s_urgency + W_QTY * s_qty

        results.append({
            **donation.to_dict(),
            "match": {
                "score":           round(score, 4),
                "distance_km":     round(distance_km, 2),
                "hours_remaining": round(hours_remaining, 1),
                "score_breakdown": {
                    "distance_score":  round(s_dist, 4),
                    "urgency_score":   round(s_urgency, 4),
                    "quantity_score":  round(s_qty, 4),
                },
            },
        })

    # Sort by score descending
    results.sort(key=lambda x: x["match"]["score"], reverse=True)

    return jsonify({
        "ngo_id":   ngo_id,
        "ngo_name": ngo.name,
        "matches":  results[:limit],
        "total_matches_found": len(results),
    }), 200
