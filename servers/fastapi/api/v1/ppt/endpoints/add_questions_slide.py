import uuid
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from models.presentation_with_slides import PresentationWithSlides
from utils.llm_calls.generate_questions_from_content import (
    generate_questions_from_presentation_content,
    generate_fallback_questions,
    extract_clean_content_from_slides,
)

logger = logging.getLogger(__name__)

ADD_QUESTIONS_ROUTER = APIRouter()


@ADD_QUESTIONS_ROUTER.post("/add-questions-slide", response_model=PresentationWithSlides)
async def add_questions_slide_to_presentation(
    presentation_id: Annotated[uuid.UUID, Body(description="Presentation ID to add questions slide to")],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Add an interactive questions slide to an existing presentation.
    This endpoint creates a new slide using the QuizSlideLayout template
    with the presentation content injected for generating relevant questions.
    """
    
    # Verify presentation exists
    presentation = await sql_session.get(PresentationModel, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Get existing slides to extract content and determine next index
    existing_slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    existing_slides_list = list(existing_slides)
    
    if not existing_slides_list:
        raise HTTPException(status_code=400, detail="Cannot add questions to a presentation with no slides")
    
    # Check if a questions slide already exists
    for slide in existing_slides_list:
        if slide.layout_group == "questions" or slide.layout == "questions:questions-quiz-slide":
            raise HTTPException(
                status_code=400, 
                detail="A questions slide already exists in this presentation"
            )
    
    # Usar la extracción centralizada que maneja estructuras JSON anidadas
    outlines = [{"content": slide.content} for slide in existing_slides_list if slide.content]
    presentation_content = extract_clean_content_from_slides(outlines)

    # Añadir título al inicio si está disponible
    if presentation.title and presentation_content:
        presentation_content = f"{presentation.title}\n\n{presentation_content}"
    elif presentation.title:
        presentation_content = presentation.title

    if not presentation_content.strip():
        presentation_content = "Esta presentación contiene información valiosa."

    # Detectar idioma de la presentación
    lang = getattr(presentation, "language", "es") or "es"

    # Generar preguntas con IA basadas en el contenido real
    try:
        logger.info(f"Generating questions for presentation '{presentation.title}' ({len(presentation_content)} chars)")
        generated_questions = await generate_questions_from_presentation_content(
            presentation_content=presentation_content,
            num_questions=5,
            language=lang,
            outlines=outlines,
        )
        logger.info(f"Generated {len(generated_questions)} questions successfully")
    except Exception as e:
        logger.warning(f"AI question generation failed: {e}. Using fallback.")
        generated_questions = generate_fallback_questions(
            presentation_content, 5, lang, outlines
        )
    
    # Calculate next slide index
    next_index = max(slide.index for slide in existing_slides_list) + 1
    
    # Create the questions slide content
    questions_slide_content = {
        "presentationContent": presentation_content,
        "title": "🎯 Evaluación de Conocimientos",
        "description": "Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.",
        "customQuestions": generated_questions
    }
    
    logger.info(f"Questions slide created with {len(generated_questions)} questions ({len(presentation_content)} chars of context)")

    # Create new questions slide
    questions_slide = SlideModel(
        id=uuid.uuid4(),
        presentation=presentation_id,
        layout_group="questions",
        layout="questions:questions-quiz-slide",
        index=next_index,
        content=questions_slide_content,
        speaker_note="Esta es una evaluación interactiva basada en el contenido de la presentación. Los usuarios pueden responder las preguntas y obtener retroalimentación inmediata."
    )
    
    # Save the new slide
    sql_session.add(questions_slide)
    await sql_session.commit()
    
    # Return updated presentation with all slides
    all_slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    
    return PresentationWithSlides(
        **presentation.model_dump(),
        slides=list(all_slides),
    )


@ADD_QUESTIONS_ROUTER.post("/check-questions-slide", response_model=dict)
async def check_if_presentation_has_questions_slide(
    presentation_id: Annotated[uuid.UUID, Body(description="Presentation ID to check")],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Check if a presentation already has a questions slide.
    Returns information about whether questions functionality is available.
    """
    
    # Verify presentation exists
    presentation = await sql_session.get(PresentationModel, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Check for existing questions slides
    slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    slides_list = list(slides)
    
    has_questions_slide = any(
        slide.layout_group == "questions" or slide.layout == "questions:questions-quiz-slide" 
        for slide in slides_list
    )
    
    total_slides = len(slides_list)
    
    return {
        "presentation_id": str(presentation_id),
        "has_questions_slide": has_questions_slide,
        "total_slides": total_slides,
        "can_add_questions": total_slides > 0 and not has_questions_slide,
        "message": (
            "Presentation already has a questions slide" if has_questions_slide
            else "Questions slide can be added" if total_slides > 0
            else "Cannot add questions to empty presentation"
        )
    }
