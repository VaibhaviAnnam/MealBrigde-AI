"""
routes/impact.py – Aggregated impact statistics endpoint.

Endpoint
--------
GET /api/impact   – returns donation totals, estimated meals, per-donor breakdown
"""

from flask import Blueprint, jsonify
from sqlalchemy import func
from app_factory import db
from models import Donation, Claim

impact_bp = Blueprint("impact", __name__)

# Rough conversion: 1 serving ≈ 0.4 kg of food saved from waste
KG_PER_SERVING = 0.4


@impact_bp.route("/impact", methods=["GET"])
def get_impact():
    # --- Overall donation counts ---
    total_posted    = Donation.query.count()
    total_available = Donation.query.filter_by(status="available").count()
    total_claimed   = Donation.query.filter_by(status="claimed").count()
    total_completed = Donation.query.filter_by(status="completed").count()
    total_cancelled = Donation.query.filter(
        Donation.status.in_(["cancelled", "expired"])
    ).count()

    # --- Servings ---
    completed_servings_row = db.session.query(
        func.sum(Donation.quantity_servings)
    ).filter_by(status="completed").first()
    completed_servings = completed_servings_row[0] or 0

    all_servings_row = db.session.query(
        func.sum(Donation.quantity_servings)
    ).first()
    all_servings = all_servings_row[0] or 0

    # --- Food waste reduction ---
    kg_saved = round(completed_servings * KG_PER_SERVING, 1)

    # --- Claims stats ---
    total_claims = Claim.query.count()

    # --- Per donor-type breakdown ---
    donor_type_rows = db.session.query(
        Donation.donor_type,
        func.count(Donation.id).label("count"),
        func.sum(Donation.quantity_servings).label("servings"),
    ).group_by(Donation.donor_type).all()

    per_donor_type = [
        {
            "donor_type": row.donor_type,
            "donations_posted": row.count,
            "total_servings": row.servings or 0,
        }
        for row in donor_type_rows
    ]

    # --- Recent completions (last 5) ---
    recent_completed = (
        Donation.query.filter_by(status="completed")
        .order_by(Donation.collection_deadline.desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "summary": {
            "total_donations_posted":    total_posted,
            "total_donations_available": total_available,
            "total_donations_claimed":   total_claimed,
            "total_donations_completed": total_completed,
            "total_donations_cancelled": total_cancelled,
            "total_claims":              total_claims,
            "estimated_meals_distributed": completed_servings,
            "total_servings_in_system":    all_servings,
            "estimated_kg_food_saved":     kg_saved,
        },
        "per_donor_type": per_donor_type,
        "recent_completions": [d.to_dict() for d in recent_completed],
    }), 200
