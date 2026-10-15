"""
SQLAlchemy models for MealBridge AI.

Tables
------
NGO        – registered NGO organisations
Donation   – surplus food posted by a donor
Claim      – an NGO's acceptance of a donation
"""

from datetime import datetime, timezone
from app_factory import db


class NGO(db.Model):
    __tablename__ = "ngos"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    # Geographic coordinates for distance-based matching
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    # Max quantity the NGO can handle per collection (servings)
    max_capacity = db.Column(db.Integer, nullable=False, default=100)
    # Comma-separated allergens the NGO cannot accept (e.g. "nuts,gluten")
    allergen_restrictions = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    claims = db.relationship("Claim", back_populates="ngo", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_email": self.contact_email,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "max_capacity": self.max_capacity,
            "allergen_restrictions": self.allergen_restrictions,
            "created_at": self.created_at.isoformat(),
        }


class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)

    # Donor information
    donor_name = db.Column(db.String(120), nullable=False)
    donor_type = db.Column(db.String(50), nullable=False)   # restaurant | canteen | bakery | event
    donor_email = db.Column(db.String(120), nullable=False)
    donor_phone = db.Column(db.String(20))

    # Food information
    food_name = db.Column(db.String(120), nullable=False)
    food_category = db.Column(db.String(50), nullable=False)  # cooked | raw | baked | packaged
    quantity_servings = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, default="")

    # Food safety fields
    allergens = db.Column(db.String(255), default="none")       # e.g. "nuts, dairy"
    storage_conditions = db.Column(db.String(255), nullable=False)  # e.g. "Keep refrigerated below 4°C"
    preparation_time = db.Column(db.DateTime, nullable=False)   # when food was prepared
    # Donor must explicitly confirm suitability; False = safety not confirmed
    donor_confirms_suitability = db.Column(db.Boolean, nullable=False, default=False)

    # Location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), default="")

    # Timing
    collection_deadline = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Status lifecycle: available → claimed → collected → completed | expired | cancelled
    status = db.Column(db.String(20), nullable=False, default="available")

    claims = db.relationship("Claim", back_populates="donation", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "donor_name": self.donor_name,
            "donor_type": self.donor_type,
            "donor_email": self.donor_email,
            "donor_phone": self.donor_phone,
            "food_name": self.food_name,
            "food_category": self.food_category,
            "quantity_servings": self.quantity_servings,
            "description": self.description,
            "allergens": self.allergens,
            "storage_conditions": self.storage_conditions,
            "preparation_time": self.preparation_time.isoformat(),
            "donor_confirms_suitability": self.donor_confirms_suitability,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "collection_deadline": self.collection_deadline.isoformat(),
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            # Derived safety flag surfaced to the UI
            "food_safety_status": "confirmed" if self.donor_confirms_suitability else "unconfirmed",
        }


class Claim(db.Model):
    __tablename__ = "claims"

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey("donations.id"), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey("ngos.id"), nullable=False)

    # Status: pending → confirmed → collected | cancelled
    status = db.Column(db.String(20), nullable=False, default="pending")
    notes = db.Column(db.Text, default="")
    claimed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    donation = db.relationship("Donation", back_populates="claims")
    ngo = db.relationship("NGO", back_populates="claims")

    def to_dict(self):
        return {
            "id": self.id,
            "donation_id": self.donation_id,
            "ngo_id": self.ngo_id,
            "status": self.status,
            "notes": self.notes,
            "claimed_at": self.claimed_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
