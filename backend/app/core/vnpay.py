import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone

from app.config import settings


def create_vnpay_payment_url(
    order_id: str,
    amount: int,        # VND, integer (e.g. 699000)
    order_info: str,    # "Nâng cấp AdSight Pro"
    ip_addr: str,
) -> str:
    """Tạo VNPay payment URL để redirect user."""
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.vnpay_tmn_code,
        "vnp_Amount": str(amount * 100),  # VNPay tính theo đồng * 100
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_id,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "subscription",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": settings.vnpay_return_url,
        "vnp_IpAddr": ip_addr,
        "vnp_CreateDate": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }

    # Sort params alphabetically và tạo hash
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    hmac_hash = hmac.HMAC(
        settings.vnpay_hash_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return f"{settings.vnpay_url}?{query_string}&vnp_SecureHash={hmac_hash}"


def verify_vnpay_response(params: dict) -> bool:
    """Verify VNPay return/IPN params signature."""
    secure_hash = params.pop("vnp_SecureHash", "")
    params.pop("vnp_SecureHashType", None)

    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    expected_hash = hmac.HMAC(
        settings.vnpay_hash_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(secure_hash, expected_hash)
