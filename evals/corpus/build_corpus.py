"""CLI del corpus B6. Uso (desde la raíz del repositorio):

    PYTHONPATH=apps/api uv run --project apps/api python evals/corpus/build_corpus.py init
    ... register --file RUTA --source-id field_0001 --source-type interview --provenance field \
                 --title "Entrevista 01 (anonimizada)" --collector researcher_01 --consent pending
    ... normalize --source-id field_0001
    ... segment   --source-id field_0001 [--min-words 40]
    ... scan      --source-id field_0001
    ... verify
    ... split     --seed 6 [--pin field_0003=hard_cases]

Solo escribe dentro de outputs/corpus/<corpus>/. Nunca invoca al modelo ni al simulador.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.application import corpus_pipeline as cp
from src.domain.v2.corpus_schemas import (
    AnnotatedSegment,
    CORPUS_SCHEMA_VERSION,
    SegmentRecord,
    SourceRecord,
    TransformationRecord,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_BASE = REPO_ROOT / "outputs" / "corpus"
SOURCES_MANIFEST = "manifests/sources.jsonl"
TRANSFORMATIONS_MANIFEST = "manifests/transformations.jsonl"


def _load_sources(root: Path) -> dict[str, SourceRecord]:
    return {r.source_id: r for r in cp.read_jsonl(root, SOURCES_MANIFEST, SourceRecord)}  # type: ignore[attr-defined]


def _save_sources(root: Path, sources: dict[str, SourceRecord]) -> None:
    cp.write_jsonl(root, SOURCES_MANIFEST, [sources[k] for k in sorted(sources)])


def _get(sources: dict[str, SourceRecord], sid: str) -> SourceRecord:
    if sid not in sources:
        sys.exit(f"Fuente no registrada: {sid}")
    return sources[sid]


def cmd_init(root: Path, args: argparse.Namespace) -> None:
    cp.init_layout(root)
    for rel in (SOURCES_MANIFEST, TRANSFORMATIONS_MANIFEST):
        target = cp.resolve_inside(root, rel)
        if not target.exists():
            cp.write_jsonl(root, rel, [])
    cp.export_json_schemas(root)
    print(f"Estructura inicializada en {root.relative_to(REPO_ROOT)}")


def cmd_register(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    if args.source_id in sources:
        sys.exit(f"La fuente {args.source_id} ya está registrada.")
    rec = cp.register_source(
        root, Path(args.file), source_id=args.source_id, source_type=args.source_type,
        provenance_class=args.provenance, title=args.title, collector_id=args.collector,
        consent_status=args.consent, language=args.language, collection_date=args.collection_date,
        location=args.location, participant_code=args.participant_code, vereda_code=args.vereda_code,
        consent_scope=args.consent_scope, allowed_for_training=args.allowed_for_training,
        usage_state=args.usage_state, notes=args.notes,
    )
    sources[rec.source_id] = rec
    _save_sources(root, sources)
    print(f"{rec.source_id} registrada raw_sha256={rec.raw_sha256}")


def cmd_normalize(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    rec, steps = cp.normalize_source(root, _get(sources, args.source_id))
    sources[rec.source_id] = rec
    log = cp.read_jsonl(root, TRANSFORMATIONS_MANIFEST, TransformationRecord)
    cp.write_jsonl(root, TRANSFORMATIONS_MANIFEST, [*log, *steps])
    _save_sources(root, sources)
    print(f"{rec.source_id} normalizada normalized_sha256={rec.normalized_sha256}")


def _normalized_text(root: Path, rec: SourceRecord) -> str:
    if not rec.normalized_path:
        sys.exit(f"{rec.source_id} aún no está normalizada.")
    return cp.resolve_inside(root, rec.normalized_path).read_text("utf-8")


def cmd_segment(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    rec = _get(sources, args.source_id)
    segments = cp.segment_paragraphs(_normalized_text(root, rec), rec.source_id, min_words=args.min_words)
    cp.write_jsonl(root, f"normalized/{rec.source_id}.segments.jsonl", segments)
    if rec.status == "normalized":
        sources[rec.source_id] = SourceRecord.model_validate({**rec.model_dump(), "status": "segmented"})
        _save_sources(root, sources)
    print(f"{rec.source_id}: {len(segments)} segmentos")


def cmd_scan(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    rec = _get(sources, args.source_id)
    text = _normalized_text(root, rec)
    pii, inj = cp.scan_pii(text), cp.scan_injection(text)
    cp.write_json(root, f"reports/scan_{rec.source_id}.json", {
        "source_id": rec.source_id,
        "normalized_sha256": rec.normalized_sha256,
        "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": cp.PIPELINE_VERSION,
        "pii_findings": [f.as_dict() for f in pii],
        "injection_findings": [f.as_dict() for f in inj],
        "requires_human_review": bool(pii or inj),
        "note": "Hallazgos heurísticos; no sustituyen la revisión humana. El texto detectado no se reproduce.",
    })
    print(f"{rec.source_id}: pii={len(pii)} injection={len(inj)}")


def cmd_verify(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    errors: list[str] = []
    for rec in sources.values():
        errors += cp.verify_source_hashes(root, rec)
        if not rec.normalized_path:
            continue
        text = _normalized_text(root, rec)
        for seg in cp.read_jsonl(root, f"normalized/{rec.source_id}.segments.jsonl", SegmentRecord):
            errors += cp.verify_against_source(seg, text)  # type: ignore[arg-type]
        for sub in ("primary", "secondary"):
            for ann in cp.read_jsonl(root, f"annotations/{sub}/{rec.source_id}.jsonl", AnnotatedSegment):
                errors += cp.verify_against_source(ann, text)  # type: ignore[arg-type]
    dups = cp.find_duplicates(sources.values())
    print(f"fuentes={len(sources)} errores={len(errors)} duplicados={len(dups)}")
    for e in errors:
        print(f"  ERROR {e}")
    if errors:
        sys.exit(1)


def cmd_split(root: Path, args: argparse.Namespace) -> None:
    sources = _load_sources(root)
    eligible = [
        r for r in sources.values()
        if r.status not in ("draft", "excluded") and r.duplicate_of is None
        and (r.consent_status == "granted" or r.provenance_class == "synthetic")
    ]
    pinned = dict(p.split("=", 1) for p in args.pin)
    manifest = cp.assign_splits(eligible, seed=args.seed, corpus_version=args.corpus_version, pinned=pinned)
    cp.write_json(root, f"splits/split_manifest_v{manifest.split_version}.json", manifest.model_dump(mode="json"))
    eligible_ids = {r.source_id for r in eligible}
    excluded = sorted(set(sources) - eligible_ids)
    print(f"particionadas={len(eligible)} excluidas={len(excluded)} {excluded}")


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Corpus B6 (schema {CORPUS_SCHEMA_VERSION})")
    parser.add_argument("--corpus", default="b6_field_v1")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    r = sub.add_parser("register")
    r.add_argument("--file", required=True)
    r.add_argument("--source-id", required=True)
    r.add_argument("--source-type", required=True)
    r.add_argument("--provenance", required=True, choices=["field", "synthetic", "derived"])
    r.add_argument("--title", required=True)
    r.add_argument("--collector", required=True)
    r.add_argument("--consent", required=True)
    r.add_argument("--language", default="es")
    r.add_argument("--collection-date", default="unknown")
    r.add_argument("--location", default="unknown")
    r.add_argument("--participant-code", default="unknown")
    r.add_argument("--vereda-code", default="unknown")
    r.add_argument("--consent-scope", action="append", default=[])
    r.add_argument("--allowed-for-training", action="store_true", default=False)
    r.add_argument("--usage-state", default="context_only", choices=["context_only", "evaluation_authorized", "training_authorized"])
    r.add_argument("--notes", default="")
    for name in ("normalize", "scan"):
        sub.add_parser(name).add_argument("--source-id", required=True)
    s = sub.add_parser("segment")
    s.add_argument("--source-id", required=True)
    s.add_argument("--min-words", type=int, default=40)
    sub.add_parser("verify")
    sp = sub.add_parser("split")
    sp.add_argument("--seed", type=int, required=True)
    sp.add_argument("--corpus-version", default="1.0.0")
    sp.add_argument("--pin", action="append", default=[], help="source_id=adversarial|hard_cases|...")
    args = parser.parse_args()

    root = cp.ensure_corpus_root(ALLOWED_BASE / args.corpus, ALLOWED_BASE)
    handlers = {
        "init": cmd_init, "register": cmd_register, "normalize": cmd_normalize, "segment": cmd_segment,
        "scan": cmd_scan, "verify": cmd_verify, "split": cmd_split,
    }
    handlers[args.cmd](root, args)


if __name__ == "__main__":
    main()
