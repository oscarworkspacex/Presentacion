import React from 'react'
import * as z from "zod";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_SUBTITLE,
    SLIDE_IMAGE_COMPACT,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'numbered-bullets-slide'
export const layoutName = 'Numbered Bullets'
export const layoutDescription = 'A slide layout with large title, supporting image, and numbered bullet points with descriptions.'

const numberedBulletsSlideSchema = z.object({
    title: z.string().min(3).max(40).default('Market Validation').meta({
        description: "Main title of the slide",
    }),
    image: ImageSchema.default({
        __image_url__: 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80',
        __image_prompt__: 'Business people analyzing charts and data on wall'
    }).meta({
        description: "Supporting image for the slide",
    }),
    bulletPoints: z.array(z.object({
        title: z.string().min(2).max(80).meta({
            description: "Bullet point title",
        }),
        description: z.string().min(10).max(150).meta({
            description: "Bullet point description",
        }),
    })).min(1).max(3).default([
        {
            title: 'Customer Insights',
            description: 'Surveys reveal that 78% of businesses are planning to invest in digital solutions, with 85% preferring customized approaches.'
        },
        {
            title: 'Pilot Program Success',
            description: 'The survey revealed that 78% of businesses plan to invest in digital solutions, and 85% prefer a tailored approach.'
        },
        {
            title: 'Market Validation',
            description: 'Early adopters reported a 40% improvement in engagement after implementing the proposed strategy.'
        },
    ]).meta({
        description: "List of numbered bullet points with descriptions",
    })
})

export const Schema = numberedBulletsSlideSchema

export type NumberedBulletsSlideData = z.infer<typeof numberedBulletsSlideSchema>

interface NumberedBulletsSlideLayoutProps {
    data?: Partial<NumberedBulletsSlideData>
}

const NumberedBulletsSlideLayout: React.FC<NumberedBulletsSlideLayoutProps> = ({ data: slideData }) => {
    const bulletPoints = (slideData?.bulletPoints || []).slice(0, 3)
    const bulletGridCols =
        bulletPoints.length === 3
            ? 'grid-cols-3'
            : bulletPoints.length === 2
              ? 'grid-cols-2'
              : 'grid-cols-1'

    return (
        <>
           <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
                rel="stylesheet"
            />

            <div
                className={`${SLIDE_CONTAINER} bg-white`}
                style={{
                    fontFamily: 'var(--heading-font-family,Inter)',
                    background:"var(--card-background-color,#ffffff)"
                }}
            >
                {(slideData as any)?.__companyName__ && (
                    <div className="absolute top-0 left-0 right-0 px-8 sm:px-12 lg:px-20 pt-4 z-10">
                        <div className="flex items-center gap-4">
                            <span className="text-sm sm:text-base font-semibold" style={{ color: 'var(--text-heading-color, #111827)' }}>
                                {(slideData as any)?.__companyName__ || 'Company Name'}
                            </span>
                            <div className="h-[2px] flex-1 opacity-70" style={{ backgroundColor: 'var(--text-heading-color, #111827)' }}></div>
                        </div>
                    </div>
                )}

                <div className="relative z-10 flex flex-col h-full px-8 sm:px-12 lg:px-20 pt-8 pb-6">
                    <div className="flex items-center justify-between gap-6 mb-6">
                        <div className="flex-1 min-w-0">
                            <h1
                                style={{ color: "var(--text-heading-color,#111827)" }}
                                className={`${SLIDE_TITLE} mb-3`}
                            >
                                {slideData?.title || 'Market Validation'}
                            </h1>
                            <div
                                style={{ background: "var(--text-heading-color,#9333ea)" }}
                                className="w-20 h-1"
                            />
                        </div>

                        <div className="flex-shrink-0 w-80 h-52">
                            <img
                                src={slideData?.image?.__image_url__ || ''}
                                alt={slideData?.image?.__image_prompt__ || slideData?.title || ''}
                                className={SLIDE_IMAGE_COMPACT}
                                style={{ background: "var(--tertiary-accent-color,#e5e7eb)" }}
                            />
                        </div>
                    </div>

                    <div className={`grid ${bulletGridCols} gap-4 flex-1 min-h-0`}>
                        {bulletPoints.map((bullet, index) => (
                            <div key={index} className="flex items-start gap-3">
                                <div className="flex-shrink-0 pt-1">
                                    <div
                                        style={{ color: "var(--text-heading-color,#111827)" }}
                                        className="text-3xl font-bold"
                                    >
                                        {String(index + 1).padStart(2, '0')}
                                    </div>
                                </div>

                                <div className="flex-1 min-w-0">
                                    <h3
                                        style={{ color: "var(--text-heading-color,#111827)" }}
                                        className={`${SLIDE_SUBTITLE} mb-2`}
                                    >
                                        {bullet.title}
                                    </h3>
                                    <p
                                        style={{ color: "var(--text-body-color,#4b5563)" }}
                                        className="text-sm leading-relaxed line-clamp-5 break-words"
                                    >
                                        {bullet.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-16 overflow-hidden pointer-events-none z-0">
                    <svg
                        className="w-full h-full opacity-20"
                        viewBox="0 0 1200 200"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M0 100C300 150 600 50 900 100C1050 125 1125 100 1200 100V200H0V100Z"
                            fill="url(#wave-gradient)"
                        />
                        <defs>
                            <linearGradient id="wave-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="var(--primary-accent-color,#9333ea)" />
                                <stop offset="50%" stopColor="var(--primary-accent-color,#9333ea)" />
                                <stop offset="100%" stopColor="var(--primary-accent-color,#9333ea)" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
            </div>
        </>
    )
}

export default NumberedBulletsSlideLayout
