# AdSight Platform - Hướng dẫn Deploy trên VPS

## Thông tin VPS hiện tại

| Thông số | Giá trị |
|----------|---------|
| IP | 112.213.88.208 |
| OS | CentOS/RHEL |
| RAM | 2 GB |
| Domain | adspyvn.com |
| CDN/SSL | Cloudflare (Flexible) |
| Project path | /opt/adsight |
| GitHub | https://github.com/phanvanhoi/AdSight.git |

## Kiến trúc

```
Internet → Cloudflare (SSL Flexible, port 80/443)
         → Origin Rule (override port 8080)
         → VPS:8080 (Nginx)
              ├── /api/*     → api:8000 (FastAPI + Uvicorn)
              ├── /assets/*  → frontend:80 (Nginx serve static)
              └── /*         → frontend:80

Docker containers (12):
  api, celery-worker, celery-beat, frontend,
  nginx, postgres, elasticsearch, redis, minio
```

## Yêu cầu

- Docker + Docker Compose v2
- Git
- Tối thiểu 2 GB RAM (đã optimize cho low-memory)

---

## 1. Cài đặt Docker (nếu chưa có)

```bash
# CentOS/RHEL
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
```

## 2. Clone source code

```bash
cd /opt
git clone https://github.com/phanvanhoi/AdSight.git adsight
cd /opt/adsight
```

## 3. Tạo file `.env.production`

Copy từ `.env.example` và chỉnh sửa:

```bash
cp .env.example .env.production
vi .env.production
```

Các biến **bắt buộc** phải thay đổi:

```ini
# App
APP_ENV=production
SECRET_KEY=<random-string-64-ky-tu>
DEBUG=false

# PostgreSQL
POSTGRES_USER=adsight
POSTGRES_PASSWORD=<mat-khau-manh>
POSTGRES_DB=adsight
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://adsight:<mat-khau-manh>@postgres:5432/adsight

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200
ES_ADS_INDEX=ads

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=<random-string-khac>
JWT_ALGORITHM=HS256

# Meta Ad Library API
META_ACCESS_TOKEN=<token-tu-facebook-graph-api>
META_API_VERSION=v19.0

# CORS - thêm domain production
CORS_ORIGINS=https://adspyvn.com,http://localhost:3000

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<doi-access-key>
MINIO_SECRET_KEY=<doi-secret-key>
MINIO_BUCKET=adsight-media
MINIO_USE_SSL=false
```

## 4. Build và chạy

```bash
cd /opt/adsight

# Build tất cả images
docker compose -f docker-compose.prod.yml build

# Chạy toàn bộ services (detached)
docker compose -f docker-compose.prod.yml up -d

# Xem logs
docker compose -f docker-compose.prod.yml logs -f
```

Thứ tự khởi động tự động: postgres/redis/elasticsearch (healthcheck) → api → celery-worker/celery-beat → frontend → nginx

## 5. Khởi tạo Database

```bash
# Chạy migration (Alembic)
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## 6. Kiểm tra services

```bash
# Trạng thái tất cả containers
docker compose -f docker-compose.prod.yml ps

# Health check API
curl http://localhost:8080/health

# Kiểm tra Elasticsearch
docker compose -f docker-compose.prod.yml exec api python -c "
from elasticsearch import Elasticsearch
es = Elasticsearch('http://elasticsearch:9200')
print(es.info())
"

# Kiểm tra ES index
docker compose -f docker-compose.prod.yml exec api python -c "
from elasticsearch import Elasticsearch
es = Elasticsearch('http://elasticsearch:9200')
print(es.indices.get_mapping(index='ads'))
"
```

---

## Cấu hình Cloudflare

### DNS
| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | adspyvn.com | 112.213.88.208 | Proxied (orange) |
| A | www | 112.213.88.208 | Proxied (orange) |

### SSL/TLS
- Mode: **Flexible** (origin không có SSL, Cloudflare handle HTTPS)
- Edge Certificates: On
- Always Use HTTPS: On

### Origin Rules
- Tạo rule: hostname = `adspyvn.com` → Override destination port = **8080**
- Lý do: Nginx container listen 8080 trên host, Cloudflare gửi traffic port 80 mặc định

### Email Routing (tùy chọn)
- admin@adspyvn.com → forward tới email cá nhân

---

## Xử lý sự cố thường gặp

### Docker container không ra internet

Kiểm tra iptables MASQUERADE cho Docker network:

```bash
# Tìm Docker bridge interface
BRIDGE=$(docker network inspect adsight_default -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || echo "172.19.0.0/16")
IFACE=$(docker network inspect adsight_default -f '{{index .Options "com.docker.network.bridge.name"}}' 2>/dev/null)

# Thêm rule NAT
iptables -t nat -A POSTROUTING -s $BRIDGE ! -o $IFACE -j MASQUERADE
iptables -A FORWARD -i $IFACE -j ACCEPT
iptables -A FORWARD -o $IFACE -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Lưu rule vĩnh viễn
yum install -y iptables-services
service iptables save
```

### VPS bị đơ / OOM (2 GB RAM)

Cấu hình đã optimize trong `docker-compose.prod.yml`:
- Elasticsearch heap: `ES_JAVA_OPTS=-Xms128m -Xmx128m` (thay vì 512m mặc định)
- API workers: `--workers 2` (thay vì 4)
- Celery concurrency: `-c 2` (thay vì 4)

Nếu vẫn OOM, thêm swap:

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
```

### Elasticsearch index lỗi (fielddata disabled)

Xóa và tạo lại index với mapping đúng:

```bash
# Xóa index cũ
docker compose -f docker-compose.prod.yml exec api python -c "
from elasticsearch import Elasticsearch
es = Elasticsearch('http://elasticsearch:9200')
es.indices.delete(index='ads', ignore=[404])
print('Deleted')
"

# Tạo lại (API tự tạo khi restart)
docker compose -f docker-compose.prod.yml restart api

# Hoặc tạo thủ công
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from elasticsearch import AsyncElasticsearch
from app.search.indexing import ADS_INDEX_SETTINGS
from app.config import settings

async def recreate():
    es = AsyncElasticsearch('http://elasticsearch:9200')
    await es.indices.create(
        index=settings.es_ads_index,
        settings=ADS_INDEX_SETTINGS['settings'],
        mappings=ADS_INDEX_SETTINGS['mappings'],
    )
    mapping = await es.indices.get_mapping(index=settings.es_ads_index)
    print('platform type:', mapping[settings.es_ads_index]['mappings']['properties']['platform']['type'])
    await es.close()

asyncio.run(recreate())
"
```

### Nginx 502 Bad Gateway

```bash
# Kiểm tra frontend container có chạy không
docker compose -f docker-compose.prod.yml ps frontend

# Kiểm tra logs
docker compose -f docker-compose.prod.yml logs --tail=50 nginx
docker compose -f docker-compose.prod.yml logs --tail=50 frontend
docker compose -f docker-compose.prod.yml logs --tail=50 api
```

Lưu ý: Frontend container listen port **80** (Nginx serve static), không phải 3000.

### bcrypt lỗi với Python 3.12

Đảm bảo `backend/requirements.txt` có pin version:

```
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
```

---

## Quy trình cập nhật code

```bash
cd /opt/adsight

# Pull code mới
git pull origin main

# Rebuild và restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --force-recreate

# Chạy migration nếu có
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Xem logs
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

Nếu chỉ cần restart một service:

```bash
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml restart celery-worker
```

---

## Thu thập dữ liệu quảng cáo

### Chạy Meta Ad Library collector thủ công

```bash
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from app.collectors.meta_collector import collect_and_store
result = asyncio.run(collect_and_store())
print(result)
"
```

### Xóa toàn bộ dữ liệu và collect lại

```bash
# 1. Xóa DB
docker compose -f docker-compose.prod.yml exec api python -c "
from sqlalchemy import create_engine, text
from app.config import settings
engine = create_engine(settings.database_url.replace('+asyncpg', ''))
with engine.connect() as conn:
    conn.execute(text('DELETE FROM ads'))
    conn.commit()
    print('DB cleared')
"

# 2. Xóa ES index
docker compose -f docker-compose.prod.yml exec api python -c "
from elasticsearch import Elasticsearch
es = Elasticsearch('http://elasticsearch:9200')
es.indices.delete(index='ads', ignore=[404])
print('ES cleared')
"

# 3. Restart API (tự tạo lại ES index)
docker compose -f docker-compose.prod.yml restart api

# 4. Collect lại
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from app.collectors.meta_collector import collect_and_store
result = asyncio.run(collect_and_store())
print(result)
"
```

---

## Ports & Volumes

### Ports expose ra host

| Port | Service | Ghi chú |
|------|---------|---------|
| 8080 | Nginx | Entry point chính, Cloudflare trỏ vào đây |
| 9001 | MinIO Console | Quản lý object storage (nên firewall) |

Tất cả service khác (api:8000, postgres:5432, es:9200, redis:6379) chỉ expose trong Docker network, không ra ngoài.

### Docker Volumes (persistent data)

| Volume | Dữ liệu |
|--------|----------|
| postgres_data | Database chính |
| es_data | Elasticsearch index |
| redis_data | Cache + Celery broker |
| minio_data | Media files (ảnh/video quảng cáo) |

### Backup dữ liệu

```bash
# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U adsight adsight > backup_$(date +%Y%m%d).sql

# Backup toàn bộ volumes
docker run --rm -v adsight_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

---

## Meta API Token

Token hiện tại là **long-lived token** (60 ngày). Cần renew trước khi hết hạn.

### Tạo long-lived token mới

```bash
curl -G "https://graph.facebook.com/v19.0/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=<APP_ID>" \
  -d "client_secret=<APP_SECRET>" \
  -d "fb_exchange_token=<SHORT_LIVED_TOKEN>"
```

Sau đó cập nhật `.env.production` và restart api:

```bash
# Sửa META_ACCESS_TOKEN trong .env.production
vi /opt/adsight/.env.production

# Restart
docker compose -f docker-compose.prod.yml up -d --force-recreate api celery-worker celery-beat
```
