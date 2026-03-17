import hashlib
import hmac
import uuid

import httpx

from app.config import settings


async def create_momo_payment(
    order_id: str,
    amount: int,        # VND, integer
    order_info: str,    # "Nâng cấp AdSight Pro"
) -> dict:
    """Tạo MoMo payment request. Returns {"pay_url": "...", "order_id": "...", "request_id": "..."}."""
    request_id = str(uuid.uuid4())

    raw_signature = (
        f"accessKey={settings.momo_access_key}"
        f"&amount={amount}"
        f"&extraData="
        f"&ipnUrl={settings.momo_notify_url}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={settings.momo_partner_code}"
        f"&redirectUrl={settings.momo_return_url}"
        f"&requestId={request_id}"
        f"&requestType=payWithMethod"
    )

    signature = hmac.HMAC(
        settings.momo_secret_key.encode("utf-8"),
        raw_signature.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    payload = {
        "partnerCode": settings.momo_partner_code,
        "partnerName": "AdSight",
        "storeId": "AdSightStore",
        "requestId": request_id,
        "amount": amount,
        "orderId": order_id,
        "orderInfo": order_info,
        "redirectUrl": settings.momo_return_url,
        "ipnUrl": settings.momo_notify_url,
        "lang": "vi",
        "requestType": "payWithMethod",
        "extraData": "",
        "signature": signature,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.momo_endpoint}/create",
            json=payload,
            timeout=30,
        )
        data = resp.json()

    if data.get("resultCode") != 0:
        raise Exception(f"MoMo error: {data.get('message', 'Unknown error')}")

    return {"pay_url": data["payUrl"], "order_id": order_id, "request_id": request_id}


def verify_momo_signature(data: dict) -> bool:
    """Verify MoMo IPN callback signature."""
    received_sig = data.get("signature", "")

    raw = (
        f"accessKey={settings.momo_access_key}"
        f"&amount={data.get('amount', '')}"
        f"&extraData={data.get('extraData', '')}"
        f"&message={data.get('message', '')}"
        f"&orderId={data.get('orderId', '')}"
        f"&orderInfo={data.get('orderInfo', '')}"
        f"&orderType={data.get('orderType', '')}"
        f"&partnerCode={data.get('partnerCode', '')}"
        f"&payType={data.get('payType', '')}"
        f"&requestId={data.get('requestId', '')}"
        f"&responseTime={data.get('responseTime', '')}"
        f"&resultCode={data.get('resultCode', '')}"
        f"&transId={data.get('transId', '')}"
    )

    expected_sig = hmac.HMAC(
        settings.momo_secret_key.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(received_sig, expected_sig)
