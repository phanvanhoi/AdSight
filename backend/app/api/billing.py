from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.momo import create_momo_payment, verify_momo_signature
from app.core.vnpay import create_vnpay_payment_url, verify_vnpay_response
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

stripe.api_key = settings.stripe_secret_key

PLAN_PRICES_VND = {
    "pro": 699000,
    "agency": 1899000,
}


@router.post("/create-checkout-session")
async def create_checkout_session(
    plan: str,  # "pro" or "agency"
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tạo Stripe Checkout session để user thanh toán."""
    price_map = {
        "pro": settings.stripe_price_pro_monthly,
        "agency": settings.stripe_price_agency_monthly,
    }
    if plan not in price_map:
        raise HTTPException(400, "Invalid plan")

    # Create or retrieve Stripe customer
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": str(user.id)},
        )
        user.stripe_customer_id = customer.id
        await db.commit()

    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_map[plan], "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.cors_origins[0]}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.cors_origins[0]}/pricing",
        metadata={"user_id": str(user.id), "plan": plan},
    )

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/create-portal-session")
async def create_portal_session(
    user: User = Depends(get_current_user),
):
    """Tạo Stripe Customer Portal session để user quản lý subscription."""
    if not user.stripe_customer_id:
        raise HTTPException(400, "Chưa có subscription")

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.cors_origins[0]}/settings",
    )
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Xử lý Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await _handle_checkout_completed(session, db)

    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await _handle_subscription_updated(subscription, db)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await _handle_subscription_deleted(subscription, db)

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        await _handle_payment_failed(invoice, db)

    return {"status": "ok"}


async def _handle_checkout_completed(session: dict, db: AsyncSession):
    """User hoàn tất thanh toán."""
    plan = session["metadata"].get("plan", "pro")

    user = (await db.execute(
        select(User).where(User.stripe_customer_id == session["customer"])
    )).scalar_one_or_none()

    if user:
        user.tier = plan
        user.stripe_subscription_id = session.get("subscription")
        user.payment_method = "stripe"
        user.subscription_status = "active"
        # Reset AI credits on upgrade
        user.ai_credits_used = 0
        user.ai_credits_reset = None
        await db.commit()


async def _handle_subscription_updated(subscription: dict, db: AsyncSession):
    """Subscription thay đổi (upgrade/downgrade)."""
    user = (await db.execute(
        select(User).where(User.stripe_customer_id == subscription["customer"])
    )).scalar_one_or_none()

    if user:
        user.subscription_status = subscription["status"]
        # Map Stripe price → tier
        price_id = subscription["items"]["data"][0]["price"]["id"]
        if price_id == settings.stripe_price_agency_monthly:
            user.tier = "agency"
        elif price_id == settings.stripe_price_pro_monthly:
            user.tier = "pro"
        await db.commit()


async def _handle_subscription_deleted(subscription: dict, db: AsyncSession):
    """Subscription bị hủy → downgrade về free."""
    user = (await db.execute(
        select(User).where(User.stripe_customer_id == subscription["customer"])
    )).scalar_one_or_none()

    if user:
        user.tier = "free"
        user.subscription_status = "canceled"
        user.stripe_subscription_id = None
        await db.commit()


async def _handle_payment_failed(invoice: dict, db: AsyncSession):
    """Thanh toán thất bại → đánh dấu past_due."""
    user = (await db.execute(
        select(User).where(User.stripe_customer_id == invoice["customer"])
    )).scalar_one_or_none()

    if user:
        user.subscription_status = "past_due"
        await db.commit()


# ---------------------------------------------------------------------------
# VNPay endpoints
# ---------------------------------------------------------------------------


@router.post("/vnpay/create")
async def create_vnpay_session(
    plan: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tạo VNPay payment URL."""
    if plan not in PLAN_PRICES_VND:
        raise HTTPException(400, "Invalid plan")

    order_id = f"adsight_{user.id}_{plan}_{int(datetime.now(timezone.utc).timestamp())}"
    amount = PLAN_PRICES_VND[plan]
    order_info = f"Nang cap AdSight {plan.capitalize()} - {user.email}"
    ip_addr = request.client.host if request.client else "127.0.0.1"

    payment_url = create_vnpay_payment_url(order_id, amount, order_info, ip_addr)
    return {"payment_url": payment_url, "order_id": order_id}


@router.get("/vnpay/return")
async def vnpay_return(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """VNPay redirect callback sau thanh toán."""
    params = dict(request.query_params)

    if not verify_vnpay_response(params.copy()):
        raise HTTPException(400, "Invalid VNPay signature")

    response_code = params.get("vnp_ResponseCode")
    order_id = params.get("vnp_TxnRef", "")

    plan = "unknown"
    if response_code == "00":  # Thành công
        # Parse order_id: adsight_{user_id}_{plan}_{timestamp}
        parts = order_id.split("_")
        if len(parts) >= 4:
            user_id = parts[1]
            plan = parts[2]
            user = (await db.execute(
                select(User).where(User.id == user_id)
            )).scalar_one_or_none()
            if user:
                user.tier = plan
                user.payment_method = "vnpay"
                user.subscription_status = "active"
                user.subscription_end = datetime.now(timezone.utc) + timedelta(days=30)
                user.ai_credits_used = 0
                user.ai_credits_reset = None
                await db.commit()

        return {"status": "success", "plan": plan if len(parts) >= 4 else "unknown"}
    else:
        return {"status": "failed", "code": response_code}


# ---------------------------------------------------------------------------
# MoMo endpoints
# ---------------------------------------------------------------------------


@router.post("/momo/create")
async def create_momo_session(
    plan: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tạo MoMo payment."""
    if plan not in PLAN_PRICES_VND:
        raise HTTPException(400, "Invalid plan")

    order_id = f"adsight_{user.id}_{plan}_{int(datetime.now(timezone.utc).timestamp())}"
    amount = PLAN_PRICES_VND[plan]
    order_info = f"Nang cap AdSight {plan.capitalize()}"

    result = await create_momo_payment(order_id, amount, order_info)
    return result


@router.post("/momo/ipn")
async def momo_ipn(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """MoMo IPN (Instant Payment Notification) callback."""
    data = await request.json()

    if not verify_momo_signature(data):
        raise HTTPException(400, "Invalid MoMo signature")

    if data.get("resultCode") == 0:  # Thành công
        order_id = data.get("orderId", "")
        parts = order_id.split("_")
        if len(parts) >= 4:
            user_id = parts[1]
            plan = parts[2]
            user = (await db.execute(
                select(User).where(User.id == user_id)
            )).scalar_one_or_none()
            if user:
                user.tier = plan
                user.payment_method = "momo"
                user.subscription_status = "active"
                user.subscription_end = datetime.now(timezone.utc) + timedelta(days=30)
                user.ai_credits_used = 0
                user.ai_credits_reset = None
                await db.commit()

    return {"status": "ok"}
