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
