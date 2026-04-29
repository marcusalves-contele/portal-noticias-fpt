"""
plan_storage.py — Persistencia server-side de planos do Prism Senior Planner.

Cada plano = 1 arquivo JSON em output/plans/{plan_id}.json.
plan_id = timestamp + hash curto. Permite versionar refinamentos via parent_id.

Estrutura do arquivo:
{
  "plan_id": "20260429-1450-a3f9",
  "created_at": "2026-04-29T14:50:12.345Z",
  "updated_at": "2026-04-29T15:10:33.001Z",
  "parent_id": null,                  # se for refinamento, aponta pro original
  "version": 1,                       # incrementa a cada refine
  "input": {                           # entrada do user
    "topic": "cartao combustivel CPK",
    "format_hint": "live_tematica",
    "message": "Monta plano completo pra...",
    "feedback_history": []            # lista de feedback applied em refines
  },
  "plan": {...},                      # output JSON do Pro (PLAN_SCHEMA)
  "validation": {...},                # validacao do plan_schema.validate_plan
  "script": null | {...},             # roteiro gerado depois (se aprovado)
  "status": "draft" | "refined" | "approved" | "scripted",
  "tags": []                          # opcional, pra filtro futuro
}
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

# Em producao Railway, volume persistente esta montado em /app/nutella-creator/data/.
# Salvar planos em data/plans/ pra sobreviver entre deploys (output/ e effemeral).
# Override via env PLANS_DIR_PATH se precisar mudar.
PLANS_DIR = Path(
    os.environ.get("PLANS_DIR_PATH")
    or (Path(__file__).parent / "data" / "plans")
)


def _ensure_dir():
    PLANS_DIR.mkdir(parents=True, exist_ok=True)


def _make_id() -> str:
    """plan_id: YYYYMMDD-HHMM-XXXX (4 hex). Ordenable + curto."""
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    suf = uuid.uuid4().hex[:4]
    return f"{ts}-{suf}"


def save_new_plan(input_data: dict, plan: dict, validation: dict) -> str:
    """Salva novo plano. Retorna plan_id."""
    _ensure_dir()
    plan_id = _make_id()
    now = datetime.now().isoformat()
    record = {
        "plan_id": plan_id,
        "created_at": now,
        "updated_at": now,
        "parent_id": None,
        "version": 1,
        "input": input_data,
        "plan": plan,
        "validation": validation,
        "script": None,
        "status": "draft",
        "tags": [],
    }
    path = PLANS_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan_id


def save_refined_plan(parent_id: str, feedback: str, new_plan: dict, new_validation: dict) -> str:
    """
    Salva refinamento como NOVA versao. parent_id aponta pro original.
    Retorna plan_id novo.
    """
    parent = get_plan(parent_id)
    if not parent:
        raise ValueError(f"Parent plan nao encontrado: {parent_id}")
    _ensure_dir()
    plan_id = _make_id()
    now = datetime.now().isoformat()

    feedback_history = parent.get("input", {}).get("feedback_history", []).copy()
    feedback_history.append({"ts": now, "feedback": feedback})

    new_input = parent.get("input", {}).copy()
    new_input["feedback_history"] = feedback_history

    record = {
        "plan_id": plan_id,
        "created_at": now,
        "updated_at": now,
        "parent_id": parent_id,
        "version": parent.get("version", 1) + 1,
        "input": new_input,
        "plan": new_plan,
        "validation": new_validation,
        "script": None,
        "status": "refined",
        "tags": parent.get("tags", []),
    }
    path = PLANS_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan_id


def attach_script(plan_id: str, script: dict) -> bool:
    """Atualiza plano com script gerado. Marca status='scripted'."""
    record = get_plan(plan_id)
    if not record:
        return False
    record["script"] = script
    record["status"] = "scripted"
    record["updated_at"] = datetime.now().isoformat()
    path = PLANS_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def update_status(plan_id: str, status: str) -> bool:
    record = get_plan(plan_id)
    if not record:
        return False
    record["status"] = status
    record["updated_at"] = datetime.now().isoformat()
    path = PLANS_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def get_plan(plan_id: str) -> dict | None:
    """Le plano. Retorna None se nao existir."""
    if not _is_safe_id(plan_id):
        return None
    path = PLANS_DIR / f"{plan_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_safe_id(plan_id: str) -> bool:
    """Sanitiza plan_id pra evitar path traversal."""
    return bool(re.fullmatch(r"[a-zA-Z0-9_-]+", plan_id))


def list_plans(limit: int = 50, status_filter: str | None = None) -> list[dict]:
    """
    Lista planos ordenados por created_at desc. Retorna summary (sem o plan completo).
    """
    _ensure_dir()
    out = []
    for p in PLANS_DIR.glob("*.json"):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            if status_filter and r.get("status") != status_filter:
                continue
            plan = r.get("plan", {}) or {}
            input_data = r.get("input", {}) or {}
            slot = plan.get("slot_recommendation", {}) or {}
            structure = plan.get("structure", {}) or {}
            out.append({
                "plan_id": r.get("plan_id"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "parent_id": r.get("parent_id"),
                "version": r.get("version", 1),
                "status": r.get("status", "draft"),
                "topic": input_data.get("topic", ""),
                "format_hint": input_data.get("format_hint", ""),
                "summary": (plan.get("plan_summary") or "")[:200],
                "slot_date": slot.get("date", ""),
                "live_number": slot.get("live_number"),
                "format": structure.get("format", ""),
                "duration_minutes": structure.get("duration_minutes"),
                "feedback_count": len(input_data.get("feedback_history", [])),
                "has_script": bool(r.get("script")),
                "validation_ok": bool((r.get("validation", {}) or {}).get("ok")),
            })
        except Exception:
            continue
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out[:limit]


def get_lineage(plan_id: str) -> list[dict]:
    """
    Retorna lineage completa (ancestral chain) de um plano: [origem, refine1, refine2, ..., self].
    Util pra UI mostrar evolucao.
    """
    chain = []
    current = get_plan(plan_id)
    while current:
        chain.append(current)
        parent_id = current.get("parent_id")
        if not parent_id:
            break
        current = get_plan(parent_id)
    chain.reverse()
    return chain


def delete_plan(plan_id: str) -> bool:
    if not _is_safe_id(plan_id):
        return False
    path = PLANS_DIR / f"{plan_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
