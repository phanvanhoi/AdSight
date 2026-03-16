# KIẾN TRÚC KỸ THUẬT — AD SPY TOOL

> Tài liệu thiết kế kiến trúc hệ thống cho Ad Intelligence Platform
> phục vụ thị trường Việt Nam / Đông Nam Á.

---

## 1. Tổng quan kiến trúc

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Web App  │  │Chrome Extension│ │Telegram Bot│ │ Mobile App│  │
│  │ (React)  │  │   (Content    │  │  (Alert   │  │ (React   │  │
│  │          │  │   Script)     │  │  Channel) │  │  Native) │  │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  └─────┬─────┘  │
│       │               │                │               │        │
└───────┼───────────────┼────────────────┼───────────────┼────────┘
        │               │                │               │
        └───────────────┴────────┬───────┴───────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                         API GATEWAY                              │
│                    (Nginx / Kong / AWS ALB)                       │
│              Rate Limiting, Auth, Load Balancing                 │
└────────────────────────────────┼────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                        │
┌───────▼───────┐  ┌────────────▼──────────┐  ┌─────────▼────────┐
│  API Service  │  │  Background Workers   │  │  AI Service      │
│  (FastAPI)    │  │  (Celery + Redis)     │  │  (FastAPI)       │
│               │  │                       │  │                  │
│ - Search API  │  │ - Data collectors     │  │ - Creative       │
│ - User mgmt  │  │ - Alert engine        │  │   analysis       │
│ - Billing    │  │ - Report generator    │  │ - Video analysis │
│ - Export     │  │ - Data enrichment     │  │ - Trend detect   │
│ - Dashboard  │  │ - Cleanup jobs        │  │ - Prediction     │
└───────┬───────┘  └────────────┬──────────┘  └─────────┬────────┘
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                │
┌───────────────────────────────┼────────────────────────────────┐
│                        DATA LAYER                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ PostgreSQL   │  │ Elasticsearch│  │ Redis                │   │
│  │              │  │              │  │                      │   │
│  │ - Users      │  │ - Ad index   │  │ - Cache              │   │
│  │ - Billing    │  │ - Full-text  │  │ - Session            │   │
│  │ - Alerts     │  │   search     │  │ - Rate limiting      │   │
│  │ - Saved ads  │  │ - Analytics  │  │ - Job queue          │   │
│  │ - Teams      │  │              │  │ - Real-time metrics  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────────────────────────────┐  │
│  │ Object Store │  │ Message Queue                            │  │
│  │ (S3/MinIO)   │  │ (RabbitMQ / Redis Streams)              │  │
│  │              │  │                                          │  │
│  │ - Ad images  │  │ - Collector tasks                       │  │
│  │ - Ad videos  │  │ - Alert events                          │  │
│  │ - Reports    │  │ - AI processing queue                   │  │
│  │ - Thumbnails │  │ - Notification events                   │  │
│  └──────────────┘  └──────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Tech Stack tổng quan

| Layer | Technology | Lý do chọn |
|-------|-----------|------------|
| **Frontend** | React + TypeScript + TailwindCSS | Ecosystem lớn, component library phong phú |
| **Backend API** | Python + FastAPI | Async support, tích hợp ML/AI dễ, type hints |
| **Background Jobs** | Celery + Redis | Proven cho task queue, scheduling, retry |
| **Database** | PostgreSQL 16 | JSONB support, full-text search tiếng Việt, mature |
| **Search Engine** | Elasticsearch 8 | Full-text search mạnh, aggregation, analytics |
| **Cache** | Redis 7 | Fast, versatile (cache, queue, pub/sub, rate limit) |
| **Object Storage** | AWS S3 / MinIO | Scalable, cheap cho media files |
| **AI/ML** | Claude API + Whisper + custom models | Best-in-class cho text/image analysis |
| **Monitoring** | Prometheus + Grafana | Industry standard, open-source |
| **Deployment** | Docker + Docker Compose → Kubernetes | Dev đơn giản, production scalable |

---

## 2. Data Collection Layer

### 2.1 Collector Architecture

```
┌─────────────────────────────────────────────────────┐
│                 COLLECTOR MANAGER                     │
│           (Celery Beat Scheduler)                     │
│                                                       │
│  Schedule:                                            │
│  ├── Meta Ad Library    → mỗi 2 giờ                 │
│  ├── TikTok Creative    → mỗi 4 giờ                 │
│  ├── Google Transparency → mỗi 6 giờ                │
│  ├── TikTok Shop        → mỗi 6 giờ                 │
│  └── VN Platforms       → mỗi 12 giờ                │
│                                                       │
│  Config per collector:                                │
│  ├── target_countries: ["VN", "TH", "ID", "PH"]     │
│  ├── categories: ["ecommerce", "beauty", "fashion"]  │
│  ├── max_concurrent_requests: 10                      │
│  ├── retry_policy: exponential_backoff                │
│  └── rate_limit: per API documentation                │
└───────────┬───────────────────────────────────────────┘
            │
    ┌───────┴───────────────────────┐
    │                               │
    ▼                               ▼
┌─────────────────┐      ┌─────────────────┐
│ API Collectors  │      │  Web Collectors  │
│                 │      │                  │
│ - Meta Ad       │      │ - Playwright     │
│   Library API   │      │   browser pool   │
│ - TikTok        │      │ - Proxy rotation │
│   Creative API  │      │ - Anti-detect    │
│ - Google Ads    │      │ - HTML parser    │
│   Transparency  │      │ - Screenshot     │
│   API           │      │   capture        │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────┐
    │   Data Pipeline          │
    │                          │
    │ 1. Raw data ingestion    │
    │ 2. Deduplication         │
    │ 3. Normalization         │
    │ 4. Enrichment            │
    │    - Language detection   │
    │    - Category classify   │
    │    - Sentiment analysis  │
    │ 5. Media download        │
    │    - Image → S3          │
    │    - Video → S3          │
    │    - Thumbnail generate  │
    │ 6. Index to ES           │
    │ 7. Store to PostgreSQL   │
    └─────────────────────────┘
```

### 2.2 Data Models

#### Ad (core entity)

```python
class Ad:
    # Identity
    id: UUID
    platform: Enum["meta", "tiktok", "google", "zalo"]
    platform_ad_id: str          # ID gốc từ platform

    # Advertiser
    advertiser_id: str
    advertiser_name: str
    advertiser_page_url: str

    # Creative
    ad_type: Enum["image", "video", "carousel", "text"]
    headline: str | None
    body_text: str | None
    cta_type: str | None         # "shop_now", "learn_more", etc.
    media_urls: JSONB | None       # URLs gốc (default=None, tránh mutable default)
    media_s3_keys: JSONB | None    # URLs đã lưu (default=None)
    thumbnail_url: str | None
    landing_page_url: str | None

    # Targeting
    target_countries: JSONB | None  # (default=None)
    target_age_min: int | None
    target_age_max: int | None
    target_gender: str | None
    target_interests: JSONB | None  # (default=None)

    # Performance (estimated)
    impressions_lower: int | None
    impressions_upper: int | None
    spend_lower: float | None
    spend_upper: float | None
    likes: int | None
    comments: int | None
    shares: int | None

    # Classification
    language: str               # detected language
    category: str | None        # auto-classified
    tags: JSONB | None           # auto + manual tags (default=None)
    sentiment: float | None     # -1 to 1

    # Metadata
    first_seen: datetime
    last_seen: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### Advertiser

```python
class Advertiser:
    id: UUID
    platform: str
    platform_advertiser_id: str
    name: str
    page_url: str
    website: str | None
    category: str | None
    country: str | None
    total_ads: int
    active_ads: int
    first_seen: datetime
    last_seen: datetime
    estimated_monthly_spend: float | None
```

#### TikTokShopProduct

```python
class TikTokShopProduct:
    id: UUID
    shop_id: str
    shop_name: str
    product_id: str
    product_name: str
    price: float
    currency: str
    category: str
    total_sold: int
    rating: float
    review_count: int
    related_ad_ids: list[UUID]     # link tới ads
    affiliate_count: int           # số KOL đang promote
    first_seen: datetime
    last_seen: datetime
```

### 2.3 Data Volume Estimation

| Metric | Estimate | Storage |
|--------|----------|---------|
| New ads/ngày (VN focus) | ~10,000-50,000 | ~50MB structured data |
| Media files/ngày | ~30,000 (images + videos) | ~5-20GB |
| Total ads sau 1 năm | ~10-15M | ~15GB structured data |
| Total media sau 1 năm | ~5-10TB | S3 storage |
| Elasticsearch index | ~10-15M documents | ~30-50GB |

---

## 3. Search & Discovery

### 3.1 Search Architecture

```
User Query
    │
    ▼
┌─────────────────────┐
│  Query Parser        │
│                      │
│  - Vietnamese NLP    │
│    tokenization      │
│  - Synonym expansion │
│  - Typo correction   │
│  - Filter extraction │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Elasticsearch       │
│                      │
│  - Multi-field       │
│    search            │
│  - Vietnamese        │
│    analyzer          │
│  - Aggregations      │
│  - Geo filtering     │
│  - Date range        │
│  - Faceted search    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Result Ranker       │
│                      │
│  - Relevance score   │
│  - Recency boost     │
│  - Engagement score  │
│  - Personalization   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Response Builder    │
│                      │
│  - Pagination        │
│  - Facet counts      │
│  - Suggestions       │
│  - Related searches  │
└─────────────────────┘
```

### 3.2 Vietnamese NLP Configuration

```json
{
  "analysis": {
    "analyzer": {
      "vietnamese_analyzer": {
        "type": "custom",
        "tokenizer": "icu_tokenizer",
        "filter": [
          "lowercase",
          "vietnamese_stop",
          "vietnamese_synonym",
          "asciifolding"
        ]
      }
    },
    "filter": {
      "vietnamese_stop": {
        "type": "stop",
        "stopwords": ["và", "của", "là", "có", "được", "cho", "với", "này"]
      },
      "vietnamese_synonym": {
        "type": "synonym",
        "synonyms": [
          "kem chống nắng, kcn, sunscreen, chống nắng",
          "serum, tinh chất, essence",
          "son môi, son, lipstick",
          "áo thun, áo phông, t-shirt",
          "giảm giá, sale, khuyến mãi, km, giảm, flash sale"
        ]
      }
    }
  }
}
```

### 3.3 Filter System

```
Available Filters:
├── Platform: [Meta, TikTok, Google, Zalo]
├── Country: [VN, TH, ID, PH, MY, SG, ...]
├── Language: [vi, en, th, id, ...]
├── Ad Type: [Image, Video, Carousel, Text]
├── CTA: [Shop Now, Learn More, Sign Up, ...]
├── Category: [Beauty, Fashion, F&B, Tech, ...]
├── Date Range: [Last 7d, 30d, 90d, custom]
├── Engagement: [min likes, min comments, min shares]
├── Spend Range: [estimated spend brackets]
├── Duration: [ads running > X days]
├── Advertiser: [specific advertiser name/ID]
├── Landing Page Domain: [specific domain]
├── Has Video: [true/false]
├── Active Status: [active, inactive, all]
└── Sort By: [relevance, newest, engagement, spend, duration]
```

---

## 4. AI Analysis Service

### 4.1 Service Architecture

```
┌────────────────────────────────────────────┐
│            AI SERVICE (FastAPI)              │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │         Request Router                │   │
│  │  POST /api/ai/analyze-creative       │   │
│  │  POST /api/ai/analyze-video          │   │
│  │  POST /api/ai/generate-brief         │   │
│  │  POST /api/ai/predict-performance    │   │
│  │  POST /api/ai/detect-trends          │   │
│  │  POST /api/ai/competitor-report      │   │
│  └──────────┬───────────────────────────┘   │
│             │                                │
│  ┌──────────▼───────────────────────────┐   │
│  │         Processing Pipeline           │   │
│  │                                       │   │
│  │  ┌─────────────┐  ┌───────────────┐  │   │
│  │  │ Media       │  │ Text          │  │   │
│  │  │ Processor   │  │ Processor     │  │   │
│  │  │             │  │               │  │   │
│  │  │ - FFmpeg    │  │ - Claude API  │  │   │
│  │  │ - Whisper   │  │ - NLP pipeline│  │   │
│  │  │ - Claude    │  │ - Sentiment   │  │   │
│  │  │   Vision    │  │ - Entity      │  │   │
│  │  │             │  │   extraction  │  │   │
│  │  └─────────────┘  └───────────────┘  │   │
│  │                                       │   │
│  │  ┌─────────────┐  ┌───────────────┐  │   │
│  │  │ ML Models   │  │ Report        │  │   │
│  │  │             │  │ Generator     │  │   │
│  │  │ - XGBoost   │  │               │  │   │
│  │  │ - Pattern   │  │ - Template    │  │   │
│  │  │   matching  │  │   engine      │  │   │
│  │  │ - Anomaly   │  │ - PDF/HTML    │  │   │
│  │  │   detection │  │   output      │  │   │
│  │  └─────────────┘  └───────────────┘  │   │
│  └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

### 4.2 AI Analysis Prompts (Claude API)

#### Creative Analysis Prompt

```
Phân tích quảng cáo sau đây và trả về JSON:

Ad Copy: {ad_text}
Image/Video Description: {media_description}
Platform: {platform}
Category: {category}

Phân tích:
1. Hook Analysis: Câu đầu tiên/3 giây đầu có gì thu hút?
2. Emotional Triggers: Cảm xúc nào được kích hoạt? (FOMO, curiosity, desire, fear, trust)
3. Value Proposition: Giá trị cốt lõi được truyền tải là gì?
4. CTA Effectiveness: CTA có rõ ràng và compelling không?
5. Visual Analysis: Layout, màu sắc, typography có hiệu quả không?
6. Target Audience: Ads này nhắm tới đối tượng nào?
7. Strengths: 3 điểm mạnh nhất
8. Weaknesses: 3 điểm có thể cải thiện
9. Score: Điểm tổng thể 1-10
10. Suggestions: 3 gợi ý cải thiện cụ thể
```

#### Video Script Analysis Prompt

```
Transcript video quảng cáo:
{transcript}

Video duration: {duration}s
Platform: {platform}

Phân tích cấu trúc script:
1. Hook (0-3s): Phân tích hook mở đầu
2. Problem Statement: Vấn đề được nêu ra
3. Solution/Product: Cách giới thiệu sản phẩm
4. Social Proof: Bằng chứng xã hội (nếu có)
5. CTA: Call-to-action cuối
6. Pacing: Tốc độ nhanh/chậm, phù hợp không?
7. Tone: Giọng điệu (funny, serious, educational, emotional)
8. Script Template: Tóm tắt thành template có thể tái sử dụng
```

### 4.3 Credit System

```
AI Feature              | Credits | Estimated Cost (API)
─────────────────────────┼─────────┼────────────────────
Creative Analysis        |    1    | ~$0.02-0.05
Video Script Analysis    |    3    | ~$0.05-0.15
Creative Brief Generator |    2    | ~$0.03-0.08
Performance Prediction   |    1    | ~$0.01-0.03
Competitor Report        |   10    | ~$0.20-0.50
Trend Analysis           |    5    | ~$0.10-0.25
Ad Copy Generation       |    2    | ~$0.03-0.08
A/B Variation Suggest    |    2    | ~$0.03-0.08

Tier Allocation:
- Free: 5 credits/tháng (trải nghiệm)
- Pro: 50 credits/tháng
- Agency: 500 credits/tháng
- Pay-per-use: $0.10/credit
```

---

## 5. Alert & Monitoring System

### 5.1 Architecture

```
┌──────────────────────────────────────────────┐
│              ALERT ENGINE                      │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │         Rule Processor                  │   │
│  │                                         │   │
│  │  For each new/updated ad:               │   │
│  │  1. Load active alert rules             │   │
│  │  2. Evaluate each rule against ad       │   │
│  │  3. If match → create alert event       │   │
│  │  4. Deduplicate (no spam)               │   │
│  │  5. Queue notification                  │   │
│  └──────────┬─────────────────────────────┘   │
│             │                                  │
│  ┌──────────▼─────────────────────────────┐   │
│  │         Alert Rules (user-defined)      │   │
│  │                                         │   │
│  │  {                                      │   │
│  │    "name": "Competitor X new ads",      │   │
│  │    "type": "competitor_watch",          │   │
│  │    "conditions": {                      │   │
│  │      "advertiser_id": "xxx",            │   │
│  │      "platform": "meta"                 │   │
│  │    },                                   │   │
│  │    "notification": {                    │   │
│  │      "channels": ["email", "telegram"], │   │
│  │      "frequency": "immediate"           │   │
│  │    }                                    │   │
│  │  }                                      │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │         Trend Detector (automated)      │   │
│  │                                         │   │
│  │  - Volume spike detection               │   │
│  │  - New category entrant detection       │   │
│  │  - Creative format shift detection      │   │
│  │  - Spend anomaly detection              │   │
│  │  Runs: every 6 hours                    │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │         Notification Dispatcher         │   │
│  │                                         │   │
│  │  Channels:                              │   │
│  │  ├── Email (AWS SES / SendGrid)        │   │
│  │  ├── Telegram Bot                       │   │
│  │  ├── Webhook                            │   │
│  │  ├── In-app notification                │   │
│  │  └── Slack integration                  │   │
│  │                                         │   │
│  │  Frequency options:                     │   │
│  │  ├── Immediate                          │   │
│  │  ├── Hourly digest                      │   │
│  │  ├── Daily digest (9:00 AM)            │   │
│  │  └── Weekly report (Monday 9:00 AM)    │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## 6. API Design

### 6.1 Core Endpoints

```
Authentication:
  POST   /api/auth/register
  POST   /api/auth/login
  POST   /api/auth/refresh
  POST   /api/auth/forgot-password

Ads Search:
  GET    /api/ads/search?q={query}&platform={}&country={}&...
  GET    /api/ads/{id}
  GET    /api/ads/{id}/similar
  GET    /api/ads/{id}/history

Advertisers:
  GET    /api/advertisers/search?q={query}
  GET    /api/advertisers/{id}
  GET    /api/advertisers/{id}/ads
  GET    /api/advertisers/{id}/stats

Saved Ads (Swipe File):
  GET    /api/boards
  POST   /api/boards
  PUT    /api/boards/{id}
  DELETE /api/boards/{id}
  POST   /api/boards/{id}/ads
  DELETE /api/boards/{id}/ads/{ad_id}

Alerts:
  GET    /api/alerts
  POST   /api/alerts
  PUT    /api/alerts/{id}
  DELETE /api/alerts/{id}
  GET    /api/alerts/{id}/history

AI Analysis:
  POST   /api/ai/analyze-creative
  POST   /api/ai/analyze-video
  POST   /api/ai/generate-brief
  POST   /api/ai/predict-performance
  POST   /api/ai/competitor-report

TikTok Shop:
  GET    /api/tiktok-shop/products/search
  GET    /api/tiktok-shop/products/{id}
  GET    /api/tiktok-shop/shops/{id}
  GET    /api/tiktok-shop/shops/{id}/products
  GET    /api/tiktok-shop/affiliates/search

Dashboard:
  GET    /api/dashboard/overview
  GET    /api/dashboard/trends
  GET    /api/dashboard/top-advertisers
  GET    /api/dashboard/top-categories

Export:
  POST   /api/export/csv
  POST   /api/export/pdf
  GET    /api/export/{job_id}/download

User & Billing:
  GET    /api/user/profile
  PUT    /api/user/profile
  GET    /api/user/usage
  GET    /api/billing/plans
  POST   /api/billing/subscribe
  POST   /api/billing/cancel
```

### 6.2 Search API Example

```
GET /api/ads/search?
  q=kem+chống+nắng&
  platform=meta,tiktok&
  country=VN&
  ad_type=video&
  date_from=2026-01-01&
  date_to=2026-03-16&
  min_likes=1000&
  sort=engagement_desc&
  page=1&
  limit=20

Response:
{
  "total": 1234,
  "page": 1,
  "limit": 20,
  "results": [
    {
      "id": "uuid-xxx",
      "platform": "tiktok",
      "advertiser": {
        "name": "Beauty Store VN",
        "page_url": "https://..."
      },
      "creative": {
        "type": "video",
        "headline": "Kem chống nắng SPF50+ ...",
        "body": "...",
        "thumbnail_url": "https://...",
        "video_url": "https://...",
        "cta": "shop_now"
      },
      "metrics": {
        "likes": 5200,
        "comments": 340,
        "shares": 120,
        "estimated_spend": {"min": 500, "max": 2000, "currency": "USD"},
        "days_running": 14
      },
      "first_seen": "2026-03-01",
      "last_seen": "2026-03-16",
      "is_active": true
    }
  ],
  "facets": {
    "platforms": {"meta": 800, "tiktok": 434},
    "ad_types": {"video": 900, "image": 300, "carousel": 34},
    "categories": {"beauty": 500, "skincare": 400, "health": 334}
  }
}
```

---

## 7. Infrastructure & Deployment

### 7.1 Development Environment

```yaml
# docker-compose.dev.yml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/adsight
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    volumes:
      - ./frontend:/app

  celery-worker:
    build: ./backend
    command: celery -A app.celery worker -l info -c 4

  celery-beat:
    build: ./backend
    command: celery -A app.celery beat -l info

  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data

  elasticsearch:
    build:
      context: ./elasticsearch   # Custom Dockerfile cài analysis-icu plugin
    ports: ["9200:9200"]
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
```

### 7.2 Production Architecture (AWS)

```
                    ┌──────────────┐
                    │  CloudFront  │
                    │  (CDN)       │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     ALB      │
                    │ (Load        │
                    │  Balancer)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼────┐ ┌─────▼─────┐
       │ ECS Fargate │ │  ECS  │ │    ECS    │
       │ (API)       │ │(Worker)│ │(AI Service)│
       │ 2-10 tasks  │ │ 2-8   │ │  1-4      │
       └──────┬──────┘ └──┬────┘ └─────┬─────┘
              │            │            │
    ┌─────────┼────────────┼────────────┼──────┐
    │         │            │            │      │
    │  ┌──────▼──────┐ ┌───▼────┐ ┌────▼───┐  │
    │  │  RDS        │ │  ES    │ │  S3    │  │
    │  │  PostgreSQL │ │  (Open │ │        │  │
    │  │  (Multi-AZ) │ │  Search│ │        │  │
    │  └─────────────┘ └────────┘ └────────┘  │
    │                                          │
    │  ┌─────────────┐ ┌────────────────────┐  │
    │  │ElastiCache  │ │  SQS / EventBridge │  │
    │  │  (Redis)    │ │  (Message Queue)   │  │
    │  └─────────────┘ └────────────────────┘  │
    │                                          │
    │              VPC (Private Subnet)         │
    └──────────────────────────────────────────┘
```

### 7.3 Cost Estimation (Monthly)

```
Development (1 developer, MVP):
├── AWS Free Tier / DigitalOcean $48/mo droplet
├── Claude API: ~$50-100/mo (development + testing)
├── Domain + SSL: ~$15/mo
├── Total: ~$100-150/mo

Early Stage (100-1000 users):
├── ECS Fargate (API + Workers): ~$150/mo
├── RDS PostgreSQL (db.t3.medium): ~$70/mo
├── OpenSearch (t3.small): ~$50/mo
├── ElastiCache (cache.t3.micro): ~$15/mo
├── S3 (1TB): ~$23/mo
├── Claude API: ~$200-500/mo
├── SES (email): ~$10/mo
├── Total: ~$500-800/mo

Growth (1000-10000 users):
├── ECS Fargate (scaled): ~$500/mo
├── RDS PostgreSQL (db.r6g.large): ~$250/mo
├── OpenSearch (m6g.large): ~$200/mo
├── ElastiCache (cache.m6g.large): ~$100/mo
├── S3 (10TB): ~$230/mo
├── CloudFront: ~$100/mo
├── Claude API: ~$1000-3000/mo
├── Total: ~$2500-4500/mo
```

---

## 8. Security

### 8.1 Authentication & Authorization

```
Authentication:
├── JWT tokens (access + refresh)
├── OAuth2 (Google, Facebook login)
├── Rate limiting per user tier
└── API key for programmatic access

Authorization:
├── Role-based (admin, user, viewer)
├── Tier-based feature gating
├── Team-based resource access
└── API key scoping

Data Security:
├── All data encrypted at rest (AES-256)
├── All traffic encrypted in transit (TLS 1.3)
├── PII minimization
├── GDPR compliance (data deletion)
└── Regular security audits
```

### 8.2 Rate Limiting

```
Free Tier:
├── 50 searches/ngày
├── 10 API calls/phút
├── 5 AI credits/tháng
└── 1MB export/ngày

Pro Tier:
├── Unlimited searches
├── 60 API calls/phút
├── 50 AI credits/tháng
└── 100MB export/ngày

Agency Tier:
├── Unlimited searches
├── 120 API calls/phút
├── 500 AI credits/tháng
└── 1GB export/ngày
```

---

## 9. Development Roadmap (Technical)

### Phase 1: MVP (Tháng 1-3)
```
Week 1-2: Project setup
├── Repository setup (monorepo)
├── Docker Compose development environment
├── CI/CD pipeline (GitHub Actions)
├── Database schema + migrations
└── Basic API structure

Week 3-4: Data collection
├── Meta Ad Library collector
├── Data pipeline (ingest → normalize → store)
├── Basic Elasticsearch indexing
└── Media download + S3 storage

Week 5-6: Core API
├── Search API with filters
├── Ad detail API
├── Authentication (JWT)
├── Rate limiting
└── Basic Vietnamese search

Week 7-8: Frontend MVP
├── Search page with filters
├── Ad detail view
├── User registration/login
├── Responsive design
└── Basic dashboard

Week 9-10: TikTok + Polish
├── TikTok Creative Center collector
├── Multi-platform search
├── Save ads (basic swipe file)
├── Export CSV
└── Landing page

Week 11-12: Launch prep
├── Free tier implementation
├── Stripe billing integration
├── Performance optimization
├── Security audit
├── Beta testing
└── Production deployment
```

### Phase 2: Growth (Tháng 4-6)
```
├── AI Creative Analysis (Claude API)
├── Competitor monitoring + alerts
├── Telegram bot notifications
├── Chrome extension
├── Vietnamese NLP improvements
├── TikTok Shop basic integration
└── Daily digest emails
```

### Phase 3: Scale (Tháng 7-12)
```
├── Advanced AI features
├── TikTok Shop deep analytics
├── Team collaboration
├── API access for developers
├── Mobile app
├── SEA market expansion
└── Enterprise features
```
