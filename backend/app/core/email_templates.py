def daily_digest_email(
    user_name: str,
    date_str: str,
    trending_ads: list[dict],
    competitor_updates: list[dict],
    stats: dict,
) -> str:
    """
    Generate HTML email for daily digest.
    trending_ads: [{"headline": "...", "platform": "...", "likes": 1000, "viral_score": 85, "id": "..."}]
    competitor_updates: [{"alert_name": "...", "count": 5}]
    stats: {"total_new_ads": 150, "top_category": "Mỹ phẩm", "most_active_platform": "meta"}
    """
    # Trending ads rows
    trending_html = ""
    for i, ad in enumerate(trending_ads[:5], 1):
        likes = ad.get("likes", 0)
        likes_str = f"{likes / 1000:.1f}K" if likes >= 1000 else str(likes)
        trending_html += f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid #f3f4f6;">
                <div style="font-weight: 600; color: #111827; font-size: 13px;">
                    {i}. {(ad.get('headline') or 'N/A')[:70]}
                </div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 3px;">
                    {ad.get('platform', '').upper()} &middot; {likes_str} likes &middot; Viral: {ad.get('viral_score', 0):.0f}
                </div>
            </td>
        </tr>
        """

    # Competitor updates rows
    competitor_html = ""
    if competitor_updates:
        competitor_html = """
        <div style="margin-top: 24px;">
            <h3 style="margin: 0 0 12px; font-size: 14px; color: #111827;">🔔 Cập nhật đối thủ</h3>
            <table style="width: 100%; border-collapse: collapse;">
        """
        for update in competitor_updates[:10]:
            competitor_html += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; color: #374151;">
                    <strong>{update.get('alert_name', 'Alert')}</strong>: {update.get('count', 0)} quảng cáo mới
                </td>
            </tr>
            """
        competitor_html += "</table></div>"

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f9fafb;">
        <div style="max-width: 560px; margin: 0 auto; padding: 40px 20px;">
            <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 24px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 18px;">🌅 AdSight Daily Digest</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 13px;">{date_str}</p>
                </div>

                <!-- Content -->
                <div style="padding: 24px;">
                    <p style="margin: 0 0 20px; font-size: 14px; color: #374151;">
                        Chào <strong>{user_name}</strong>, đây là tóm tắt hôm qua:
                    </p>

                    <!-- Stats -->
                    <div style="display: flex; background: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="text-align: center; padding: 8px;">
                                    <div style="font-size: 20px; font-weight: 700; color: #6366f1;">{stats.get('total_new_ads', 0):,}</div>
                                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Ads mới</div>
                                </td>
                                <td style="text-align: center; padding: 8px; border-left: 1px solid #e5e7eb;">
                                    <div style="font-size: 14px; font-weight: 600; color: #374151;">{stats.get('top_category', 'N/A')}</div>
                                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Ngành hot nhất</div>
                                </td>
                                <td style="text-align: center; padding: 8px; border-left: 1px solid #e5e7eb;">
                                    <div style="font-size: 14px; font-weight: 600; color: #374151;">{stats.get('most_active_platform', 'N/A').upper()}</div>
                                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Platform active</div>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Trending Ads -->
                    <h3 style="margin: 0 0 12px; font-size: 14px; color: #111827;">🔥 Trending Ads</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        {trending_html}
                    </table>

                    {competitor_html}

                    <div style="margin-top: 24px; text-align: center;">
                        <a href="https://app.adsight.vn/" style="display: inline-block; padding: 10px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600;">
                            Mở AdSight
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="padding: 16px 24px; background: #f9fafb; border-top: 1px solid #f3f4f6; text-align: center;">
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        Bạn nhận email này vì đã bật Daily Digest.
                        <br/>
                        <a href="https://app.adsight.vn/settings" style="color: #6366f1;">Tắt Daily Digest</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def competitor_alert_email(alert_name: str, match_value: str, ad_count: int, ads_preview: list[dict]) -> str:
    """
    Generate HTML email for competitor alert.
    ads_preview: list of {"headline": "...", "platform": "...", "ad_type": "...", "first_seen": "..."}
    """
    ads_html = ""
    for ad in ads_preview[:5]:
        ads_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #f3f4f6;">
                <div style="font-weight: 600; color: #111827;">{ad.get('headline', 'No headline')[:80]}</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                    {ad.get('platform', '').upper()} &middot; {ad.get('ad_type', '')} &middot; {ad.get('first_seen', '')}
                </div>
            </td>
        </tr>
        """

    extra_note = f'<p style="font-size: 12px; color: #9ca3af; margin-top: 12px;">V\u00e0 {ad_count - 5} ads kh\u00e1c...</p>' if ad_count > 5 else ''

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f9fafb;">
        <div style="max-width: 560px; margin: 0 auto; padding: 40px 20px;">
            <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: #6366f1; padding: 24px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 18px;">Competitor Alert</h1>
                </div>

                <!-- Content -->
                <div style="padding: 24px;">
                    <h2 style="margin: 0 0 8px; font-size: 16px; color: #111827;">
                        {alert_name}: {ad_count} qu\u1ea3ng c\u00e1o m\u1edbi
                    </h2>
                    <p style="margin: 0 0 20px; font-size: 14px; color: #6b7280;">
                        Ph\u00e1t hi\u1ec7n {ad_count} ads m\u1edbi t\u1eeb &quot;{match_value}&quot;.
                    </p>

                    <table style="width: 100%; border-collapse: collapse;">
                        {ads_html}
                    </table>

                    {extra_note}

                    <div style="margin-top: 24px; text-align: center;">
                        <a href="https://app.adsight.vn/alerts" style="display: inline-block; padding: 10px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600;">
                            Xem chi ti\u1ebft
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="padding: 16px 24px; background: #f9fafb; border-top: 1px solid #f3f4f6; text-align: center;">
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        B\u1ea1n nh\u1eadn email n\u00e0y v\u00ec \u0111\u00e3 b\u1eadt th\u00f4ng b\u00e1o cho alert &quot;{alert_name}&quot;.
                        <br/>
                        <a href="https://app.adsight.vn/settings" style="color: #6366f1;">T\u1eaft th\u00f4ng b\u00e1o email</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
