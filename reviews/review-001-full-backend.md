# Full Backend Review Report
**Date:** 2026-03-16
**Reviewer:** Tab B (Claude Code)
**Scope:** Toàn bộ backend codebase + config + infrastructure

---

## Executive Summary

Backend framework được xây dựng tốt, kiến trúc rõ ràng, đúng pattern FastAPI + SQLAlchemy async. Tuy nhiên có **5 issues CRITICAL** cần fix trước khi chạy, và nhiều issues quan trọng về security, performance cần xử lý trước khi production.

**Tổng findings:** 42 issues
- CRITICAL (phải fix): 5
- HIGH (nên fix sớm): 12
- MEDIUM (nên fix): 14
- LOW (nice to have): 11

---

## CRITICAL Issues (Phải fix ngay)

### C1. ES plugin `analysis-icu` chưa được cài
- **File:** [indexing.py](backend/app/search/indexing.py), [docker-compose.yml](docker-compose.yml)
- **Vấn đề:** Vietnamese analyzer dùng `icu_tokenizer` nhưng plugin `analysis-icu` chưa có trong ES container. App sẽ **crash khi tạo index**.
- **Fix:** Thêm vào docker-compose hoặc tạo custom ES Dockerfile:
  ```yaml
  elasticsearch:
    build:
      context: ./elasticsearch
      dockerfile: Dockerfile
  ```
  ```dockerfile
  FROM docker.elastic.co/elasticsearch/elasticsearch:8.12.0
  RUN bin/elasticsearch-plugin install analysis-icu
  ```

### C2. Synchronous boto3 block async event loop
- **File:** [storage.py](backend/app/core/storage.py)
- **Vấn đề:** `boto3` là sync library, gọi trong async FastAPI sẽ block event loop khi upload/download file lớn. Gây lag toàn bộ API.
- **Fix:** Dùng `aioboto3` hoặc wrap trong `asyncio.get_event_loop().run_in_executor(None, sync_func)`

### C3. Thiếu unique constraint trên Ad và Advertiser
- **File:** [ad.py](backend/app/models/ad.py), [advertiser.py](backend/app/models/advertiser.py)
- **Vấn đề:** Không có DB-level unique constraint cho `(platform, platform_ad_id)` và `(platform, platform_advertiser_id)`. Pipeline deduplicate bằng query nhưng race condition có thể tạo duplicate.
- **Fix:** Thêm `__table_args__`:
  ```python
  __table_args__ = (UniqueConstraint("platform", "platform_ad_id", name="uq_ad_platform"),)
  ```

### C4. `bulk_index_ads` mutates input data
- **File:** [indexing.py:108](backend/app/search/indexing.py)
- **Vấn đề:** `ad.pop("id")` xóa field `id` khỏi dict gốc. Caller (`pipeline.py`) có thể cần `id` sau đó. Side effect nguy hiểm.
- **Fix:** Dùng `ad_id = ad.get("id")` và exclude `id` khi build body, hoặc copy dict trước khi pop.

### C5. Không có rate limiting trên auth endpoints
- **File:** [auth.py](backend/app/api/auth.py)
- **Vấn đề:** `/login`, `/register`, `/refresh` không có rate limit. Dễ bị brute force password, spam registration.
- **Fix:** Dùng `slowapi` hoặc middleware rate limit.

---

## HIGH Issues (Nên fix sớm)

### H1. Password validation thiếu
- **File:** [schemas/auth.py](backend/app/schemas/auth.py)
- **Vấn đề:** `password: str` không có min length. User có thể đặt password "1".
- **Fix:** `password: str = Field(min_length=8, max_length=128)`

### H2. Refresh token không bị invalidate
- **File:** [auth.py](backend/app/api/auth.py)
- **Vấn đề:** Sau khi dùng refresh token để lấy token mới, token cũ vẫn valid. Token replay attack.
- **Fix:** Dùng token blacklist trong Redis, hoặc token rotation với jti claim.

### H3. Thiếu logout endpoint
- **File:** [auth.py](backend/app/api/auth.py)
- **Vấn đề:** Không cách nào revoke access/refresh token.
- **Fix:** Thêm `POST /auth/logout` + token blacklist trong Redis.

### H4. `remove_ad_from_board` không check ownership
- **File:** [boards.py:93](backend/app/api/boards.py)
- **Vấn đề:** Chỉ check `board_id + ad_id`, không verify `Board.user_id == current_user.id`. Bất kỳ authenticated user nào biết IDs đều xóa được.
- **Fix:** Join Board và check user_id.

### H5. CORS hardcoded
- **File:** [main.py:34](backend/app/main.py)
- **Vấn đề:** `allow_origins` chỉ có localhost. Production sẽ bị CORS block.
- **Fix:** Thêm `cors_origins` vào `config.py`, đọc từ env.

### H6. `get_optional_user` không check `is_active`
- **File:** [dependencies.py:51](backend/app/dependencies.py)
- **Vấn đề:** User bị deactivate vẫn pass qua `get_optional_user` và có thể dùng features.
- **Fix:** Thêm check `if user and not user.is_active: return None`

### H7. CSV export thiếu UTF-8 BOM
- **File:** [export_service.py](backend/app/services/export_service.py)
- **Vấn đề:** Excel mở CSV tiếng Việt sẽ hiển thị lỗi font nếu thiếu BOM.
- **Fix:** Thêm `output.write('\ufeff')` trước khi write header.

### H8. Celery tasks tạo event loop mới mỗi lần
- **File:** [collection_tasks.py](backend/app/tasks/collection_tasks.py)
- **Vấn đề:** `asyncio.new_event_loop()` mỗi task execution là anti-pattern, tốn resource.
- **Fix:** Dùng `asgiref.sync.async_to_sync` hoặc Celery pool async.

### H9. Celery tasks không có time_limit
- **File:** [collection_tasks.py](backend/app/tasks/collection_tasks.py)
- **Vấn đề:** Task có thể chạy vô hạn nếu API hang.
- **Fix:** `@celery.task(time_limit=300, soft_time_limit=240)`

### H10. ES deprecated `body` parameter
- **File:** Nhiều files (search_service.py, dashboard_service.py, queries.py, indexing.py)
- **Vấn đề:** ES Python client 8.x deprecate `body={}`. Sẽ warning hoặc break.
- **Fix:** Dùng keyword args: `es.search(index=..., query=..., aggs=..., sort=...)`

### H11. `elasticsearch/config` volume mount không tồn tại
- **File:** [docker-compose.yml:98](docker-compose.yml)
- **Vấn đề:** `./elasticsearch/config` chưa tạo. Docker sẽ tạo empty dir, có thể gây lỗi.
- **Fix:** Tạo thư mục hoặc xóa volume mount.

### H12. Makefile reference scripts chưa tồn tại
- **File:** [Makefile:47-51](Makefile)
- **Vấn đề:** `scripts.init_es` và `scripts.seed_data` chưa được tạo.
- **Fix:** Tạo `backend/scripts/init_es.py` và `backend/scripts/seed_data.py`.

---

## MEDIUM Issues

### M1. S3 client tạo mới mỗi lần gọi
- **File:** [storage.py](backend/app/core/storage.py) — `get_s3_client()` không cache
- **Fix:** Singleton pattern giống Redis/ES

### M2. DB pool_size hardcoded
- **File:** [database.py](backend/app/core/database.py) — `pool_size=20, max_overflow=10`
- **Fix:** Config qua env

### M3. `decode_token` nuốt errors
- **File:** [security.py](backend/app/core/security.py) — Không log JWTError
- **Fix:** Thêm logging cho debug

### M4. `onupdate=func.now()` chỉ ORM level
- **File:** [models/base.py](backend/app/models/base.py)
- **Vấn đề:** Direct SQL update sẽ không trigger. Nên thêm DB trigger.

### M5. Ad.advertiser_id là string, không FK
- **File:** [ad.py](backend/app/models/ad.py)
- **Vấn đề:** Không có relationship với Advertiser model. Data integrity risk.

### M6. `date_from/date_to` là string thay vì date type
- **File:** [schemas/search.py](backend/app/schemas/search.py)
- **Fix:** Dùng `datetime.date` hoặc validate format

### M7. Dashboard endpoints không có auth
- **File:** [dashboard.py](backend/app/api/dashboard.py)
- **Vấn đề:** Public endpoints, có thể leak business metrics

### M8. Export limit không phân biệt tier
- **File:** [export.py](backend/app/api/export.py)
- **Vấn đề:** `100 if free else 1000` — starter, pro, agency cùng limit

### M9. Meta collector hardcode `ad_type = "image"`
- **File:** [meta_collector.py](backend/app/collectors/meta_collector.py)
- **Vấn đề:** Không detect carousel/video

### M10. TikTok API endpoint không official
- **File:** [tiktok_collector.py](backend/app/collectors/tiktok_collector.py)
- **Vấn đề:** `creative_radar_api` là internal API, có thể bị block bất cứ lúc nào

### M11. ES connection không có health check
- **File:** [es_client.py](backend/app/search/es_client.py)

### M12. `_collect_meta` vs `_collect_tiktok` error handling inconsistent
- **File:** [collection_tasks.py](backend/app/tasks/collection_tasks.py)

### M13. `get_ad_detail` trả raw model, không có response schema
- **File:** [ads.py](backend/app/api/ads.py)

### M14. MinIO thiếu healthcheck trong docker-compose
- **File:** [docker-compose.yml](docker-compose.yml)

---

## LOW Issues

### L1. Frontend Dockerfile sẽ fail (chưa có package.json)
### L2. `BoardListResponse` schema defined nhưng không sử dụng
### L3. `SECRET_KEY` vs `JWT_SECRET_KEY` mục đích không rõ
### L4. Beat schedule nên configurable qua env
### L5. `debug=True` sẽ echo tất cả SQL — potential data leak trong logs
### L6. Frontend thiếu `depends_on: api` trong docker-compose
### L7. `get_board_ads` thiếu response_model
### L8. Access token xuất hiện trong URL params (Meta API) — nên mask trong logs
### L9. `request_params = None` trong meta pagination — logic unclear
### L10. `or 0` pattern trong search_service.py — defensive nhưng thừa
### L11. Alembic chưa được init (thiếu `alembic/` folder)

---

## Code vs Docs Alignment

| Docs Requirement | Status | Notes |
|---|---|---|
| Facebook + TikTok collectors | ✅ Done | Meta + TikTok implemented |
| Vietnamese NLP search | ⚠️ Partial | Analyzer defined but ES plugin missing |
| User registration + free tier | ✅ Done | Auth + tier checking |
| Save ads (swipe file / boards) | ✅ Done | Full CRUD |
| CSV export | ✅ Done | UTF-8 issue |
| Basic dashboard | ✅ Done | Overview + trending |
| Responsive frontend | ❌ Not started | Only Dockerfile |
| Landing page | ❌ Not started | |
| Rate limiting | ❌ Missing | Not implemented |
| Google Ads collector | ❌ Phase 3 | As planned |
| AI analysis | ❌ Phase 2 | As planned |
| Chrome extension | ❌ Phase 2 | As planned |

**Verdict:** Backend đang đúng hướng Phase 1 MVP. ~70% backend done, frontend chưa bắt đầu.

---

## Top 5 Priority Actions

1. **Fix C1** — Cài `analysis-icu` plugin cho ES (blocker)
2. **Fix C3** — Thêm unique constraints cho Ad/Advertiser (data integrity)
3. **Fix C5 + H1** — Rate limiting + password validation (security)
4. **Fix C4** — Không mutate input data trong bulk_index
5. **Fix H4** — Board ownership check trong remove_ad

---

## Architecture Score

| Category | Score | Notes |
|---|---|---|
| **Structure** | 8/10 | Clean separation, good patterns |
| **Security** | 5/10 | Missing rate limit, token management, password rules |
| **Error Handling** | 6/10 | Inconsistent, some silent failures |
| **Scalability** | 7/10 | Good foundations (async, ES, Celery), some bottlenecks |
| **Code Quality** | 7/10 | Clean, readable, good naming |
| **Completeness** | 6/10 | MVP ~70%, some stubs and missing pieces |
| **Overall** | 6.5/10 | Solid foundation, needs security hardening |
