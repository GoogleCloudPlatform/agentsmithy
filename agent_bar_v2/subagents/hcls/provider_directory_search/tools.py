# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Search tools for the Provider Directory Search agent.

Provides geospatial, text, and relational search across practitioners,
facilities, and organizations in the provider directory.
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Optional

from .data import PRACTITIONERS, FACILITIES, ORGANIZATIONS


# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------

def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _text_match(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


# ---------------------------------------------------------------------------
# Index helpers — build once at import time
# ---------------------------------------------------------------------------

_org_by_id: dict[str, dict] = {o["id"]: o for o in ORGANIZATIONS}
_fac_by_id: dict[str, dict] = {f["id"]: f for f in FACILITIES}
_prac_by_npi: dict[str, dict] = {p["npi"]: p for p in PRACTITIONERS}
_org_by_npi: dict[str, dict] = {o["npi"]: o for o in ORGANIZATIONS}
_fac_by_npi: dict[str, dict] = {f["npi"]: f for f in FACILITIES}


def _format_practitioner(p: dict, distance: Optional[float] = None) -> dict:
    name = f"{p['prefix']} {p['first_name']} {p['last_name']}".strip()
    orgs = [_org_by_id[oid]["name"] for oid in p.get("organization_ids", []) if oid in _org_by_id]
    facs = [_fac_by_id[fid]["name"] for fid in p.get("facility_ids", []) if fid in _fac_by_id]
    result = {
        "npi": p["npi"],
        "name": name,
        "credentials": p["credentials"],
        "specialty": p["specialty"],
        "subspecialties": p.get("subspecialties", []),
        "gender": p["gender"],
        "languages": p["languages"],
        "phone": p["phone"],
        "address": _format_address(p["address"]),
        "accepting_new_patients": p["accepting_new_patients"],
        "telehealth_available": p["telehealth_available"],
        "organizations": orgs,
        "facilities": facs,
    }
    if distance is not None:
        result["distance_miles"] = round(distance, 1)
    return result


def _format_facility(f: dict, distance: Optional[float] = None) -> dict:
    org_name = _org_by_id.get(f.get("organization_id", ""), {}).get("name", "")
    result = {
        "id": f["id"],
        "npi": f["npi"],
        "name": f["name"],
        "type": f["type"],
        "organization": org_name,
        "phone": f["phone"],
        "address": _format_address(f["address"]),
        "services": f.get("services", []),
        "hours": f.get("hours", ""),
    }
    if distance is not None:
        result["distance_miles"] = round(distance, 1)
    return result


def _format_organization(o: dict) -> dict:
    facs = [f["name"] for f in FACILITIES if f.get("organization_id") == o["id"]]
    return {
        "id": o["id"],
        "npi": o["npi"],
        "name": o["name"],
        "type": o["type"],
        "phone": o["phone"],
        "address": _format_address(o["address"]),
        "website": o.get("website", ""),
        "facilities": facs,
    }


def _format_address(addr: dict) -> str:
    return f"{addr['street']}, {addr['city']}, {addr['state']} {addr['zip']}"


# ---------------------------------------------------------------------------
# Public tool functions — exposed to the agent
# ---------------------------------------------------------------------------

def search_practitioners(
    name: str = "",
    specialty: str = "",
    city: str = "",
    zip_code: str = "",
    accepting_new_patients: Optional[bool] = None,
    telehealth_available: Optional[bool] = None,
    language: str = "",
    gender: str = "",
) -> dict:
    """Search for practitioners (doctors, NPs, PAs) in the provider directory.

    All filter parameters are optional and combined with AND logic.
    Returns matching practitioners with their details.

    Args:
        name: Full or partial name to search (e.g. "Chen" or "Sarah Chen").
        specialty: Medical specialty (e.g. "Cardiology", "Family Medicine", "Pediatrics").
        city: City name (e.g. "Houston", "Katy", "Sugar Land").
        zip_code: ZIP code (e.g. "77030").
        accepting_new_patients: If True, only show providers accepting new patients.
        telehealth_available: If True, only show providers offering telehealth.
        language: Language spoken (e.g. "Spanish", "Mandarin").
        gender: Provider gender ("Male" or "Female").

    Returns:
        A dict with "count" and "results" (list of matching practitioners).
    """
    try:
        results = []
        for p in PRACTITIONERS:
            full_name = f"{p['first_name']} {p['last_name']}"
            if name and not _text_match(full_name, name):
                continue
            if specialty and not _text_match(p["specialty"], specialty):
                if not any(_text_match(s, specialty) for s in p.get("subspecialties", [])):
                    continue
            if city and not _text_match(p["address"]["city"], city):
                continue
            if zip_code and p["address"]["zip"] != zip_code:
                continue
            if accepting_new_patients is not None and p["accepting_new_patients"] != accepting_new_patients:
                continue
            if telehealth_available is not None and p["telehealth_available"] != telehealth_available:
                continue
            if language and not any(_text_match(lang, language) for lang in p["languages"]):
                continue
            if gender and not _text_match(p["gender"], gender):
                continue
            results.append(_format_practitioner(p))
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Error in search_practitioners: {e}" }


def find_nearby_practitioners(
    latitude: float,
    longitude: float,
    radius_miles: float = 10.0,
    specialty: str = "",
    accepting_new_patients: Optional[bool] = None,
) -> dict:
    """Find practitioners near a geographic location.

    Searches by latitude/longitude within a given radius. Useful when the
    user provides an address or says "near me".

    Args:
        latitude: Latitude of the search center (e.g. 29.7604 for downtown Houston).
        longitude: Longitude of the search center (e.g. -95.3698 for downtown Houston).
        radius_miles: Search radius in miles (default 10).
        specialty: Optional specialty filter.
        accepting_new_patients: Optional filter for new-patient availability.

    Returns:
        A dict with "count" and "results" sorted by distance.
    """
    try:
        results = []
        for p in PRACTITIONERS:
            if specialty and not _text_match(p["specialty"], specialty):
                if not any(_text_match(s, specialty) for s in p.get("subspecialties", [])):
                    continue
            if accepting_new_patients is not None and p["accepting_new_patients"] != accepting_new_patients:
                continue
            dist = _haversine_miles(latitude, longitude, p["address"]["latitude"], p["address"]["longitude"])
            if dist <= radius_miles:
                results.append(_format_practitioner(p, distance=dist))
        results.sort(key=lambda r: r["distance_miles"])
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Error in find_nearby_practitioners: {e}" }


def search_facilities(
    name: str = "",
    facility_type: str = "",
    city: str = "",
    zip_code: str = "",
    service: str = "",
) -> dict:
    """Search for healthcare facilities (hospitals, clinics, urgent care centers, etc.).

    All filter parameters are optional and combined with AND logic.

    Args:
        name: Full or partial facility name.
        facility_type: Type of facility (e.g. "hospital", "clinic", "urgent_care",
            "community_health_center", "pediatric_clinic", "womens_health_clinic").
        city: City name.
        zip_code: ZIP code.
        service: A service offered (e.g. "emergency", "cardiology", "dental",
            "primary_care", "laboratory", "imaging").

    Returns:
        A dict with "count" and "results" (list of matching facilities).
    """
    try:
        results = []
        for f in FACILITIES:
            if name and not _text_match(f["name"], name):
                continue
            if facility_type and not _text_match(f["type"], facility_type):
                continue
            if city and not _text_match(f["address"]["city"], city):
                continue
            if zip_code and f["address"]["zip"] != zip_code:
                continue
            if service and not any(_text_match(s, service) for s in f.get("services", [])):
                continue
            results.append(_format_facility(f))
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Error in search_facilities: {e}" }


def find_nearby_facilities(
    latitude: float,
    longitude: float,
    radius_miles: float = 10.0,
    facility_type: str = "",
    service: str = "",
) -> dict:
    """Find healthcare facilities near a geographic location.

    Args:
        latitude: Latitude of the search center.
        longitude: Longitude of the search center.
        radius_miles: Search radius in miles (default 10).
        facility_type: Optional type filter (e.g. "hospital", "urgent_care").
        service: Optional service filter (e.g. "emergency", "laboratory").

    Returns:
        A dict with "count" and "results" sorted by distance.
    """
    try:
        results = []
        for f in FACILITIES:
            if facility_type and not _text_match(f["type"], facility_type):
                continue
            if service and not any(_text_match(s, service) for s in f.get("services", [])):
                continue
            dist = _haversine_miles(latitude, longitude, f["address"]["latitude"], f["address"]["longitude"])
            if dist <= radius_miles:
                results.append(_format_facility(f, distance=dist))
        results.sort(key=lambda r: r["distance_miles"])
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Error in find_nearby_facilities: {e}" }


def search_organizations(
    name: str = "",
    organization_type: str = "",
    city: str = "",
) -> dict:
    """Search for healthcare organizations (hospital systems, medical groups, etc.).

    Args:
        name: Full or partial organization name.
        organization_type: Type of organization (e.g. "hospital_system",
            "medical_group", "community_health_center", "specialty_group").
        city: City where the organization is headquartered.

    Returns:
        A dict with "count" and "results" including affiliated facilities.
    """
    try:
        results = []
        for o in ORGANIZATIONS:
            if name and not _text_match(o["name"], name):
                continue
            if organization_type and not _text_match(o["type"], organization_type):
                continue
            if city and not _text_match(o["address"]["city"], city):
                continue
            results.append(_format_organization(o))
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Error in search_organizations: {e}" }


def get_provider_details(npi: str) -> dict:
    """Get full details for a specific provider, facility, or organization by NPI number.

    The NPI (National Provider Identifier) is a unique 10-digit number assigned
    to healthcare providers. Use this tool when you have a specific NPI and want
    complete details.

    Args:
        npi: The 10-digit NPI number.

    Returns:
        Full details for the entity, or an error message if not found.
    """
    try:
        if npi in _prac_by_npi:
            return {"type": "practitioner", "details": _format_practitioner(_prac_by_npi[npi])}
        if npi in _fac_by_npi:
            return {"type": "facility", "details": _format_facility(_fac_by_npi[npi])}
        if npi in _org_by_npi:
            return {"type": "organization", "details": _format_organization(_org_by_npi[npi])}
        return {"error": f"No provider found with NPI {npi}"}
    except Exception as e:
        return {"status": "error", "message": f"Error in get_provider_details: {e}" }


def find_practitioners_at_facility(facility_name: str) -> dict:
    """Find all practitioners who practice at a given facility.

    Useful for answering questions like "Who are the doctors at Memorial Hermann?"
    or "What specialists are available at Houston Methodist?"

    Args:
        facility_name: Full or partial facility name.

    Returns:
        Matching facility info and the practitioners who practice there.
    """
    try:
        matching_facilities = [f for f in FACILITIES if _text_match(f["name"], facility_name)]
        if not matching_facilities:
            return {"error": f"No facility found matching '{facility_name}'", "results": []}

        all_results = []
        for fac in matching_facilities:
            practitioners = [
                _format_practitioner(p)
                for p in PRACTITIONERS
                if fac["id"] in p.get("facility_ids", [])
            ]
            all_results.append({
                "facility": _format_facility(fac),
                "practitioner_count": len(practitioners),
                "practitioners": practitioners,
            })
        return {"count": len(all_results), "results": all_results}
    except Exception as e:
        return {"status": "error", "message": f"Error in find_practitioners_at_facility: {e}" }


def find_practitioners_in_organization(organization_name: str) -> dict:
    """Find all practitioners affiliated with a given organization.

    Useful for answering questions like "Who are the doctors in the Lone Star
    Medical Group?" or "List providers at Gulf Coast Community Health."

    Args:
        organization_name: Full or partial organization name.

    Returns:
        Matching organization info and affiliated practitioners.
    """
    try:
        matching_orgs = [o for o in ORGANIZATIONS if _text_match(o["name"], organization_name)]
        if not matching_orgs:
            return {"error": f"No organization found matching '{organization_name}'", "results": []}

        all_results = []
        for org in matching_orgs:
            practitioners = [
                _format_practitioner(p)
                for p in PRACTITIONERS
                if org["id"] in p.get("organization_ids", [])
            ]
            all_results.append({
                "organization": _format_organization(org),
                "practitioner_count": len(practitioners),
                "practitioners": practitioners,
            })
        return {"count": len(all_results), "results": all_results}
    except Exception as e:
        return {"status": "error", "message": f"Error in find_practitioners_in_organization: {e}" }


tools = [
    search_practitioners,
    find_nearby_practitioners,
    search_facilities,
    find_nearby_facilities,
    search_organizations,
    get_provider_details,
    find_practitioners_at_facility,
    find_practitioners_in_organization,
]
