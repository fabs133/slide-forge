"""Style instructions for slide content generation."""

from __future__ import annotations

STYLE_INSTRUCTIONS: dict[str, str] = {
    "keywords": (
        "Each bullet point must be a single keyword or a short phrase of 2-3 words maximum. "
        "No verbs. No complete sentences. Think of slide tags, not explanations. "
        "Example: 'Verschlüsselung', 'BSI-Grundschutz', 'Zero Trust'"
    ),
    "sentences": (
        "Each bullet point must be one complete sentence of 8-15 words. "
        "Structure: subject + verb + specific point. No vague filler. "
        "Example: 'Firewalls filtern eingehenden Netzwerkverkehr anhand definierter Regeln.'"
    ),
    "academic": (
        "Each bullet point must be a precise, formal sentence using correct domain terminology. "
        "Where applicable, reference specific standards, regulations, or measurable figures. "
        "No informal language. "
        "Example: 'Die DSGVO (Art. 32) verpflichtet Verantwortliche zur Implementierung "
        "technischer Schutzmaßnahmen entsprechend dem Stand der Technik.'"
    ),
}


def get_style_instruction(style: str) -> str:
    """Return the prompt instruction for the given style value."""
    return STYLE_INSTRUCTIONS[style]
