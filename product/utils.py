from django.core.signing import Signer, BadSignature
import hashlib, uuid, time, requests
from django.conf import settings
import json

BANGLA_TO_ENGLISH_DIGIT = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
signer = Signer()

def normalize_phone(phone):
    """Convert Bangla digits to English and clean phone number"""
    if not phone:
        return ""
    phone = str(phone).translate(BANGLA_TO_ENGLISH_DIGIT)
    digits = ''.join(c for c in phone if c.isdigit())
    return digits[-11:] if digits else ""

def get_guest_phone_from_cookie(request):
    """Safely get and verify guest phone from cookie"""
    cookie_value = request.COOKIES.get('guest_phone')
    if not cookie_value:
        return None
    try:
        return signer.unsign(cookie_value)
    except BadSignature:
        return None
    


PIXEL_ID = settings.FACEBOOK_PIXEL_ID
ACCESS_TOKEN = settings.FACEBOOK_ACCESS_TOKEN
API_VERSION = settings.FACEBOOK_API_VERSION


def sha256_hash(value):
    if not value:
        return None
    s = str(value).strip().lower()
    return hashlib.sha256(s.encode()).hexdigest()

def hash_data(data):
    return hashlib.sha256(data.strip().lower().encode()).hexdigest() if data else None

def _ensure_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [v for v in val if v not in (None, "")]
    return [val]

def normalize_user_data(user_data):
    if isinstance(user_data, str):
        try:
            user_data = json.loads(user_data)
        except:
            user_data = {}
    if not isinstance(user_data, dict):
        user_data = {}

    normalized = {}
    for k, vals in user_data.items():
        if not vals:
            continue
        if k in ("em", "ph"):
            normalized[k] = [hash_data(v) for v in _ensure_list(vals) if v]
        elif k in ("fbc", "fbp", "fn", "client_ip_address", "client_user_agent", "external_id"):
            normalized[k] = _ensure_list(vals)
        else:
            normalized[k] = vals
    return normalized

def send_event(event_name, user_data=None, custom_data=None, test_event_code=None, event_id=None):
    event_id = event_id or str(uuid.uuid4())
    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "event_id": event_id,
            "action_source": "website",
            "user_data": normalize_user_data(user_data or {}),
            "custom_data": custom_data or {}
        }],
        "access_token": ACCESS_TOKEN
    }
    if test_event_code:
        payload["test_event_code"] = test_event_code

    try:
        r = requests.post(f"https://graph.facebook.com/{API_VERSION}/{PIXEL_ID}/events",
                          json=payload, timeout=6)
        r.raise_for_status()
    except Exception as e:
        print(f"[CAPI ERROR] {event_name} | event_id={event_id} | error={e}")
        print("payload:", payload)
    print(f"[CAPI SENT] {event_name} | event_id={event_id}")
    return event_id




