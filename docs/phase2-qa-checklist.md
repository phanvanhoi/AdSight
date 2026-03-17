# Phase 2 — Manual QA Checklist

## Environment
- [ ] `make dev` starts all services without errors
- [ ] `make migrate` runs all migrations (001-009) successfully
- [ ] `make init-es` creates ES index with updated analyzer
- [ ] Frontend loads at http://localhost:3000

## Task 16 — Paid Plans
- [ ] Pricing page loads with correct VND prices
- [ ] Stripe checkout: click Pro → redirect → complete → tier updates
- [ ] VNPay: click → redirect → return → tier updates
- [ ] MoMo: click → redirect → IPN callback → tier updates
- [ ] Free → Pro tier change reflects in /me response
- [ ] Tier limits enforced: free user sees search limit toast at 50

## Task 17 — AI Creative Analysis
- [ ] Free user clicks AI Analysis → 403 upgrade prompt
- [ ] Pro user clicks AI Analysis → loading → result panel shows
- [ ] All sections render: summary, hook, emotions, CTA, strengths, suggestions
- [ ] Second click on same ad → cached=true, no credit consumed
- [ ] Credits exhausted → 429 message

## Task 18 — Competitor Monitoring
- [ ] Create alert (advertiser_name type) → appears in list
- [ ] Toggle alert active/paused
- [ ] Delete alert with confirmation
- [ ] Free user → upgrade gate on create

## Task 19 — Email Alerts
- [ ] SMTP configured → competitor alert triggers email
- [ ] Email HTML renders correctly in Gmail/Outlook
- [ ] Unsubscribe link in footer works
- [ ] Toggle off email alerts in Settings → no more emails

## Task 20 — Telegram Bot
- [ ] Settings → "Kết nối" → opens t.me/BotUsername link
- [ ] /start {token} in Telegram → "Kết nối thành công" message
- [ ] /status → shows connected email
- [ ] /stop → disconnects
- [ ] Settings shows "Đã kết nối" after connecting
- [ ] "Ngắt kết nối" button works
- [ ] Competitor alert → Telegram message received

## Task 21 — Advanced Filters
- [ ] Platform toggle buttons (multi-select) work
- [ ] Category dropdown populated from facets
- [ ] Date range filter works
- [ ] Advanced section toggle (spend, viral, is_hot, has_discount)
- [ ] Sort by "Viral score cao" works
- [ ] "Xóa bộ lọc" resets all filters
- [ ] Active filter count shows in header badge
- [ ] Mobile: filter button toggles panel

## Task 22 — Advertiser Profile
- [ ] Advertiser detail page loads with stats cards
- [ ] Ads Timeline bar chart renders
- [ ] Platform breakdown pie chart renders
- [ ] Ad type breakdown pie chart renders
- [ ] Top Performing Ads section shows clickable rows
- [ ] Category badges display
- [ ] Platform filter buttons filter ads table
- [ ] Pagination works
- [ ] All Vietnamese text has correct diacritics

## Task 23 — Daily Digest
- [ ] Settings: Daily Digest checkbox toggles
- [ ] Celery beat fires task at 00:00 UTC
- [ ] Email received with trending ads, competitor updates, stats
- [ ] HTML renders correctly
- [ ] "Tắt Daily Digest" link in footer

## Task 24 — Vietnamese NLP v2
- [ ] Search "kcn" returns results with "kem chống nắng"
- [ ] Search "dt" returns results with "điện thoại"
- [ ] Autocomplete: type "kem" → dropdown shows suggestions
- [ ] Click suggestion → fills search bar + triggers search
- [ ] Arrow keys navigate suggestions, Enter selects
- [ ] Click outside closes dropdown
- [ ] Categorizer: ads correctly categorized into Du lịch, Xe cộ
- [ ] `python -m scripts.reindex_es` works
- [ ] `python -m scripts.reindex_es --synonyms-only` works
