"""Seed script for Easy Holiday Firestore collections: destinations & public_holidays."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-1b134bc81ede"

DESTINATIONS = [
    {
        "id": "panaji_goa",
        "town": "Panaji",
        "state": "Goa",
        "country": "India",
        "latitude": 15.4989,
        "longitude": 73.8278,
        "avg_daily_budget_inr": 3500,
        "best_season": "Oct – Mar",
        "top_highlights": ["Fontainhas Latin Quarter", "Mandovi River Cruise", "Miramar Beach"]
    },
    {
        "id": "calangute_goa",
        "town": "Calangute",
        "state": "Goa",
        "country": "India",
        "latitude": 15.5437,
        "longitude": 73.7553,
        "avg_daily_budget_inr": 3000,
        "best_season": "Oct – Mar",
        "top_highlights": ["Calangute Beach", "Water Sports", "Baga Nightlife"]
    },
    {
        "id": "palolem_goa",
        "town": "Palolem",
        "state": "Goa",
        "country": "India",
        "latitude": 15.0100,
        "longitude": 74.0232,
        "avg_daily_budget_inr": 2800,
        "best_season": "Nov – Mar",
        "top_highlights": ["Palolem Beach", "Butterfly Beach Kayaking", "Silent Noise Club"]
    },
    {
        "id": "lonavala_maharashtra",
        "town": "Lonavala",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.7557,
        "longitude": 73.4091,
        "avg_daily_budget_inr": 2200,
        "best_season": "Jul – Feb",
        "top_highlights": ["Tiger's Leap", "Bhushi Dam", "Karla Caves", "Chikki Shopping"]
    },
    {
        "id": "mahabaleshwar_maharashtra",
        "town": "Mahabaleshwar",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 17.9307,
        "longitude": 73.6477,
        "avg_daily_budget_inr": 2500,
        "best_season": "Oct – Jun",
        "top_highlights": ["Arthur's Seat", "Venna Lake", "Mapro Garden Strawberries"]
    },
    {
        "id": "jaipur_rajasthan",
        "town": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "avg_daily_budget_inr": 3200,
        "best_season": "Oct – Mar",
        "top_highlights": ["Amer Fort", "Hawa Mahal", "City Palace", "Chokhi Dhani"]
    },
    {
        "id": "udaipur_rajasthan",
        "town": "Udaipur",
        "state": "Rajasthan",
        "country": "India",
        "latitude": 24.5854,
        "longitude": 73.7125,
        "avg_daily_budget_inr": 3800,
        "best_season": "Oct – Mar",
        "top_highlights": ["Lake Pichola", "City Palace", "Jagmandir", "Saheliyon-ki-Bari"]
    },
    {
        "id": "hampi_karnataka",
        "town": "Hampi",
        "state": "Karnataka",
        "country": "India",
        "latitude": 15.3350,
        "longitude": 76.4600,
        "avg_daily_budget_inr": 1800,
        "best_season": "Oct – Mar",
        "top_highlights": ["Virupaksha Temple", "Vijaya Vittala Chariot", "Matanga Hill"]
    },
    {
        "id": "kochi_kerala",
        "town": "Kochi",
        "state": "Kerala",
        "country": "India",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "avg_daily_budget_inr": 2800,
        "best_season": "Oct – Mar",
        "top_highlights": ["Fort Kochi Chinese Fishing Nets", "Mattancherry Palace"]
    },
    {
        "id": "munnar_kerala",
        "town": "Munnar",
        "state": "Kerala",
        "country": "India",
        "latitude": 10.0889,
        "longitude": 77.0595,
        "avg_daily_budget_inr": 2500,
        "best_season": "Sep – May",
        "top_highlights": ["Tea Gardens", "Eravikulam National Park", "Mattupetty Dam"]
    },
    {
        "id": "rishikesh_uttarakhand",
        "town": "Rishikesh",
        "state": "Uttarakhand",
        "country": "India",
        "latitude": 30.0869,
        "longitude": 78.2676,
        "avg_daily_budget_inr": 1800,
        "best_season": "Sep – Jun",
        "top_highlights": ["Laxman Jhula", "Ganga Aarti at Triveni Ghat", "River Rafting"]
    },
]

PUBLIC_HOLIDAYS_2026 = [
    {
        "date": "2026-01-26",
        "holiday_name": "Republic Day",
        "type": "Gazetted National Holiday",
        "impact_level": "High (Dry Day, Official Closures)",
        "country_code": "IN",
    },
    {
        "date": "2026-03-04",
        "holiday_name": "Holi",
        "type": "Gazetted Festival",
        "impact_level": "High (Morning Closures, Transportation Adjustments)",
        "country_code": "IN",
    },
    {
        "date": "2026-08-15",
        "holiday_name": "Independence Day",
        "type": "Gazetted National Holiday",
        "impact_level": "High (Dry Day, Official Closures)",
        "country_code": "IN",
    },
    {
        "date": "2026-10-02",
        "holiday_name": "Gandhi Jayanti",
        "type": "Gazetted National Holiday",
        "impact_level": "High (Dry Day, Government Closures)",
        "country_code": "IN",
    },
    {
        "date": "2026-10-20",
        "holiday_name": "Dussehra (Vijayadashami)",
        "type": "Gazetted Festival",
        "impact_level": "High (Heavy Traffic, Festive Crowds)",
        "country_code": "IN",
    },
    {
        "date": "2026-11-08",
        "holiday_name": "Diwali (Deepavali)",
        "type": "Gazetted Festival",
        "impact_level": "High (Market Closures, Peak Season Rates)",
        "country_code": "IN",
    },
    {
        "date": "2026-12-25",
        "holiday_name": "Christmas Day",
        "type": "Gazetted Holiday",
        "impact_level": "Moderate (Tourist Hotspot Festivities)",
        "country_code": "IN",
    },
]


import time

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connected to Firestore project: {db.project}")

    dest_ref = db.collection("destinations")
    for dest in DESTINATIONS:
        doc_id = dest["id"]
        doc_data = {k: v for k, v in dest.items() if k != "id"}
        for attempt in range(5):
            try:
                dest_ref.document(doc_id).set(doc_data)
                print(f"Seeded destination: {dest['town']}, {dest['state']}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {doc_id}: {e}. Retrying...")
                time.sleep(2)

    holidays_ref = db.collection("public_holidays")
    for hol in PUBLIC_HOLIDAYS_2026:
        doc_id = hol["date"]
        for attempt in range(5):
            try:
                holidays_ref.document(doc_id).set(hol)
                print(f"Seeded public holiday: {hol['holiday_name']} on {hol['date']}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {doc_id}: {e}. Retrying...")
                time.sleep(2)

    print("Firestore seeding complete!")


if __name__ == "__main__":
    seed_database()

