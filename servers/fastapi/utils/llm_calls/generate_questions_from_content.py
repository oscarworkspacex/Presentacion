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


class SingleQuestionResponse(BaseModel):
    question: GeneratedQuestion


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
            len(cleaned) >= 8
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
    chunks = extract_slide_chunks(slides_content)
    if not chunks:
        return ""

    all_parts = []
    for i, chunk in enumerate(chunks):
        all_parts.append(f"[Slide {i + 1}]")
        all_parts.append(chunk)

    return "\n".join(all_parts)


def extract_slide_chunks(slides_content: List[Dict[str, Any]]) -> List[str]:
    """Extrae el texto de cada slide como fragmentos independientes."""
    chunks: List[str] = []

    for slide in slides_content:
        if not slide:
            continue

        raw = slide.get("content", slide)
        texts = _extract_text_from_value(raw)
        if not texts:
            continue

        chunk = " ".join(texts).strip()
        if len(chunk) >= 20:
            chunks.append(chunk)

    return chunks


def _normalize_for_comparison(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _question_similarity(a: str, b: str) -> float:
    """Mide similitud simple entre dos preguntas (0 = distintas, 1 = iguales)."""
    words_a = set(_normalize_for_comparison(a).split())
    words_b = set(_normalize_for_comparison(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union else 0.0


def deduplicate_questions(
    questions: List[Dict[str, Any]],
    similarity_threshold: float = 0.55,
) -> List[Dict[str, Any]]:
    """Elimina preguntas repetidas o casi idénticas."""
    unique: List[Dict[str, Any]] = []

    for question in questions:
        question_text = question.get("question", "").strip()
        if not question_text:
            continue

        is_duplicate = False
        for existing in unique:
            if _normalize_for_comparison(question_text) == _normalize_for_comparison(existing["question"]):
                is_duplicate = True
                break
            if _question_similarity(question_text, existing["question"]) >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(question)

    for index, question in enumerate(unique):
        question["id"] = index + 1

    return unique


def _format_question(q: GeneratedQuestion, question_id: int) -> Dict[str, Any]:
    correct = max(0, min(3, q.correct_answer))
    options = q.options[:4]
    while len(options) < 4:
        options.append(f"Opción {len(options) + 1}")
    
    # Crear un nuevo dict completamente independiente para evitar referencias compartidas
    return {
        "id": int(question_id),
        "question": str(q.question.strip()),
        "options": [str(opt) for opt in options],
        "correctAnswer": int(correct),
        "explanation": str(q.explanation),
    }


def _extract_facts_from_slide(chunk: str) -> List[Dict[str, str]]:
    """Extrae hechos concretos del texto de un slide para guiar preguntas coherentes."""
    facts: List[Dict[str, str]] = []
    sentences = [s.strip() for s in re.split(r'[.!?\n]\s+', chunk) if len(s.strip()) >= 12]

    formations = re.findall(r'\b\d-\d-\d\b', chunk)
    for formation in dict.fromkeys(formations):
        facts.append({"type": "formation", "value": formation, "context": chunk[:200]})

    duration_matches = re.finditer(
        r'(\d+(?:[.,]\d+)?)\s*(minutos|minuto|min)\b',
        chunk,
        re.IGNORECASE,
    )
    for match in duration_matches:
        facts.append({
            "type": "duration",
            "value": f"{match.group(1)} minutos",
            "context": chunk[:200],
        })

    player_matches = re.finditer(
        r'(\d+)\s*(jugadores|jugador)\b',
        chunk,
        re.IGNORECASE,
    )
    for match in player_matches:
        facts.append({
            "type": "players",
            "value": f"{match.group(1)} jugadores",
            "context": chunk[:200],
        })

    for sentence in sentences[:4]:
        if len(sentence) >= 20:
            facts.append({"type": "statement", "value": sentence[:120], "context": chunk[:200]})

    # Números genéricos al final, evitando el dígito de nombres como "Fútbol 7"
    number_matches = re.finditer(r'\b(\d+(?:[.,]\d+)?)\b', chunk)
    for match in number_matches:
        start = match.start()
        prefix = chunk[max(0, start - 12):start]
        if re.search(r'[A-Za-zÁÉÍÓÚáéíóú]\s*$', prefix):
            continue
        value = match.group(1)
        if any(f["type"] in {"duration", "players", "formation"} and value in f["value"] for f in facts):
            continue
        facts.append({"type": "number", "value": value, "context": chunk[:200]})

    priority = {"duration": 0, "formation": 1, "players": 2, "statement": 3, "number": 4}
    unique_facts: List[Dict[str, str]] = []
    seen = set()
    for fact in sorted(facts, key=lambda item: priority.get(item["type"], 99)):
        key = (fact["type"], fact["value"])
        if key not in seen:
            seen.add(key)
            unique_facts.append(fact)

    return unique_facts[:6]


def _basic_validation(question: str, options: List[str]) -> bool:
    """Validación mínima: estructura básica correcta."""
    # Solo verificar que no esté vacío y tenga 4 opciones diferentes
    if not question or len(question.strip()) < 5:
        return False
    if len(options) != 4:
        return False
    if len(set(opt.strip().lower() for opt in options)) < 4:
        return False
    return True




def _facts_prompt_block(facts: List[Dict[str, str]], language: str) -> str:
    if not facts:
        return ""

    lines = []
    for index, fact in enumerate(facts[:5], start=1):
        lines.append(f"{index}. [{fact['type']}] {fact['value']}")

    header = "HECHOS DETECTADOS EN ESTE SLIDE:" if language == "es" else "FACTS DETECTED IN THIS SLIDE:"
    return f"\n{header}\n" + "\n".join(lines)


def _is_generic_question(question_text: str) -> bool:
    """Validación mínima: rechaza solo preguntas extremadamente vagas."""
    normalized = _normalize_for_comparison(question_text)
    # Solo rechazar si la pregunta es completamente vacía o trivial
    if len(normalized) < 10:
        return True
    return False


async def _generate_single_question_for_slide(
    client: LLMClient,
    slide_index: int,
    slide_chunk: str,
    language: str,
    existing_questions: List[str],
) -> Optional[Dict[str, Any]]:
    """Genera exactamente una pregunta coherente para un slide concreto."""
    facts = _extract_facts_from_slide(slide_chunk)
    facts_block = _facts_prompt_block(facts, language)

    existing_block = ""
    if existing_questions:
        joined = "\n".join(f"- {q}" for q in existing_questions)
        existing_block = (
            f"\n\nPREGUNTAS YA USADAS (NO repitas ni reformules ninguna de estas):\n{joined}"
            if language == "es"
            else f"\n\nALREADY USED QUESTIONS (do NOT repeat or rephrase any of these):\n{joined}"
        )

    if language == "es":
        system_prompt = """Eres un generador de preguntas de evaluación.

INSTRUCCIÓN CRÍTICA: Debes responder SIEMPRE en formato JSON, NUNCA en texto plano.
IDIOMA: Genera la pregunta en ESPAÑOL (mismo idioma del contenido).

PROCESO OBLIGATORIO (sigue estos pasos):

PASO 1: Lee el contenido del slide y encuentra UN DATO CONCRETO.
Ejemplos de datos concretos:
- Un número específico: "7 jugadores", "25 minutos", "2 tiempos"
- Una formación: "3-2-1", "4-4-2"  
- Un nombre: "Copa América", "Mundial"
- Una fecha: "1990", "cada 4 años"
- Una regla: "el portero no puede salir"

PASO 2: Pregunta ESPECÍFICA sobre ese dato (NO genérica).
❌ MAL: "¿Cuál es una característica?"
✅ BIEN: "¿Cuántos jugadores tiene cada equipo?"

PASO 3: 4 opciones del MISMO TIPO.
Si es número → todas opciones son números
Si es formación → todas opciones son formaciones

PASO 4: La correcta DEBE estar en el slide.

RESPONDE SIEMPRE ASÍ (JSON):
{"question":{"question":"¿Pregunta aquí?","options":["opción 1","opción 2","opción 3","opción 4"],"correct_answer":0,"explanation":"Explicación"}}"""
        user_prompt = f"""CONTENIDO:
{slide_chunk[:1800]}

DATOS DETECTADOS:
{facts_block}

{existing_block}

GENERA JSON CON 1 PREGUNTA ESPECÍFICA EN ESPAÑOL."""
    else:
        system_prompt = """You are an assessment question generator.

CRITICAL INSTRUCTION: You must ALWAYS respond in JSON format, NEVER in plain text.
LANGUAGE: Generate the question in ENGLISH (same language as content).

MANDATORY PROCESS (follow these steps):

STEP 1: Read slide content and find ONE CONCRETE FACT.
Examples of concrete facts:
- A specific number: "7 players", "25 minutes", "2 halves"
- A formation: "3-2-1", "4-4-2"
- A name: "Copa America", "World Cup"
- A date: "1990", "every 4 years"
- A rule: "goalkeeper cannot leave"

STEP 2: SPECIFIC question about that fact (NOT generic).
❌ BAD: "What is a characteristic?"
✅ GOOD: "How many players per team?"

STEP 3: 4 options of the SAME TYPE.
If number → all options are numbers
If formation → all options are formations

STEP 4: Correct answer MUST be in the slide.

ALWAYS RESPOND LIKE THIS (JSON):
{"question":{"question":"Question here?","options":["option 1","option 2","option 3","option 4"],"correct_answer":0,"explanation":"Explanation"}}"""
        user_prompt = f"""CONTENT:
{slide_chunk[:1800]}

DETECTED FACTS:
{facts_block}

{existing_block}

GENERATE JSON WITH 1 SPECIFIC QUESTION IN ENGLISH."""

    raw_response = await client.generate(
        messages=[
            LLMSystemMessage(content=system_prompt),
            LLMUserMessage(content=user_prompt),
        ],
        model=get_model(),
        max_tokens=700,
    )

    if not raw_response:
        return None

    parsed = _safe_parse_json(raw_response)
    if not parsed:
        return None

    question_payload = parsed.get("question", parsed)
    try:
        generated = GeneratedQuestion(**question_payload)
    except Exception:
        return None

    formatted = _format_question(generated, slide_index + 1)
    question_text = formatted["question"]
    
    # Log de la pregunta generada para debugging
    logger.info(f"Pregunta generada para slide {slide_index + 1}: {question_text[:100]}")

    # Validación mínima: estructura básica
    if not _basic_validation(question_text, formatted["options"]):
        logger.warning(f"Pregunta rechazada por validación básica: {question_text[:80]}")
        return None

    # Evitar duplicados
    for existing in existing_questions:
        if _normalize_for_comparison(question_text) == _normalize_for_comparison(existing):
            return None
        if _question_similarity(question_text, existing) >= 0.55:
            return None

    return formatted


async def _generate_questions_per_slide(
    slide_chunks: List[str],
    num_questions: int,
    language: str,
) -> List[Dict[str, Any]]:
    """Genera una pregunta independiente por cada slide."""
    client = LLMClient()
    questions: List[Dict[str, Any]] = []
    existing_texts: List[str] = []

    for index, chunk in enumerate(slide_chunks[:num_questions]):
        generated = await _generate_single_question_for_slide(
            client,
            index,
            chunk,
            language,
            existing_texts,
        )
        if generated:
            questions.append(generated)
            existing_texts.append(generated["question"])
            continue

        fallback = _build_fallback_question_for_slide(index, chunk, language)
        if fallback and _validate_question_quality(fallback, chunk) and not any(
            _question_similarity(fallback["question"], existing) >= 0.55
            for existing in existing_texts
        ):
            fallback["id"] = len(questions) + 1
            questions.append(fallback)
            existing_texts.append(fallback["question"])

    for index, question in enumerate(questions):
        question["id"] = index + 1

    return questions[:num_questions]


def _build_slide_prompt_sections(slide_chunks: List[str]) -> str:
    sections = []
    for index, chunk in enumerate(slide_chunks):
        sections.append(f"--- SLIDE {index + 1} ---\n{chunk[:900]}")
    return "\n\n".join(sections)


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
        language: Idioma sugerido ('es' o 'en')
        outlines: Lista de dicts con el contenido de cada slide (opcional)

    Returns:
        Lista de preguntas formateadas para el frontend
    """
    slide_chunks: List[str] = []
    if outlines:
        slide_chunks = extract_slide_chunks(outlines)
        clean_content = extract_clean_content_from_slides(outlines)
        if len(clean_content.strip()) > 50:
            base_content = clean_content
            logger.info(
                f"Using {len(outlines)} slide outlines ({len(base_content)} chars, {len(slide_chunks)} chunks)"
            )
        else:
            base_content = presentation_content
            logger.info("Outlines yielded no useful text, falling back to presentation_content")
    else:
        base_content = presentation_content
        slide_chunks = [
            chunk.strip()
            for chunk in re.split(r'\[Slide \d+\]', base_content)
            if len(chunk.strip()) >= 20
        ]

    if len(base_content.strip()) < 30 and not slide_chunks:
        logger.warning("Content too short to generate meaningful questions")
        raise ValueError("Insufficient content for question generation")

    if not slide_chunks:
        slide_chunks = [base_content[:1200]]

    # Estrategia: 1 pregunta por slide para máxima diversidad
    per_slide_questions = await _generate_questions_per_slide(
        slide_chunks,
        num_questions,
        language,
    )

    if len(per_slide_questions) >= min(num_questions, len(slide_chunks)):
        logger.info(f"Generated {len(per_slide_questions)} unique per-slide questions")
        return per_slide_questions[:num_questions]

    # Completar faltantes con fallback por slide
    existing_texts = [q["question"] for q in per_slide_questions]
    for index, chunk in enumerate(slide_chunks):
        if len(per_slide_questions) >= num_questions:
            break
        fallback = _build_fallback_question_for_slide(index, chunk, language)
        if not fallback:
            continue
        if any(_question_similarity(fallback["question"], existing) >= 0.55 for existing in existing_texts):
            continue
        fallback["id"] = len(per_slide_questions) + 1
        per_slide_questions.append(fallback)
        existing_texts.append(fallback["question"])

    final_questions = deduplicate_questions(per_slide_questions)[:num_questions]
    for index, question in enumerate(final_questions):
        question["id"] = index + 1

    if not final_questions:
        raise ValueError("Could not generate unique questions from presentation content")

    logger.info(f"Successfully generated {len(final_questions)} unique questions")
    return final_questions


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: preguntas basadas en análisis del texto (sin LLM)
# ─────────────────────────────────────────────────────────────────────────────

def _build_fallback_question_for_slide(
    slide_index: int,
    chunk: str,
    language: str,
) -> Optional[Dict[str, Any]]:
    """
    Fallback simple: extrae hechos del slide y crea una pregunta de afirmación.
    Sin templates hardcodeados - funcionará para cualquier tema.
    """
    # Extraer oraciones/hechos del contenido
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', chunk) if len(s.strip()) >= 20]
    
    if not sentences:
        return None
    
    # Tomar la primera oración como hecho verdadero
    true_statement = sentences[0][:120]
    
    # Crear la pregunta de forma universal
    if language == "es":
        question = "Según el contenido presentado en este slide, ¿cuál de las siguientes afirmaciones es correcta?"
        explanation = f"El slide indica que: {true_statement}"
        false_prefix = "Esta información no aparece en el contenido"
    else:
        question = "According to the content presented in this slide, which of the following statements is correct?"
        explanation = f"The slide states that: {true_statement}"
        false_prefix = "This information does not appear in the content"
    
    # Opciones: la verdadera + otras oraciones del slide como distractores
    options = [true_statement]
    
    # Agregar otras oraciones como distractores si existen
    for sent in sentences[1:4]:
        if sent != true_statement and len(sent) >= 15:
            options.append(sent[:120])
    
    # Completar con opciones genéricas si faltan
    while len(options) < 4:
        options.append(f"{false_prefix} ({len(options)})")
    
    # Eliminar duplicados y limitar a 4
    options = list(dict.fromkeys(options))[:4]
    
    question_data = {
        "id": slide_index + 1,
        "question": question,
        "options": options,
        "correctAnswer": 0,  # La primera opción es siempre la correcta
        "explanation": explanation,
    }
    
    # Validación básica
    if len(question_data["options"]) != 4:
        return None
    
    return question_data


def generate_fallback_questions(
    content: str,
    num_questions: int,
    language: str,
    outlines: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Genera preguntas de fallback analizando el texto sin LLM.
    Crea una pregunta distinta por cada slide o frase relevante.
    """
    slide_chunks: List[str] = []
    if outlines:
        slide_chunks = extract_slide_chunks(outlines)

    if not slide_chunks:
        analysis_content = re.sub(r'\[Slide \d+\]', '', content)
        slide_chunks = [
            sentence.strip()
            for sentence in re.split(r'[.!?]\s+', analysis_content)
            if len(sentence.strip()) >= 35
        ]

    questions: List[Dict[str, Any]] = []
    for index, chunk in enumerate(slide_chunks):
        if len(questions) >= num_questions:
            break
        fallback = _build_fallback_question_for_slide(index, chunk, language)
        if fallback:
            questions.append(fallback)

    return deduplicate_questions(questions)[:num_questions]
