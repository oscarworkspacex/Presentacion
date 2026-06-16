import React from "react";
import { HelpCircle } from "lucide-react";

interface QuizSlideThumbnailProps {
  questionCount?: number;
  title?: string;
}

const QuizSlideThumbnail: React.FC<QuizSlideThumbnailProps> = ({
  questionCount = 5,
  title = "Evaluación de Conocimientos",
}) => {
  return (
    <div className="w-full h-full min-h-[120px] bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center justify-center p-4 text-center">
      <HelpCircle className="w-8 h-8 text-indigo-600 mb-2" />
      <p className="text-sm font-semibold text-gray-800 line-clamp-2">{title}</p>
      <p className="text-xs text-gray-600 mt-1">
        {questionCount} preguntas de opción múltiple
      </p>
    </div>
  );
};

export default QuizSlideThumbnail;
