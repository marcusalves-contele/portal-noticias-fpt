"""
knowledge_base.py — Knowledge layer for PRISM OS Studio.
Loads domain docs from knowledge/ dir and builds system prompts per mode.
Includes Operational Memory (Layer 2): learned patterns from user feedback.
"""

import os
import json
from datetime import datetime
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# --- Operational Memory (Layer 2) ---

MEMORY_FILE = Path(__file__).parent / "operational_memory.json"
MAX_MEMORIES = 20


def _load_memories() -> list:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_memories(memories: list):
    MEMORY_FILE.write_text(
        json.dumps(memories[-MAX_MEMORIES:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_memory(memory_type: str, content: str, metadata: dict = None):
    """Add operational memory entry. Types: approval, rejection, feedback, pattern."""
    memories = _load_memories()
    memories.append({
        "type": memory_type,
        "content": content,
        "metadata": metadata or {},
        "ts": datetime.now().isoformat(),
    })
    _save_memories(memories)


def get_memories_context() -> str:
    """Get operational memories formatted for system prompt injection."""
    memories = _load_memories()
    if not memories:
        return ""

    lines = ["## OPERATIONAL MEMORY (learned from past sessions)\n"]
    for m in memories:
        prefix = {
            "approval": "GOOD",
            "rejection": "AVOID",
            "feedback": "NOTE",
            "pattern": "PATTERN",
        }.get(m["type"], "NOTE")
        lines.append(f"- [{prefix}] {m['content']}")

    return "\n".join(lines)


def list_memories() -> list:
    return _load_memories()


def clear_memories():
    _save_memories([])

# Registry: each doc with metadata
KNOWLEDGE_REGISTRY = [
    {
        "id": "brand-fpt-agent",
        "filename": "brand-fpt-agent.md",
        "category": "brand",
        "description": "Biblia da marca FPT para agentes: design tokens, 7 personas, tom de voz, regras absolutas",
        "enabled": True,
        "priority": 1,
        "tokens_est": 7500,
    },
    {
        "id": "brand-fpt",
        "filename": "brand-fpt.md",
        "category": "brand",
        "description": "Marca FPT completa: posicionamento Sage Pragmatico, arquetipo, paleta, tipografia",
        "enabled": True,
        "priority": 1,
        "tokens_est": 6500,
    },
    {
        "id": "sistema-thumbnails-ai",
        "filename": "sistema-thumbnails-ai.md",
        "category": "technical",
        "description": "Specs Gemini: temperature=0, face-lock, refs, anti-patterns thumbnails",
        "enabled": True,
        "priority": 1,
        "tokens_est": 1700,
    },
    {
        "id": "thumbnail-ai-creator",
        "filename": "thumbnail-ai-creator.md",
        "category": "technical",
        "description": "Sistema thumbnail implementado: face-lock 2 etapas, modelos",
        "enabled": True,
        "priority": 1,
        "tokens_est": 150,
    },
    {
        "id": "entrevista-arquetipo-julio",
        "filename": "entrevista-arquetipo-julio-PROCESSADO.md",
        "category": "brand",
        "description": "Autenticidade Julio: arquetipo Sage Pragmatico, frases reais, viloes, proposito",
        "enabled": True,
        "priority": 1,
        "tokens_est": 1300,
    },
    {
        "id": "design-system-fleet",
        "filename": "design-system-fleet.md",
        "category": "brand",
        "description": "Design system Fleet: cores oficiais, logo, tipografia DM Serif/Sans",
        "enabled": True,
        "priority": 1,
        "tokens_est": 500,
    },
    {
        "id": "prism-os",
        "filename": "prism-os.md",
        "category": "content",
        "description": "Visao PRISM OS: calendario 4 videos/semana, modulos, pipeline",
        "enabled": True,
        "priority": 2,
        "tokens_est": 2200,
    },
    {
        "id": "nutella-plano-producao",
        "filename": "nutella-plano-producao-master.md",
        "category": "content",
        "description": "Formula cortes virais: 4/semana, regras publicacao, backlog priorizado",
        "enabled": True,
        "priority": 2,
        "tokens_est": 4000,
    },
    {
        "id": "playbook-conteudo",
        "filename": "playbook-conteudo-contele-2026.md",
        "category": "content",
        "description": "Framework conteudo: E-E-A-T, diferencial especialista real, funil",
        "enabled": True,
        "priority": 2,
        "tokens_est": 3300,
    },
    {
        "id": "estrategia-instagram",
        "filename": "estrategia-instagram-2026.md",
        "category": "reference",
        "description": "Hook patterns: acusatorio, numero, contraste. Algoritmo 2026",
        "enabled": True,
        "priority": 2,
        "tokens_est": 1400,
    },
]

# Which categories to include per mode
MODE_CATEGORIES = {
    "thumbnail": ["brand", "technical", "reference"],
    "research": ["brand", "content", "reference"],
    "script": ["brand", "content", "reference"],
    "strategy": ["brand", "content", "technical", "reference"],
    "question": ["brand", "content", "technical", "reference"],
}

# In-memory cache
_cache: dict[str, str] = {}
_flags_override: dict[str, bool] = {}


def _load_doc(doc: dict) -> str:
    """Load a single doc from disk, with cache."""
    doc_id = doc["id"]
    if doc_id not in _cache:
        path = KNOWLEDGE_DIR / doc["filename"]
        if path.exists():
            _cache[doc_id] = path.read_text(encoding="utf-8")
        else:
            _cache[doc_id] = ""
    return _cache[doc_id]


def reload_cache():
    """Force reload all docs from disk."""
    _cache.clear()
    for doc in KNOWLEDGE_REGISTRY:
        _load_doc(doc)


def set_flag(doc_id: str, enabled: bool):
    """Override enabled flag for a doc at runtime."""
    _flags_override[doc_id] = enabled


def is_enabled(doc: dict) -> bool:
    """Check if doc is enabled (respecting runtime overrides)."""
    if doc["id"] in _flags_override:
        return _flags_override[doc["id"]]
    return doc.get("enabled", True)


def list_knowledge() -> list[dict]:
    """List all docs with current flags and load status."""
    result = []
    for doc in KNOWLEDGE_REGISTRY:
        content = _load_doc(doc)
        result.append({
            "id": doc["id"],
            "filename": doc["filename"],
            "category": doc["category"],
            "description": doc["description"],
            "enabled": is_enabled(doc),
            "priority": doc["priority"],
            "tokens_est": doc["tokens_est"],
            "loaded": bool(content),
        })
    return result


def get_system_prompt(mode: str = "question", flags: dict | None = None) -> str:
    """Build system prompt for a given mode, respecting flags."""
    allowed_categories = MODE_CATEGORIES.get(mode, MODE_CATEGORIES["question"])

    # Apply temporary flags if provided
    effective_flags = dict(_flags_override)
    if flags:
        effective_flags.update(flags)

    sections = []
    total_tokens = 0

    # Sort by priority (1 first)
    sorted_docs = sorted(KNOWLEDGE_REGISTRY, key=lambda d: d["priority"])

    for doc in sorted_docs:
        if doc["category"] not in allowed_categories:
            continue

        enabled = effective_flags.get(doc["id"], doc.get("enabled", True))
        if not enabled:
            continue

        content = _load_doc(doc)
        if not content:
            continue

        sections.append(f"## [{doc['category'].upper()}] {doc['description']}\n\n{content}")
        total_tokens += doc["tokens_est"]

    if not sections:
        return ""

    # Append operational memories after docs
    memories_ctx = get_memories_context()
    if memories_ctx:
        sections.append(memories_ctx)

    header = (
        f"You are PRISM Studio, the AI content production assistant for Frota Para Todos (FPT) "
        f"and Contele. You have deep knowledge of the brand, content strategy, and production pipeline.\n\n"
        f"Mode: {mode.upper()} | Knowledge loaded: {len(sections)} docs (~{total_tokens} tokens)\n\n"
        f"Use the knowledge below to give informed, brand-aligned responses. "
        f"When generating thumbnails, follow the technical specs exactly. "
        f"When answering questions, cite specific data from the docs.\n\n"
        f"---\n\n"
    )

    return header + "\n\n---\n\n".join(sections)


def get_tokens_summary(mode: str = "question", flags: dict | None = None) -> dict:
    """Get token usage summary for a mode."""
    allowed_categories = MODE_CATEGORIES.get(mode, MODE_CATEGORIES["question"])
    effective_flags = dict(_flags_override)
    if flags:
        effective_flags.update(flags)

    total = 0
    enabled_count = 0

    for doc in KNOWLEDGE_REGISTRY:
        if doc["category"] not in allowed_categories:
            continue
        enabled = effective_flags.get(doc["id"], doc.get("enabled", True))
        if enabled:
            total += doc["tokens_est"]
            enabled_count += 1

    return {
        "mode": mode,
        "docs_enabled": enabled_count,
        "tokens_total": total,
        "context_pct": round(total / 1_000_000 * 100, 2),
    }
