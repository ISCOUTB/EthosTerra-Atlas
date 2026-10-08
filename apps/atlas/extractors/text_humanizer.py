"""apps/atlas/extractors/text_humanizer.py

Sanitizador determinista y ligero para campos de presentación humana en creencias eBDI.
Inspirado en las directrices de la skill 'humanizer' (basada en 'Signs of AI writing' de Wikipedia).

Propósito y Garantías:
1. Aplica reglas fácticas de sobriedad y des-robotización exclusivamente sobre
   los campos de lectura humana: `ebdi_belief_assertion`, `behavioral_effect` y `trigger_condition`.
2. Preserva de manera inmutable:
   - `raw_excerpt` (mantiene íntegro el Verbatim Gate anti-alucinación al 100%).
   - `belief_key` y `applicable_divipolas`.
   - `activation_rule_template` (código formal MVEL para el simulador).
   - Hashes criptográficos SHA-256 e identificadores de sistema.
3. Latencia sub-milisegundo, cero llamadas adicionales a LLM, determinismo estricto.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.atlas.schemas.context_schemas import TerritorialBeliefItem


class TextHumanizer:
    """Sanitizador léxico determinista contra manierismos y clichés de redacción sintética de IA."""

    # §8: Sustitución de guiones largos (em-dash y en-dash) por puntuación sobria estándar
    RE_EM_DASH = re.compile(r"\s*[—–]\s*|\s+--\s+")

    # §12: Léxico inflado o sobreutilizado comúnmente por modelos de lenguaje
    REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
        # Retórica grandilocuente e inflada
        (re.compile(r"\bdesempeña un papel (?:crucial|clave|fundamental) en\b", re.IGNORECASE), "participa en"),
        (re.compile(r"\bjuega un papel (?:crucial|clave|fundamental) en\b", re.IGNORECASE), "incide en"),
        (re.compile(r"\bsirve como (?:un )?testimonio de\b", re.IGNORECASE), "refleja"),
        (re.compile(r"\bes un testimonio de\b", re.IGNORECASE), "muestra"),
        (re.compile(r"\bmarcando un hito (?:en|para)\b", re.IGNORECASE), "formalizando"),
        (re.compile(r"\ballanando el camino para\b", re.IGNORECASE), "facilitando"),
        (re.compile(r"\ben el vibrante paisaje (?:productivo|agrícola|rural)\b", re.IGNORECASE), "en el sector productivo"),
        (re.compile(r"\bpaisaje productivo\b", re.IGNORECASE), "entorno productivo"),
        (re.compile(r"\brich tapestry\b", re.IGNORECASE), "conjunto"),
        (re.compile(r"\btapiz (?:cultural|social|productivo)\b", re.IGNORECASE), "tejido social"),
        (re.compile(r"\bde manera meticulosa\b", re.IGNORECASE), "en detalle"),
        (re.compile(r"\bmeticulosamente\b", re.IGNORECASE), "en detalle"),
        (re.compile(r"\benfoque robusto\b", re.IGNORECASE), "enfoque técnico"),
        (re.compile(r"\bmarco robusto\b", re.IGNORECASE), "marco operativo"),
        (re.compile(r"\buna robusta estrategia\b", re.IGNORECASE), "una estrategia técnica"),
        (re.compile(r"\buna sólida y robusta\b", re.IGNORECASE), "una"),
        # §15: Shallow riders superficiales
        (re.compile(r",\s*destacando la importancia de\b", re.IGNORECASE), ", priorizando"),
        (re.compile(r",\s*resaltando la necesidad de\b", re.IGNORECASE), ", requiriendo"),
        (re.compile(r",\s*asegurando así un futuro prometedor\b", re.IGNORECASE), ""),
        (re.compile(r",\s*lo que subraya su relevancia\b", re.IGNORECASE), ""),
        # §1: Contrastes forzados "no es solo X, sino Y"
        (re.compile(r"\bno solo ([^,]+),\s*sino (?:que también )?([^.]+)", re.IGNORECASE), r"\1 y \2"),
        (re.compile(r"\bno es solo ([^,]+),\s*sino ([^.]+)", re.IGNORECASE), r"\1 y \2"),
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitiza una cadena de texto eliminando tics retóricos de IA."""
        if not text:
            return ""

        clean = text.strip()

        # 1. Normalizar em-dashes y en-dashes (§8)
        # Si está entre palabras, lo convertimos en coma o paréntesis según el contexto
        clean = cls.RE_EM_DASH.sub(", ", clean)

        # 2. Aplicar sustituciones léxicas sobrias
        for pattern, replacement in cls.REPLACEMENTS:
            clean = pattern.sub(replacement, clean)

        # 3. Limpieza de puntuación redundante o espaciado irregular
        clean = re.sub(r",\s*,+", ",", clean)
        clean = re.sub(r"\s{2,}", " ", clean)
        clean = re.sub(r"\s+([.,;:])", r"\1", clean)
        clean = clean.strip()

        # Si termina en coma por efecto del recorte de un rider, sustituir por punto
        if clean.endswith(","):
            clean = clean[:-1].strip() + "."

        return clean

    @classmethod
    def sanitize_belief_presentation(
        cls,
        belief: TerritorialBeliefItem,
    ) -> TerritorialBeliefItem:
        """Sanitiza estrictamente los campos de presentación humana de una creencia eBDI.

        Garantía Absoluta:
        - `raw_excerpt` permanece INTACTO (Verbatim Gate 100%).
        - `belief_key`, `divipola`, `activation_rule_template`, hashes y metadatos no son alterados.
        """
        if belief.ebdi_belief_assertion:
            belief.ebdi_belief_assertion = cls.sanitize_text(belief.ebdi_belief_assertion)

        if belief.behavioral_effect:
            belief.behavioral_effect = cls.sanitize_text(belief.behavioral_effect)

        if belief.trigger_condition:
            belief.trigger_condition = cls.sanitize_text(belief.trigger_condition)

        return belief
