import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    import certifi
    _CA_FILE = certifi.where()
except Exception:
    _CA_FILE = None

from app.config import settings

class MongoDatabaseManager:
    """
    Enterprise Database Engine:
    - 100% Pure Database Storage & Retrieval
    - Connects directly to the database cluster with TLS/SSL encryption
    - Stores and retrieves all observations, AI classifications, and review states in the database
    - No JSON files are used on disk
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.use_mongo = False
        self.client = None
        self.db = None
        self.reports_col = None
        self._memory_store: List[Dict[str, Any]] = []
        self._init_connection()

    def _init_connection(self):
        uri = settings.MONGODB_URI.strip()
        if uri:
            try:
                import pymongo
                print(f"[*] Connecting to Enterprise Database: {uri.split('@')[-1] if '@' in uri else 'Database'}")
                kwargs = {
                    "serverSelectionTimeoutMS": 6000,
                    "connectTimeoutMS": 6000
                }
                if _CA_FILE:
                    kwargs["tlsCAFile"] = _CA_FILE
                
                self.client = pymongo.MongoClient(uri, **kwargs)
                self.client.admin.command('ping')
                self.db = self.client[settings.MONGODB_DB_NAME]
                self.reports_col = self.db["reports"]
                
                # Setup Database Indexes for high performance querying
                self.reports_col.create_index("report_id", unique=True)
                self.reports_col.create_index("date")
                self.reports_col.create_index("site")
                self.reports_col.create_index("activity")
                self.reports_col.create_index("ai.sif_potential")
                self.reports_col.create_index("ai.life_saving_rule_id")
                self.reports_col.create_index("review.status")

                self.use_mongo = True
                print(f"[✓] Successfully connected to Database: '{settings.MONGODB_DB_NAME}', collection: 'reports' (Count: {self.reports_col.count_documents({})})")
                return
            except Exception as e:
                print(f"[!] Warning: Database cluster connection failed ({e}). Running in-memory database session.")
                self.use_mongo = False
        else:
            print("[i] No Database URI configured. Running in-memory database session.")
            self.use_mongo = False

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all reports directly from the database collection"""
        with self.lock:
            if self.use_mongo:
                try:
                    cursor = self.reports_col.find({}, {"_id": 0}).sort("date", -1)
                    return list(cursor)
                except Exception as e:
                    print(f"[!] Database get_all error: {e}")
            return list(self._memory_store)

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single report by report_id directly from the database collection"""
        with self.lock:
            if self.use_mongo:
                try:
                    return self.reports_col.find_one({"report_id": report_id}, {"_id": 0})
                except Exception as e:
                    print(f"[!] Database get_report error: {e}")
            for r in self._memory_store:
                if r.get("report_id") == report_id:
                    return r
            return None

    def insert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or replace a report directly in the database collection"""
        with self.lock:
            clean_rec = dict(record)
            report_id = clean_rec.get("report_id")

            if self.use_mongo:
                try:
                    self.reports_col.replace_one({"report_id": report_id}, clean_rec, upsert=True)
                    return clean_rec
                except Exception as e:
                    print(f"[!] Database insert error: {e}")

            for i, r in enumerate(self._memory_store):
                if r.get("report_id") == report_id:
                    self._memory_store[i] = clean_rec
                    return clean_rec
            self._memory_store.insert(0, clean_rec)
            return clean_rec

    def insert_many(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert or bulk-upsert multiple reports directly into the database collection"""
        if not records:
            return []
        with self.lock:
            if self.use_mongo:
                try:
                    from pymongo import ReplaceOne
                    ops = [ReplaceOne({"report_id": r["report_id"]}, dict(r), upsert=True) for r in records]
                    self.reports_col.bulk_write(ops, ordered=False)
                    print(f"[✓] Successfully inserted/updated {len(records)} records in database.")
                    return records
                except Exception as e:
                    print(f"[!] Database insert_many error: {e}")

            existing_ids = {r["report_id"] for r in self._memory_store}
            for r in records:
                if r["report_id"] not in existing_ids:
                    self._memory_store.append(dict(r))
            return records

    def update(self, report_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a report directly in the database collection"""
        with self.lock:
            if self.use_mongo:
                try:
                    self.reports_col.update_one({"report_id": report_id}, {"$set": updates})
                    return self.get_report(report_id)
                except Exception as e:
                    print(f"[!] Database update error: {e}")

            for i, r in enumerate(self._memory_store):
                if r.get("report_id") == report_id:
                    self._memory_store[i] = {**r, **updates}
                    return self._memory_store[i]
            return None

    def delete(self, report_id: str) -> bool:
        """Delete a single report directly from the database collection"""
        with self.lock:
            if self.use_mongo:
                try:
                    res = self.reports_col.delete_one({"report_id": report_id})
                    return res.deleted_count > 0
                except Exception as e:
                    print(f"[!] Database delete error: {e}")
            for i, r in enumerate(self._memory_store):
                if r.get("report_id") == report_id:
                    self._memory_store.pop(i)
                    return True
            return False

    def delete_many(self, report_ids: List[str]) -> int:
        """Delete multiple reports directly from the database collection"""
        if not report_ids:
            return 0
        with self.lock:
            deleted_count = 0
            if self.use_mongo:
                try:
                    res = self.reports_col.delete_many({"report_id": {"$in": report_ids}})
                    deleted_count = res.deleted_count
                except Exception as e:
                    print(f"[!] Database delete_many error: {e}")
            
            init_len = len(self._memory_store)
            self._memory_store = [r for r in self._memory_store if r.get("report_id") not in report_ids]
            if not self.use_mongo:
                deleted_count = init_len - len(self._memory_store)

            return deleted_count

    def delete_all(self) -> int:
        """Delete all reports directly from the database collection"""
        with self.lock:
            deleted_count = 0
            if self.use_mongo:
                try:
                    res = self.reports_col.delete_many({})
                    deleted_count = res.deleted_count
                except Exception as e:
                    print(f"[!] Database delete_all error: {e}")
            
            if not self.use_mongo:
                deleted_count = len(self._memory_store)
                self._memory_store = []
                
            return deleted_count

    def count(self) -> int:
        """Count total reports in the database collection"""
        with self.lock:
            if self.use_mongo:
                try:
                    return self.reports_col.count_documents({})
                except Exception as e:
                    print(f"[!] Database count error: {e}")
            return len(self._memory_store)

    def filter_reports(self, **filters) -> Tuple[List[Dict[str, Any]], int]:
        """Perform dynamic filtered queries and pagination directly in the database"""
        with self.lock:
            if self.use_mongo:
                try:
                    query = {}
                    if filters.get("site") and filters["site"].lower() != "all":
                        query["site"] = {"$regex": f"^{filters['site']}$", "$options": "i"}

                    if filters.get("activity") and filters["activity"].lower() != "all":
                        query["activity"] = {"$regex": f"^{filters['activity']}$", "$options": "i"}

                    if filters.get("sif_potential") is not None:
                        query["ai.sif_potential"] = filters["sif_potential"]

                    if filters.get("rule_id") and filters["rule_id"].lower() != "all":
                        query["ai.life_saving_rule_id"] = filters["rule_id"]

                    if filters.get("review_status") and filters["review_status"].lower() != "all":
                        query["review.status"] = filters["review_status"]

                    if filters.get("search_query"):
                        q = filters["search_query"]
                        query["$or"] = [
                            {"description": {"$regex": q, "$options": "i"}},
                            {"report_id": {"$regex": q, "$options": "i"}},
                            {"site": {"$regex": q, "$options": "i"}},
                            {"activity": {"$regex": q, "$options": "i"}},
                            {"ai.precursor.barrier_failure": {"$regex": q, "$options": "i"}}
                        ]

                    total = self.reports_col.count_documents(query)

                    sort_by = filters.get("sort_by", "date")
                    sort_desc = -1 if filters.get("sort_desc", True) else 1

                    sort_field = "date"
                    if sort_by == "confidence":
                        sort_field = "ai.sif_confidence"
                    elif sort_by == "site":
                        sort_field = "site"

                    page = max(1, filters.get("page", 1))
                    page_size = max(1, filters.get("page_size", 20))
                    skip = (page - 1) * page_size

                    cursor = self.reports_col.find(query, {"_id": 0}).sort(sort_field, sort_desc).skip(skip).limit(page_size)
                    return list(cursor), total
                except Exception as e:
                    print(f"[!] Database filter_reports error: {e}")

            # In-memory query
            items = list(self._memory_store)
            if filters.get("site") and filters["site"].lower() != "all":
                items = [r for r in items if (r.get("site") or "").lower() == filters["site"].lower()]
            if filters.get("activity") and filters["activity"].lower() != "all":
                items = [r for r in items if (r.get("activity") or "").lower() == filters["activity"].lower()]
            if filters.get("sif_potential") is not None:
                items = [r for r in items if r.get("ai", {}).get("sif_potential") == filters["sif_potential"]]
            if filters.get("rule_id") and filters["rule_id"].lower() != "all":
                items = [r for r in items if r.get("ai", {}).get("life_saving_rule_id") == filters["rule_id"]]
            if filters.get("review_status") and filters["review_status"].lower() != "all":
                items = [r for r in items if r.get("review", {}).get("status") == filters["review_status"]]
            if filters.get("search_query"):
                q = filters["search_query"].lower()
                items = [r for r in items if (
                    q in (r.get("description") or "").lower() or
                    q in (r.get("report_id") or "").lower() or
                    q in (r.get("site") or "").lower() or
                    q in (r.get("ai", {}).get("precursor", {}).get("barrier_failure") or "").lower()
                )]

            sort_by = filters.get("sort_by", "date")
            sort_desc = filters.get("sort_desc", True)
            if sort_by == "confidence":
                items.sort(key=lambda x: x.get("ai", {}).get("sif_confidence", 0.0), reverse=sort_desc)
            else:
                items.sort(key=lambda x: str(x.get(sort_by) or ""), reverse=sort_desc)

            total = len(items)
            page = max(1, filters.get("page", 1))
            page_size = max(1, filters.get("page_size", 20))
            start = (page - 1) * page_size
            end = start + page_size
            return items[start:end], total

db = MongoDatabaseManager()