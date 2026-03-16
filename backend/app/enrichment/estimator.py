"""
Spend / Performance Estimator.

Computes estimated metrics from raw ad data:
- estimated_daily_spend, estimated_total_spend
- cpm_estimate
- engagement_rate
- viral_score (0-100)
- is_hot flag
"""

from datetime import datetime, timezone


def estimate_ad_metrics(ad_data: dict) -> dict:
    """
    Estimate spend and performance metrics for an ad.

    ad_data keys used:
        first_seen, last_seen, spend_lower, spend_upper,
        impressions_lower, impressions_upper,
        likes, comments, shares, platform

    Returns:
        {
            "estimated_daily_spend": float | None,
            "estimated_total_spend": float | None,
            "cpm_estimate": float | None,
            "engagement_rate": float | None,
            "viral_score": float,
            "is_hot": bool,
        }
    """
    result = {
        "estimated_daily_spend": None,
        "estimated_total_spend": None,
        "cpm_estimate": None,
        "engagement_rate": None,
        "viral_score": 0.0,
        "is_hot": False,
    }

    # --- Days running ---
    first_seen = _parse_dt(ad_data.get("first_seen"))
    last_seen = _parse_dt(ad_data.get("last_seen"))

    if first_seen and last_seen:
        days_running = max((last_seen - first_seen).days, 1)
    else:
        days_running = 1

    # --- Spend estimation ---
    spend_lower = ad_data.get("spend_lower")
    spend_upper = ad_data.get("spend_upper")

    if spend_lower is not None and spend_upper is not None:
        estimated_total = (spend_lower + spend_upper) / 2
        result["estimated_total_spend"] = round(estimated_total, 2)
        result["estimated_daily_spend"] = round(estimated_total / days_running, 2)

    # --- CPM estimation ---
    imp_lower = ad_data.get("impressions_lower")
    imp_upper = ad_data.get("impressions_upper")

    if (
        result["estimated_total_spend"] is not None
        and imp_lower is not None
        and imp_upper is not None
    ):
        impressions_mid = (imp_lower + imp_upper) / 2
        if impressions_mid > 0:
            result["cpm_estimate"] = round(
                result["estimated_total_spend"] / impressions_mid * 1000, 2
            )

    # --- Engagement ---
    likes = ad_data.get("likes") or 0
    comments = ad_data.get("comments") or 0
    shares = ad_data.get("shares") or 0
    total_engagement = likes + comments + shares

    platform = ad_data.get("platform", "")

    if imp_lower is not None and imp_upper is not None:
        impressions_mid = (imp_lower + imp_upper) / 2
        if impressions_mid > 0:
            result["engagement_rate"] = round(total_engagement / impressions_mid, 6)
    elif platform == "tiktok" and likes > 0:
        # TikTok heuristic: estimated impressions ≈ likes × 15
        estimated_impressions = likes * 15
        result["engagement_rate"] = round(total_engagement / estimated_impressions, 6)

    # --- Viral score (0-100) ---
    # Components: er_score (40%) + recency_score (30%) + engagement_abs_score (30%)
    er = result["engagement_rate"] or 0.0
    er_score = min(1.0, er * 20)

    recency_days = days_running
    if last_seen:
        recency_days = max((datetime.now(timezone.utc) - last_seen).days, 0)
    recency_score = max(0.0, 1 - recency_days / 30)

    engagement_abs_score = min(1.0, total_engagement / 10000)

    viral_score = round(
        (er_score * 0.4 + recency_score * 0.3 + engagement_abs_score * 0.3) * 100, 1
    )
    result["viral_score"] = viral_score

    # --- Hot flag ---
    result["is_hot"] = (
        viral_score > 70 and days_running < 14 and total_engagement > 500
    )

    return result


def _parse_dt(value) -> datetime | None:
    """Parse a datetime value from string or datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    try:
        from dateutil.parser import parse as parse_date
        dt = parse_date(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None
