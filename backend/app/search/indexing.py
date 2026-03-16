from elasticsearch import AsyncElasticsearch

from app.config import settings

ADS_INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "vietnamese_analyzer": {
                    "type": "custom",
                    "tokenizer": "icu_tokenizer",
                    "filter": [
                        "lowercase",
                        "icu_folding",
                        "vietnamese_stop",
                        "vietnamese_synonym",
                    ],
                }
            },
            "filter": {
                "vietnamese_stop": {
                    "type": "stop",
                    "stopwords": [
                        "và", "của", "là", "có", "được", "cho", "với", "này",
                        "trong", "không", "những", "một", "các", "để", "từ",
                        "khi", "đã", "như", "cũng", "nhưng", "hay", "hoặc",
                    ],
                },
                "vietnamese_synonym": {
                    "type": "synonym",
                    "synonyms": [
                        "kem chống nắng, kcn, sunscreen, chống nắng",
                        "serum, tinh chất, essence",
                        "son môi, son, lipstick",
                        "áo thun, áo phông, tshirt, t-shirt",
                        "giảm giá, sale, khuyến mãi, km, flash sale",
                        "miễn phí, free, 0 đồng",
                        "điện thoại, smartphone, dt",
                        "quần áo, thời trang, fashion",
                        "mỹ phẩm, cosmetics, skincare",
                        "đồ ăn, thức ăn, food, đồ ăn vặt",
                        "giày dép, giày, dép, shoes",
                        "túi xách, balo, bag",
                    ],
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "platform": {"type": "keyword"},
            "platform_ad_id": {"type": "keyword"},
            "advertiser_id": {"type": "keyword"},
            "advertiser_name": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "advertiser_page_url": {"type": "keyword"},
            "ad_type": {"type": "keyword"},
            "headline": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
            },
            "body_text": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
            },
            "cta_type": {"type": "keyword"},
            "media_urls": {"type": "keyword"},
            "thumbnail_url": {"type": "keyword"},
            "landing_page_url": {"type": "keyword"},
            "target_countries": {"type": "keyword"},
            "target_age_min": {"type": "integer"},
            "target_age_max": {"type": "integer"},
            "target_gender": {"type": "keyword"},
            "likes": {"type": "integer"},
            "comments": {"type": "integer"},
            "shares": {"type": "integer"},
            "impressions_lower": {"type": "long"},
            "impressions_upper": {"type": "long"},
            "spend_lower": {"type": "float"},
            "spend_upper": {"type": "float"},
            "language": {"type": "keyword"},
            "category": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "sentiment": {"type": "float"},
            "first_seen": {"type": "date"},
            "last_seen": {"type": "date"},
            "is_active": {"type": "boolean"},
            "created_at": {"type": "date"},
            # Enrichment fields
            "category_l1": {"type": "keyword"},
            "category_l2": {"type": "keyword"},
            "detected_offers": {"type": "object", "enabled": False},
            "emotional_triggers": {"type": "object", "enabled": False},
            "target_audience_guess": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
            },
            "estimated_daily_spend": {"type": "float"},
            "estimated_total_spend": {"type": "float"},
            "cpm_estimate": {"type": "float"},
            "engagement_rate": {"type": "float"},
            "viral_score": {"type": "float"},
            "is_hot": {"type": "boolean"},
        }
    },
}


async def create_ads_index(es: AsyncElasticsearch):
    index = settings.es_ads_index
    exists = await es.indices.exists(index=index)
    if not exists:
        await es.indices.create(
            index=index,
            settings=ADS_INDEX_SETTINGS["settings"],
            mappings=ADS_INDEX_SETTINGS["mappings"],
        )
        print(f"Created index '{index}' with Vietnamese analyzer")
    else:
        print(f"Index '{index}' already exists")


async def index_ad(es: AsyncElasticsearch, ad_id: str, ad_data: dict):
    await es.index(
        index=settings.es_ads_index,
        id=ad_id,
        document=ad_data,
    )


async def bulk_index_ads(es: AsyncElasticsearch, ads: list[dict]):
    if not ads:
        return
    actions = []
    for ad in ads:
        ad_copy = ad.copy()
        ad_id = ad_copy.pop("id", None) or ad_copy.get("platform_ad_id")
        actions.append({"index": {"_index": settings.es_ads_index, "_id": str(ad_id)}})
        actions.append(ad_copy)

    await es.bulk(operations=actions, refresh="wait_for")
