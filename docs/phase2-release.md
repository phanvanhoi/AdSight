# Phase 2 Release — AdSight v0.2.0

## Overview

Phase 2 adds monetization, AI analysis, competitor monitoring, notification channels, and search improvements to AdSight.

**Timeline**: Tasks 16-24 (9 tasks)
**New files**: ~30
**Modified files**: ~40

---

## Features Delivered

### Task 16 — Paid Plans & Billing
- **Stripe** international card payments (auto-recurring)
- **VNPay** ATM/QR payments (redirect flow, SHA512 signature)
- **MoMo** e-wallet (API flow, SHA256 HMAC, IPN callback)
- Tier system: Free → Pro ($29/699K VND) → Agency ($79/1.9M VND)
- Tier enforcement: search limits, AI credits, boards, alerts, exports
- Pricing page with VND/USD toggle
- Expired subscription check (Celery beat, 00:30 UTC)

### Task 17 — AI Creative Analysis
- Claude API integration (AsyncAnthropic, claude-sonnet-4-6)
- Analysis endpoint: POST `/ads/{id}/ai-analysis`
- 7-day caching per ad (JSONB field)
- Credit system: 50/month (Pro), 500/month (Agency)
- Frontend panel: hook analysis, emotional triggers, CTA, copy analysis, strengths/weaknesses, suggestions, performance prediction

### Task 18 — Competitor Monitoring
- CompetitorAlert model: advertiser_name, advertiser_group, keyword types
- Notification model: in-app notification system
- Celery task: check every 2h across all active alerts
- CRUD API with tier-based alert limits
- Alerts management page with create/toggle/delete
- NotificationBell component with unread count badge + polling

### Task 19 — Email Alerts
- SMTP email sender with graceful degradation
- Branded HTML email template (inline CSS, indigo header)
- Celery task: send_alert_email on competitor match
- email_alerts_enabled toggle per user

### Task 20 — Telegram Bot
- Telegram Bot API: send messages, connect/disconnect
- One-time token flow: Settings → t.me/BotUsername?start={token}
- Webhook endpoint: /start, /status, /stop commands
- Celery task: send_telegram_alert alongside email
- Settings UI: connect/disconnect, toggle enabled

### Task 21 — Advanced Filters
- Exposed all backend ES filters to frontend: platform (multi-select), category_l1, date range, spend range, viral score, is_hot, has_discount
- Redesigned FilterPanel: collapsible, advanced section, active count badge, reset button
- Sort option: "Viral score cao"
- Mobile responsive: toggle button on small screens

### Task 22 — Advertiser Profile Enhancement
- Analytics endpoint: platform breakdown, ads timeline, category breakdown, ad type breakdown, top ads, avg engagement/viral
- Bar chart (timeline) + Pie charts (platform, ad type) using recharts
- Top Performing Ads section with viral score coloring
- Stats cards: total ads, est. spend, active count, first ad date
- Fixed all Vietnamese diacritics

### Task 23 — Daily Digest Email
- Daily email for paid users: trending ads, competitor updates, stats
- Celery beat at 00:00 UTC (7:00 AM VN)
- Branded digest template with gradient header
- daily_digest_enabled toggle in Settings
- Conditional competitor section (hidden if no updates)

### Task 24 — Vietnamese NLP v2
- Expanded synonym dictionary: 12 → 40+ groups (10 categories)
- Search-time synonyms: no reindex needed for synonym updates
- Expanded stopwords: 23 → 49 words
- 2 new L1 categories: Du lịch, Xe cộ
- New subcategories: Nước hoa, Chăm sóc tóc
- Search autocomplete API: GET `/search/suggest?q=...`
- SearchBar with autocomplete dropdown, debounce, keyboard navigation
- Reindex script: `python -m scripts.reindex_es` (full) / `--synonyms-only` (hot update)

---

## Database Migrations

| Migration | Description |
|-----------|-------------|
| 004 | Stripe fields (customer_id, subscription_id, payment_method, status, end) |
| 005 | AI analysis fields (ai_analysis JSONB, ai_analyzed_at) |
| 006 | Competitor alerts + Notifications tables |
| 007 | email_alerts_enabled on users |
| 008 | Telegram fields (chat_id, enabled) |
| 009 | daily_digest_enabled on users |

Run: `alembic upgrade head`

---

## Environment Variables (New)

```env
# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_PRO_MONTHLY=price_xxx
STRIPE_PRICE_AGENCY_MONTHLY=price_xxx

# VNPay
VNPAY_TMN_CODE=
VNPAY_HASH_SECRET=
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=

# MoMo
MOMO_PARTNER_CODE=
MOMO_ACCESS_KEY=
MOMO_SECRET_KEY=
MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api
MOMO_RETURN_URL=
MOMO_NOTIFY_URL=

# Claude AI
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-sonnet-4-6

# Telegram Bot
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=AdSightBot

# Email (SMTP)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@adsight.vn
SMTP_FROM_NAME=AdSight
```

---

## Celery Beat Schedule (New Tasks)

| Task | Schedule | Description |
|------|----------|-------------|
| check_expired_subscriptions | 00:30 UTC daily | Expire overdue VNPay/MoMo subs |
| check_competitor_ads | Every 2h (:10) | Check all active alerts |
| send_daily_digest | 00:00 UTC daily | Daily digest for paid users |

---

## API Endpoints (New)

### Billing
- `POST /billing/create-checkout-session?plan=pro|agency` — Stripe checkout
- `POST /billing/create-portal-session` — Stripe portal
- `POST /billing/webhook` — Stripe webhook
- `POST /billing/vnpay/create?plan=pro|agency` — VNPay URL
- `GET /billing/vnpay/return` — VNPay callback
- `POST /billing/momo/create?plan=pro|agency` — MoMo URL
- `POST /billing/momo-ipn` — MoMo IPN

### AI Analysis
- `POST /ads/{id}/ai-analysis` — Analyze ad (1 credit)

### Alerts & Notifications
- `GET/POST /alerts/` — List/Create alerts
- `PATCH/DELETE /alerts/{id}` — Update/Delete alert
- `GET /notifications/` — List notifications
- `GET /notifications/unread-count` — Unread count
- `PATCH /notifications/{id}/read` — Mark read
- `POST /notifications/mark-all-read` — Mark all read

### Telegram
- `POST /auth/telegram/connect` — Get connect URL
- `POST /auth/telegram/disconnect` — Disconnect
- `POST /telegram/webhook` — Bot webhook

### Search
- `GET /search/suggest?q=&limit=` — Autocomplete

### Advertisers
- `GET /advertisers/{id}/analytics` — Advertiser analytics

### Settings
- `PATCH /auth/settings` — Update email_alerts, telegram_enabled, daily_digest, full_name

---

## Deployment Checklist

### Pre-deploy
- [ ] All migrations tested locally
- [ ] `make test-all` passes
- [ ] `make lint` passes
- [ ] `.env` updated with all new variables
- [ ] Stripe webhook endpoint registered
- [ ] VNPay merchant account configured
- [ ] MoMo partner account configured

### Deploy
- [ ] `docker-compose build`
- [ ] `alembic upgrade head` (migrations 004-009)
- [ ] `python -m scripts.reindex_es` (new analyzer + synonyms)
- [ ] Verify ES index has `vietnamese_search_analyzer`
- [ ] Celery worker + beat restart

### Post-deploy
- [ ] Create Telegram bot via @BotFather
- [ ] Set webhook: `POST api.telegram.org/bot{TOKEN}/setWebhook?url=https://api.adsight.vn/api/telegram/webhook`
- [ ] Set bot commands via BotFather: start, status, stop
- [ ] Configure SMTP (ses/mailgun/sendgrid)
- [ ] Test Stripe webhook with `stripe listen --forward-to`
- [ ] Verify daily digest fires at 7:00 AM VN
- [ ] Smoke test: register → upgrade → create alert → verify notification

---

## Known Limitations (Phase 2)

1. **Telegram token store**: In-memory dict. Server restart loses pending tokens (user retries connect). Production → Redis with TTL.
2. **VNPay/MoMo**: Manual subscription — no auto-renewal. Celery expires after subscription_end.
3. **AI Analysis**: Depends on Claude API availability. 502 on failure.
4. **Daily Digest**: "Top category" heuristic uses first trending ad's category (simplified).
5. **Search-time synonyms**: Minor performance overhead vs index-time. Acceptable at current scale.
6. **Webhook security**: Telegram webhook has no signature verification (acceptable for MVP).
