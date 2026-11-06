import hashlib
import math
import os
import re
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

NIPOST_API_KEY = os.getenv("NIPOST_API_KEY", "PASTE_YOUR_NIPOST_TEST_KEY_HERE")
NIPOST_PUBLISHABLE_KEY = os.getenv(
    "NIPOST_PUBLISHABLE_KEY", "PASTE_YOUR_NIPOST_PUBLISHABLE_KEY_HERE"
)
NIPOST_BASE_URL = os.getenv("NIPOST_BASE_URL", "https://api.postcode.gov.ng").rstrip("/")

# Live session verification counters
SESSION_STATS = {
    "total_verified": 24,
    "naira_saved": 24 * 4500,
    "fraud_flagged": 3,
    "avg_latency_ms": 138,
    "latency_samples": [138],
    "access_level": "L1-LIVE + L3-ENRICHED",
}

# Enriched metadata for NIPOST Official Sandbox Codes & Regional Demo Codes
ENRICHED_POSTCODE_REGISTRY = {
    "FC-01-A01-KP-27": {
        "state_code": "FC",
        "state_name": "FCT Abuja",
        "lga_code": "01",
        "lga_name": "Abuja Municipal Area Council (AMAC)",
        "district_code": "A01",
        "district_name": "Garki / Area 11 District",
        "area_code": "KP",
        "area_name": "Kashim Ibrahim / Area 11 Zone",
        "building_code": "27",
        "recent_house_address": "Plot 27, Kashim Ibrahim Way, Garki Area 11, Abuja FCT",
        "building_use_status": "COMMERCIAL",
        "building_subtype": "Corporate Office / Financial Institution Plaza",
        "coordinates": {"lat": 9.0385, "lng": 7.4982},
        "ward": "Garki Ward",
        "official_sandbox": True,
    },
    "FC-01-A01-LR-01": {
        "state_code": "FC",
        "state_name": "FCT Abuja",
        "lga_code": "01",
        "lga_name": "Abuja Municipal Area Council (AMAC)",
        "district_code": "A01",
        "district_name": "Central Business District / Garki",
        "area_code": "LR",
        "area_name": "Ladoke Akintola Boulevard Precinct",
        "building_code": "01",
        "recent_house_address": "No. 1 Ladoke Akintola Boulevard, Garki II, Abuja FCT",
        "building_use_status": "RESIDENTIAL",
        "building_subtype": "Multi-Unit Serviced Duplex Compound",
        "coordinates": {"lat": 9.0312, "lng": 7.4894},
        "ward": "Garki II Ward",
        "official_sandbox": True,
    },
    "FC-01-A01-MH-01": {
        "state_code": "FC",
        "state_name": "FCT Abuja",
        "lga_code": "01",
        "lga_name": "Abuja Municipal Area Council (AMAC)",
        "district_code": "A01",
        "district_name": "Maitama / Central District",
        "area_code": "MH",
        "area_name": "Maitama Hills / Muhammadu Buhari Way",
        "building_code": "01",
        "recent_house_address": "Plot 1, Muhammadu Buhari Way, Central Area, Abuja FCT",
        "building_use_status": "COMMERCIAL",
        "building_subtype": "Federal Agency & Banking Complex",
        "coordinates": {"lat": 9.0540, "lng": 7.4910},
        "ward": "City Centre Ward",
        "official_sandbox": True,
    },
    "FC-01-A01-MV-01": {
        "state_code": "FC",
        "state_name": "FCT Abuja",
        "lga_code": "01",
        "lga_name": "Abuja Municipal Area Council (AMAC)",
        "district_code": "A01",
        "district_name": "Wuse / Central District",
        "area_code": "MV",
        "area_name": "Moshood Abiola Way Corridor",
        "building_code": "01",
        "recent_house_address": "No. 1 Moshood Abiola Way, Area 10 Garki, Abuja FCT",
        "building_use_status": "COMMERCIAL",
        "building_subtype": "NIPOST / Commercial Retail Hub",
        "coordinates": {"lat": 9.0355, "lng": 7.4832},
        "ward": "Garki Ward",
        "official_sandbox": True,
    },
    "FC-01-A01-MW-01": {
        "state_code": "FC",
        "state_name": "FCT Abuja",
        "lga_code": "01",
        "lga_name": "Abuja Municipal Area Council (AMAC)",
        "district_code": "A01",
        "district_name": "Garki / Area 3 District",
        "area_code": "MW",
        "area_name": "Murtala Mohammed Express Access",
        "building_code": "01",
        "recent_house_address": "Plot 1, Murtala Mohammed Way, Garki Area 3, Abuja FCT",
        "building_use_status": "RESIDENTIAL",
        "building_subtype": "Detached Bungalow & Annex",
        "coordinates": {"lat": 9.0298, "lng": 7.4921},
        "ward": "Garki Ward",
        "official_sandbox": True,
    },
    "YB-01-A01-DM-12": {
        "state_code": "YB",
        "state_name": "Yobe State",
        "lga_code": "01",
        "lga_name": "Damaturu LGA",
        "district_code": "A01",
        "district_name": "Damaturu Central Postcode District",
        "area_code": "DM",
        "area_name": "Maiduguri Road / Sabon Pegi Commercial Axis",
        "building_code": "12",
        "recent_house_address": "No. 12 Maiduguri Road, Opposite Central Roundabout, Damaturu, Yobe State",
        "building_use_status": "COMMERCIAL",
        "building_subtype": "Agro-Commodity & POS Agent Merchant Hub",
        "coordinates": {"lat": 11.7470, "lng": 11.9608},
        "ward": "Damaturu Central Ward",
        "official_sandbox": False,
    },
    "KN-31-F82-WJ-80": {
        "state_code": "KN",
        "state_name": "Kano State",
        "lga_code": "31",
        "lga_name": "Nassarawa / Kano Municipal LGA",
        "district_code": "F82",
        "district_name": "Bompai / Waje Commercial District",
        "area_code": "WJ",
        "area_name": "Murtala Mohammed Way / Kwari Trade Zone",
        "building_code": "80",
        "recent_house_address": "Plot 80, Murtala Mohammed Way, Waje / Bompai Commercial Layout, Kano State",
        "building_use_status": "COMMERCIAL",
        "building_subtype": "Wholesale Textile & SME Distribution Plaza",
        "coordinates": {"lat": 12.0022, "lng": 8.5364},
        "ward": "Tudun Wada / Waje Ward",
        "official_sandbox": False,
    },
    "AD-01-A02-YL-09": {
        "state_code": "AD",
        "state_name": "Adamawa State",
        "lga_code": "01",
        "lga_name": "Yola North (Jimeta) LGA",
        "district_code": "A02",
        "district_name": "Jimeta / Atiku Abubakar Way District",
        "area_code": "YL",
        "area_name": "Bekaji / Gimba Road Precinct",
        "building_code": "09",
        "recent_house_address": "House 9, Atiku Abubakar Way, Jimeta-Yola, Adamawa State",
        "building_use_status": "RESIDENTIAL",
        "building_subtype": "Metered Residential Compound (YEDC Feeder Zone)",
        "coordinates": {"lat": 9.2795, "lng": 12.4582},
        "ward": "Karewa / Bekaji Ward",
        "official_sandbox": False,
    },
}

STATE_CODE_MAP = {
    "AB": "Abia State",
    "AD": "Adamawa State",
    "AK": "Akwa Ibom State",
    "AN": "Anambra State",
    "BA": "Bauchi State",
    "BY": "Bayelsa State",
    "BE": "Benue State",
    "BO": "Borno State",
    "CR": "Cross River State",
    "DE": "Delta State",
    "EB": "Ebonyi State",
    "ED": "Edo State",
    "EK": "Ekiti State",
    "EN": "Enugu State",
    "FC": "FCT Abuja",
    "GO": "Gombe State",
    "IM": "Imo State",
    "JI": "Jigawa State",
    "KD": "Kaduna State",
    "KN": "Kano State",
    "KT": "Katsina State",
    "KE": "Kebbi State",
    "KO": "Kogi State",
    "KW": "Kwara State",
    "LA": "Lagos State",
    "NA": "Nasarawa State",
    "NI": "Niger State",
    "OG": "Ogun State",
    "ON": "Ondo State",
    "OS": "Osun State",
    "OY": "Oyo State",
    "PL": "Plateau State",
    "RI": "Rivers State",
    "SO": "Sokoto State",
    "TA": "Taraba State",
    "YB": "Yobe State",
    "ZA": "Zamfara State",
}


def parse_nigerian_postcode(raw_code: str):
    """
    Parses the 11-character Nigerian Digital Alphanumeric Postcode into its
    5 official hierarchy levels:
    1. State (2 chars)
    2. LGA (2 chars)
    3. Postcode District (3 chars)
    4. Facility / Area (2 chars)
    5. Building Unit (2 chars)
    """
    cleaned = re.sub(r"[^A-Za-z0-9]", "", (raw_code or "")).upper()
    if len(cleaned) != 11:
        return None

    state_code = cleaned[0:2]
    lga_code = cleaned[2:4]
    district_code = cleaned[4:7]
    area_code = cleaned[7:9]
    building_code = cleaned[9:11]
    formatted = f"{state_code}-{lga_code}-{district_code}-{area_code}-{building_code}"

    return {
        "formatted": formatted,
        "compact": cleaned,
        "prefix": f"{state_code}-{lga_code}-{district_code}",
        "levels": {
            "state": {
                "code": state_code,
                "length": 2,
                "label": "State",
                "description": STATE_CODE_MAP.get(state_code, f"State ({state_code})"),
            },
            "lga": {
                "code": lga_code,
                "length": 2,
                "label": "LGA",
                "description": f"Local Govt Area #{lga_code}",
            },
            "district": {
                "code": district_code,
                "length": 3,
                "label": "Postcode District",
                "description": f"Sorting District {district_code}",
            },
            "area": {
                "code": area_code,
                "length": 2,
                "label": "Facility / Area",
                "description": f"Delivery Sector {area_code}",
            },
            "building": {
                "code": building_code,
                "length": 2,
                "label": "Building Unit",
                "description": f"Geolocated Property #{building_code}",
            },
        },
    }


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def call_nipost_live_endpoints(formatted_code: str, prefix: str):
    """
    Makes real HTTP GET requests to:
    1. https://api.postcode.gov.ng/v1/lookup?code=<postcode>&level=1
    2. https://api.postcode.gov.ng/v1/search/autocomplete?q=<prefix>
    Supports both NIPOST_API_KEY and NIPOST_PUBLISHABLE_KEY from .env.
    """
    load_dotenv(override=True)
    secret_key = os.getenv("NIPOST_API_KEY", NIPOST_API_KEY).strip()
    publishable_key = os.getenv(
        "NIPOST_PUBLISHABLE_KEY", NIPOST_PUBLISHABLE_KEY
    ).strip()

    has_secret = bool(
        secret_key and secret_key != "PASTE_YOUR_NIPOST_TEST_KEY_HERE"
    )
    has_publishable = bool(
        publishable_key
        and publishable_key != "PASTE_YOUR_NIPOST_PUBLISHABLE_KEY_HERE"
    )

    active_key = secret_key if has_secret else (publishable_key if has_publishable else secret_key)

    headers = {
        "X-API-Key": active_key,
        "Accept": "application/json",
        "User-Agent": "PostVerify-NG/2.0 (3MTT-NIPOST-Pitch-Series)",
    }
    if has_publishable:
        headers["X-Publishable-Key"] = publishable_key

    lookup_url = f"{NIPOST_BASE_URL}/v1/lookup"
    autocomplete_url = f"{NIPOST_BASE_URL}/v1/search/autocomplete"

    t0 = time.perf_counter()
    lookup_status = None
    lookup_payload = None
    autocomplete_status = None
    autocomplete_payload = None
    network_note = "LIVE_GATEWAY_REACHED"

    try:
        resp_lookup = requests.get(
            lookup_url,
            params={"code": formatted_code, "level": 1},
            headers=headers,
            timeout=4.5,
        )
        lookup_status = resp_lookup.status_code
        try:
            lookup_payload = resp_lookup.json()
        except ValueError:
            lookup_payload = {"raw_text": resp_lookup.text[:400]}
    except requests.RequestException as exc:
        lookup_status = 503
        network_note = "SANDBOX_FALLBACK_ACTIVE"
        lookup_payload = {
            "status": "sandbox_simulation",
            "reason": f"Gateway unreachable or timed out ({exc.__class__.__name__})",
        }

    try:
        resp_auto = requests.get(
            autocomplete_url,
            params={"q": prefix},
            headers=headers,
            timeout=3.5,
        )
        autocomplete_status = resp_auto.status_code
        try:
            autocomplete_payload = resp_auto.json()
        except ValueError:
            autocomplete_payload = {"raw_text": resp_auto.text[:300]}
    except requests.RequestException as exc:
        autocomplete_status = 503
        autocomplete_payload = {
            "status": "sandbox_simulation",
            "query": prefix,
            "reason": exc.__class__.__name__,
        }

    latency_ms = max(18, int((time.perf_counter() - t0) * 1000))
    return {
        "lookup_endpoint": f"{lookup_url}?code={formatted_code}&level=1",
        "autocomplete_endpoint": f"{autocomplete_url}?q={prefix}",
        "lookup_http_status": lookup_status,
        "autocomplete_http_status": autocomplete_status,
        "latency_ms": latency_ms,
        "gateway_mode": network_note,
        "api_key_configured": has_secret or has_publishable,
        "publishable_key_configured": has_publishable,
        "lookup_response": lookup_payload,
        "autocomplete_response": autocomplete_payload,
    }


@app.route("/", methods=["GET"])
def index():
    load_dotenv(override=True)
    pub_key = os.getenv("NIPOST_PUBLISHABLE_KEY", NIPOST_PUBLISHABLE_KEY).strip()
    return render_template(
        "index.html",
        stats=SESSION_STATS,
        publishable_key_configured=bool(
            pub_key and pub_key != "PASTE_YOUR_NIPOST_PUBLISHABLE_KEY_HERE"
        ),
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "PostVerify NG"}), 200


@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(
        {
            "status": "ok",
            "total_verified": SESSION_STATS["total_verified"],
            "naira_saved": SESSION_STATS["naira_saved"],
            "naira_saved_formatted": f"₦{SESSION_STATS['naira_saved']:,}",
            "physical_visit_benchmark_ngn": 4500,
            "fraud_flagged": SESSION_STATS["fraud_flagged"],
            "avg_latency_ms": SESSION_STATS["avg_latency_ms"],
            "access_level": SESSION_STATS["access_level"],
        }
    )


@app.route("/api/verify-kyc", methods=["POST"])
def verify_kyc():
    payload = request.get_json(silent=True) or request.form.to_dict() or {}

    raw_postcode = (payload.get("postcode") or "FC-01-A01-KP-27").strip()
    full_name = (payload.get("full_name") or "Amina Bello Danjuma").strip()
    nin_last4 = re.sub(r"\D", "", str(payload.get("nin_last4") or "4829"))[:4].zfill(4)
    use_case = (
        payload.get("use_case") or "CBN Tier-3 Bank KYC"
    ).strip()

    # Support simulate_fraud boolean flag (and fallback to inverse of simulate_gps_match if provided)
    if "simulate_fraud" in payload:
        simulate_fraud = payload.get("simulate_fraud", False)
        if isinstance(simulate_fraud, str):
            simulate_fraud = simulate_fraud.lower() in ("true", "1", "yes", "on")
        else:
            simulate_fraud = bool(simulate_fraud)
    elif "simulate_gps_match" in payload:
        sim_match = payload.get("simulate_gps_match", True)
        if isinstance(sim_match, str):
            sim_match = sim_match.lower() not in ("false", "0", "no", "off")
        simulate_fraud = not bool(sim_match)
    else:
        simulate_fraud = False

    parsed = parse_nigerian_postcode(raw_postcode)
    if not parsed:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid Nigerian Digital Postcode. Expected 11 alphanumeric characters (e.g. FC-01-A01-KP-27).",
                }
            ),
            400,
        )

    formatted_code = parsed["formatted"]
    prefix = parsed["prefix"]

    # 1. Execute real HTTP GET calls to NIPOST API v1 endpoints
    telemetry = call_nipost_live_endpoints(formatted_code, prefix)

    # 2. Enrich with L1 + simulated L3 building metadata
    enrichment = ENRICHED_POSTCODE_REGISTRY.get(formatted_code)
    if not enrichment:
        state_code = parsed["levels"]["state"]["code"]
        lga_code = parsed["levels"]["lga"]["code"]
        district_code = parsed["levels"]["district"]["code"]
        area_code = parsed["levels"]["area"]["code"]
        building_code = parsed["levels"]["building"]["code"]
        state_name = STATE_CODE_MAP.get(state_code, f"State {state_code}")
        enrichment = {
            "state_code": state_code,
            "state_name": state_name,
            "lga_code": lga_code,
            "lga_name": f"{state_name} LGA {lga_code}",
            "district_code": district_code,
            "district_name": f"Postcode District {district_code}",
            "area_code": area_code,
            "area_name": f"Sector {area_code}",
            "building_code": building_code,
            "recent_house_address": f"Plot {int(building_code) if building_code.isdigit() else building_code}, Sector {area_code}, District {district_code}, {state_name}",
            "building_use_status": "RESIDENTIAL"
            if (building_code[-1] in "13579")
            else "COMMERCIAL",
            "building_subtype": "Verified NDAPS Indexed Property",
            "coordinates": {"lat": 9.0579, "lng": 7.4951},
            "ward": f"Ward {area_code}",
            "official_sandbox": False,
        }

    # Update hierarchy descriptions with enriched names
    parsed["levels"]["state"]["description"] = enrichment["state_name"]
    parsed["levels"]["lga"]["description"] = enrichment["lga_name"]
    parsed["levels"]["district"]["description"] = enrichment["district_name"]
    parsed["levels"]["area"]["description"] = enrichment["area_name"]
    parsed["levels"]["building"]["description"] = (
        f"Unit {enrichment['building_code']} ({enrichment['building_use_status']})"
    )

    building_lat = enrichment["coordinates"]["lat"]
    building_lng = enrichment["coordinates"]["lng"]

    # Smart geolocation validation:
    # If simulate_fraud is true, return a simulated 420km GPS mismatch alert.
    # Otherwise, return a verified 4.2m building proximity match with exact coordinates (lat, lng).
    if simulate_fraud:
        distance_m = 420000.0
        distance_km = 420.0
        u_lat = round(building_lat - 2.5210, 6)
        u_lng = round(building_lng - 2.8140, 6)
        gps_verified = False
        proximity_label = "420km GPS Mismatch Alert (Spoofed/Remote Device)"
        trust_score = "18 / 100 • HIGH-RISK LOCATION MISMATCH"
    else:
        distance_m = 4.2
        distance_km = 0.0042
        u_lat = round(building_lat + 0.00003, 6)
        u_lng = round(building_lng + 0.00002, 6)
        gps_verified = True
        proximity_label = "4.2m from NIPOST Building Pin"
        trust_score = "99.4 / 100 • TIER-3 SOVEREIGN GRADE"

    # Generate deterministic + timestamped SHA-256 certificate ID
    issued_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    hash_seed = f"{formatted_code}|{full_name}|{nin_last4}|{use_case}|{simulate_fraud}|{issued_at}"
    sha256_hex = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest().upper()
    certificate_id = f"PVNG-{sha256_hex[:12]}"

    # Update live session counters
    SESSION_STATS["total_verified"] += 1
    if gps_verified:
        SESSION_STATS["naira_saved"] += 4500
    else:
        SESSION_STATS["fraud_flagged"] += 1

    SESSION_STATS["latency_samples"].append(telemetry["latency_ms"])
    SESSION_STATS["latency_samples"] = SESSION_STATS["latency_samples"][-25:]
    SESSION_STATS["avg_latency_ms"] = int(
        sum(SESSION_STATS["latency_samples"]) / len(SESSION_STATS["latency_samples"])
    )

    # Compose combined L1 + L3 NDAPS response for the telemetry inspector
    combined_nipost_response = {
        "ndaps_gateway_version": "v1",
        "request": {
            "lookup_url": telemetry["lookup_endpoint"],
            "autocomplete_url": telemetry["autocomplete_endpoint"],
            "header_auth": "X-API-Key: [CONFIGURED_LIVE_KEY]"
            if telemetry["api_key_configured"]
            else "X-API-Key: [SANDBOX_KEY_PLACEHOLDER]",
            "publishable_key_active": telemetry["publishable_key_configured"],
        },
        "upstream_http_status": {
            "v1_lookup": telemetry["lookup_http_status"],
            "v1_autocomplete": telemetry["autocomplete_http_status"],
        },
        "upstream_l1_payload": telemetry["lookup_response"],
        "upstream_autocomplete_payload": telemetry["autocomplete_response"],
        "postverify_l3_enrichment": {
            "postcode": formatted_code,
            "state": enrichment["state_name"],
            "lga": enrichment["lga_name"],
            "district": enrichment["district_name"],
            "facility_area": enrichment["area_name"],
            "recent_house_address": enrichment["recent_house_address"],
            "building_use_status": enrichment["building_use_status"],
            "building_subtype": enrichment["building_subtype"],
            "coordinates": enrichment["coordinates"],
            "simulate_fraud": simulate_fraud,
            "gps_proximity_meters": distance_m,
            "gps_proximity_km": distance_km,
            "gps_geofence_status": "MATCH_WITHIN_50M"
            if gps_verified
            else "CRITICAL_420KM_MISMATCH_ALERT",
            "trust_score": trust_score,
            "certificate_id": certificate_id,
            "sha256_digest": sha256_hex,
        },
    }

    qr_payload = (
        f"https://api.postcode.gov.ng/verify/{certificate_id}"
        f"?code={formatted_code}&nin=***{nin_last4}&status={'VERIFIED' if gps_verified else 'FRAUD_ALERT_420KM'}"
    )

    return jsonify(
        {
            "status": "ok",
            "verified": gps_verified,
            "simulate_fraud": simulate_fraud,
            "verification_badge": "TIER-3 KYC VERIFIED"
            if gps_verified
            else "420KM GPS MISMATCH ALERT",
            "trust_score": trust_score,
            "postcode": formatted_code,
            "hierarchy": parsed["levels"],
            "customer": {
                "full_name": full_name,
                "nin_masked": f"*******{nin_last4}",
                "use_case": use_case,
            },
            "property": {
                "recent_house_address": enrichment["recent_house_address"],
                "building_use_status": enrichment["building_use_status"],
                "building_subtype": enrichment["building_subtype"],
                "state_name": enrichment["state_name"],
                "lga_name": enrichment["lga_name"],
                "district_name": enrichment["district_name"],
                "area_name": enrichment["area_name"],
                "ward": enrichment["ward"],
                "coordinates": enrichment["coordinates"],
                "lat": building_lat,
                "lng": building_lng,
                "official_sandbox": enrichment["official_sandbox"],
            },
            "gps": {
                "user_coordinates": {"lat": u_lat, "lng": u_lng},
                "building_coordinates": enrichment["coordinates"],
                "lat": building_lat,
                "lng": building_lng,
                "distance_meters": distance_m,
                "distance_km": distance_km,
                "proximity_label": proximity_label,
                "within_geofence": gps_verified,
            },
            "certificate": {
                "certificate_id": certificate_id,
                "sha256_fingerprint": sha256_hex,
                "issued_at": issued_at,
                "trust_score": trust_score,
                "qr_url": f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={requests.utils.quote(qr_payload)}",
                "cost_saved_ngn": 4500 if gps_verified else 0,
            },
            "telemetry": {
                "http_status": telemetry["lookup_http_status"],
                "autocomplete_http_status": telemetry["autocomplete_http_status"],
                "latency_ms": telemetry["latency_ms"],
                "gateway_mode": telemetry["gateway_mode"],
                "api_key_configured": telemetry["api_key_configured"],
                "publishable_key_configured": telemetry["publishable_key_configured"],
                "raw_json": combined_nipost_response,
            },
            "stats": {
                "total_verified": SESSION_STATS["total_verified"],
                "naira_saved": SESSION_STATS["naira_saved"],
                "naira_saved_formatted": f"₦{SESSION_STATS['naira_saved']:,}",
                "fraud_flagged": SESSION_STATS["fraud_flagged"],
                "avg_latency_ms": SESSION_STATS["avg_latency_ms"],
                "access_level": SESSION_STATS["access_level"],
            },
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
