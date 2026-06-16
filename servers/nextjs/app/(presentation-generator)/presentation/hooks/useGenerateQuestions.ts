"use client";

import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "sonner";
import { RootState } from "@/store/store";
import { addNewSlide, setPresentationData } from "@/store/slices/presentationGeneration";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";
import {
  cancelPendingAutoSave,
  setSkipAutoSave,
} from "./useAutoSave";

export function isQuizSlide(slide: { layout?: string; layout_group?: string } | null | undefined): boolean {
  return Boolean(
    slide?.layout?.includes("questions-quiz-slide") ||
    slide?.layout_group === "questions"
  );
}

export function findQuizSlideIndex(slides: { layout?: string }[] | undefined): number {
  if (!slides) return -1;
  return slides.findIndex((slide) => isQuizSlide(slide));
}

interface UseGenerateQuestionsOptions {
  presentationId: string;
  disabled?: boolean;
  onQuestionsAdded?: (quizSlideIndex: number) => void;
}

export function useGenerateQuestions({
  presentationId,
  disabled = false,
  onQuestionsAdded,
}: UseGenerateQuestionsOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const [hasQuestions, setHasQuestions] = useState<boolean | null>(null);
  const dispatch = useDispatch();
  const presentationData = useSelector(
    (state: RootState) => state.presentationGeneration.presentationData
  );

  const slides = presentationData?.slides;
  const quizSlideIndex = findQuizSlideIndex(slides);

  const checkQuestionsStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/ppt/check-questions-slide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(presentationId),
      });

      if (response.ok) {
        const data = await response.json();
        setHasQuestions(data.has_questions_slide);
        return data;
      }
      throw new Error("Failed to check questions status");
    } catch (error) {
      console.error("Error checking questions status:", error);
      return null;
    }
  }, [presentationId]);

  const navigateToQuiz = useCallback(
    (index: number) => {
      onQuestionsAdded?.(index);
    },
    [onQuestionsAdded]
  );

  const generateQuestions = useCallback(async () => {
    if (disabled || isLoading) return;

    setIsLoading(true);

    try {
      const status = await checkQuestionsStatus();

      if (status?.has_questions_slide) {
        const existingIndex = findQuizSlideIndex(slides);
        if (existingIndex >= 0) {
          navigateToQuiz(existingIndex);
        }
        toast.info("Preguntas ya disponibles", {
          description: "Esta presentación ya tiene un slide de evaluación.",
        });
        setIsLoading(false);
        return;
      }

      if (!status?.can_add_questions) {
        toast.error("No se pueden generar preguntas", {
          description:
            status?.message ||
            "No es posible generar preguntas para esta presentación.",
        });
        setIsLoading(false);
        return;
      }

      const response = await fetch("/api/v1/ppt/add-questions-slide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(presentationId),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add questions slide");
      }

      const data = await response.json();

      if (data.slides?.length > 0 && slides) {
        const quizSlide = data.slides[data.slides.length - 1];
        dispatch(
          addNewSlide({
            slideData: quizSlide,
            index: slides.length - 1,
          })
        );
        navigateToQuiz(slides.length);
      }

      toast.success("Preguntas generadas", {
        description:
          "Se agregó una evaluación de 5 preguntas al final de tu presentación.",
      });

      trackEvent(MixpanelEvent.Presentation_Add_Questions_Slide);
      setHasQuestions(true);
    } catch (error: unknown) {
      console.error("Error generating questions:", error);
      const message =
        error instanceof Error ? error.message : "Error desconocido";

      if (message.includes("already exists")) {
        toast.info("Preguntas ya disponibles", {
          description: "Esta presentación ya tiene un slide de evaluación.",
        });
        setHasQuestions(true);
      } else if (message.includes("no slides")) {
        toast.error("Presentación vacía", {
          description:
            "No se pueden generar preguntas en una presentación sin diapositivas.",
        });
      } else {
        toast.error("No se pudieron generar las preguntas", {
          description: "Ocurrió un error inesperado. Por favor intenta de nuevo.",
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, [
    disabled,
    isLoading,
    checkQuestionsStatus,
    slides,
    presentationId,
    dispatch,
    navigateToQuiz,
  ]);

  const regenerateQuestions = useCallback(async () => {
    if (disabled || isLoading) return;

    setIsLoading(true);
    cancelPendingAutoSave();
    setSkipAutoSave(true);

    try {
      toast.info("Regenerando preguntas...", {
        description: "Esto puede tomar unos segundos.",
      });

      const response = await fetch("/api/v1/ppt/regenerate-questions-slide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(presentationId),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to regenerate questions slide");
      }

      const data = await response.json();
      dispatch(setPresentationData(data));

      const newQuizIndex = findQuizSlideIndex(data.slides);
      if (newQuizIndex >= 0) {
        navigateToQuiz(newQuizIndex);
      }

      toast.success("Preguntas regeneradas", {
        description:
          "Se han generado nuevas preguntas basadas en el contenido actual.",
      });

      trackEvent(MixpanelEvent.Presentation_Add_Questions_Slide);
    } catch (error) {
      console.error("Error regenerating questions:", error);
      toast.error("No se pudieron regenerar las preguntas", {
        description: "Ocurrió un error inesperado. Por favor intenta de nuevo.",
      });
    } finally {
      setSkipAutoSave(false);
      setIsLoading(false);
    }
  }, [disabled, isLoading, presentationId, dispatch, navigateToQuiz]);

  const goToQuiz = useCallback(() => {
    if (quizSlideIndex >= 0) {
      navigateToQuiz(quizSlideIndex);
    }
  }, [quizSlideIndex, navigateToQuiz]);

  useEffect(() => {
    if (hasQuestions === null && presentationId) {
      checkQuestionsStatus();
    }
  }, [presentationId, hasQuestions, checkQuestionsStatus]);

  useEffect(() => {
    if (quizSlideIndex >= 0) {
      setHasQuestions(true);
    }
  }, [quizSlideIndex]);

  return {
    isLoading,
    hasQuestions: hasQuestions === true || quizSlideIndex >= 0,
    quizSlideIndex,
    generateQuestions,
    regenerateQuestions,
    goToQuiz,
    checkQuestionsStatus,
  };
}
