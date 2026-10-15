"""
tests/test_api.py – pytest suite for MealBridge AI backend.

Covers:
- Donation CRUD + validation
- NGO CRUD
- Claim creation, status transitions
- Matching engine (scoring, allergen filter, distance filter)
- Impact statistics
"""

import sys
import os
import pytest
from datetime import datetime, timedelta, timezone

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_factory import create_app, db as _db
from models import NGO, Donation, Claim


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Create application with in-memory SQLite for the test session."""
    _app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
    })
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Wipe all rows before every test for isolation."""
    with app.app_context():
        Claim.query.delete()
        Donation.query.delete()
        NGO.query.delete()
        _db.session.commit()
    yield


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc)


def _dt(hours=0):
    return (NOW + timedelta(hours=hours)).isoformat()


def _donation_payload(**overrides):
    base = {
        "donor_name":                "Test Restaurant",
        "donor_type":                "restaurant",
        "donor_email":               "test@example.com",
        "food_name":                 "Test Food",
        "food_category":             "cooked",
        "quantity_servings":         50,
        "allergens":                 "none",
        "storage_conditions":        "Keep refrigerated.",
        "preparation_time":          _dt(-1),
        "donor_confirms_suitability": True,
        "latitude":                  12.97,
        "longitude":                 77.59,
        "collection_deadline":       _dt(6),
    }
    base.update(overrides)
    return base


def _ngo_payload(**overrides):
    base = {
        "name":           "Test NGO",
        "contact_email":  "ngo@example.org",
        "latitude":       12.97,
        "longitude":      77.59,
        "max_capacity":   100,
    }
    base.update(overrides)
    return base


# ──────────────────────────────────────────────────────────────────────────────
# Donation tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDonationCreate:
    def test_create_valid(self, client):
        r = client.post("/api/donations", json=_donation_payload())
        assert r.status_code == 201
        data = r.get_json()
        assert data["food_name"] == "Test Food"
        assert data["food_safety_status"] == "confirmed"
        assert data["status"] == "available"

    def test_safety_unconfirmed_flag(self, client):
        r = client.post("/api/donations", json=_donation_payload(
            donor_confirms_suitability=False
        ))
        assert r.status_code == 201
        assert r.get_json()["food_safety_status"] == "unconfirmed"

    def test_missing_required_fields(self, client):
        r = client.post("/api/donations", json={})
        assert r.status_code == 422
        errors = r.get_json()["errors"]
        assert any("Donor name" in e for e in errors)
        assert any("food_name" in e.lower() or "food name" in e.lower() for e in errors)

    def test_invalid_donor_type(self, client):
        r = client.post("/api/donations", json=_donation_payload(donor_type="zoo"))
        assert r.status_code == 422
        assert any("donor_type" in e for e in r.get_json()["errors"])

    def test_negative_quantity(self, client):
        r = client.post("/api/donations", json=_donation_payload(quantity_servings=-5))
        assert r.status_code == 422
        assert any("quantity_servings" in e for e in r.get_json()["errors"])

    def test_deadline_before_prep(self, client):
        r = client.post("/api/donations", json=_donation_payload(
            preparation_time=_dt(2),
            collection_deadline=_dt(1),
        ))
        assert r.status_code == 422
        assert any("deadline" in e.lower() for e in r.get_json()["errors"])

    def test_missing_suitability_confirmation(self, client):
        payload = _donation_payload()
        del payload["donor_confirms_suitability"]
        r = client.post("/api/donations", json=payload)
        assert r.status_code == 422

    def test_no_json_body(self, client):
        r = client.post("/api/donations", data="not json",
                        content_type="text/plain")
        assert r.status_code == 400


class TestDonationRead:
    def test_list_empty(self, client):
        r = client.get("/api/donations")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_list_with_data(self, client):
        client.post("/api/donations", json=_donation_payload())
        r = client.get("/api/donations")
        assert r.status_code == 200
        assert len(r.get_json()) == 1

    def test_filter_by_status(self, client):
        client.post("/api/donations", json=_donation_payload())
        r = client.get("/api/donations?status=available")
        assert r.status_code == 200
        assert len(r.get_json()) == 1

        r2 = client.get("/api/donations?status=completed")
        assert r2.status_code == 200
        assert len(r2.get_json()) == 0

    def test_invalid_status_filter(self, client):
        r = client.get("/api/donations?status=unknown")
        assert r.status_code == 400

    def test_get_by_id(self, client):
        created = client.post("/api/donations", json=_donation_payload()).get_json()
        r = client.get(f"/api/donations/{created['id']}")
        assert r.status_code == 200
        assert r.get_json()["id"] == created["id"]

    def test_get_nonexistent(self, client):
        r = client.get("/api/donations/99999")
        assert r.status_code == 404

    def test_filter_by_donor_email(self, client):
        client.post("/api/donations", json=_donation_payload(donor_email="a@x.com"))
        client.post("/api/donations", json=_donation_payload(donor_email="b@x.com"))
        r = client.get("/api/donations?donor_email=a@x.com")
        assert len(r.get_json()) == 1


class TestDonationUpdate:
    def test_patch_status(self, client):
        created = client.post("/api/donations", json=_donation_payload()).get_json()
        r = client.patch(f"/api/donations/{created['id']}", json={"status": "cancelled"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "cancelled"

    def test_patch_invalid_status(self, client):
        created = client.post("/api/donations", json=_donation_payload()).get_json()
        r = client.patch(f"/api/donations/{created['id']}", json={"status": "flying"})
        assert r.status_code == 422


class TestDonationDelete:
    def test_delete_available(self, client):
        created = client.post("/api/donations", json=_donation_payload()).get_json()
        r = client.delete(f"/api/donations/{created['id']}")
        assert r.status_code == 200

    def test_delete_claimed_rejected(self, client):
        # Create donation and NGO, then claim it
        don = client.post("/api/donations", json=_donation_payload()).get_json()
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        r = client.delete(f"/api/donations/{don['id']}")
        assert r.status_code == 409


# ──────────────────────────────────────────────────────────────────────────────
# NGO tests
# ──────────────────────────────────────────────────────────────────────────────

class TestNGO:
    def test_create_ngo(self, client):
        r = client.post("/api/ngos", json=_ngo_payload())
        assert r.status_code == 201
        assert r.get_json()["name"] == "Test NGO"

    def test_duplicate_email(self, client):
        client.post("/api/ngos", json=_ngo_payload())
        r = client.post("/api/ngos", json=_ngo_payload())
        assert r.status_code == 409

    def test_list_ngos(self, client):
        client.post("/api/ngos", json=_ngo_payload())
        r = client.get("/api/ngos")
        assert r.status_code == 200
        assert len(r.get_json()) == 1

    def test_get_ngo(self, client):
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        r = client.get(f"/api/ngos/{ngo['id']}")
        assert r.status_code == 200

    def test_get_nonexistent_ngo(self, client):
        r = client.get("/api/ngos/99999")
        assert r.status_code == 404


# ──────────────────────────────────────────────────────────────────────────────
# Claim tests
# ──────────────────────────────────────────────────────────────────────────────

class TestClaims:
    def _setup(self, client):
        don = client.post("/api/donations", json=_donation_payload()).get_json()
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        return don, ngo

    def test_create_claim(self, client):
        don, ngo = self._setup(client)
        r = client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        assert r.status_code == 201
        assert r.get_json()["status"] == "pending"

    def test_donation_becomes_claimed(self, client):
        don, ngo = self._setup(client)
        client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        r = client.get(f"/api/donations/{don['id']}")
        assert r.get_json()["status"] == "claimed"

    def test_double_claim_rejected(self, client):
        don, ngo = self._setup(client)
        client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        r2 = client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        assert r2.status_code == 409

    def test_claim_already_claimed_donation(self, client):
        don, ngo = self._setup(client)
        ngo2 = client.post("/api/ngos", json=_ngo_payload(
            name="NGO2", contact_email="ngo2@example.org"
        )).get_json()
        client.post("/api/claims", json={"ngo_id": ngo["id"], "donation_id": don["id"]})
        r = client.post("/api/claims", json={"ngo_id": ngo2["id"], "donation_id": don["id"]})
        assert r.status_code == 409

    def test_update_claim_to_collected(self, client):
        don, ngo = self._setup(client)
        claim = client.post("/api/claims", json={
            "ngo_id": ngo["id"], "donation_id": don["id"]
        }).get_json()
        r = client.patch(f"/api/claims/{claim['id']}/status", json={"status": "collected"})
        assert r.status_code == 200
        # Donation should now be completed
        don_r = client.get(f"/api/donations/{don['id']}")
        assert don_r.get_json()["status"] == "completed"

    def test_cancel_claim_reverts_donation(self, client):
        don, ngo = self._setup(client)
        claim = client.post("/api/claims", json={
            "ngo_id": ngo["id"], "donation_id": don["id"]
        }).get_json()
        r = client.patch(f"/api/claims/{claim['id']}/status", json={"status": "cancelled"})
        assert r.status_code == 200
        don_r = client.get(f"/api/donations/{don['id']}")
        assert don_r.get_json()["status"] == "available"


# ──────────────────────────────────────────────────────────────────────────────
# Matching tests
# ──────────────────────────────────────────────────────────────────────────────

class TestMatching:
    def test_no_ngo(self, client):
        r = client.get("/api/matches/99999")
        assert r.status_code == 404

    def test_empty_donations(self, client):
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        r = client.get(f"/api/matches/{ngo['id']}")
        assert r.status_code == 200
        assert r.get_json()["matches"] == []

    def test_returns_available_donation(self, client):
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        client.post("/api/donations", json=_donation_payload())
        r = client.get(f"/api/matches/{ngo['id']}")
        assert r.status_code == 200
        assert len(r.get_json()["matches"]) == 1

    def test_allergen_filter(self, client):
        """NGO that cannot accept nuts should not see nut donations."""
        ngo = client.post("/api/ngos", json=_ngo_payload(
            allergen_restrictions="nuts"
        )).get_json()
        client.post("/api/donations", json=_donation_payload(allergens="nuts, peanuts"))
        r = client.get(f"/api/matches/{ngo['id']}")
        assert r.get_json()["matches"] == []

    def test_allergen_no_conflict(self, client):
        ngo = client.post("/api/ngos", json=_ngo_payload(
            allergen_restrictions="nuts"
        )).get_json()
        # Donation has only gluten – no conflict
        client.post("/api/donations", json=_donation_payload(allergens="gluten"))
        r = client.get(f"/api/matches/{ngo['id']}")
        assert len(r.get_json()["matches"]) == 1

    def test_distance_filter(self, client):
        """Donation far away should be excluded with tight distance cap."""
        ngo = client.post("/api/ngos", json=_ngo_payload(
            latitude=12.97, longitude=77.59
        )).get_json()
        # Donate from London (~8000 km away)
        client.post("/api/donations", json=_donation_payload(
            latitude=51.5, longitude=-0.12
        ))
        r = client.get(f"/api/matches/{ngo['id']}?max_distance_km=50")
        assert r.get_json()["matches"] == []

    def test_score_breakdown_present(self, client):
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        client.post("/api/donations", json=_donation_payload())
        r = client.get(f"/api/matches/{ngo['id']}")
        match = r.get_json()["matches"][0]
        assert "score" in match["match"]
        assert "distance_km" in match["match"]
        assert "score_breakdown" in match["match"]

    def test_expired_excluded(self, client):
        """A donation whose deadline is in the past must not appear in matches."""
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        client.post("/api/donations", json=_donation_payload(
            preparation_time=_dt(-10),
            collection_deadline=_dt(-1),   # already passed
        ))
        r = client.get(f"/api/matches/{ngo['id']}")
        assert r.get_json()["matches"] == []


# ──────────────────────────────────────────────────────────────────────────────
# Impact tests
# ──────────────────────────────────────────────────────────────────────────────

class TestImpact:
    def test_empty_impact(self, client):
        r = client.get("/api/impact")
        assert r.status_code == 200
        summary = r.get_json()["summary"]
        assert summary["total_donations_posted"] == 0
        assert summary["estimated_meals_distributed"] == 0

    def test_impact_counts_donations(self, client):
        client.post("/api/donations", json=_donation_payload())
        r = client.get("/api/impact")
        summary = r.get_json()["summary"]
        assert summary["total_donations_posted"] == 1
        assert summary["total_donations_available"] == 1

    def test_impact_after_completion(self, client):
        don = client.post("/api/donations", json=_donation_payload(quantity_servings=80)).get_json()
        ngo = client.post("/api/ngos", json=_ngo_payload()).get_json()
        claim = client.post("/api/claims", json={
            "ngo_id": ngo["id"], "donation_id": don["id"]
        }).get_json()
        client.patch(f"/api/claims/{claim['id']}/status", json={"status": "collected"})

        r = client.get("/api/impact")
        summary = r.get_json()["summary"]
        assert summary["total_donations_completed"] == 1
        assert summary["estimated_meals_distributed"] == 80
        assert summary["estimated_kg_food_saved"] == pytest.approx(80 * 0.4)
