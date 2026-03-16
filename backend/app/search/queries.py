from app.schemas.search import SearchRequest


def build_search_query(request: SearchRequest) -> dict:
    must = []
    filters = []

    # Text search
    if request.q:
        must.append({
            "multi_match": {
                "query": request.q,
                "fields": [
                    "headline^3",
                    "body_text^2",
                    "advertiser_name^2",
                    "category",
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "analyzer": "vietnamese_analyzer",
            }
        })

    # Platform filter
    if request.platform:
        platforms = [p.strip() for p in request.platform.split(",")]
        filters.append({"terms": {"platform": platforms}})

    # Country filter
    if request.country:
        countries = [c.strip().upper() for c in request.country.split(",")]
        filters.append({"terms": {"target_countries": countries}})

    # Ad type filter
    if request.ad_type:
        ad_types = [t.strip() for t in request.ad_type.split(",")]
        filters.append({"terms": {"ad_type": ad_types}})

    # Date range
    date_range = {}
    if request.date_from:
        date_range["gte"] = request.date_from
    if request.date_to:
        date_range["lte"] = request.date_to
    if date_range:
        filters.append({"range": {"first_seen": date_range}})

    # Min likes
    if request.min_likes:
        filters.append({"range": {"likes": {"gte": request.min_likes}}})

    # Enrichment filters
    if request.category_l1:
        filters.append({"term": {"category_l1": request.category_l1}})
    if request.category_l2:
        filters.append({"term": {"category_l2": request.category_l2}})
    if request.min_spend is not None:
        filters.append({"range": {"estimated_daily_spend": {"gte": request.min_spend}}})
    if request.max_spend is not None:
        filters.append({"range": {"estimated_daily_spend": {"lte": request.max_spend}}})
    if request.min_viral_score is not None:
        filters.append({"range": {"viral_score": {"gte": request.min_viral_score}}})
    if request.is_hot is not None:
        filters.append({"term": {"is_hot": request.is_hot}})
    if request.has_discount is True:
        filters.append({"exists": {"field": "detected_offers"}})

    # Build bool query
    bool_query = {}
    if must:
        bool_query["must"] = must
    else:
        bool_query["must"] = [{"match_all": {}}]
    if filters:
        bool_query["filter"] = filters

    # Sort
    sort = []
    if request.sort == "newest":
        sort = [{"first_seen": {"order": "desc", "missing": "_last"}}]
    elif request.sort == "engagement":
        sort = [
            {"likes": {"order": "desc", "missing": "_last"}},
            {"comments": {"order": "desc", "missing": "_last"}},
        ]
    elif request.sort == "viral":
        sort = [{"viral_score": {"order": "desc", "missing": "_last"}}]
    elif request.sort == "relevance" and request.q:
        sort = ["_score", {"likes": {"order": "desc", "missing": "_last"}}]
    else:
        sort = [{"first_seen": {"order": "desc", "missing": "_last"}}]

    return {
        "query": {"bool": bool_query},
        "sort": sort,
        "aggs": {
            "platforms": {"terms": {"field": "platform", "size": 10}},
            "ad_types": {"terms": {"field": "ad_type", "size": 10}},
            "categories": {"terms": {"field": "category", "size": 20}},
            "categories_l1": {"terms": {"field": "category_l1", "size": 20}},
        },
    }
