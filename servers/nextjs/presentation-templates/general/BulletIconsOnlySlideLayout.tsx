import React from 'react'
import * as z from "zod";
import { ImageSchema, IconSchema } from '@/presentation-templates/defaultSchemes';
import { RemoteSvgIcon } from '@/app/hooks/useRemoteSvgIcon';
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_SUBTITLE,
    SLIDE_IMAGE_SIDE,
    getBulletGridCols,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'bullet-icons-only-slide'
export const layoutName = 'Bullet Icons Only'
export const layoutDescription = 'A slide layout with title, grid of bullet points (title and description) with icons, and a supporting image.'

const bulletIconsOnlySlideSchema = z.object({
    title: z.string().min(3).max(40).default('Solutions').meta({
        description: "Main title of the slide",
    }),
    image: ImageSchema.default({
        __image_url__: 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80',
        __image_prompt__: 'Business professionals collaborating and discussing solutions'
    }).meta({
        description: "Supporting image for the slide",
    }),
    bulletPoints: z.array(z.object({
        title: z.string().min(2).max(80).meta({
            description: "Bullet point title",
        }),
        subtitle: z.string().min(5).max(150).optional().meta({
            description: "Optional short subtitle or brief explanation",
        }),
        icon: IconSchema,
    })).min(2).max(3).default([
        {
            title: 'Custom Software',
            subtitle: 'We create tailored software to optimize processes and boost efficiency.',
            icon: {
                __icon_url__: 'https://presenton-public.s3.ap-southeast-1.amazonaws.com/static/icons/bold/code-bold.svg',
                __icon_query__: 'code software development'
            }
        },
        {
            title: 'Digital Consulting',
            subtitle: 'Our consultants guide organizations in leveraging the latest technologies.',
            icon: {
                __icon_url__: 'https://presenton-public.s3.ap-southeast-1.amazonaws.com/static/icons/bold/users-four-bold.svg',
                __icon_query__: 'users consulting team'
            }
        },
        {
            title: 'Support Services',
            subtitle: 'We provide ongoing support to help businesses adapt and maintain performance.',
            icon: {
                __icon_url__: 'https://presenton-public.s3.ap-southeast-1.amazonaws.com/static/icons/bold/headphones-bold.svg',
                __icon_query__: 'headphones support service'
            }
        },
    ]).meta({
        description: "List of bullet points with icons and optional subtitles",
    })
})

export const Schema = bulletIconsOnlySlideSchema

export type BulletIconsOnlySlideData = z.infer<typeof bulletIconsOnlySlideSchema>

interface BulletIconsOnlySlideLayoutProps {
    data?: Partial<BulletIconsOnlySlideData>
}

const BulletIconsOnlySlideLayout: React.FC<BulletIconsOnlySlideLayoutProps> = ({ data: slideData }) => {
    const bulletPoints = (slideData?.bulletPoints || []).slice(0, 3)
    const bulletGridCols = getBulletGridCols(bulletPoints.length)

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
                    background: "var(--card-background-color,#ffffff)"
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

                <div className="absolute top-0 left-0 w-32 h-full opacity-10 overflow-hidden pointer-events-none">
                    <svg className="w-full h-full" viewBox="0 0 100 400" fill="none">
                        <path d="M0 100C25 150 50 50 75 100C87.5 125 100 100 100 100V0H0V100Z" fill="#8b5cf6" opacity="0.4" />
                        <path d="M0 200C37.5 250 62.5 150 100 200V150C75 175 50 150 25 175L0 200Z" fill="#8b5cf6" opacity="0.3" />
                    </svg>
                </div>

                <div className="relative z-10 flex h-full px-8 sm:px-12 lg:px-20 pt-10 pb-6 items-center gap-6">
                    <div className="flex-1 flex flex-col min-h-0 min-w-0">
                        <h1
                            style={{ color: "var(--text-heading-color,#111827)" }}
                            className={`${SLIDE_TITLE} mb-4`}
                        >
                            {slideData?.title || 'Solutions'}
                        </h1>

                        <div className={`grid ${bulletGridCols} gap-4 flex-1 min-h-0 content-center`}>
                            {bulletPoints.map((bullet, index) => (
                                <div key={index} className="flex items-start gap-3">
                                    <div
                                        style={{ background: "var(--primary-accent-color,#9333ea)" }}
                                        className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                                    >
                                        <RemoteSvgIcon
                                            url={bullet.icon.__icon_url__}
                                            strokeColor={"currentColor"}
                                            className="w-5 h-5"
                                            color="var(--text-heading-color,#ffffff)"
                                            title={bullet.icon.__icon_query__}
                                        />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3
                                            style={{ color: "var(--text-heading-color,#111827)" }}
                                            className={SLIDE_SUBTITLE}
                                        >
                                            {bullet.title}
                                        </h3>
                                        {bullet.subtitle && (
                                            <p
                                                style={{ color: "var(--text-body-color,#4b5563)" }}
                                                className="text-sm lg:text-base leading-relaxed line-clamp-2 mt-1"
                                            >
                                                {bullet.subtitle}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex-shrink-0 w-80 flex items-center justify-center relative">
                        <div
                            style={{ color: "var(--primary-accent-color,#9333ea)" }}
                            className="absolute top-4 right-4 opacity-60 pointer-events-none"
                        >
                            <svg width="24" height="24" viewBox="0 0 32 32" fill="currentColor">
                                <path d="M16 0l4.12 8.38L28 12l-7.88 3.62L16 24l-4.12-8.38L4 12l7.88-3.62L16 0z" />
                            </svg>
                        </div>
                        <div className="w-full max-h-[300px] rounded-2xl overflow-hidden shadow-lg">
                            <img
                                src={slideData?.image?.__image_url__ || ''}
                                alt={slideData?.image?.__image_prompt__ || slideData?.title || ''}
                                className={SLIDE_IMAGE_SIDE}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default BulletIconsOnlySlideLayout
