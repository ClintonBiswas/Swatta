from django.core.signing import Signer, BadSignature

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



