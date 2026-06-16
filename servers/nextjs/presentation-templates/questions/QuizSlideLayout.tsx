import React, { useState, useEffect, useMemo } from 'react'
import * as z from "zod";

export const layoutId = 'questions-quiz-slide'
export const layoutName = 'Evaluación de Conocimientos'
export const layoutDescription = 'Layout interactivo con 5 preguntas sobre el contenido de la presentación y cálculo de puntaje.'

const quizSlideSchema = z.object({
    presentationContent: z.string().default('').meta({
        description: "Contenido completo de la presentación para generar preguntas relevantes",
    }),
    title: z.string().min(5).max(50).default('Evaluación de Conocimientos').meta({
        description: "Título de la evaluación",
    }),
    description: z.string().min(10).max(200).default('Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.').meta({
        description: "Descripción de la evaluación",
    }),
    customQuestions: z.array(z.object({
        question: z.string(),
        options: z.array(z.string()),
        correctAnswer: z.number(),
        explanation: z.string()
    })).optional().meta({
        description: "Preguntas personalizadas (opcional)",
    })
})

export const Schema = quizSlideSchema

export type QuizSlideData = z.infer<typeof quizSlideSchema>

interface Question {
    id: number;
    question: string;
    options: string[];
    correctAnswer: number;
    explanation: string;
}

interface QuizSlideLayoutProps {
    data?: Partial<QuizSlideData>
}

const QuizSlideLayout: React.FC<QuizSlideLayoutProps> = ({ data: slideData }) => {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedAnswers, setSelectedAnswers] = useState<number[]>([]);
    const [showResults, setShowResults] = useState(false);

    const questionsSignature = useMemo(
        () => JSON.stringify(slideData?.customQuestions ?? []),
        [slideData?.customQuestions]
    );

    const questions = useMemo((): Question[] => {
        try {
            const parsed = JSON.parse(questionsSignature) as Array<{
                id?: number;
                question: string;
                options: string[];
                correctAnswer: number;
                explanation: string;
            }>;
            if (!Array.isArray(parsed) || parsed.length === 0) {
                return [];
            }
            return parsed.map((q, index) => ({
                id: q.id ?? index + 1,
                question: q.question,
                options: [...q.options],
                correctAnswer: q.correctAnswer,
                explanation: q.explanation,
            }));
        } catch {
            return [];
        }
    }, [questionsSignature]);

    useEffect(() => {
        setCurrentQuestion(0);
        setSelectedAnswers(new Array(questions.length).fill(-1));
        setShowResults(false);
    }, [questionsSignature, questions.length]);

    const handleAnswerSelect = (questionIndex: number, answerIndex: number) => {
        setSelectedAnswers((prev) => {
            // Una vez seleccionada, la respuesta queda bloqueada y no se puede
            // cambiar (evita falsificar el resultado tras ver la explicación).
            if (prev[questionIndex] !== -1) {
                return prev;
            }
            const next = [...prev];
            next[questionIndex] = answerIndex;
            return next;
        });
    };

    const calculateScore = () => {
        let correct = 0;
        questions.forEach((question, index) => {
            if (selectedAnswers[index] === question.correctAnswer) {
                correct++;
            }
        });
        return correct;
    };

    const getScoreMessage = (score: number) => {
        const percentage = (score / questions.length) * 100;
        if (percentage >= 80) return "¡Excelente! Has comprendido muy bien el contenido.";
        if (percentage >= 60) return "¡Bien! Tienes un buen entendimiento del tema.";
        if (percentage >= 40) return "Regular. Te recomendamos revisar algunos conceptos.";
        return "Necesitas estudiar más el contenido presentado.";
    };

    const canFinishQuiz = selectedAnswers.length === questions.length &&
        selectedAnswers.every((answer) => answer !== -1);

    if (questions.length === 0) {
        return (
            <div data-interactive="true" className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
                <div className="max-w-xl bg-white rounded-xl shadow-lg p-8 text-center">
                    <h2 className="text-2xl font-bold text-gray-800 mb-3">
                        Preguntas no disponibles
                    </h2>
                    <p className="text-gray-600">
                        Elimina este slide y vuelve a pulsar el botón <strong>Preguntas</strong> para generar un cuestionario basado en el contenido de tu presentación.
                    </p>
                </div>
            </div>
        );
    }

    if (showResults) {
        const score = calculateScore();
        const percentage = (score / questions.length) * 100;

        return (
            <div data-interactive="true" className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 p-8">
                <div className="max-w-2xl mx-auto">
                    <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                        <h1 className="text-3xl font-bold text-gray-800 mb-4">
                            Resultados de la Evaluación
                        </h1>

                        <div className="mb-8">
                            <div className="text-6xl font-bold text-blue-600 mb-2">
                                {score}/{questions.length}
                            </div>
                            <div className="text-xl text-gray-600 mb-4">
                                {percentage.toFixed(0)}% de aciertos
                            </div>
                            <p className="text-lg text-gray-700">
                                {getScoreMessage(score)}
                            </p>
                        </div>

                        <div className="bg-gray-50 rounded-lg p-6 mb-6">
                            <h3 className="text-lg font-semibold mb-4">Resumen de respuestas:</h3>
                            <div className="space-y-2">
                                {questions.map((question, index) => (
                                    <div key={`summary-${index}-${question.id}`} className="flex items-center justify-between">
                                        <span className="text-sm">Pregunta {index + 1}:</span>
                                        <span className={`text-sm font-medium ${
                                            selectedAnswers[index] === question.correctAnswer
                                                ? 'text-green-600'
                                                : 'text-red-600'
                                        }`}>
                                            {selectedAnswers[index] === question.correctAnswer ? '✓ Correcta' : '✗ Incorrecta'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            type="button"
                            onClick={() => {
                                setCurrentQuestion(0);
                                setSelectedAnswers(new Array(questions.length).fill(-1));
                                setShowResults(false);
                            }}
                            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Repetir Evaluación
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const currentQ = questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questions.length) * 100;

    if (!currentQ) {
        return null;
    }

    return (
        <div data-interactive="true" className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
            <div className="max-w-2xl mx-auto">
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex justify-between items-center mb-4">
                        <h1 className="text-2xl font-bold text-gray-800">
                            {slideData?.title || 'Evaluación de Conocimientos'}
                        </h1>
                        <span className="text-sm text-gray-500">
                            Pregunta {currentQuestion + 1} de {questions.length}
                        </span>
                    </div>

                    <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>

                    <p className="text-gray-600">
                        {slideData?.description || 'Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.'}
                    </p>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-6">
                        {currentQ.question}
                    </h2>

                    <div className="space-y-3">
                        {currentQ.options.map((option, index) => {
                            const isLocked = selectedAnswers[currentQuestion] !== -1;
                            const isSelected = selectedAnswers[currentQuestion] === index;
                            const isCorrectOption = index === currentQ.correctAnswer;
                            const isWrongSelection = isLocked && isSelected && !isCorrectOption;

                            let optionClasses = 'border-gray-200 hover:border-gray-300 hover:bg-gray-50';
                            if (isLocked) {
                                if (isCorrectOption) {
                                    optionClasses = 'border-green-500 bg-green-50 text-green-800';
                                } else if (isWrongSelection) {
                                    optionClasses = 'border-red-500 bg-red-50 text-red-800';
                                } else {
                                    optionClasses = 'border-gray-200 bg-white text-gray-400';
                                }
                            } else if (isSelected) {
                                optionClasses = 'border-blue-500 bg-blue-50 text-blue-700';
                            }

                            let markerClasses = 'border-gray-300';
                            if (isLocked) {
                                if (isCorrectOption) {
                                    markerClasses = 'border-green-500 bg-green-500';
                                } else if (isWrongSelection) {
                                    markerClasses = 'border-red-500 bg-red-500';
                                }
                            } else if (isSelected) {
                                markerClasses = 'border-blue-500 bg-blue-500';
                            }

                            return (
                                <button
                                    type="button"
                                    key={`q${currentQuestion}-opt${index}`}
                                    onClick={() => handleAnswerSelect(currentQuestion, index)}
                                    disabled={isLocked}
                                    className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                                        isLocked ? 'cursor-not-allowed' : ''
                                    } ${optionClasses}`}
                                >
                                    <div className="flex items-center">
                                        <div className={`w-5 h-5 rounded-full border-2 mr-3 shrink-0 flex items-center justify-center ${markerClasses}`}>
                                            {isLocked && isCorrectOption && (
                                                <span className="text-white text-xs font-bold leading-none">✓</span>
                                            )}
                                            {isWrongSelection && (
                                                <span className="text-white text-xs font-bold leading-none">✗</span>
                                            )}
                                            {!isLocked && isSelected && (
                                                <div className="w-2 h-2 bg-white rounded-full"></div>
                                            )}
                                        </div>
                                        <span>{option}</span>
                                    </div>
                                </button>
                            );
                        })}
                    </div>

                    {selectedAnswers[currentQuestion] !== -1 && (
                        <>
                            <div className={`mt-6 p-4 rounded-lg ${
                                selectedAnswers[currentQuestion] === currentQ.correctAnswer
                                    ? 'bg-green-50'
                                    : 'bg-red-50'
                            }`}>
                                <p className={`text-sm font-semibold mb-1 ${
                                    selectedAnswers[currentQuestion] === currentQ.correctAnswer
                                        ? 'text-green-800'
                                        : 'text-red-800'
                                }`}>
                                    {selectedAnswers[currentQuestion] === currentQ.correctAnswer
                                        ? '✓ ¡Respuesta correcta!'
                                        : '✗ Respuesta incorrecta'}
                                </p>
                            </div>
                            <div className="mt-3 p-4 bg-blue-50 rounded-lg">
                                <p className="text-sm text-blue-800">
                                    <strong>Explicación:</strong> {currentQ.explanation}
                                </p>
                            </div>
                        </>
                    )}
                </div>

                <div className="flex justify-between">
                    <button
                        type="button"
                        onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
                        disabled={currentQuestion === 0}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Anterior
                    </button>

                    {currentQuestion < questions.length - 1 ? (
                        <button
                            type="button"
                            onClick={() => setCurrentQuestion((prev) => prev + 1)}
                            disabled={selectedAnswers[currentQuestion] === -1}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Siguiente
                        </button>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setShowResults(true)}
                            disabled={!canFinishQuiz}
                            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Finalizar Evaluación
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default QuizSlideLayout;
