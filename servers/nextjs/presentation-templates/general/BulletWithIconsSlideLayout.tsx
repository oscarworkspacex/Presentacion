import React from 'react'
import * as z from "zod";
import { ImageSchema, IconSchema } from '@/presentation-templates/defaultSchemes';
import { RemoteSvgIcon } from '@/app/hooks/useRemoteSvgIcon';
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_BODY,
    SLIDE_SUBTITLE,
    SLIDE_ACCENT_LINE,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'bullet-with-icons-slide'
export const layoutName = 'Bullet with Icons'
export const layoutDescription = 'A bullets style slide with main content, supporting image, and bullet points with icons and descriptions.'

const bulletWithIconsSlideSchema = z.object({
    title: z.string().min(3).max(40).default('Problem').meta({
        description: "Main title of the slide",
    }),
    description: z.string().max(180).default('Businesses face challenges with outdated technology and rising costs, limiting efficiency and growth in competitive markets.').meta({
        description: "Main description text explaining the problem or topic",
    }),
    image: ImageSchema.default({
        __image_url__: 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80',
        __image_prompt__: 'Business people analyzing documents and charts in office'
    }).meta({
        description: "Supporting image for the slide",
    }),
    bulletPoints: z.array(z.object({
        title: z.string().min(2).max(60).meta({
            description: "Bullet point title",
        }),
        description: z.string().min(10).max(130).meta({
            description: "Bullet point description",
        }),
        icon: IconSchema,
    })).min(1).max(4).default([
        {
            title: 'Inefficiency',
            description: 'Businesses struggle to find digital tools that meet their needs, causing operational slowdowns.',
            icon: {
                __icon_url__: 'https://presenton-public.s3.ap-southeast-1.amazonaws.com/static/icons/bold/checks-bold.svg',
                __icon_query__: 'warning alert inefficiency'
            }
        },
        {
            title: 'High Costs',
            description: 'Outdated systems increase expenses, while small businesses struggle to expand their market reach.',
            icon: {
                __icon_url__: 'https://presenton-public.s3.ap-southeast-1.amazonaws.com/static/icons/bold/fediverse-logo-bold.svg',
                __icon_query__: 'trending up costs chart'
            }
        }
    ]).meta({
        description: "List of bullet points with icons and descriptions",
    })
})

export const Schema = bulletWithIconsSlideSchema

export type BulletWithIconsSlideData = z.infer<typeof bulletWithIconsSlideSchema>

interface BulletWithIconsSlideLayoutProps {
    data?: Partial<BulletWithIconsSlideData>
}

const BulletWithIconsSlideLayout: React.FC<BulletWithIconsSlideLayoutProps> = ({ data: slideData }) => {
    const bulletPoints = (slideData?.bulletPoints || []).slice(0, 3)

    return (
        <>
            <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
                rel="stylesheet"
            />

            <div
                className={`${SLIDE_CONTAINER} bg-gradient-to-br from-gray-50 to-white`}
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

                <div className="relative z-10 flex flex-col h-full px-8 sm:px-12 lg:px-20 pt-8 pb-6">
                    <div className="mb-5">
                        <h1
                            style={{ color: "var(--text-heading-color,#111827)" }}
                            className={SLIDE_TITLE}
                        >
                            {slideData?.title || 'Problem'}
                        </h1>
                        <div
                            style={{ background: "var(--primary-accent-color,#9333ea)" }}
                            className={`${SLIDE_ACCENT_LINE} mt-3`}
                        />
                    </div>

                    <div className="flex-1 min-h-0 grid grid-cols-2 gap-8">
                        <div className="relative min-h-0 flex items-center justify-center">
                            <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                                <svg className="w-full h-full opacity-30" viewBox="0 0 200 200">
                                    <defs>
                                        <pattern id="grid-bwi" width="20" height="20" patternUnits="userSpaceOnUse">
                                            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="var(--primary-accent-color,#9333ea)" strokeWidth="0.5" />
                                        </pattern>
                                    </defs>
                                    <rect width="100%" height="100%" fill="url(#grid-bwi)" />
                                </svg>
                            </div>
                            <div className="relative z-10 w-full h-full rounded-2xl overflow-hidden shadow-lg">
                                <img
                                    src={slideData?.image?.__image_url__ || ''}
                                    alt={slideData?.image?.__image_prompt__ || slideData?.title || ''}
                                    className="w-full h-full object-cover"
                                    style={{ background: "var(--tertiary-accent-color,#e5e7eb)" }}
                                />
                            </div>
                        </div>

                        <div className="flex flex-col justify-center min-h-0">
                            <p
                                style={{ color: "var(--text-body-color,#4b5563)" }}
                                className={`${SLIDE_BODY} mb-4`}
                            >
                                {slideData?.description || 'Businesses face challenges with outdated technology and rising costs, limiting efficiency and growth in competitive markets.'}
                            </p>

                            <div className="space-y-3">
                                {bulletPoints.map((bullet, index) => (
                                    <div key={index} className="flex items-start gap-3">
                                        <div
                                            style={{ background: "var(--primary-accent-color,#9333ea)" }}
                                            className="flex-shrink-0 w-10 h-10 rounded-lg shadow-md flex items-center justify-center"
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
                                                className={`${SLIDE_SUBTITLE} mb-1`}
                                            >
                                                {bullet.title}
                                            </h3>
                                            <div
                                                style={{ background: "var(--primary-accent-color,#9333ea)" }}
                                                className="w-10 h-0.5 mb-2"
                                            />
                                            <p
                                                style={{ color: "var(--text-body-color,#4b5563)" }}
                                                className="text-sm leading-relaxed line-clamp-3 break-words"
                                            >
                                                {bullet.description}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default BulletWithIconsSlideLayout
