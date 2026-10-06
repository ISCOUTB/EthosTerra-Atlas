"""Pipeline reproducible del corpus B6: registro, normalización, segmentación,
escaneo de PII/inyección y particiones.

Reglas de seguridad:
- toda escritura se confina a una raíz de corpus ubicada bajo `outputs/corpus/`;
- las fuentes originales nunca se sobrescriben (copia de solo lectura);
- el texto del corpus es dato no confiable: los escáneres solo reportan, no ejecutan ni reescriben;
- no se infiere ni completa ningún metadato desconocido.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel

from src.domain.v2.corpus_schemas import (
    AnnotatedSegment,
    SegmentRecord,
    SourceRecord,
    SplitManifest,
    TransformationRecord,
)

PIPELINE_VERSION = "1.0.0"
CORPUS_DIRS = ("sources", "normalized", "annotations/primary", "annotations/secondary",
               "manifests", "splits", "reports", "schemas")
RANDOM_SPLITS = ("train", "validation", "test")


class CorpusPathError(ValueError):
    """Intento de lectura/escritura fuera de la raíz permitida."""


class CorpusIntegrityError(ValueError):
    """Violación de inmutabilidad, hash u offsets."""


# --------------------------------------------------------------------------- rutas


def ensure_corpus_root(corpus_root: Path, allowed_base: Path) -> Path:
    """Valida que la raíz del corpus esté dentro de `allowed_base` (p. ej. `<repo>/outputs/corpus`)."""
    base = allowed_base.resolve()
    root = corpus_root.resolve()
    if base.name != "corpus" or base.parent.name != "outputs":
        raise CorpusPathError("La base permitida debe ser '<repo>/outputs/corpus'.")
    if root == base or not root.is_relative_to(base):
        raise CorpusPathError(f"La raíz del corpus debe estar dentro de {base}.")
    return root


def resolve_inside(corpus_root: Path, relative: str) -> Path:
    target = (corpus_root / relative).resolve()
    if not target.is_relative_to(corpus_root.resolve()):
        raise CorpusPathError(f"Ruta fuera de la raíz del corpus: {relative}")
    return target


def init_layout(corpus_root: Path) -> None:
    for d in CORPUS_DIRS:
        resolve_inside(corpus_root, d).mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- hashing / escritura


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".tmp_", suffix=target.suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_once(corpus_root: Path, relative: str, data: bytes, read_only: bool = False) -> Path:
    """Escribe un artefacto inmutable. Idempotente si el contenido es idéntico; falla si difiere."""
    target = resolve_inside(corpus_root, relative)
    if target.exists():
        if sha256_bytes(target.read_bytes()) != sha256_bytes(data):
            raise CorpusIntegrityError(f"Se rechaza sobrescribir un artefacto inmutable: {relative}")
        return target
    _atomic_write_bytes(target, data)
    if read_only:
        target.chmod(0o444)
    return target


def write_json(corpus_root: Path, relative: str, payload: object) -> Path:
    """Escritura atómica de artefactos derivados (manifiestos, reportes)."""
    target = resolve_inside(corpus_root, relative)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _atomic_write_bytes(target, data)
    return target


def write_jsonl(corpus_root: Path, relative: str, records: Iterable[BaseModel]) -> Path:
    target = resolve_inside(corpus_root, relative)
    lines = [r.model_dump_json() for r in records]
    _atomic_write_bytes(target, ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"))
    return target


def read_jsonl(corpus_root: Path, relative: str, model: type[BaseModel]) -> list[BaseModel]:
    target = resolve_inside(corpus_root, relative)
    if not target.exists():
        return []
    return [model.model_validate_json(line) for line in target.read_text("utf-8").splitlines() if line.strip()]


# --------------------------------------------------------------------------- Fase 1: registro


def register_source(
    corpus_root: Path,
    original_file: Path,
    *,
    source_id: str,
    source_type: str,
    provenance_class: str,
    title: str,
    collector_id: str,
    consent_status: str,
    language: str = "es",
    collection_date: str = "unknown",
    location: str = "unknown",
    participant_code: str = "unknown",
    vereda_code: str = "unknown",
    consent_scope: list[str] | None = None,
    allowed_for_training: bool = False,
    usage_state: str = "context_only",
    version: str = "1.0.0",
    notes: str = "",
) -> SourceRecord:
    """Copia byte a byte el original a `sources/` (solo lectura) y devuelve su registro en borrador."""
    raw = original_file.read_bytes()
    if not raw:
        raise CorpusIntegrityError("La fuente está vacía.")
    suffix = original_file.suffix.lower() or ".txt"
    if suffix not in (".txt", ".md"):
        raise CorpusIntegrityError(f"Formato no soportado en v1: {suffix} (solo texto plano).")
    raw_rel = f"sources/{source_id}{suffix}"
    record = SourceRecord(
        source_id=source_id,
        source_type=source_type,  # type: ignore[arg-type]
        provenance_class=provenance_class,  # type: ignore[arg-type]
        title=title,
        language=language,
        collection_date=collection_date,
        location=location,
        collector_id=collector_id,
        consent_status=consent_status,  # type: ignore[arg-type]
        participant_code=participant_code,
        vereda_code=vereda_code,
        consent_scope=consent_scope or [],
        allowed_for_training=allowed_for_training,
        usage_state=usage_state,  # type: ignore[arg-type]
        raw_path=raw_rel,
        raw_sha256=sha256_bytes(raw),
        version=version,
        status="draft",
        notes=notes,
    )
    write_once(corpus_root, raw_rel, raw, read_only=True)
    return record


def find_duplicates(records: Iterable[SourceRecord]) -> dict[str, list[str]]:
    """Agrupa fuentes con hash idéntico (crudo o normalizado)."""
    groups: dict[str, list[str]] = {}
    for r in records:
        for h in {r.raw_sha256, r.normalized_sha256} - {None}:
            groups.setdefault(h, []).append(r.source_id)  # type: ignore[arg-type]
    return {h: sorted(set(ids)) for h, ids in groups.items() if len(set(ids)) > 1}


def verify_source_hashes(corpus_root: Path, record: SourceRecord) -> list[str]:
    errors: list[str] = []
    raw_path = resolve_inside(corpus_root, record.raw_path)
    if not raw_path.exists():
        errors.append(f"{record.source_id}: falta {record.raw_path}")
    elif sha256_bytes(raw_path.read_bytes()) != record.raw_sha256:
        errors.append(f"{record.source_id}: raw_sha256 no coincide")
    if record.normalized_path:
        norm_path = resolve_inside(corpus_root, record.normalized_path)
        if not norm_path.exists():
            errors.append(f"{record.source_id}: falta {record.normalized_path}")
        elif sha256_bytes(norm_path.read_bytes()) != record.normalized_sha256:
            errors.append(f"{record.source_id}: normalized_sha256 no coincide")
    return errors


# --------------------------------------------------------------------------- Fase 2: normalización

_INLINE_WS = re.compile(r"[ ]{2,}")
_TRAILING_WS = re.compile(r"[ ]+\n")
_BLANK_RUNS = re.compile(r"\n{3,}")
_WS_CHARS = re.compile(r"[\t\u00a0\u2000-\u200a\u202f\u205f\u3000]")


def normalize_text(raw: bytes) -> tuple[str, list[tuple[str, str, str, str]]]:
    """Normalización conservadora: codificación y espacios. Nunca cambia palabras,
    mayúsculas, tildes, puntuación ni expresiones dialectales.

    Devuelve (texto, [(step, descripción, hash_entrada, hash_salida)]).
    """
    steps: list[tuple[str, str, str, str]] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CorpusIntegrityError(f"La fuente no es UTF-8 válido; requiere revisión humana: {exc}") from exc
    steps.append(("decode_utf8", "Decodificación UTF-8 estricta", sha256_bytes(raw), sha256_text(text)))

    def apply(step: str, desc: str, fn) -> None:
        nonlocal text
        before = text
        text = fn(text)
        steps.append((step, desc, sha256_text(before), sha256_text(text)))

    apply("strip_bom", "Eliminar BOM inicial", lambda t: t.removeprefix("\ufeff"))
    apply("unicode_nfc", "Normalización Unicode NFC (tildes compuestas)", lambda t: unicodedata.normalize("NFC", t))
    apply("newline_lf", "CRLF/CR a LF", lambda t: t.replace("\r\n", "\n").replace("\r", "\n"))
    apply("whitespace_chars_to_space", "Tabuladores y espacios Unicode a espacio", lambda t: _WS_CHARS.sub(" ", t))
    apply("collapse_inline_spaces", "Colapsar espacios repetidos", lambda t: _INLINE_WS.sub(" ", t))
    apply("strip_trailing_line_spaces", "Quitar espacios al final de línea", lambda t: _TRAILING_WS.sub("\n", t))
    apply("collapse_blank_lines", "Máximo una línea en blanco entre párrafos", lambda t: _BLANK_RUNS.sub("\n\n", t))
    apply("strip_document_edges", "Quitar espacios al inicio y final del documento", lambda t: t.strip())
    if not text:
        raise CorpusIntegrityError("El texto normalizado quedó vacío.")
    return text, steps


def _word_multiset(text: str) -> list[str]:
    return sorted(re.findall(r"\w+", unicodedata.normalize("NFC", text)))


def normalize_source(corpus_root: Path, record: SourceRecord) -> tuple[SourceRecord, list[TransformationRecord]]:
    raw = resolve_inside(corpus_root, record.raw_path).read_bytes()
    if sha256_bytes(raw) != record.raw_sha256:
        raise CorpusIntegrityError(f"{record.source_id}: el original no coincide con raw_sha256.")
    text, steps = normalize_text(raw)
    if _word_multiset(text) != _word_multiset(raw.decode("utf-8")):
        raise CorpusIntegrityError(f"{record.source_id}: la normalización alteró palabras.")
    norm_rel = f"normalized/{record.source_id}.txt"
    data = text.encode("utf-8")
    write_once(corpus_root, norm_rel, data)
    now = datetime.now(timezone.utc)
    transformations = [
        TransformationRecord(
            source_id=record.source_id,
            step=step,  # type: ignore[arg-type]
            description=desc,
            changed=h_in != h_out,
            input_sha256=h_in,
            output_sha256=h_out,
            tool_version=PIPELINE_VERSION,
            timestamp_utc=now,
        )
        for step, desc, h_in, h_out in steps
    ]
    updated = record.model_copy(
        update={"normalized_path": norm_rel, "normalized_sha256": sha256_bytes(data), "status": "normalized"}
    )
    return SourceRecord.model_validate(updated.model_dump()), transformations


# --------------------------------------------------------------------------- Fase 3: segmentación


def segment_paragraphs(text: str, source_id: str, min_words: int = 40) -> list[SegmentRecord]:
    """Segmenta por párrafos (línea en blanco) y fusiona hacia adelante los párrafos
    con menos de `min_words` palabras para preservar contexto. Offsets exactos."""
    paragraphs = [(m.start(), m.end()) for m in re.finditer(r"[^\n](?:.|\n(?!\n))*", text)]
    spans: list[tuple[int, int]] = []
    current: tuple[int, int] | None = None
    for start, end in paragraphs:
        current = (current[0], end) if current else (start, end)
        if len(text[current[0]:current[1]].split()) >= min_words:
            spans.append(current)
            current = None
    if current:
        if spans and len(text[current[0]:current[1]].split()) < min_words:
            spans[-1] = (spans[-1][0], current[1])
        else:
            spans.append(current)
    return [
        SegmentRecord(
            segment_id=f"{source_id}_seg_{i:04d}",
            source_id=source_id,
            text=text[s:e],
            char_start=s,
            char_end=e,
            segmentation_method=f"paragraph_merge_min{min_words}",
            segmentation_version=PIPELINE_VERSION,
        )
        for i, (s, e) in enumerate(spans, start=1)
    ]


def verify_against_source(item: SegmentRecord | AnnotatedSegment, normalized_text: str) -> list[str]:
    errors: list[str] = []
    if normalized_text[item.char_start:item.char_end] != item.text:
        errors.append(f"{item.segment_id}: el texto no coincide con la fuente normalizada")
    if isinstance(item, AnnotatedSegment):
        for span in item.evidence_spans:
            if normalized_text[span.char_start:span.char_end] != span.quote:
                errors.append(f"{item.segment_id}: cita desalineada {span.quote!r}")
    return errors


# --------------------------------------------------------------------------- escáneres (solo reportan)


@dataclass(frozen=True)
class ScanFinding:
    kind: str
    pattern: str
    char_start: int
    char_end: int

    def as_dict(self) -> dict[str, object]:
        # No se incluye el texto detectado para no propagar PII a los reportes.
        return {"kind": self.kind, "pattern": self.pattern, "char_start": self.char_start, "char_end": self.char_end}


_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone_or_id_number": re.compile(r"(?<!\d)(?:\+?\d[\d .-]{6,}\d)(?!\d)"),
    "self_name": re.compile(r"\b(?:me llamo|mi nombre es|soy (?:el|la) señora?)\s+[A-ZÁÉÍÓÚÑ]\w+", re.IGNORECASE),
    "named_place": re.compile(r"\b(?:vereda|finca|corregimiento|hacienda)\s+(?:(?:el|la|los|las|de)\s+)?[A-ZÁÉÍÓÚÑ]\w+"),
}

_INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignore_instructions": re.compile(r"\b(?:ignora|olvida|ignore|disregard)\b.{0,40}\b(?:instruc|prompt|reglas|rules)", re.IGNORECASE),
    "role_override": re.compile(r"\b(?:eres un|act[uú]a como|you are now|system\s*:|assistant\s*:)", re.IGNORECASE),
    "prompt_markup": re.compile(r"(?:<\|[^|]*\|>|\[/?INST\]|<\/?(?:system|user|assistant)>|```)", re.IGNORECASE),
    "command_like": re.compile(r"(?:\brm\s+-rf\b|\bsudo\b|\bcurl\s+http|\bos\.system\b|\bexec\()", re.IGNORECASE),
    "output_override": re.compile(r"\b(?:responde|devuelve|return|output)\b.{0,30}\b(?:json|pure|conflict|aprobad)", re.IGNORECASE),
}


def _scan(text: str, patterns: dict[str, re.Pattern[str]], kind: str) -> list[ScanFinding]:
    return [
        ScanFinding(kind, name, m.start(), m.end())
        for name, rx in patterns.items()
        for m in rx.finditer(text)
    ]


def scan_pii(text: str) -> list[ScanFinding]:
    return _scan(text, _PII_PATTERNS, "pii")


def scan_injection(text: str) -> list[ScanFinding]:
    return _scan(text, _INJECTION_PATTERNS, "injection")


# --------------------------------------------------------------------------- Fase 6: particiones


def assign_splits(
    sources: Iterable[SourceRecord | str],
    *,
    seed: int,
    corpus_version: str,
    split_version: str = "1.0.0",
    ratios: dict[str, float] | None = None,
    pinned: dict[str, str] | None = None,
    participant_map: dict[str, str] | None = None,
    training_allowed_map: dict[str, bool] | None = None,
) -> SplitManifest:
    """Asigna fuentes completas agrupadas por participant_code para evitar fuga entre particiones.

    Invariantes metodológicos:
    - Ningún participant_code puede aparecer en más de una partición (train / validation / test).
    - Toda fuente en 'train' debe tener allowed_for_training=True (rechazo de training sin autorización).
    - 'adversarial' y 'hard_cases' solo se asignan por curaduría explícita ('pinned').
    - Si se pasan IDs simples sin participant_map, cada ID se trata como participante individual (compatibilidad).
    """
    ratios = ratios or {"train": 0.6, "validation": 0.2, "test": 0.2}
    if set(ratios) != set(RANDOM_SPLITS) or abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("ratios debe cubrir train/validation/test y sumar 1.0.")

    source_items = list(sources)
    source_to_participant: dict[str, str] = {}
    source_to_allowed_training: dict[str, bool] = {}
    source_ids: list[str] = []

    for item in source_items:
        if isinstance(item, SourceRecord):
            sid = item.source_id
            pid = item.participant_code
            can_train = item.allowed_for_training
        else:
            sid = str(item)
            pid = participant_map.get(sid, sid) if participant_map else sid
            can_train = training_allowed_map.get(sid, True) if training_allowed_map is not None else True

        source_ids.append(sid)
        source_to_participant[sid] = pid
        source_to_allowed_training[sid] = can_train

    ids = sorted(set(source_ids))
    pinned = dict(pinned or {})
    unknown_pins = set(pinned) - set(ids)
    if unknown_pins:
        raise ValueError(f"Fuentes fijadas inexistentes: {sorted(unknown_pins)}")

    participant_to_sources: dict[str, list[str]] = {}
    for sid in ids:
        pid = source_to_participant[sid]
        participant_to_sources.setdefault(pid, []).append(sid)

    # Validar consistencia de fuentes fijadas por participante
    pinned_participants: dict[str, str] = {}
    for sid, split in pinned.items():
        pid = source_to_participant[sid]
        if pid in pinned_participants and pinned_participants[pid] != split:
            raise ValueError(f"Conflicto de asignación: participante '{pid}' tiene fuentes fijadas en particiones distintas.")
        pinned_participants[pid] = split

    assignments: dict[str, list[str]] = {k: [] for k in (*RANDOM_SPLITS, "adversarial", "hard_cases")}
    participant_assignments: dict[str, list[str]] = {k: [] for k in (*RANDOM_SPLITS, "adversarial", "hard_cases")}

    for pid, split in pinned_participants.items():
        participant_assignments[split].append(pid)
        assignments[split].extend(participant_to_sources[pid])

    free_participants = sorted(
        (pid for pid in participant_to_sources if pid not in pinned_participants),
        key=lambda pid: sha256_text(f"{seed}:{pid}"),
    )

    n = len(free_participants)
    n_train = round(n * ratios["train"])
    n_val = round(n * ratios["validation"])

    for pid in free_participants[:n_train]:
        participant_assignments["train"].append(pid)
        assignments["train"].extend(participant_to_sources[pid])

    for pid in free_participants[n_train:n_train + n_val]:
        participant_assignments["validation"].append(pid)
        assignments["validation"].extend(participant_to_sources[pid])

    for pid in free_participants[n_train + n_val:]:
        participant_assignments["test"].append(pid)
        assignments["test"].extend(participant_to_sources[pid])

    assignments = {k: sorted(v) for k, v in assignments.items()}
    participant_assignments = {k: sorted(v) for k, v in participant_assignments.items()}

    # Verificación de soberanía y consentimiento: rechazo estricto de training no autorizado
    for sid in assignments["train"]:
        if not source_to_allowed_training.get(sid, False):
            raise CorpusIntegrityError(
                f"Rechazo de training sin autorización: la fuente '{sid}' (participante '{source_to_participant[sid]}') "
                "tiene allowed_for_training=False."
            )

    listing = json.dumps(assignments, sort_keys=True, separators=(",", ":"))
    return SplitManifest(
        split_version=split_version,
        corpus_version=corpus_version,
        strategy="by_participant_code",
        seed=seed,
        ratios=ratios,
        assignments=assignments,  # type: ignore[arg-type]
        participant_assignments=participant_assignments,  # type: ignore[arg-type]
        pinned=pinned,  # type: ignore[arg-type]
        listing_sha256=sha256_text(listing),
    )


# --------------------------------------------------------------------------- contratos exportados


def export_json_schemas(corpus_root: Path) -> list[Path]:
    """Exporta JSON Schema derivado de Pydantic (única fuente de verdad)."""
    models: dict[str, type[BaseModel]] = {
        "source_record": SourceRecord,
        "transformation_record": TransformationRecord,
        "segment_record": SegmentRecord,
        "annotated_segment": AnnotatedSegment,
        "split_manifest": SplitManifest,
    }
    return [
        write_json(corpus_root, f"schemas/{name}.schema.json", model.model_json_schema())
        for name, model in models.items()
    ]
