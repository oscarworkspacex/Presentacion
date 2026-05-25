"""
Generación de preguntas de evaluación basadas en el contenido real de una presentación.
Las preguntas son generadas 100% por IA usando el contenido específico de los slides.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from models.llm_message import LLMSystemMessage, LLMUserMessage
from services.llm_client import LLMClient
from utils.llm_provider import get_model

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de validación
# ─────────────────────────────────────────────────────────────────────────────

class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str


class QuestionsResponse(BaseModel):
    questions: List[GeneratedQuestion]


# ─────────────────────────────────────────────────────────────────────────────
# Extracción de texto limpio desde estructuras JSON anidadas de slides
# ─────────────────────────────────────────────────────────────────────────────

def _extract_text_from_value(value: Any, depth: int = 0) -> List[str]:
    """Extrae recursivamente todo el texto legible de cualquier estructura de datos."""
    if depth > 5:
        return []

    texts = []

    if isinstance(value, str):
        cleaned = value.strip()
        # Ignorar URLs, placeholders y strings muy cortos
        if (
            len(cleaned) > 15
            and not cleaned.startswith("http")
            and not cleaned.startswith("/static")
            and not cleaned.startswith("__")
        ):
            texts.append(cleaned)

    elif isinstance(value, list):
        for item in value:
            texts.extend(_extract_text_from_value(item, depth + 1))

    elif isinstance(value, dict):
        # Campos internos del sistema a ignorar
        skip_keys = {"__image_prompt__", "__image_url__", "__speaker_note__"}
        priority_keys = {"title", "content", "text", "description", "subtitle",
                         "body", "mainContent", "label", "value", "heading",
                         "bullet", "bullets", "points", "items"}

        # Primero los campos prioritarios
        for key in priority_keys:
            if key in value and key not in skip_keys:
                texts.extend(_extract_text_from_value(value[key], depth + 1))

        # Luego el resto
        for key, val in value.items():
            if key not in priority_keys and key not in skip_keys:
                texts.extend(_extract_text_from_value(val, depth + 1))

    return texts


def extract_clean_content_from_slides(slides_content: List[Dict[str, Any]]) -> str:
    """
    Extrae todo el texto útil de los slides de una presentación.

    Args:
        slides_content: Lista de dicts de contenido de slides

    Returns:
        Texto limpio concatenado listo para enviar al LLM
    """
    all_parts = []

    for i, slide in enumerate(slides_content):
        if not slide:
            continue

        # Si el slide tiene la key "content" anidada (cuando viene de outlines)
        raw = slide.get("content", slide)

        texts = _extract_text_from_value(raw)
        if texts:
            # Encabezar cada slide para que el LLM entienda la estructura
            all_parts.append(f"[Slide {i + 1}]")
            all_parts.extend(texts)

    return "\n".join(all_parts)


# ─────────────────────────────────────────────────────────────────────────────
# Parseo seguro del JSON devuelto por el LLM
# ─────────────────────────────────────────────────────────────────────────────

def _safe_parse_json(raw: str) -> Optional[Dict]:
    """
    Parsea JSON de la respuesta del LLM, manejando casos donde
    el modelo envuelve la respuesta en bloques de código markdown.
    """
    if not raw:
        return None

    # Eliminar bloques markdown si los hay
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    # Intentar encontrar el JSON dentro de la respuesta
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f"JSON parse failed. Raw (first 500 chars): {raw[:500]}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Generación principal con LLM
# ─────────────────────────────────────────────────────────────────────────────

async def generate_questions_from_presentation_content(
    presentation_content: str,
    num_questions: int = 5,
    language: str = "es",
    outlines: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Genera preguntas de opción múltiple específicas al contenido real de la presentación.

    Args:
        presentation_content: Texto del contenido de la presentación
        num_questions: Número de preguntas a generar
        language: Idioma ('es' o 'en')
        outlines: Lista de dicts con el contenido de cada slide (opcional)

    Returns:
        Lista de preguntas formateadas para el frontend
    """
    client = LLMClient()

    # Usar outlines si están disponibles para extraer texto limpio
    if outlines:
        clean_content = extract_clean_content_from_slides(outlines)
        if len(clean_content.strip()) > 50:
            base_content = clean_content
            logger.info(f"Using {len(outlines)} slide outlines as base content ({len(base_content)} chars)")
        else:
            base_content = presentation_content
            logger.info("Outlines yielded no useful text, falling back to presentation_content")
    else:
        base_content = presentation_content

    # Truncar si es demasiado largo (evitar límites de tokens)
    max_length = 6000
    if len(base_content) > max_length:
        base_content = base_content[:max_length] + "\n[...contenido truncado...]"

    if len(base_content.strip()) < 30:
        logger.warning("Content too short to generate meaningful questions")
        raise ValueError("Insufficient content for question generation")

    system_prompt_es = f"""Eres un experto en evaluación educativa. Tu única tarea es leer el contenido de una presentación y generar {num_questions} preguntas de opción múltiple basadas EXCLUSIVAMENTE en ese contenido.

REGLAS ESTRICTAS:
1. Cada pregunta DEBE referirse a hechos, datos, nombres o conceptos CONCRETOS que aparezcan en el contenido.
2. NO hagas preguntas genéricas como "¿Cuál es el tema principal?" o "¿Qué aspecto se destaca?".
3. Cada pregunta tiene exactamente 4 opciones (A, B, C, D).
4. Solo 1 opción es correcta. Las otras 3 deben ser plausibles pero incorrectas.
5. El índice correct_answer es 0 para A, 1 para B, 2 para C, 3 para D.
6. Varía cuál opción es la correcta: no pongas siempre la misma posición como correcta.
7. La explicación debe citar explícitamente el dato del contenido.

Responde ÚNICAMENTE con JSON válido, sin texto adicional, sin markdown:
{{
  "questions": [
    {{
      "question": "Pregunta concreta basada en el contenido",
      "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "correct_answer": 0,
      "explanation": "Según el contenido, [citar dato exacto]."
    }}
  ]
}}"""

    system_prompt_en = f"""You are an educational assessment expert. Your only task is to read presentation content and generate {num_questions} multiple-choice questions based EXCLUSIVELY on that content.

STRICT RULES:
1. Each question MUST refer to concrete facts, data, names or concepts that APPEAR in the content.
2. Do NOT make generic questions like "What is the main topic?" or "What aspect is highlighted?".
3. Each question has exactly 4 options (A, B, C, D).
4. Only 1 option is correct. The other 3 must be plausible but wrong.
5. correct_answer index is 0 for A, 1 for B, 2 for C, 3 for D.
6. Vary which option is correct: don't always put the same position as correct.
7. The explanation must explicitly cite the data from the content.

Respond ONLY with valid JSON, no extra text, no markdown:
{{
  "questions": [
    {{
      "question": "Concrete question based on the content",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "According to the content, [cite exact data]."
    }}
  ]
}}"""

    user_prompt_es = f"""CONTENIDO DE LA PRESENTACIÓN:
{base_content}

Genera {num_questions} preguntas de opción múltiple basadas únicamente en el contenido anterior. Cada pregunta debe evaluar un hecho o concepto ESPECÍFICO que aparezca en el texto. Responde solo con JSON."""

    user_prompt_en = f"""PRESENTATION CONTENT:
{base_content}

Generate {num_questions} multiple-choice questions based only on the content above. Each question must evaluate a SPECIFIC fact or concept that appears in the text. Respond only with JSON."""

    system_prompt = system_prompt_es if language == "es" else system_prompt_en
    user_prompt = user_prompt_es if language == "es" else user_prompt_en

    logger.info(f"Sending {len(base_content)} chars to LLM for question generation")

    raw_response = await client.generate(
        messages=[
            LLMSystemMessage(content=system_prompt),
            LLMUserMessage(content=user_prompt),
        ],
        model=get_model(),
        max_tokens=2500,
    )

    if not raw_response:
        raise ValueError("Empty response from LLM")

    parsed = _safe_parse_json(raw_response)
    if not parsed:
        raise ValueError("Could not parse JSON from LLM response")

    questions_data = QuestionsResponse(**parsed)

    if not questions_data.questions:
        raise ValueError("LLM returned empty questions list")

    # Formatear para el frontend
    formatted = []
    for i, q in enumerate(questions_data.questions):
        # Validar que correct_answer esté en rango
        correct = max(0, min(3, q.correct_answer))
        formatted.append({
            "id": i + 1,
            "question": q.question,
            "options": q.options[:4],  # Asegurar máximo 4 opciones
            "correctAnswer": correct,
            "explanation": q.explanation,
        })

    logger.info(f"Successfully generated {len(formatted)} questions from real content")
    return formatted


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: preguntas basadas en análisis del texto (sin LLM)
# ─────────────────────────────────────────────────────────────────────────────

def generate_fallback_questions(
    content: str,
    num_questions: int,
    language: str,
    outlines: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Genera preguntas de fallback analizando el texto sin LLM.
    Extrae palabras clave, cifras y frases para construir preguntas específicas.
    """

    # Usar el contenido limpio de outlines si está disponible
    if outlines:
        clean = extract_clean_content_from_slides(outlines)
        analysis_content = clean if len(clean.strip()) > 50 else content
    else:
        analysis_content = content

    # Eliminar los marcadores [Slide N] para que no contaminen el análisis
    clean_for_analysis = re.sub(r'\[Slide \d+\]', '', analysis_content)

    # ── Extracción de datos ──────────────────────────────────────────────────
    numbers = re.findall(r'\b\d+(?:[.,]\d+)?%?\b', clean_for_analysis)
    years = re.findall(r'\b(?:19|20)\d{2}\b', clean_for_analysis)
    capitalized = re.findall(
        r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,})*\b',
        clean_for_analysis,
    )

    # Frecuencia de palabras (ignorar stopwords y marcadores internos)
    stopwords = {
        'para', 'con', 'que', 'por', 'como', 'una', 'del', 'las', 'los',
        'este', 'esta', 'pero', 'más', 'muy', 'son', 'fue', 'han', 'hay',
        'slide', 'the', 'and', 'for', 'with', 'that', 'this', 'are', 'was', 'have',
    }
    words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{5,}\b', clean_for_analysis)
    freq: Dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if wl not in stopwords:
            freq[wl] = freq.get(wl, 0) + 1

    top_words = [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:8]]
    main_topic = capitalized[0] if capitalized else (top_words[0] if top_words else "el tema")
    second_topic = (capitalized[1] if len(capitalized) > 1 else
                    top_words[1] if len(top_words) > 1 else "el concepto")

    # Frases completas para usar como base de preguntas
    sentences = [s.strip() for s in re.split(r'[.!?]', analysis_content) if len(s.strip()) > 40]

    # ── Construcción de preguntas con correctAnswer variado ──────────────────
    questions = []

    def make_q(question, options, correct, explanation):
        return {
            "id": len(questions) + 1,
            "question": question,
            "options": options,
            "correctAnswer": correct,
            "explanation": explanation,
        }

    # Q1 – Sobre el tema central (correct = 2)
    questions.append(make_q(
        f"¿Qué describe principalmente '{main_topic}' en esta presentación?",
        [
            f"Un dato secundario de apoyo",
            f"Un concepto no relacionado con {second_topic}",
            f"El elemento central que se desarrolla a lo largo de la presentación",
            f"Una conclusión ambigua sin base factual",
        ],
        correct=2,
        explanation=f"'{main_topic}' es el concepto principal que estructura el contenido de la presentación.",
    ))

    # Q2 – Sobre cifras (correct = 0 o 3 dependiendo de si hay datos)
    if numbers:
        num = numbers[0]
        questions.append(make_q(
            f"¿Qué dato numérico ({num}) se menciona en la presentación?",
            [
                f"Una cifra concreta relacionada con {main_topic}",
                f"Un número hipotético sin fuente",
                f"Una estimación aproximada sin validar",
                f"Un dato histórico sin relevancia actual",
            ],
            correct=0,
            explanation=f"El valor {num} es un dato específico que aparece en el contenido de la presentación.",
        ))
    elif sentences:
        sentence = sentences[0][:80]
        questions.append(make_q(
            f"¿Qué afirma la presentación sobre {main_topic}?",
            [
                f"Lo que se describe: '{sentence}...'",
                f"Una afirmación opuesta a la presentada",
                f"Un punto de vista no incluido en la presentación",
                f"Una definición alternativa no mencionada",
            ],
            correct=0,
            explanation=f"La presentación afirma específicamente esto sobre {main_topic}.",
        ))

    # Q3 – Sobre el segundo concepto (correct = 1)
    questions.append(make_q(
        f"¿Cuál es la relación entre '{main_topic}' y '{second_topic}' según la presentación?",
        [
            f"Son conceptos opuestos sin relación",
            f"'{second_topic}' complementa o forma parte de '{main_topic}'",
            f"'{second_topic}' sustituye completamente a '{main_topic}'",
            f"La presentación no los relaciona",
        ],
        correct=1,
        explanation=f"La presentación presenta '{second_topic}' como un elemento que complementa a '{main_topic}'.",
    ))

    # Q4 – Sobre años/fechas (correct = 3)
    if years:
        year = years[0]
        questions.append(make_q(
            f"¿Qué relevancia tiene el año {year} para el tema de la presentación?",
            [
                f"Es una fecha sin impacto en el tema",
                f"Marca el inicio de un período no relacionado",
                f"Es solo una referencia bibliográfica",
                f"Señala un hito importante relacionado con {main_topic}",
            ],
            correct=3,
            explanation=f"El año {year} aparece en la presentación como un hito significativo.",
        ))
    else:
        questions.append(make_q(
            f"¿Qué aspecto de '{main_topic}' destaca más la presentación?",
            [
                f"Sus limitaciones y desventajas",
                f"Su historia sin aplicación actual",
                f"Datos no verificados sobre el tema",
                f"Su impacto y relevancia en el contexto presentado",
            ],
            correct=3,
            explanation=f"La presentación pone énfasis en el impacto y relevancia de '{main_topic}'.",
        ))

    # Q5 – Pregunta de síntesis (correct = 2)
    third_topic = top_words[2] if len(top_words) > 2 else "los resultados"
    questions.append(make_q(
        f"¿Qué conclusión puede extraerse sobre '{third_topic}' a partir de la presentación?",
        [
            f"'{third_topic}' no tiene relevancia en este contexto",
            f"'{third_topic}' contradice el argumento principal",
            f"'{third_topic}' refuerza los puntos clave de la presentación",
            f"'{third_topic}' fue descartado como tema secundario",
        ],
        correct=2,
        explanation=f"La presentación muestra que '{third_topic}' es consistente con y refuerza los puntos principales.",
    ))

    # Completar si hacen falta más preguntas
    while len(questions) < num_questions:
        idx = len(questions) % len(questions[:5])
        extra = questions[idx].copy()
        extra["id"] = len(questions) + 1
        extra["question"] = "Revisión: " + extra["question"]
        questions.append(extra)

    return questions[:num_questions]
