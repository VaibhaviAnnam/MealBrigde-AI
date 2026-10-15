# MealBridge AI — Smart Food Waste and Donation Platform

Connect restaurants, canteens, bakeries and event organisers that have surplus
food with NGOs that can collect and distribute it safely.

---

## Project Structure

```
MealBridge-AI/
├── backend/
│   ├── app.py                  # Flask entry point
│   ├── app_factory.py          # App factory + db instance
│   ├── models.py               # SQLAlchemy models (Donation, NGO, Claim)
│   ├── routes/
│   │   ├── donations.py        # Donor CRUD endpoints
│   │   ├── ngos.py             # NGO + claim endpoints
│   │   ├── matching.py         # Rule-based matching engine
│   │   └── impact.py           # Impact statistics
│   ├── seed_data.py            # Sample data loader
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py         # pytest backend tests (41 tests)
│
├── frontend/
│   ├── src/
│   │   ├── App.js              # Router + Navbar
│   │   ├── App.css             # Global styles + CSS variables
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Landing page
│   │   │   ├── DonorDashboard.jsx
│   │   │   ├── NgoDashboard.jsx
│   │   │   └── ImpactDashboard.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── DonationCard.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   └── FoodSafetyWarning.jsx
│   │   └── services/
│   │       └── api.js          # Axios API wrapper
│   └── package.json
│
└── README.md
```

---

## Prerequisites

| Tool    | Required version |
|---------|-----------------|
| Python  | 3.10 or newer   |
| Node.js | 16 or newer     |
| npm     | 8 or newer      |

---

## Setup and Run

### 1 — Backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Load sample data (creates mealbridge.db in backend/)
python seed_data.py

# Start the Flask development server
python app.py
```

The API is now available at **http://localhost:5000**.

### 2 — Frontend

Open a **second terminal** (keep the backend running):

```bash
cd frontend
npm install
npm start
```

The React app opens at **http://localhost:3000**.

---

## Seed Data Summary

The seed script inserts:

| Category   | Count |
|------------|-------|
| NGOs       | 3     |
| Donations  | 10    |
| Claims     | 3     |

Sample donors include The Leela Palace, IIT Bangalore Canteen, Britannia Bakery,
a corporate tech-park event, Meghana Foods, Cafe Coffee Day, and others — all
located in Bangalore, India.

Sample NGOs include Akshaya Patra Foundation, Robin Hood Army Bangalore, and
No Food Waste, each with different locations, capacities, and allergen restrictions.

---

## Running the Backend Tests

```bash
cd backend
python -m pytest tests/test_api.py -v
```

All 41 tests should pass. Tests use an in-memory SQLite database and are fully
isolated (each test starts with an empty database).

---

## API Reference

### Donations

| Method | Endpoint                          | Description             |
|--------|-----------------------------------|-------------------------|
| POST   | `/api/donations`                  | Create donation         |
| GET    | `/api/donations`                  | List (filter: ?status=, ?donor_email=) |
| GET    | `/api/donations/<id>`             | Get one donation        |
| PATCH  | `/api/donations/<id>`             | Update status           |
| DELETE | `/api/donations/<id>`             | Delete (available only) |

### NGOs & Claims

| Method | Endpoint                          | Description             |
|--------|-----------------------------------|-------------------------|
| POST   | `/api/ngos`                       | Register NGO            |
| GET    | `/api/ngos`                       | List NGOs               |
| GET    | `/api/ngos/<id>`                  | Get one NGO             |
| POST   | `/api/claims`                     | Create claim            |
| GET    | `/api/claims`                     | List (filter: ?ngo_id=, ?donation_id=) |
| PATCH  | `/api/claims/<id>/status`         | Update claim status     |

### Matching & Impact

| Method | Endpoint                          | Description             |
|--------|-----------------------------------|-------------------------|
| GET    | `/api/matches/<ngo_id>`           | Get scored matches (?max_distance_km=, ?limit=) |
| GET    | `/api/impact`                     | Platform-wide stats     |

---

## Matching Algorithm

The matching engine is **entirely rule-based** — no machine learning is used or claimed.

For each available donation, a match score in [0, 1] is computed as:

```
score = 0.4 × S_dist + 0.4 × S_urgency + 0.2 × S_qty

S_dist    = 1 / (1 + distance_km)
S_urgency = 1 / (1 + hours_until_deadline)
S_qty     = 1 - |donation_qty - ngo_capacity| / max(donation_qty, ngo_capacity)
```

Donations are also hard-filtered by:
- **Allergen conflict** — excluded entirely if the donation's allergens overlap with the NGO's restrictions
- **Distance cap** — excluded if beyond `max_distance_km` (default 50 km)
- **Expiry** — excluded if the collection deadline has already passed

Full score breakdown (distance, urgency, quantity sub-scores) is returned in the
API response for transparency.

---

## Food Safety

- Donors must tick a **"I confirm this food is suitable for donation"** checkbox before posting.
- The API returns a `food_safety_status` field: `"confirmed"` or `"unconfirmed"`.
- The UI displays a **visible amber warning banner** on any unconfirmed donation.
- Food safety is **never automatically granted** — it requires explicit donor confirmation.
- NGOs must review allergen information and storage conditions before accepting and distributing food.

---

## Stopping the Servers

- Backend: press **Ctrl+C** in the terminal running `python app.py`.
- Frontend: press **Ctrl+C** in the terminal running `npm start`.

Neither process runs in the background after you stop it.

---

## Design Decisions

- **SQLite** keeps the project self-contained with no external database service.
- **CORS** is enabled on the Flask side so the CRA dev server (port 3000) can reach the API (port 5000) without a proxy.
- **App factory pattern** (`app_factory.py`) separates app creation from the entry point so tests can create isolated app instances with in-memory databases.
- **Donation status lifecycle**: `available → claimed → completed` (happy path), with `cancelled` and `expired` for edge cases.
- **Claim status lifecycle**: `pending → confirmed → collected`, with `cancelled` available at any active stage.
