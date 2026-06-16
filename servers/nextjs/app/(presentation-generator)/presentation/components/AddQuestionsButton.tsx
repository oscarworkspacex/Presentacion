"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { HelpCircle, Loader2, Plus } from "lucide-react";
import { useGenerateQuestions } from "../hooks/useGenerateQuestions";

interface AddQuestionsButtonProps {
  presentation_id: string;
  disabled?: boolean;
  variant?: "header" | "end-card" | "present-overlay";
  onQuestionsAdded?: (quizSlideIndex: number) => void;
}

const AddQuestionsButton: React.FC<AddQuestionsButtonProps> = ({
  presentation_id,
  disabled = false,
  variant = "header",
  onQuestionsAdded,
}) => {
  const {
    isLoading,
    hasQuestions,
    generateQuestions,
    regenerateQuestions,
    goToQuiz,
  } = useGenerateQuestions({
    presentationId: presentation_id,
    disabled,
    onQuestionsAdded,
  });

  if (variant === "end-card") {
    return (
      <div className="flex flex-col sm:flex-row items-center gap-3 mt-2">
        {hasQuestions ? (
          <>
            <Button
              onClick={regenerateQuestions}
              disabled={disabled || isLoading}
              variant="outline"
              className="rounded-full px-6"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <HelpCircle className="w-4 h-4 mr-2" />
              )}
              {isLoading ? "Regenerando..." : "Regenerar preguntas"}
            </Button>
            <Button
              onClick={goToQuiz}
              disabled={disabled || isLoading}
              className="rounded-full px-6 bg-[#5146E5] hover:bg-[#4338ca]"
            >
              Ir a la evaluaci?n
            </Button>
          </>
        ) : (
          <Button
            onClick={generateQuestions}
            disabled={disabled || isLoading}
            className="rounded-full px-8 bg-[#5146E5] hover:bg-[#4338ca]"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Plus className="w-4 h-4 mr-2" />
            )}
            {isLoading ? "Generando..." : "Generar preguntas"}
          </Button>
        )}
      </div>
    );
  }

  if (variant === "present-overlay") {
    if (hasQuestions) return null;

    return (
      <Button
        onClick={(e) => {
          e.stopPropagation();
          generateQuestions();
        }}
        disabled={disabled || isLoading}
        className="rounded-full px-6 bg-[#5146E5] hover:bg-[#4338ca] text-white shadow-lg"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Plus className="w-4 h-4 mr-2" />
        )}
        {isLoading ? "Generando..." : "Generar preguntas"}
      </Button>
    );
  }

  if (hasQuestions) {
    return (
      <Button
        onClick={regenerateQuestions}
        disabled={disabled || isLoading}
        variant="ghost"
        className="border border-white/70 font-bold text-white rounded-[32px] transition-all duration-300 group hover:bg-white hover:text-[#5146E5] disabled:opacity-50"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
        ) : (
          <HelpCircle className="w-4 h-4 mr-1 group-hover:text-[#5146E5]" />
        )}
        {isLoading ? "Regenerando..." : "Regenerar preguntas"}
      </Button>
    );
  }

  return (
    <Button
      onClick={generateQuestions}
      disabled={disabled || isLoading}
      variant="ghost"
      className="border border-white font-bold text-white rounded-[32px] transition-all duration-300 group hover:bg-white hover:text-[#5146E5] disabled:opacity-50"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
      ) : (
        <Plus className="w-4 h-4 mr-1 group-hover:text-[#5146E5]" />
      )}
      {isLoading ? "Generando..." : "Generar preguntas"}
    </Button>
  );
};

export default AddQuestionsButton;
