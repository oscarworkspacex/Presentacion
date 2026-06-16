"use client";

import React from "react";
import { HelpCircle } from "lucide-react";
import AddQuestionsButton from "./AddQuestionsButton";

interface GenerateQuestionsEndCardProps {
  presentationId: string;
  disabled?: boolean;
  onQuestionsAdded?: (quizSlideIndex: number) => void;
}

const GenerateQuestionsEndCard: React.FC<GenerateQuestionsEndCardProps> = ({
  presentationId,
  disabled = false,
  onQuestionsAdded,
}) => {
  return (
    <div className="w-full max-w-[1280px] mx-auto my-8 p-8 bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="flex flex-col items-center text-center gap-4">
        <div className="w-14 h-14 rounded-full bg-[#5146E5]/10 flex items-center justify-center">
          <HelpCircle className="w-7 h-7 text-[#5146E5]" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            ¿Listo para evaluar el aprendizaje?
          </h3>
          <p className="text-gray-600 max-w-md">
            Genera una encuesta de 5 preguntas de opción múltiple (4 opciones
            cada una) basada en el contenido de tu presentación.
          </p>
        </div>
        <AddQuestionsButton
          presentation_id={presentationId}
          disabled={disabled}
          variant="end-card"
          onQuestionsAdded={onQuestionsAdded}
        />
      </div>
    </div>
  );
};

export default GenerateQuestionsEndCard;
