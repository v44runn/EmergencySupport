import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

KEY_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# guard so uvicorn --reload doesn't initialize twice
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(KEY_PATH))

db = firestore.client()

REQUESTS = "requests"
VEHICLES = "vehicles"
ZONES = "blocked_zones"
PLANS = "plans"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- generic helpers ----------

def _save(collection: str, id_: str, data: dict) -> dict:
    db.collection(collection).document(id_).set(data)
    return data

def _get(collection: str, id_: str) -> Optional[dict]:
    doc = db.collection(collection).document(id_).get()
    return (doc.to_dict() or {}) if doc.exists else None

def _list(collection: str) -> list[dict]:
    return [d.to_dict() or {} for d in db.collection(collection).stream()]

def _delete(collection: str, id_: str) -> bool:
    ref = db.collection(collection).document(id_)
    existed = ref.get().exists
    ref.delete()
    return existed


# ---------- requests ----------

def create_request(data: dict) -> dict:
    id_ = new_id("req")
    return _save(REQUESTS, id_, {**data, "id": id_, "status": "pending", "created_at": now_iso()})


def list_requests(status: Optional[str] = None) -> list[dict]:
    items = _list(REQUESTS)
    return [r for r in items if status is None or r.get("status") == status]


def get_request(id_: str) -> Optional[dict]:
    return _get(REQUESTS, id_)


def update_request_status(id_: str, status: str) -> Optional[dict]:
    if not _get(REQUESTS, id_):
        return None
    db.collection(REQUESTS).document(id_).update({"status": status})
    return _get(REQUESTS, id_)


def delete_request(id_: str) -> bool:
    return _delete(REQUESTS, id_)


# ---------- vehicles ----------

def create_vehicle(data: dict) -> dict:
    id_ = new_id("veh")
    return _save(VEHICLES, id_, {**data, "id": id_})


def list_vehicles() -> list[dict]:
    return _list(VEHICLES)


def delete_vehicle(id_: str) -> bool:
    return _delete(VEHICLES, id_)


# ---------- blocked zones ----------

def create_zone(data: dict) -> dict:
    id_ = new_id("zone")
    return _save(ZONES, id_, {**data, "id": id_, "created_at": now_iso()})


def list_zones() -> list[dict]:
    return _list(ZONES)


def delete_zone(id_: str) -> bool:
    return _delete(ZONES, id_)


# ---------- plans (dispatch assignments) ----------

def save_plan(plan: dict) -> dict:
    return _save(PLANS, plan["id"], plan)


def list_plans() -> list[dict]:
    return sorted(_list(PLANS), key=lambda p: p.get("version", 0))


def latest_plan() -> Optional[dict]:
    plans = list_plans()
    return plans[-1] if plans else None
