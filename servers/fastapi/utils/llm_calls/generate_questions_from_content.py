"""
Generación de preguntas de evaluación basadas en el contenido real de una presentación.

Las preguntas son generadas por IA usando EXCLUSIVAMENTE el contenido de los slides.
Reglas clave:
- Nivel profesional (comprensión / aplicación), no trivia obvia.
- Toda la información (pregunta, opciones, respuesta correcta y explicación) debe
  provenir 100% del contenido de las diapositivas. Prohibido conocimiento externo.
- Se valida "grounding": se descartan preguntas cuya respuesta correcta no esté
  respaldada por el texto de los slides.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from models.llm_message import LLMSystemMessage, LLMUserMessage
from services.llm_client import LLMClient
from utils.llm_provider import get_model

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de validación / esquema de respuesta del LLM
# ─────────────────────────────────────────────────────────────────────────────

class GeneratedQuestion(BaseModel):
    question: str = Field(description="Enunciado de la pregunta")
    options: List[str] = Field(description="Exactamente 4 opciones de respuesta")
    correct_answer: int = Field(description="Índice (0-3) de la opción correcta")
    explanation: str = Field(description="Explicación citando lo que dice el slide")


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

    Returns:
        Texto limpio concatenado y numerado por slide, listo para el LLM.
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


# ─────────────────────────────────────────────────────────────────────────────
# Normalización y similitud (para deduplicar y validar grounding)
# ─────────────────────────────────────────────────────────────────────────────

# Palabras vacías que no aportan a la validación de "grounding"
_STOPWORDS: Set[str] = {
    # Español
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "a", "ante", "con", "contra", "desde", "en", "entre", "hacia", "hasta",
    "para", "por", "segun", "sin", "sobre", "tras", "y", "e", "o", "u", "que",
    "como", "cual", "cuando", "donde", "es", "son", "ser", "esta", "este",
    "estos", "estas", "esto", "su", "sus", "se", "lo", "le", "les", "mas",
    "muy", "tambien", "pero", "porque", "si", "no", "ni", "ya", "cada", "todo",
    "todos", "toda", "todas", "otro", "otra", "tiene", "tienen", "puede",
    "pueden", "debe", "deben", "ningun", "ninguna", "siguiente", "siguientes",
    # Inglés
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "but",
    "with", "without", "from", "by", "as", "is", "are", "be", "this", "that",
    "these", "those", "it", "its", "they", "their", "which", "what", "when",
    "where", "how", "can", "could", "should", "must", "also", "more", "very",
    "each", "all", "any", "some", "other", "has", "have", "does",
}


def _normalize_for_comparison(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _significant_tokens(text: str) -> Set[str]:
    """Devuelve los tokens significativos (sin stopwords ni palabras cortas)."""
    tokens = _normalize_for_comparison(text).split()
    result: Set[str] = set()
    for token in tokens:
        if token in _STOPWORDS:
            continue
        # Conservar números y palabras de al menos 3 caracteres
        if token.isdigit() or len(token) >= 3:
            result.add(token)
    return result


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


# ─────────────────────────────────────────────────────────────────────────────
# Formateo y validación de preguntas
# ─────────────────────────────────────────────────────────────────────────────

def _format_question(q: GeneratedQuestion, question_id: int) -> Optional[Dict[str, Any]]:
    """Normaliza una pregunta generada al formato del frontend."""
    options = [str(opt).strip() for opt in q.options if str(opt).strip()]
    # Eliminar opciones duplicadas conservando el orden
    options = list(dict.fromkeys(options))

    if len(options) != 4:
        return None

    correct = q.correct_answer
    if not isinstance(correct, int) or correct < 0 or correct > 3:
        return None

    return {
        "id": int(question_id),
        "question": str(q.question.strip()),
        "options": options,
        "correctAnswer": int(correct),
        "explanation": str(q.explanation).strip(),
    }


def _basic_validation(question: str, options: List[str]) -> bool:
    """Validación mínima: estructura básica correcta."""
    if not question or len(question.strip()) < 8:
        return False
    if len(options) != 4:
        return False
    if len(set(opt.strip().lower() for opt in options)) < 4:
        return False
    return True


def _is_grounded(
    question: Dict[str, Any],
    content_tokens: Set[str],
    min_ratio: float = 0.5,
) -> bool:
    """
    Verifica que la respuesta correcta esté respaldada por el contenido de los slides.

    Una pregunta se considera "grounded" si una proporción suficiente de los
    tokens significativos de la opción correcta aparece en el contenido de los
    slides. Esto evita preguntas/respuestas inventadas con datos externos.
    """
    if not content_tokens:
        return False

    options = question.get("options", [])
    correct_index = question.get("correctAnswer", 0)
    if correct_index < 0 or correct_index >= len(options):
        return False

    correct_text = options[correct_index]
    correct_tokens = _significant_tokens(correct_text)

    # Si la respuesta correcta no tiene tokens significativos (p.ej. "Sí"/"No"),
    # nos apoyamos en que la pregunta esté relacionada con el contenido.
    if not correct_tokens:
        question_tokens = _significant_tokens(question.get("question", ""))
        if not question_tokens:
            return False
        overlap = len(question_tokens & content_tokens) / len(question_tokens)
        return overlap >= min_ratio

    present = len(correct_tokens & content_tokens)
    ratio = present / len(correct_tokens)
    return ratio >= min_ratio


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

def _build_system_prompt(language: str) -> str:
    if language == "es":
        return """Eres un diseñador experto de evaluaciones académicas y profesionales.

Tu tarea: crear preguntas de opción múltiple de NIVEL PROFESIONAL para evaluar la
comprensión de una presentación.

REGLAS ABSOLUTAS (su incumplimiento invalida la respuesta):
1. FUENTE ÚNICA: Toda la información (enunciado, las 4 opciones, la respuesta
   correcta y la explicación) debe provenir EXCLUSIVAMENTE del contenido de los
   slides que se te entregan. PROHIBIDO usar conocimiento externo o inventar datos.
2. RESPUESTA VERIFICABLE: La opción correcta debe poder confirmarse leyendo el
   contenido. La explicación debe indicar qué parte del contenido lo respalda.
3. CALIDAD PROFESIONAL: Evita trivia obvia o preguntas de relleno. Evalúa
   comprensión, relaciones causa-efecto, aplicación de conceptos y datos clave.
4. DISTRACTORES PLAUSIBLES: Las 3 opciones incorrectas deben ser verosímiles y
   del mismo tipo que la correcta, pero claramente incorrectas según el contenido.
   No uses opciones como "Ninguna de las anteriores" ni texto de relleno.
5. FORMATO: Exactamente 4 opciones por pregunta. `correct_answer` es el índice
   (0 a 3) de la opción correcta. Varía la posición de la respuesta correcta.
6. IDIOMA: Redacta TODO en español.
7. SIN REPETIR: No repitas ni reformules la misma pregunta.

Responde ÚNICAMENTE con el JSON solicitado."""

    return """You are an expert designer of academic and professional assessments.

Your task: create PROFESSIONAL-LEVEL multiple-choice questions to evaluate the
understanding of a presentation.

ABSOLUTE RULES (violations invalidate the answer):
1. SINGLE SOURCE: All information (stem, the 4 options, the correct answer and the
   explanation) must come EXCLUSIVELY from the provided slide content. You are
   FORBIDDEN from using external knowledge or inventing data.
2. VERIFIABLE ANSWER: The correct option must be confirmable by reading the
   content. The explanation must state which part of the content supports it.
3. PROFESSIONAL QUALITY: Avoid obvious trivia or filler questions. Assess
   understanding, cause-effect relationships, application of concepts and key data.
4. PLAUSIBLE DISTRACTORS: The 3 incorrect options must be believable and of the
   same type as the correct one, but clearly wrong per the content. Do not use
   options like "None of the above" or filler text.
5. FORMAT: Exactly 4 options per question. `correct_answer` is the index (0 to 3)
   of the correct option. Vary the position of the correct answer.
6. LANGUAGE: Write EVERYTHING in English.
7. NO REPEATS: Do not repeat or rephrase the same question.

Respond ONLY with the requested JSON."""


def _build_user_prompt(
    content: str,
    num_questions: int,
    language: str,
    existing_questions: Optional[List[str]] = None,
) -> str:
    existing_block = ""
    if existing_questions:
        joined = "\n".join(f"- {q}" for q in existing_questions)
        if language == "es":
            existing_block = (
                f"\n\nPREGUNTAS YA GENERADAS (NO las repitas ni reformules):\n{joined}"
            )
        else:
            existing_block = (
                f"\n\nALREADY GENERATED QUESTIONS (do NOT repeat or rephrase):\n{joined}"
            )

    if language == "es":
        return f"""CONTENIDO DE LA PRESENTACIÓN (única fuente permitida):
\"\"\"
{content[:9000]}
\"\"\"

Genera exactamente {num_questions} preguntas de opción múltiple profesionales,
basadas únicamente en el contenido anterior.{existing_block}"""

    return f"""PRESENTATION CONTENT (only allowed source):
\"\"\"
{content[:9000]}
\"\"\"

Generate exactly {num_questions} professional multiple-choice questions, based
only on the content above.{existing_block}"""


# ─────────────────────────────────────────────────────────────────────────────
# Generación principal con LLM (salida estructurada)
# ─────────────────────────────────────────────────────────────────────────────

async def _request_questions(
    client: LLMClient,
    content: str,
    num_questions: int,
    language: str,
    existing_questions: Optional[List[str]] = None,
) -> List[GeneratedQuestion]:
    """Pide preguntas al LLM usando salida estructurada y las valida vía Pydantic."""
    messages = [
        LLMSystemMessage(content=_build_system_prompt(language)),
        LLMUserMessage(
            content=_build_user_prompt(content, num_questions, language, existing_questions)
        ),
    ]

    raw = await client.generate_structured(
        model=get_model(),
        messages=messages,
        response_format=QuestionsResponse.model_json_schema(),
        strict=True,
        max_tokens=3000,
    )

    if not raw:
        return []

    try:
        parsed = QuestionsResponse(**raw)
    except Exception as exc:
        logger.warning(f"No se pudo validar la respuesta del LLM: {exc}")
        # Intento tolerante: tomar la lista de 'questions' si viene presente
        questions_raw = raw.get("questions") if isinstance(raw, dict) else None
        if not isinstance(questions_raw, list):
            return []
        parsed_questions: List[GeneratedQuestion] = []
        for item in questions_raw:
            try:
                parsed_questions.append(GeneratedQuestion(**item))
            except Exception:
                continue
        return parsed_questions

    return parsed.questions


async def generate_questions_from_presentation_content(
    presentation_content: str,
    num_questions: int = 5,
    language: str = "es",
    outlines: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Genera preguntas de opción múltiple profesionales basadas exclusivamente en el
    contenido real de la presentación.

    Returns:
        Lista de preguntas formateadas para el frontend.
    """
    # Construir el contenido base y el conjunto de tokens para validar grounding
    if outlines:
        clean_content = extract_clean_content_from_slides(outlines)
        if len(clean_content.strip()) > 50:
            base_content = clean_content
            logger.info(
                f"Using {len(outlines)} slide outlines ({len(base_content)} chars)"
            )
        else:
            base_content = presentation_content
            logger.info("Outlines yielded no useful text, falling back to presentation_content")
    else:
        base_content = presentation_content

    if len(base_content.strip()) < 30:
        logger.warning("Content too short to generate meaningful questions")
        raise ValueError("Insufficient content for question generation")

    content_tokens = _significant_tokens(base_content)

    client = LLMClient()

    # Pedimos algunas preguntas extra para compensar las que se descarten por
    # validación / duplicados.
    requested = min(num_questions + 3, num_questions * 2)

    generated = await _request_questions(
        client, base_content, requested, language
    )

    valid_questions: List[Dict[str, Any]] = []
    existing_texts: List[str] = []

    def _try_accept(gq: GeneratedQuestion) -> bool:
        formatted = _format_question(gq, len(valid_questions) + 1)
        if not formatted:
            return False
        if not _basic_validation(formatted["question"], formatted["options"]):
            return False
        if not _is_grounded(formatted, content_tokens):
            logger.info(f"Pregunta descartada por falta de grounding: {formatted['question'][:80]}")
            return False
        for existing in existing_texts:
            if _normalize_for_comparison(formatted["question"]) == _normalize_for_comparison(existing):
                return False
            if _question_similarity(formatted["question"], existing) >= 0.55:
                return False
        valid_questions.append(formatted)
        existing_texts.append(formatted["question"])
        return True

    for gq in generated:
        if len(valid_questions) >= num_questions:
            break
        _try_accept(gq)

    # Segunda pasada si faltan preguntas válidas
    if len(valid_questions) < num_questions:
        missing = num_questions - len(valid_questions)
        logger.info(f"Faltan {missing} preguntas válidas, solicitando una pasada adicional")
        try:
            extra = await _request_questions(
                client, base_content, missing + 2, language, existing_texts
            )
            for gq in extra:
                if len(valid_questions) >= num_questions:
                    break
                _try_accept(gq)
        except Exception as exc:
            logger.warning(f"La pasada adicional de preguntas falló: {exc}")

    final_questions = deduplicate_questions(valid_questions)[:num_questions]
    for index, question in enumerate(final_questions):
        question["id"] = index + 1

    if not final_questions:
        raise ValueError("Could not generate grounded questions from presentation content")

    logger.info(f"Successfully generated {len(final_questions)} grounded questions")
    for i, q in enumerate(final_questions, 1):
        logger.info(f"  Final Q{i}: {q.get('question', '')}")

    return final_questions


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: preguntas basadas en el texto (sin LLM)
#
# Solo se usa si la generación con IA falla por completo. Construye preguntas
# del tipo "¿qué afirmación aparece en el contenido?" usando frases REALES de los
# slides como opciones. Nunca inventa información: si no hay suficientes frases
# reales para 4 opciones, esa pregunta se omite.
# ─────────────────────────────────────────────────────────────────────────────

def _split_into_statements(text: str) -> List[str]:
    """Divide un texto en afirmaciones limpias y razonablemente largas."""
    sentences = [s.strip() for s in re.split(r'[.!?\n]\s+', text) if len(s.strip()) >= 25]
    # Recortar para que sean opciones manejables
    return [s[:140] for s in sentences]


def _build_fallback_question_from_statements(
    question_index: int,
    correct_statement: str,
    distractor_pool: List[str],
    language: str,
) -> Optional[Dict[str, Any]]:
    """
    Construye una pregunta usando una afirmación verdadera (del contenido) y 3
    distractores tomados de OTRAS frases reales del contenido. Si no hay 3
    distractores reales disponibles, devuelve None (no se inventa nada).
    """
    distractors: List[str] = []
    for candidate in distractor_pool:
        if candidate == correct_statement:
            continue
        if candidate in distractors:
            continue
        if _question_similarity(candidate, correct_statement) >= 0.7:
            continue
        distractors.append(candidate)
        if len(distractors) == 3:
            break

    if len(distractors) < 3:
        return None

    options = [correct_statement] + distractors
    # Validar que las 4 opciones sean distintas
    if len(set(opt.strip().lower() for opt in options)) < 4:
        return None

    if language == "es":
        question_text = "¿Cuál de las siguientes afirmaciones corresponde al contenido de la presentación?"
        explanation = f"El contenido indica que: {correct_statement}"
    else:
        question_text = "Which of the following statements matches the presentation content?"
        explanation = f"The content states that: {correct_statement}"

    return {
        "id": question_index + 1,
        "question": question_text,
        "options": options,
        "correctAnswer": 0,
        "explanation": explanation,
    }


def generate_fallback_questions(
    content: str,
    num_questions: int,
    language: str,
    outlines: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Genera preguntas de respaldo (sin LLM) usando exclusivamente frases reales del
    contenido como opciones. No inventa información.
    """
    slide_chunks: List[str] = []
    if outlines:
        slide_chunks = extract_slide_chunks(outlines)

    if not slide_chunks:
        cleaned = re.sub(r'\[Slide \d+\]', '', content)
        slide_chunks = [cleaned]

    # Reunir todas las afirmaciones reales disponibles
    all_statements: List[str] = []
    for chunk in slide_chunks:
        for statement in _split_into_statements(chunk):
            if statement not in all_statements:
                all_statements.append(statement)

    questions: List[Dict[str, Any]] = []
    used_correct: List[str] = []

    for correct_statement in all_statements:
        if len(questions) >= num_questions:
            break
        if correct_statement in used_correct:
            continue
        # Distractores = otras frases reales del contenido
        distractor_pool = [s for s in all_statements if s != correct_statement]
        question = _build_fallback_question_from_statements(
            len(questions), correct_statement, distractor_pool, language
        )
        if question:
            questions.append(question)
            used_correct.append(correct_statement)

    # No se deduplica por enunciado: todas las preguntas de respaldo comparten el
    # mismo enunciado pero tienen respuestas correctas distintas (ya garantizadas
    # únicas mediante `used_correct`).
    final = questions[:num_questions]
    for index, question in enumerate(final):
        question["id"] = index + 1
    return final
