import json
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, Query

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.user_profile import UserProfilePayload, UserProfileResponse
from app.services.reply_templates import as_payload as reply_templates
from app.services.user_profile import UserProfileService


router = APIRouter(prefix="/settings", tags=["user-profile"])

service = UserProfileService()


@router.get("/profile", response_model=UserProfileResponse)
def read_profile(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        return service.get(conn, user_id)


@router.put("/profile", response_model=UserProfileResponse)
def write_profile(
    payload: UserProfilePayload,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        return service.save(conn, user_id, payload)


@router.get("/reply-templates")
def list_reply_templates():
    """Ready-made rule text; the user still edits whatever they pick."""
    return {"templates": reply_templates()}


@router.get("/location")
def describe_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """Turn the phone/browser GPS fix into a human readable place.

    Reverse geocoding is a convenience: if the public service is slow or
    unreachable the caller still gets the coordinates back, so "读不到地址"
    never blocks the user from saving their profile.
    """
    fallback = f"纬度 {lat:.4f}，经度 {lng:.4f}"
    short = _place_from_bigdatacloud(lat, lng) or _place_from_nominatim(lat, lng)
    return {"label": short or fallback, "fallback": not short}


def _fetch_json(url: str, timeout: float = 5.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "junshi-profile/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read(200_000).decode("utf-8"))


def _place_from_bigdatacloud(lat: float, lng: float) -> str:
    """Free, key-less reverse geocoder; the only one reachable from the server.

    Nominatim is blocked from this host, so it stays as a second try.
    """
    query = urllib.parse.urlencode(
        {"latitude": f"{lat:.6f}", "longitude": f"{lng:.6f}", "localityLanguage": "zh"}
    )
    try:
        data = _fetch_json(f"https://api.bigdatacloud.net/data/reverse-geocode-client?{query}")
    except Exception:
        return ""
    province = str(data.get("principalSubdivision") or "").strip()
    city = str(data.get("city") or "").strip()
    district = str(data.get("locality") or "").strip()
    parts = []
    for part in (province, city, district):
        if part and part not in parts:
            parts.append(part)
    # 只要最细的三级，再往上是国家，用户不需要。
    return "".join(parts[:3])


def _place_from_nominatim(lat: float, lng: float) -> str:
    query = urllib.parse.urlencode(
        {"format": "jsonv2", "zoom": "14", "accept-language": "zh-CN", "lat": lat, "lon": lng}
    )
    try:
        data = _fetch_json(f"https://nominatim.openstreetmap.org/reverse?{query}", timeout=4)
    except Exception:
        return ""
    label = str(data.get("display_name") or "").strip()
    parts = [part.strip() for part in label.split(",") if part.strip()]
    return "".join(parts[:3])
