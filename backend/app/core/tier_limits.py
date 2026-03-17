from dataclasses import dataclass


@dataclass
class TierLimits:
    searches_per_day: int         # -1 = unlimited
    platforms: list[str]          # ["meta"] or ["meta", "tiktok", "google"]
    max_boards: int               # -1 = unlimited
    max_saved_ads: int            # -1 = unlimited
    ai_credits_per_month: int     # 0 = none
    max_alerts: int               # 0 = none
    data_retention_days: int      # 7, 90, -1 (full)
    can_export: bool
    export_max_rows: int


TIER_LIMITS: dict[str, TierLimits] = {
    "free": TierLimits(
        searches_per_day=50,
        platforms=["meta"],
        max_boards=3,
        max_saved_ads=50,
        ai_credits_per_month=0,
        max_alerts=0,
        data_retention_days=7,
        can_export=True,
        export_max_rows=100,
    ),
    "pro": TierLimits(
        searches_per_day=-1,
        platforms=["meta", "tiktok", "google"],
        max_boards=-1,
        max_saved_ads=-1,
        ai_credits_per_month=50,
        max_alerts=5,
        data_retention_days=90,
        can_export=True,
        export_max_rows=10000,
    ),
    "agency": TierLimits(
        searches_per_day=-1,
        platforms=["meta", "tiktok", "google"],
        max_boards=-1,
        max_saved_ads=-1,
        ai_credits_per_month=500,
        max_alerts=50,
        data_retention_days=-1,
        can_export=True,
        export_max_rows=100000,
    ),
}


def get_tier_limits(tier: str) -> TierLimits:
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])
