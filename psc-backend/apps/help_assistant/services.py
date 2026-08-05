from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from django.conf import settings


DOC_GLOBS = (
    "Docs/*.md",
    "Docs/modules/**/*.md",
    "UPDATED_DOCS_V2/**/*.md",
    "safety_docsuite/*.md",
    "APP_FLOW.md",
    "README.md",
)

SKIPPED_DOC_PATTERNS = (
    "progress",
    "test_progress",
    "LESSONS",
    "DEBUG_AGENT",
    "DEAD_CODE",
    "CLAUDE",
)

MODULE_ALIASES = {
    "inspection": ("inspection", "deficiency", "defect", "psc", "audit", "port state"),
    "car": ("car", "corrective action", "root cause", "evidence", "physical verification"),
    "circular": ("circular", "alert", "work instruction", "ksm library"),
    "orb": ("orb", "oil record book"),
    "safety": ("safety", "near miss", "incident", "soi", "scm", "mscat"),
    "scm": ("scm", "safety committee", "meeting"),
    "sync": ("sync", "offline", "conflict"),
    "notifications": ("notification", "overdue"),
}

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "what",
    "when",
    "where",
    "which",
    "does",
    "how",
    "why",
    "can",
    "will",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "you",
    "your",
    "our",
    "into",
    "about",
    "using",
    "used",
    "user",
    "users",
}

QUERY_EXPANSIONS = {
    "approve": {"approval", "approved", "accept", "accepted", "review", "reviewed"},
    "approval": {"approve", "approved", "accept", "accepted", "review", "reviewed"},
    "car": {"corrective", "action", "correctiveaction"},
    "circular": {"alert", "work", "instruction", "library"},
    "defect": {"deficiency", "finding", "inspection"},
    "deficiency": {"defect", "finding", "inspection"},
    "document": {"docs", "guide", "manual", "pdf"},
    "evidence": {"photo", "attachment", "proof", "document"},
    "incident": {"accident", "safety", "report"},
    "inspection": {"audit", "deficiency", "defect", "finding"},
    "near": {"miss", "safety"},
    "notification": {"alert", "message", "overdue"},
    "orb": {"oil", "record", "book"},
    "reject": {"return", "rework", "send", "back"},
    "report": {"pdf", "document", "export"},
    "scm": {"safety", "committee", "meeting"},
    "submit": {"create", "save", "send", "raise"},
    "sync": {"offline", "upload", "download", "conflict"},
}

ACTION_TERMS = {
    "add",
    "assign",
    "attach",
    "check",
    "choose",
    "click",
    "close",
    "complete",
    "create",
    "download",
    "enter",
    "fill",
    "open",
    "publish",
    "raise",
    "review",
    "save",
    "select",
    "send",
    "submit",
    "upload",
}


@dataclass(frozen=True)
class HelpChunk:
    id: str
    title: str
    module: str
    source_path: str
    text: str


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: HelpChunk
    score: float


_CACHE: dict[str, Any] = {"loaded_at": 0.0, "chunks": []}


def _project_root() -> Path:
    return Path(settings.BASE_DIR).resolve().parent


def _should_skip(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    return any(pattern.lower() in normalized.lower() for pattern in SKIPPED_DOC_PATTERNS)


def _detect_module(text: str, path: Path) -> str:
    haystack = f"{path.as_posix()} {text[:2000]}".lower()
    for module, aliases in MODULE_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            return module
    return "general"


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_markdown(text: str, source_path: Path) -> list[HelpChunk]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []

    sections: list[tuple[str, str]] = []
    current_title = source_path.stem.replace("_", " ").replace("-", " ").strip() or "Help Document"
    current_lines: list[str] = []

    for line in cleaned.splitlines():
        heading = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if heading and current_lines:
            sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = heading.group(2).strip()
            current_lines = [line]
        else:
            if heading:
                current_title = heading.group(2).strip()
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    chunks: list[HelpChunk] = []
    root = _project_root()
    relative_path = source_path.relative_to(root).as_posix()

    for title, section in sections:
        words = section.split()
        if len(words) <= 260:
            parts = [section]
        else:
            parts = [" ".join(words[i : i + 220]) for i in range(0, len(words), 180)]

        for index, part in enumerate(parts):
            normalized = _clean_text(part)
            if len(normalized) < 80:
                continue
            chunk_hash = hashlib.sha256(f"{relative_path}:{title}:{index}:{normalized}".encode("utf-8")).hexdigest()
            chunks.append(
                HelpChunk(
                    id=chunk_hash[:32],
                    title=title,
                    module=_detect_module(normalized, source_path),
                    source_path=relative_path,
                    text=normalized[:2400],
                )
            )

    return chunks


def load_help_chunks(force: bool = False) -> list[HelpChunk]:
    now = time.time()
    if not force and _CACHE["chunks"] and now - float(_CACHE["loaded_at"]) < 300:
        return list(_CACHE["chunks"])

    root = _project_root()
    chunks: list[HelpChunk] = []
    seen: set[Path] = set()

    for pattern in DOC_GLOBS:
        for path in root.glob(pattern):
            if path in seen or not path.is_file() or _should_skip(path):
                continue
            seen.add(path)
            try:
                chunks.extend(_split_markdown(path.read_text(encoding="utf-8", errors="ignore"), path))
            except OSError:
                continue

    _CACHE["chunks"] = chunks
    _CACHE["loaded_at"] = now
    return list(chunks)


def _normalize_token(token: str) -> str:
    token = token.lower().strip("_")
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


def _tokenize(value: str, *, expand: bool = False) -> set[str]:
    tokens = {
        _normalize_token(token)
        for token in re.findall(r"[a-zA-Z0-9_]{3,}", value.lower())
        if _normalize_token(token) and _normalize_token(token) not in STOP_WORDS
    }
    if not expand:
        return tokens

    expanded = set(tokens)
    for token in tokens:
        expanded.update(QUERY_EXPANSIONS.get(token, set()))
    return expanded


def _query_phrases(question: str) -> set[str]:
    raw_tokens = [
        _normalize_token(token)
        for token in re.findall(r"[a-zA-Z0-9_]{3,}", question.lower())
        if _normalize_token(token) and _normalize_token(token) not in STOP_WORDS
    ]
    phrases: set[str] = set()
    for size in (2, 3):
        for index in range(0, max(len(raw_tokens) - size + 1, 0)):
            phrases.add(" ".join(raw_tokens[index : index + size]))
    return phrases


def _question_intent(question: str) -> str:
    normalized = question.lower()
    if any(word in normalized for word in ("how", "step", "create", "submit", "upload", "download")):
        return "how"
    if any(word in normalized for word in ("why", "purpose", "reason")):
        return "why"
    if any(word in normalized for word in ("error", "issue", "problem", "fail", "stuck")):
        return "troubleshoot"
    return "what"


def _module_from_context(question: str, context: dict[str, Any]) -> str | None:
    candidates = [str(context.get("module") or ""), str(context.get("route") or ""), question]
    haystack = " ".join(candidates).lower()
    for module, aliases in MODULE_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            return module
    return None


def lexical_search(question: str, context: dict[str, Any], limit: int = 5) -> list[RetrievedChunk]:
    chunks = load_help_chunks()
    query_tokens = _tokenize(question, expand=True)
    query_phrases = _query_phrases(question)
    preferred_module = _module_from_context(question, context)
    scored: list[RetrievedChunk] = []

    for chunk in chunks:
        title_tokens = _tokenize(chunk.title)
        body_tokens = _tokenize(chunk.text)
        all_tokens = title_tokens | body_tokens | {chunk.module}
        if not all_tokens:
            continue
        overlap_tokens = query_tokens & all_tokens
        overlap = len(overlap_tokens)
        if overlap == 0:
            continue

        title_overlap = len(query_tokens & title_tokens)
        body_overlap = len(query_tokens & body_tokens)
        coverage = overlap / max(len(query_tokens), 1)
        score = coverage + (title_overlap * 0.45) + (body_overlap * 0.08)

        chunk_haystack = f"{chunk.title}\n{chunk.source_path}\n{chunk.text}".lower()
        phrase_hits = sum(1 for phrase in query_phrases if phrase in chunk_haystack)
        score += min(phrase_hits * 0.25, 0.75)

        if preferred_module and chunk.module == preferred_module:
            score += 0.45
        if preferred_module and preferred_module in chunk.source_path.lower():
            score += 0.15

        route_hint = str(context.get("route") or "").lower().replace("/", " ").strip()
        if route_hint and route_hint in chunk.text.lower():
            score += 0.15

        scored.append(RetrievedChunk(chunk=chunk, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    response = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object response")
    return data


def _embedding(text: str) -> list[float] | None:
    api_key = os.getenv("HELP_EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
    url = os.getenv("HELP_EMBEDDING_URL") or "https://api.openai.com/v1/embeddings"
    model = os.getenv("HELP_EMBEDDING_MODEL") or "text-embedding-3-small"
    if not api_key:
        return None
    payload = {"model": model, "input": text[:6000]}
    data = _post_json(url, payload, headers={"Authorization": f"Bearer {api_key}"})
    vector = data.get("data", [{}])[0].get("embedding")
    return vector if isinstance(vector, list) else None


def qdrant_search(question: str, context: dict[str, Any], limit: int = 5) -> list[str]:
    qdrant_url = (os.getenv("HELP_QDRANT_URL") or "").rstrip("/")
    collection = os.getenv("HELP_QDRANT_COLLECTION") or "vims_help"
    if not qdrant_url:
        return []

    vector = _embedding(question)
    if not vector:
        return []

    must_filters: list[dict[str, Any]] = []
    module = _module_from_context(question, context)
    if module:
        must_filters.append({"key": "module", "match": {"value": module}})

    payload = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
        "filter": {"must": must_filters} if must_filters else None,
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    data = _post_json(f"{qdrant_url}/collections/{collection}/points/search", payload)
    result = data.get("result", [])
    if not isinstance(result, list):
        return []
    ids: list[str] = []
    for item in result:
        if not isinstance(item, dict):
            continue
        payload_data = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        chunk_id = payload_data.get("chunk_id") or item.get("id")
        if chunk_id:
            ids.append(str(chunk_id))
    return ids


def retrieve_chunks(question: str, context: dict[str, Any], limit: int = 5) -> tuple[list[RetrievedChunk], str]:
    chunks_by_id = {chunk.id: chunk for chunk in load_help_chunks()}
    qdrant_ids: list[str] = []
    try:
        qdrant_ids = qdrant_search(question, context, limit=limit)
    except Exception:
        qdrant_ids = []

    retrieved: list[RetrievedChunk] = []
    for rank, chunk_id in enumerate(qdrant_ids):
        chunk = chunks_by_id.get(chunk_id)
        if chunk:
            retrieved.append(RetrievedChunk(chunk=chunk, score=1.0 - rank * 0.05))

    if retrieved:
        return retrieved[:limit], "qdrant"

    return lexical_search(question, context, limit=limit), "local"


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    sources = []
    for index, item in enumerate(chunks, start=1):
        sources.append(
            f"[{index}] {item.chunk.title}\n"
            f"Module: {item.chunk.module}\n"
            f"Source: {item.chunk.source_path}\n"
            f"Content:\n{item.chunk.text}"
        )
    return (
        "You are the VIMS Help assistant. Answer only from the supplied VIMS help sources. "
        "If the sources do not contain the answer, say that the current Help knowledge base does not contain enough information. "
        "Keep the answer practical and cite source numbers inline.\n\n"
        f"Question: {question}\n\n"
        "Sources:\n"
        + "\n\n".join(sources)
    )


def llm_answer(question: str, chunks: list[RetrievedChunk]) -> str | None:
    api_key = os.getenv("HELP_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    url = os.getenv("HELP_LLM_URL") or "https://api.openai.com/v1/chat/completions"
    model = os.getenv("HELP_LLM_MODEL") or "gpt-4.1-mini"
    if not api_key or not chunks:
        return None
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": "Answer as a concise VIMS software guide."},
            {"role": "user", "content": _build_prompt(question, chunks)},
        ],
    }
    data = _post_json(url, payload, headers={"Authorization": f"Bearer {api_key}"}, timeout=45)
    message = data.get("choices", [{}])[0].get("message", {}).get("content")
    return str(message).strip() if message else None


def _strip_markdown(value: str) -> str:
    value = re.sub(r"```.*?```", " ", value, flags=re.DOTALL)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*[-*]\s+\[[ xX]\]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*[-*]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", value)
    value = re.sub(r"\|", " ", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


def _split_answer_units(text: str) -> list[str]:
    cleaned = _strip_markdown(text)
    if not cleaned:
        return []
    units = re.split(r"(?<=[.!?])\s+|;\s+|\n+", cleaned)
    return [unit.strip(" -") for unit in units if 45 <= len(unit.strip()) <= 320]


def _score_answer_unit(unit: str, query_tokens: set[str], intent: str, source_rank: int) -> float:
    unit_tokens = _tokenize(unit)
    if not unit_tokens:
        return 0.0

    overlap = len(query_tokens & unit_tokens)
    if overlap == 0:
        return 0.0

    score = overlap / max(len(query_tokens), 1)
    normalized = unit.lower()
    if intent == "how" and (ACTION_TERMS & unit_tokens):
        score += 0.35
    if intent == "why" and any(term in normalized for term in ("because", "purpose", "ensure", "so that", "to allow")):
        score += 0.25
    if intent == "troubleshoot" and any(term in normalized for term in ("error", "failed", "required", "missing", "cannot", "must")):
        score += 0.3
    if intent == "what" and any(term in normalized for term in ("is used", "means", "allows", "covers", "includes")):
        score += 0.15
    score += max(0, 0.2 - source_rank * 0.04)
    return score


def _best_answer_units(question: str, chunks: list[RetrievedChunk], limit: int = 4) -> list[tuple[str, int]]:
    query_tokens = _tokenize(question, expand=True)
    intent = _question_intent(question)
    candidates: list[tuple[float, str, int]] = []
    seen_units: set[str] = set()

    for source_index, item in enumerate(chunks[:5], start=1):
        for unit in _split_answer_units(item.chunk.text):
            normalized = unit.lower()
            if normalized in seen_units:
                continue
            seen_units.add(normalized)
            score = _score_answer_unit(unit, query_tokens, intent, source_index)
            if score > 0:
                candidates.append((score, unit, source_index))

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected: list[tuple[str, int]] = []
    selected_words: set[str] = set()
    for _, unit, source_index in candidates:
        unit_words = _tokenize(unit)
        if selected and len(unit_words & selected_words) / max(len(unit_words), 1) > 0.7:
            continue
        selected.append((unit, source_index))
        selected_words.update(unit_words)
        if len(selected) >= limit:
            break

    return selected


def fallback_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            "I could not find enough information in the current VIMS Help documents for this question. "
            "Add the relevant module guide or field/workflow note to the Help knowledge base and re-index it."
        )

    answer_units = _best_answer_units(question, chunks)
    if not answer_units:
        top = chunks[0].chunk
        excerpt = re.sub(r"\s+", " ", _strip_markdown(top.text)).strip()
        if len(excerpt) > 700:
            excerpt = excerpt[:700].rsplit(" ", 1)[0] + "..."
        return f"Based on the current VIMS Help documents, the closest match is from {top.title}: {excerpt}"

    lines = ["Based on the current VIMS Help documents:"]
    for unit, source_index in answer_units:
        lines.append(f"- {unit} [{source_index}]")

    source_lines = []
    used_sources = sorted({source_index for _, source_index in answer_units})
    for source_index in used_sources:
        chunk = chunks[source_index - 1].chunk
        source_lines.append(f"[{source_index}] {chunk.title} - {chunk.source_path}")

    return "\n".join(lines + ["", "Sources:", *source_lines])


def answer_question(question: str, context: dict[str, Any]) -> dict[str, Any]:
    retrieved, retrieval_mode = retrieve_chunks(question, context)
    answer = None
    llm_mode = "not_configured"
    try:
        answer = llm_answer(question, retrieved)
        if answer:
            llm_mode = "configured"
    except Exception:
        answer = None
        llm_mode = "error_fallback"

    if not answer:
        answer = fallback_answer(question, retrieved)

    sources = [
        {
            "id": item.chunk.id,
            "title": item.chunk.title,
            "module": item.chunk.module,
            "source_path": item.chunk.source_path,
            "score": round(item.score, 3),
        }
        for item in retrieved
    ]
    return {
        "answer": answer,
        "sources": sources,
        "retrieval_mode": retrieval_mode,
        "llm_mode": llm_mode,
        "suggested_questions": suggested_questions(context),
    }


def suggested_questions(context: dict[str, Any] | None = None) -> list[str]:
    context = context or {}
    route = str(context.get("route") or "").lower()
    module = _module_from_context("", context)
    if "inspection" in route or module == "inspection":
        return [
            "How do I create an inspection?",
            "Why is the inspection report mandatory?",
            "How are deficiencies and CARs connected?",
            "What happens after an inspection is submitted?",
        ]
    if "car" in route or module == "car":
        return [
            "How do I submit a CAR?",
            "What evidence is required for corrective action?",
            "How does PIC and DPA review work?",
            "Why can a CAR be returned for rework?",
        ]
    if "safety" in route or module in {"safety", "scm"}:
        return [
            "What is the purpose of the SCM module?",
            "How do near miss and incident workflows differ?",
            "How does SCM auto-feed work?",
            "What is an SOI finding?",
        ]
    if "circular" in route or module == "circular":
        return [
            "How do I create a circular?",
            "How do ship users acknowledge circulars?",
            "What is the KSM library?",
        ]
    if "orb" in route or module == "orb":
        return [
            "What is the ORB module used for?",
            "How do ship users enter ORB records?",
            "How are ORB PDFs exported?",
        ]
    return [
        "What is the purpose of the SCM module?",
        "How do I create a defect report?",
        "How does the approval workflow work?",
        "What is the difference between Planned Maintenance and Defect Jobs?",
    ]


def status_payload() -> dict[str, Any]:
    chunks = load_help_chunks()
    modules: dict[str, int] = {}
    for chunk in chunks:
        modules[chunk.module] = modules.get(chunk.module, 0) + 1
    return {
        "documents_indexed": len({chunk.source_path for chunk in chunks}),
        "chunks_indexed": len(chunks),
        "modules": modules,
        "qdrant_configured": bool(os.getenv("HELP_QDRANT_URL")),
        "embedding_configured": bool(os.getenv("HELP_EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")),
        "llm_configured": bool(os.getenv("HELP_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")),
        "source": "file_backed_help_knowledge_base",
    }


def qdrant_upsert_payload() -> str:
    chunks = load_help_chunks()
    points = [
        {
            "id": chunk.id,
            "payload": {
                "chunk_id": chunk.id,
                "title": chunk.title,
                "module": chunk.module,
                "source_path": chunk.source_path,
                "text": chunk.text,
            },
        }
        for chunk in chunks
    ]
    return json.dumps({"points": points}, indent=2)


def upsert_help_chunks_to_qdrant(limit: int | None = None, dry_run: bool = False) -> dict[str, Any]:
    qdrant_url = (os.getenv("HELP_QDRANT_URL") or "").rstrip("/")
    collection = os.getenv("HELP_QDRANT_COLLECTION") or "vims_help"
    if not qdrant_url:
        raise RuntimeError("HELP_QDRANT_URL is not configured.")

    chunks = load_help_chunks()
    if limit is not None:
        chunks = chunks[:limit]
    if not chunks:
        return {"indexed": 0, "collection": collection, "dry_run": dry_run}

    points: list[dict[str, Any]] = []
    vector_size: int | None = None
    for chunk in chunks:
        vector = _embedding(chunk.text)
        if not vector:
            raise RuntimeError("Embedding generation failed. Configure HELP_EMBEDDING_API_KEY or OPENAI_API_KEY.")
        vector_size = vector_size or len(vector)
        points.append(
            {
                "id": chunk.id,
                "vector": vector,
                "payload": {
                    "chunk_id": chunk.id,
                    "title": chunk.title,
                    "module": chunk.module,
                    "source_path": chunk.source_path,
                    "text": chunk.text,
                },
            }
        )

    if dry_run:
        return {
            "indexed": len(points),
            "collection": collection,
            "vector_size": vector_size,
            "dry_run": True,
        }

    collection_payload = {"vectors": {"size": vector_size, "distance": "Cosine"}}
    collection_response = requests.put(
        f"{qdrant_url}/collections/{collection}",
        json=collection_payload,
        timeout=30,
    )
    if collection_response.status_code not in {200, 201}:
        collection_response.raise_for_status()

    batch_size = int(os.getenv("HELP_QDRANT_BATCH_SIZE", "64"))
    for offset in range(0, len(points), batch_size):
        batch = points[offset : offset + batch_size]
        response = requests.put(
            f"{qdrant_url}/collections/{collection}/points",
            params={"wait": "true"},
            json={"points": batch},
            timeout=60,
        )
        response.raise_for_status()

    return {
        "indexed": len(points),
        "collection": collection,
        "vector_size": vector_size,
        "dry_run": False,
    }
