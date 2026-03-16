# PRODUCT ROADMAP — AD SPY PLATFORM

> Lộ trình phát triển sản phẩm theo từng giai đoạn,
> bao gồm tính năng, mục tiêu, và KPI cho mỗi phase.

---

## Tầm nhìn sản phẩm

**Sản phẩm:** Nền tảng Ad Intelligence đầu tiên tập trung vào thị trường Việt Nam và Đông Nam Á, tích hợp AI phân tích creative, với mô hình freemium giúp mọi seller/marketer đều có thể tiếp cận.

**Tên dự kiến:** AdVN / SpyAds VN / AdScope (cần research thêm)

**Tagline:** "Biết đối thủ chạy ads gì — trước khi họ biết bạn đang theo dõi"

---

## Phase 1: MVP — Foundation (Tháng 1-3)

### Mục tiêu
- Launch sản phẩm có thể dùng được (usable, not perfect)
- Thu hút 1,000 users đăng ký đầu tiên
- Validate product-market fit tại thị trường VN

### Tính năng

| # | Tính năng | Mô tả | Priority |
|---|-----------|-------|----------|
| 1.1 | **Facebook Ads Search** | Tìm kiếm ads đang chạy trên Facebook/Instagram tại VN. Dữ liệu từ Meta Ad Library API. Filter theo: keyword, advertiser, country, ad type, date range, CTA | P0 - Must have |
| 1.2 | **TikTok Ads Search** | Tìm kiếm ads từ TikTok Creative Center. Filter tương tự Facebook. Focus vào ads chạy tại VN | P0 - Must have |
| 1.3 | **Vietnamese Search** | Tìm kiếm hiểu tiếng Việt: xử lý dấu, viết tắt phổ biến, từ đồng nghĩa cơ bản | P0 - Must have |
| 1.4 | **Ad Detail View** | Xem chi tiết 1 ad: creative (image/video), copy, CTA, metrics, advertiser info, landing page, thời gian chạy | P0 - Must have |
| 1.5 | **User Registration** | Đăng ký/đăng nhập bằng email hoặc Google OAuth. Free tier mặc định | P0 - Must have |
| 1.6 | **Save Ads** | Lưu ads vào bộ sưu tập cá nhân (basic swipe file). Tối đa 50 ads cho free tier | P1 - Should have |
| 1.7 | **Export CSV** | Xuất kết quả tìm kiếm ra file CSV | P1 - Should have |
| 1.8 | **Basic Dashboard** | Trang chủ hiển thị: trending ads hôm nay, top advertisers VN, top categories | P1 - Should have |
| 1.9 | **Landing Page** | Trang giới thiệu sản phẩm, pricing, CTA đăng ký | P0 - Must have |
| 1.10 | **Responsive Design** | Hoạt động tốt trên mobile browser (chưa cần app) | P1 - Should have |

### Không làm trong Phase 1
- AI analysis
- TikTok Shop integration
- Alert/monitoring
- Team collaboration
- Chrome extension
- Mobile app
- Billing/payment (chỉ có free tier)

### KPIs
| Metric | Target |
|--------|--------|
| Registered users | 1,000 |
| Daily active users (DAU) | 100 |
| Searches/ngày | 500 |
| Ads saved/user (avg) | 10 |
| NPS score | > 30 |
| Page load time | < 2s |
| Uptime | > 99% |

### Milestones
| Tuần | Milestone | Deliverable |
|------|-----------|-------------|
| W1-2 | Project setup | Repo, Docker env, CI/CD, DB schema |
| W3-4 | Data pipeline | Meta collector chạy ổn, 100K+ ads VN |
| W5-6 | Core search | Search API + basic UI hoạt động |
| W7-8 | Frontend MVP | Full search UI, ad detail, auth |
| W9-10 | TikTok + Polish | TikTok collector, multi-platform, save ads |
| W11-12 | Launch | Production deploy, landing page, beta launch |

---

## Phase 2: Growth — Monetization & Engagement (Tháng 4-6)

### Mục tiêu
- Kích hoạt monetization (paid tiers)
- Tăng retention thông qua alerts và AI
- Đạt 5,000 users, 100 paying customers

### Tính năng

| # | Tính năng | Mô tả | Priority |
|---|-----------|-------|----------|
| 2.1 | **Paid Plans** | Triển khai Starter ($9), Pro ($29), Agency ($79). Tích hợp Stripe hoặc payment gateway VN (VNPay, MoMo) | P0 |
| 2.2 | **AI Creative Analysis** | Phân tích 1 ad bằng AI: hook, emotional trigger, CTA, điểm mạnh/yếu, gợi ý cải thiện. Dùng Claude API | P0 |
| 2.3 | **Competitor Monitoring** | Nhập fanpage/TikTok account đối thủ → tự động track ads mới của họ | P0 |
| 2.4 | **Email Alerts** | Thông báo khi: đối thủ launch ads mới, keyword match, trend mới | P0 |
| 2.5 | **Telegram Bot** | Gửi alert qua Telegram (phổ biến tại VN hơn Slack) | P1 |
| 2.6 | **Chrome Extension** | Save ads khi lướt Facebook/TikTok vào swipe file trong tool | P1 |
| 2.7 | **Advanced Filters** | Thêm filter: engagement range, spend estimate, ad duration, demographic | P1 |
| 2.8 | **Advertiser Profile** | Trang profile cho mỗi advertiser: tất cả ads, timeline, spend estimate | P1 |
| 2.9 | **Daily Digest** | Email tóm tắt mỗi sáng: ads mới của đối thủ, trending trong ngành | P2 |
| 2.10 | **Vietnamese NLP v2** | Cải thiện synonym dictionary, thêm slang, viết tắt mới. Category taxonomy VN | P2 |

### KPIs
| Metric | Target |
|--------|--------|
| Total users | 5,000 |
| Paying customers | 100 |
| MRR (Monthly Recurring Revenue) | $2,000 |
| DAU | 500 |
| Alert setup rate | 30% of active users |
| AI analysis usage | 20% of Pro users/tuần |
| Churn rate (monthly) | < 10% |

---

## Phase 3: Differentiation — AI & TikTok Shop (Tháng 7-12)

### Mục tiêu
- Trở thành tool Ad Spy #1 tại VN
- Deep TikTok Shop integration (unique selling point)
- AI features nâng cao tạo moat

### Tính năng

| # | Tính năng | Mô tả | Priority |
|---|-----------|-------|----------|
| 3.1 | **TikTok Shop Analytics** | Product search, shop analysis, revenue estimate, affiliate tracking | P0 |
| 3.2 | **AI Video Analysis** | Whisper transcribe video → Claude phân tích script, hook, storytelling | P0 |
| 3.3 | **AI Creative Brief** | Từ saved ads → auto-generate creative brief cho designer/video editor | P0 |
| 3.4 | **Trend Detection** | AI tự động phát hiện trend mới: format, product, messaging angle | P1 |
| 3.5 | **Product-Ads Mapping** | Sản phẩm X → tất cả ads đang chạy cho nó từ mọi seller | P1 |
| 3.6 | **Affiliate Tracker** | KOL nào đang promote sản phẩm nào, performance estimate | P1 |
| 3.7 | **Ad Copy Generator** | Từ product info + ref ads → generate ad copy variations | P1 |
| 3.8 | **Winning Ad Predictor** | ML model dự đoán ads nào có khả năng perform tốt | P2 |
| 3.9 | **Weekly Competitor Report** | Auto-generate báo cáo cạnh tranh hàng tuần (PDF) | P2 |
| 3.10 | **Google Ads Coverage** | Thêm Google Ads Transparency Center data | P2 |

### KPIs
| Metric | Target |
|--------|--------|
| Total users | 20,000 |
| Paying customers | 500 |
| MRR | $10,000 |
| DAU | 2,000 |
| TikTok Shop queries/ngày | 1,000 |
| AI features usage | 40% of paid users/tuần |
| NPS | > 50 |

---

## Phase 4: Scale — Enterprise & SEA (Năm 2)

### Mục tiêu
- Mở rộng ra Đông Nam Á (Thailand, Indonesia, Philippines)
- Enterprise features cho agency lớn
- API platform cho developers

### Tính năng

| # | Tính năng | Mô tả | Priority |
|---|-----------|-------|----------|
| 4.1 | **Team Collaboration** | Multi-user workspace, shared boards, comments, roles | P0 |
| 4.2 | **API Access** | Public API cho developers, documentation, sandbox | P0 |
| 4.3 | **SEA Expansion** | Thêm data Thailand, Indonesia, Philippines. Localize UI | P0 |
| 4.4 | **Client Portal** | Agency tạo read-only view cho client xem competitive report | P1 |
| 4.5 | **White-label Reports** | Agency xuất report với branding riêng | P1 |
| 4.6 | **Mobile App** | React Native app cho iOS/Android | P1 |
| 4.7 | **Slack Integration** | Bot share trending ads vào Slack channel | P2 |
| 4.8 | **Shopee/Lazada Ads** | Thu thập ads trên sàn TMĐT | P2 |
| 4.9 | **Custom Integrations** | Webhook, Zapier, Make.com integration | P2 |
| 4.10 | **Enterprise SSO** | SAML/OIDC cho enterprise customers | P2 |

### KPIs
| Metric | Target |
|--------|--------|
| Total users | 100,000 |
| Paying customers | 2,000 |
| MRR | $50,000 |
| SEA users (non-VN) | 20% |
| API customers | 50 |
| Enterprise contracts | 10 |
| Team workspaces | 200 |

---

## Competitive Moat Strategy

### Moat xây dựng theo thời gian

```
Tháng 1-6: DATA MOAT
├── Thu thập data VN sớm hơn đối thủ
├── Lịch sử ads VN dài hơn (ai bắt đầu sau sẽ thiếu data cũ)
├── Vietnamese NLP dictionary phong phú hơn
└── Category taxonomy VN chính xác hơn

Tháng 7-12: AI MOAT
├── AI model trained trên data VN → chính xác hơn cho VN
├── Pattern recognition từ winning ads VN
├── User feedback loop → AI cải thiện liên tục
└── Proprietary ML models cho prediction

Năm 2+: NETWORK MOAT
├── User-generated tags, notes, ratings → crowdsourced intelligence
├── Team libraries → switching cost cao
├── API ecosystem → third-party integrations
├── Community → brand loyalty
└── SEA data → regional moat
```

---

## Go-to-Market Strategy

### Phase 1: Acquisition

```
Channel                    | Tactic                          | Budget
───────────────────────────┼─────────────────────────────────┼────────
Facebook Groups            | Post giá trị trong group        | $0
                           | seller/marketer VN              |
TikTok organic             | Video "spy ads đối thủ miễn     | $0
                           | phí" → viral potential          |
SEO                        | Blog: "cách tìm ads đối thủ",  | $0
                           | "top winning ads VN"            |
KOL/Influencer marketing   | Cho KOL marketing dùng miễn    | $500
                           | phí → review                   |
Product Hunt / AppSumo     | Launch deal                     | $200
Community (Zalo groups)    | Share tips + tool trong group   | $0
                           | seller VN                       |
```

### Phase 2: Activation & Retention

```
- Onboarding flow: guided tour → first search → first save → first alert
- Weekly "Trending Ads VN" email → drive return visits
- Telegram community → support + engagement
- Feature unlock gamification (đạt X searches → unlock Y)
- Vietnamese-first content (blog, tutorial, case study)
```

### Phase 3: Revenue

```
- Freemium → Pro upsell khi user hit limits
- AI credits as premium feature
- Annual plan discount (20%)
- Agency referral program
- AppSumo lifetime deal cho early traction
- VN payment methods: MoMo, VNPay, bank transfer
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Meta/TikTok block API access | Trung bình | Cao | Đa dạng nguồn data, cache historical data |
| Đối thủ lớn (BigSpy/PiPiADS) focus VN | Thấp | Trung bình | First-mover advantage, local knowledge moat |
| User VN không sẵn sàng trả tiền | Trung bình | Cao | Freemium model, giá thấp, VN payment methods |
| Chi phí AI API cao khi scale | Trung bình | Trung bình | Credit system, self-hosted models khi đủ lớn |
| Legal/ToS issues khi scraping | Trung bình | Cao | Ưu tiên official APIs, legal review |
| Thay đổi platform policies | Cao | Trung bình | Đa nền tảng, không phụ thuộc 1 nguồn |
| Technical scalability | Thấp | Trung bình | Cloud-native architecture, auto-scaling |

---

## Team Structure (Đề xuất)

### Phase 1 (MVP): 2-3 người
```
├── Full-stack Developer (lead) — Backend + Frontend + DevOps
├── Full-stack Developer — Data collection + Search
└── (Optional) Designer/UI — UI/UX, landing page
```

### Phase 2 (Growth): 4-6 người
```
├── Backend Developer — API + AI integration
├── Frontend Developer — Web app + Chrome extension
├── Data Engineer — Collectors + pipeline + Vietnamese NLP
├── Product/Marketing — GTM, content, community
└── (Optional) Mobile Developer
└── (Optional) Designer
```

### Phase 3+ (Scale): 8-12 người
```
├── Engineering (5-7)
│   ├── Backend (2)
│   ├── Frontend (1-2)
│   ├── Data/ML (1-2)
│   └── DevOps/SRE (1)
├── Product (1)
├── Marketing (1-2)
├── Sales (1) — Enterprise/Agency
└── Support (1)
```

---

## Budget Estimation

### Phase 1 (3 tháng)
```
Infrastructure:     $300-450    ($100-150/tháng)
Domain + tools:     $200        (one-time)
Claude API (dev):   $150-300    ($50-100/tháng)
Marketing:          $200        (KOL + launch)
──────────────────────────────
Total:              ~$850-1,150
```

### Phase 2 (3 tháng)
```
Infrastructure:     $1,500-2,400  ($500-800/tháng)
Claude API:         $600-1,500    ($200-500/tháng)
Marketing:          $1,000
Payment gateway:    $100 setup
──────────────────────────────────
Total:              ~$3,200-5,000
```

### Phase 3 (6 tháng)
```
Infrastructure:     $6,000-12,000  ($1,000-2,000/tháng)
Claude API:         $3,000-9,000   ($500-1,500/tháng)
Marketing:          $3,000
Salaries (if any):  variable
──────────────────────────────────────
Total:              ~$12,000-24,000 (excl. salaries)
```
