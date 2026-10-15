"""
app.py – entry point for the MealBridge AI Flask server.

Run with:
    python app.py
"""

from app_factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
