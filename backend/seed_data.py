"""
seed_data.py – Populate the database with sample data for demonstration.

Run with:
    python seed_data.py

All coordinates are in Bangalore, India (lat ~12.97 / lon ~77.59).
Deadlines are set relative to a fixed reference date so the data
looks realistic on any day the demo is run.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure backend package root is on path when run directly
sys.path.insert(0, os.path.dirname(__file__))

from app_factory import create_app, db
from models import NGO, Donation, Claim

# ──────────────────────────────────────────────────────────────────────────────
# Reference "now" – all deadlines are relative to this
# ──────────────────────────────────────────────────────────────────────────────
NOW = datetime.now(timezone.utc)


def dt(hours_from_now):
    return NOW + timedelta(hours=hours_from_now)


def dt_past(hours_ago):
    return NOW - timedelta(hours=hours_ago)


# ──────────────────────────────────────────────────────────────────────────────
# Seed
# ──────────────────────────────────────────────────────────────────────────────

def seed():
    app = create_app()
    with app.app_context():
        # Clear existing data (for idempotent re-seeding)
        Claim.query.delete()
        Donation.query.delete()
        NGO.query.delete()
        db.session.commit()

        # ── NGOs ──────────────────────────────────────────────────────────────
        ngos = [
            NGO(
                name="Akshaya Patra Foundation",
                contact_email="akshaya@example.org",
                phone="+91-80-23010000",
                latitude=12.9716,
                longitude=77.5946,
                max_capacity=500,
                allergen_restrictions="",
            ),
            NGO(
                name="Robin Hood Army Bangalore",
                contact_email="robinhood.blr@example.org",
                phone="+91-98001-11111",
                latitude=12.9352,
                longitude=77.6245,
                max_capacity=150,
                allergen_restrictions="nuts",
            ),
            NGO(
                name="No Food Waste",
                contact_email="nfw@example.org",
                phone="+91-98002-22222",
                latitude=13.0100,
                longitude=77.5500,
                max_capacity=200,
                allergen_restrictions="",
            ),
        ]
        db.session.add_all(ngos)
        db.session.flush()   # populate IDs

        # ── Donations ─────────────────────────────────────────────────────────
        donations_data = [
            # 1 – available, confirmed, urgent (3 h)
            dict(
                donor_name="The Leela Palace",
                donor_type="restaurant",
                donor_email="leela@example.com",
                donor_phone="+91-80-25211234",
                food_name="Buffet Surplus – Paneer & Dal",
                food_category="cooked",
                quantity_servings=120,
                description="Left-over lunch buffet items, freshly prepared.",
                allergens="dairy",
                storage_conditions="Keep hot above 60°C or refrigerate immediately below 4°C.",
                preparation_time=dt_past(2),
                donor_confirms_suitability=True,
                latitude=12.9590,
                longitude=77.6490,
                address="23 Old Airport Road, Bangalore",
                collection_deadline=dt(3),
                status="available",
            ),
            # 2 – available, confirmed, moderate urgency (8 h)
            dict(
                donor_name="IIT Bangalore Canteen",
                donor_type="canteen",
                donor_email="iitb.canteen@example.edu",
                donor_phone="+91-80-22222222",
                food_name="South Indian Meals – Rice, Sambar, Rasam",
                food_category="cooked",
                quantity_servings=200,
                description="Freshly cooked student meals surplus from today's batch.",
                allergens="none",
                storage_conditions="Refrigerate below 4°C within 30 minutes.",
                preparation_time=dt_past(1),
                donor_confirms_suitability=True,
                latitude=13.0200,
                longitude=77.5700,
                address="IIT Campus, North Bangalore",
                collection_deadline=dt(8),
                status="available",
            ),
            # 3 – available, confirmed, low urgency (24 h) – packaged
            dict(
                donor_name="Britannia Bakery Outlet",
                donor_type="bakery",
                donor_email="britannia.outlet@example.com",
                donor_phone="+91-80-33333333",
                food_name="Bread Loaves – Assorted",
                food_category="baked",
                quantity_servings=80,
                description="Day-old bread loaves, sealed in original packaging.",
                allergens="gluten",
                storage_conditions="Store at room temperature, consume within 24 hours.",
                preparation_time=dt_past(20),
                donor_confirms_suitability=True,
                latitude=12.9800,
                longitude=77.5900,
                address="12 MG Road, Bangalore",
                collection_deadline=dt(24),
                status="available",
            ),
            # 4 – available, NOT yet confirmed (safety unconfirmed)
            dict(
                donor_name="TechPark Corporate Event",
                donor_type="event",
                donor_email="events@techpark.example.com",
                donor_phone="+91-80-44444444",
                food_name="Conference Lunch Boxes",
                food_category="packaged",
                quantity_servings=350,
                description="Individually packed lunch boxes from all-day corporate event.",
                allergens="nuts, dairy, gluten",
                storage_conditions="Refrigerate below 4°C. Unknown preparation environment.",
                preparation_time=dt_past(4),
                donor_confirms_suitability=False,
                latitude=12.9400,
                longitude=77.6700,
                address="Whitefield Tech Park, Bangalore",
                collection_deadline=dt(6),
                status="available",
            ),
            # 5 – claimed
            dict(
                donor_name="Meghana Foods",
                donor_type="restaurant",
                donor_email="meghana@example.com",
                donor_phone="+91-80-55555555",
                food_name="Biryani Surplus",
                food_category="cooked",
                quantity_servings=90,
                description="Chicken and veg biryani surplus from peak-hour service.",
                allergens="none",
                storage_conditions="Keep hot above 60°C. Collect within 2 hours.",
                preparation_time=dt_past(1),
                donor_confirms_suitability=True,
                latitude=12.9500,
                longitude=77.6100,
                address="Koramangala, Bangalore",
                collection_deadline=dt(2),
                status="claimed",
            ),
            # 6 – completed
            dict(
                donor_name="Cafe Coffee Day HQ",
                donor_type="restaurant",
                donor_email="ccd@example.com",
                donor_phone="+91-80-66666666",
                food_name="Sandwiches & Wraps",
                food_category="packaged",
                quantity_servings=60,
                description="End-of-day packaged sandwiches and wraps, sealed.",
                allergens="gluten, dairy",
                storage_conditions="Refrigerate below 4°C.",
                preparation_time=dt_past(10),
                donor_confirms_suitability=True,
                latitude=12.9720,
                longitude=77.5950,
                address="Brigade Road, Bangalore",
                collection_deadline=dt_past(2),
                status="completed",
            ),
            # 7 – available, confirmed
            dict(
                donor_name="Manipal University Canteen",
                donor_type="canteen",
                donor_email="manipal.canteen@example.edu",
                donor_phone="+91-80-77777777",
                food_name="Veg Thali Surplus",
                food_category="cooked",
                quantity_servings=150,
                description="Complete veg thali surplus – roti, sabzi, rice, dal.",
                allergens="gluten, dairy",
                storage_conditions="Keep hot or refrigerate promptly below 4°C.",
                preparation_time=dt_past(1),
                donor_confirms_suitability=True,
                latitude=12.9900,
                longitude=77.5600,
                address="Manipal Campus, Bangalore",
                collection_deadline=dt(5),
                status="available",
            ),
            # 8 – available, confirmed, nut-free
            dict(
                donor_name="Sweet Chariot Bakery",
                donor_type="bakery",
                donor_email="sweetchriot@example.com",
                donor_phone="+91-80-88888888",
                food_name="Pastries & Cakes – Assorted",
                food_category="baked",
                quantity_servings=45,
                description="Surplus pastries from today's display, no nuts used.",
                allergens="gluten, dairy",
                storage_conditions="Refrigerate below 4°C, consume within 12 hours.",
                preparation_time=dt_past(5),
                donor_confirms_suitability=True,
                latitude=12.9650,
                longitude=77.5800,
                address="Indiranagar, Bangalore",
                collection_deadline=dt(7),
                status="available",
            ),
            # 9 – available, confirmed, very urgent (1 h)
            dict(
                donor_name="Marriott Whitefield",
                donor_type="restaurant",
                donor_email="marriott.wf@example.com",
                donor_phone="+91-80-99999999",
                food_name="Dinner Buffet – Mixed Veg & Non-Veg",
                food_category="cooked",
                quantity_servings=180,
                description="End-of-dinner buffet items. Must be collected immediately.",
                allergens="dairy",
                storage_conditions="Hot food: collect within 1 hour. Cannot be reheated.",
                preparation_time=dt_past(3),
                donor_confirms_suitability=True,
                latitude=12.9300,
                longitude=77.6900,
                address="Whitefield, Bangalore",
                collection_deadline=dt(1),
                status="available",
            ),
            # 10 – completed
            dict(
                donor_name="Bangalore University Canteen",
                donor_type="canteen",
                donor_email="bu.canteen@example.edu",
                donor_phone="+91-80-10101010",
                food_name="North Indian Lunch Surplus",
                food_category="cooked",
                quantity_servings=250,
                description="Surplus from large batch for exam day – chapati, dal, rice.",
                allergens="gluten",
                storage_conditions="Refrigerate below 4°C within 1 hour of preparation.",
                preparation_time=dt_past(12),
                donor_confirms_suitability=True,
                latitude=12.9600,
                longitude=77.5700,
                address="Jnana Bharathi Campus, Bangalore",
                collection_deadline=dt_past(6),
                status="completed",
            ),
        ]

        donations = []
        for d in donations_data:
            donations.append(Donation(**d))
        db.session.add_all(donations)
        db.session.flush()

        # ── Claims ────────────────────────────────────────────────────────────
        # Link completed donations to claims
        completed_ids = [d.id for d in donations if d.status == "completed"]
        claimed_ids   = [d.id for d in donations if d.status == "claimed"]

        claims = []
        for don_id in completed_ids:
            claims.append(Claim(
                donation_id=don_id,
                ngo_id=ngos[0].id,
                status="collected",
                notes="Collected on time. All food distributed.",
            ))
        for don_id in claimed_ids:
            claims.append(Claim(
                donation_id=don_id,
                ngo_id=ngos[1].id,
                status="confirmed",
                notes="On the way to pick up.",
            ))

        db.session.add_all(claims)
        db.session.commit()

        print("OK  Seed data inserted successfully.")
        print(f"   NGOs:      {len(ngos)}")
        print(f"   Donations: {len(donations)}")
        print(f"   Claims:    {len(claims)}")


if __name__ == "__main__":
    seed()
