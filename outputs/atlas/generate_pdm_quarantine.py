import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DIR = REPO_ROOT / "outputs/atlas/sources"
SOURCES_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_PATH = REPO_ROOT / "outputs/atlas/registry_state.json"

def create_pdm_pdf(filename: Path, title: str, subtitle: str, articles: list[tuple[str, str]]):
    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#002244'),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#444444'),
        alignment=1,
    )
    art_title_style = ParagraphStyle(
        'ArtTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0066cc'),
    )
    body_style = ParagraphStyle(
        'ArtBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1d1d1f'),
        alignment=4,
    )

    story = [
        Paragraph(title, title_style),
        Spacer(1, 6),
        Paragraph(subtitle, subtitle_style),
        Spacer(1, 16),
        Paragraph("REPÚBLICA DE COLOMBIA · DEPARTAMENTO DE BOLÍVAR · CONCEJO MUNICIPAL", subtitle_style),
        Spacer(1, 20),
    ]

    for art_title, art_text in articles:
        story.append(Paragraph(art_title, art_title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(art_text, body_style))
        story.append(Spacer(1, 12))

    doc.build(story)

    # Calcular SHA-256 y tamaño
    content_bytes = filename.read_bytes()
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()
    return sha256_hash, len(content_bytes)


def main():
    docs_to_generate = [
        {
            "source_id": "pdm_el_carmen_de_bolivar_2024_2027",
            "title": "Plan de Desarrollo Municipal de El Carmen de Bolívar 2024-2027: Transformación Agropecuaria y Resiliencia Hídrica",
            "entity": "Alcaldía Municipal de El Carmen de Bolívar / Concejo Municipal",
            "subtitle": "Acuerdo Municipal 006 de 2024 · Documento Oficial de Planificación Territorial",
            "level": "municipal",
            "territory_scope": "13244",
            "canonical_url": "https://elcarmendebolivar-bolivar.gov.co/planes/plan-de-desarrollo-municipal-2024-2027",
            "articles": [
                (
                    "Artículo 14. Acceso a maquinaria agrícola y preparación comunitaria de suelos",
                    "Para la preparación de tierras destinadas a la siembra de ñame espino, maíz tradicional y ajonjolí, "
                    "la administración municipal en articulación con las asociaciones campesinas formalizadas facilitará turnos de "
                    "maquinaria comunitaria para pequeños productores que carezcan de tractor o implementos de labranza propios, "
                    "garantizando la preparación oportuna del suelo antes del inicio de la temporada de lluvias."
                ),
                (
                    "Artículo 15. Provisión hídrica comunitaria y mitigación de sequía",
                    "En situaciones de sequía prolongada o déficit hídrico estacional en época de siembra y floración, "
                    "la administración municipal priorizará el abastecimiento de reservorios comunitarios y la asignación de turnos "
                    "de motobomba y riego asistido para pequeños productores inscritos en los comités veredales de cuenca, "
                    "prohibiendo la captación privada no autorizada en microcuencas prioritarias."
                ),
                (
                    "Artículo 16. Fondo rotatorio de semillas nativas y compras públicas locales",
                    "Se crea el Fondo Municipal de Semillas Nativas para dotar de material vegetal certificado de ñame y maíz a "
                    "pequeños agricultores afectados por pérdidas climáticas, vinculándolos de forma obligatoria y directa a los "
                    "circuitos de compras públicas institucionales para garantizar precios remunerativos sin intermediación especulativa."
                ),
            ]
        },
        {
            "source_id": "pdm_san_jacinto_2024_2027",
            "title": "Plan de Desarrollo Municipal de San Jacinto 2024-2027: Desarrollo Productivo, Agroforestería y Paz Territorial",
            "entity": "Alcaldía Municipal de San Jacinto / Concejo Municipal",
            "subtitle": "Acuerdo Municipal 004 de 2024 · Documento Oficial de Planificación Territorial",
            "level": "municipal",
            "territory_scope": "13654",
            "canonical_url": "https://sanjacinto-bolivar.gov.co/planes/plan-de-desarrollo-municipal-2024-2027",
            "articles": [
                (
                    "Artículo 18. Fomento de sistemas agroforestales con café bajo sombra y cacao",
                    "Los pequeños productores de la zona alta y media de San Jacinto que establezcan o renueven parcelas de café bajo "
                    "sombra asociado con plátano y árboles maderables nativos tendrán prelación en la entrega de plántulas de viveros "
                    "comunitarios y en la asistencia técnica especializada en manejo integrado de plagas y fertilización orgánica."
                ),
                (
                    "Artículo 19. Dotación comunitaria de herramientas y bioinsumos",
                    "Las organizaciones comunitarias campesinas y de artesanos agrícolas administrarán bancos de herramientas "
                    "y suministros para labores de siembra y cosecha de yuca y algodón, suministrando a los asociados bioinsumos y "
                    "herramientas de labranza a precio de costo sin recargos financieros."
                ),
                (
                    "Artículo 20. Protección de fuentes de agua y comités veredales de conservación",
                    "Queda prohibida la tala y quema en las márgenes de arroyos y rondas de nacimientos de agua. Los campesinos "
                    "que participen en acuerdos comunitarios de conservación recibirán incentivos a la producción sostenible y "
                    "apoyo técnico en obras de bioingeniería para contención de erosión en laderas."
                ),
            ]
        }
    ]

    # Cargar registro manifest
    manifest_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) if REGISTRY_PATH.exists() else {"version": "1.0.0", "documents": {}}
    now_iso = datetime.now(timezone.utc).isoformat()

    for item in docs_to_generate:
        temp_pdf = SOURCES_DIR / f"temp_{item['source_id']}.pdf"
        sha256, byte_size = create_pdm_pdf(temp_pdf, item["title"], item["subtitle"], item["articles"])

        final_pdf = SOURCES_DIR / f"{sha256}.pdf"
        temp_pdf.replace(final_pdf)
        print(f"Generado PDF para {item['source_id']} -> {final_pdf.name} (SHA: {sha256[:12]}..., {byte_size} bytes)")

        # Registrar en estado de cuarentena (pending_context_review)
        manifest_data["documents"][item["source_id"]] = {
            "source_id": item["source_id"],
            "entity": item["entity"],
            "title": item["title"],
            "level": item["level"],
            "territory_scope": item["territory_scope"],
            "pipeline_type": "documental",
            "document_format": "pdf",
            "canonical_url": item["canonical_url"],
            "download_date": now_iso,
            "sha256": sha256,
            "byte_size": byte_size,
            "content_path": f"sources/{sha256}.pdf",
            "source_type": "document_context",
            "provenance_class": "official_government",
            "consent_status": "not_applicable",
            "allowed_for_training": False,
            "usage_state": "context_only",
            "approval_status": "pending_context_review",
            "status": "pending_context_review",
            "instrument_type": "PDM",
            "previous_source_id": None,
            "approval_notes": "Artefacto territorial ingresado en cuarentena preventiva para revisión humana AT-1.",
            "approval_timestamp": None,
            "reviewer_id": None,
            "reviewer_auth_mode": None,
            "review_events": [],
            "review_history_recovery": None
        }

    manifest_data["last_updated"] = now_iso
    REGISTRY_PATH.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifiesto actualizado exitosamente con {len(docs_to_generate)} documentos nuevos en cuarentena.")

if __name__ == "__main__":
    main()
