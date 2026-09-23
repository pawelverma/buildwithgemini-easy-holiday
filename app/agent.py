# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


import requests
from google import genai
from google.cloud import firestore, storage
from google.adk.tools import ToolContext


from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name="projects/671741015434/locations/us-east4/reasoningEngines/3831301043543605248"
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Easy Holiday, an agentic travel planning assistant originating from Pune, India. "
        "You remember the user's travel preferences across sessions (home city, home currency, "
        "budget level, diet, travel pace, and interests) and use them to personalize your travel itineraries and advice."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


def get_destinations() -> list[dict]:
    """Retrieve available travel destinations from Firestore database.

    Returns:
        List of destination dictionaries containing town, state, country, best season, avg_daily_budget_inr, and top highlights.
    """
    db = firestore.Client(project="qwiklabs-gcp-01-1b134bc81ede")
    docs = db.collection("destinations").stream()
    destinations = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        destinations.append(d)
    return destinations


def get_public_holidays(year: int = 2026) -> list[dict]:
    """Retrieve official public holidays in India from Firestore database for planning long weekends.

    Args:
        year: Year for public holidays (default 2026).

    Returns:
        List of public holiday dictionaries containing date, holiday_name, type, and impact_level.
    """
    db = firestore.Client(project="qwiklabs-gcp-01-1b134bc81ede")
    docs = db.collection("public_holidays").stream()
    holidays = []
    for doc in docs:
        h = doc.to_dict()
        if h.get("date", "").startswith(str(year)):
            holidays.append(h)
    return holidays


def save_trip_to_firestore(destination: str, start_date: str, end_date: str, total_cost_inr: float, itinerary_summary: str) -> str:
    """Save a planned trip itinerary to Firestore 'trips' collection.

    Args:
        destination: Target destination town/city name.
        start_date: Trip start date (YYYY-MM-DD).
        end_date: Trip end date (YYYY-MM-DD).
        total_cost_inr: Calculated total budget in INR.
        itinerary_summary: Summary of the planned day-by-day itinerary.

    Returns:
        Status message with saved document ID.
    """
    db = firestore.Client(project="qwiklabs-gcp-01-1b134bc81ede")
    trip_data = {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "total_cost_inr": total_cost_inr,
        "itinerary_summary": itinerary_summary,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    doc_ref = db.collection("trips").document()
    doc_ref.set(trip_data)
    return f"Trip to {destination} saved successfully with ID: {doc_ref.id}"


def geocode_location(location_name: str) -> dict:
    """Geocode a city or town name using Open-Meteo Geocoding API to get latitude, longitude, and location details.

    Args:
        location_name: The name of the city or town to geocode (e.g. 'Pune', 'Panaji', 'Jaipur').

    Returns:
        Dict containing location details including latitude, longitude, name, country, and state.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(url, params={"name": location_name, "count": 1, "language": "en", "format": "json"}, timeout=10)
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return {"error": f"No geocoding results found for '{location_name}'."}
    res = results[0]
    return {
        "name": res.get("name"),
        "latitude": res.get("latitude"),
        "longitude": res.get("longitude"),
        "country": res.get("country"),
        "state": res.get("admin1"),
    }


def get_weather_forecast(latitude: float, longitude: float, start_date: str = None, end_date: str = None) -> dict:
    """Fetch daily weather forecast from Open-Meteo for specified coordinates.

    Args:
        latitude: Geographical latitude coordinate.
        longitude: Geographical longitude coordinate.
        start_date: Optional target start date (YYYY-MM-DD) to verify against forecast window.
        end_date: Optional target end date (YYYY-MM-DD) to verify against forecast window.

    Returns:
        Dict containing daily weather data or a notice if requested dates fall beyond the 16-day forecast window.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    daily = data.get("daily", {})
    available_dates = daily.get("time", [])

    if not available_dates:
        return {"error": "Weather forecast unavailable for these coordinates."}

    max_available = available_dates[-1]
    min_available = available_dates[0]

    # Check forecast window boundaries
    if start_date and (start_date > max_available or start_date < min_available):
        return {
            "status": "beyond_forecast_window",
            "message": f"Requested date {start_date} is beyond the available 16-day forecast window ({min_available} to {max_available}). Weather forecasts cannot be predicted beyond this window.",
            "max_forecast_date": max_available,
        }

    return {
        "latitude": latitude,
        "longitude": longitude,
        "available_forecast_dates": available_dates,
        "daily_max_temp_c": daily.get("temperature_2m_max"),
        "daily_min_temp_c": daily.get("temperature_2m_min"),
        "daily_precipitation_mm": daily.get("precipitation_sum"),
    }


def get_exchange_rates(base_currency: str = "EUR", target_currency: str = "INR") -> dict:
    """Fetch live currency exchange rates from Frankfurter API.

    Args:
        base_currency: Source currency code (e.g. 'EUR', 'USD', 'GBP').
        target_currency: Target currency code (e.g. 'INR', 'USD', 'EUR').

    Returns:
        Dict containing conversion rate date, base currency, and target currency rate.
    """
    url = f"https://api.frankfurter.dev/v1/latest?from={base_currency.upper()}&to={target_currency.upper()}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return {"error": f"Failed to fetch exchange rates for {base_currency} to {target_currency}."}
    data = resp.json()
    return {
        "base_currency": data.get("base"),
        "date": data.get("date"),
        "rates": data.get("rates", {}),
    }


async def generate_travel_poster(destination: str, tool_context: ToolContext, custom_prompt: str = None) -> dict:
    """Generate a travel-poster style image for a destination using gemini-3.1-flash-lite-image model in global region, save as an artifact, and upload to public Cloud Storage.

    Args:
        destination: Name of the travel destination (e.g. 'Panaji', 'Jaipur', 'Munnar').
        tool_context: ADK ToolContext instance injected by framework.
        custom_prompt: Optional custom prompt description for the poster design.

    Returns:
        Dict containing status, artifact filename, and public Cloud Storage URL (https://storage.googleapis.com/<bucket>/<object>).
    """
    client = genai.Client(vertexai=True, project="qwiklabs-gcp-01-1b134bc81ede", location="global")
    prompt = custom_prompt or f"A vibrant vintage travel poster of {destination}, India showcasing iconic landmarks, scenic views, bold typography style, artistic travel illustration."
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )
    
    image_bytes = None
    mime_type = "image/jpeg"
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            if part.inline_data.mime_type:
                mime_type = part.inline_data.mime_type
            break
            
    if not image_bytes:
        return {"error": "Failed to generate image bytes from model response."}

    clean_dest = destination.lower().replace(" ", "_").replace(",", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"{clean_dest}_poster_{timestamp}.{ext}"

    # 1. Save artifact with tool_context
    part_artifact = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=part_artifact)

    # 2. Upload image bytes directly to public GCS bucket
    BUCKET_NAME = "easy-holiday-qwiklabs-gcp-01-1b134bc81ede"
    object_path = f"posters/{filename}"
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_path}"

    return {
        "status": "success",
        "destination": destination,
        "artifact_filename": filename,
        "public_url": public_url,
    }


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    tools=[
        get_destinations,
        get_public_holidays,
        save_trip_to_firestore,
        geocode_location,
        get_weather_forecast,
        get_exchange_rates,
        generate_travel_poster,
        get_current_time,
        PreloadMemoryTool(),
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
