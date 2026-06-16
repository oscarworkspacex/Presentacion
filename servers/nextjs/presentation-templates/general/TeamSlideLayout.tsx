import React from 'react'
import * as z from "zod";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_BODY,
    SLIDE_ACCENT_LINE,
    getTeamGridCols,
    getTeamPhotoSize,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'team-slide'
export const layoutName = 'Team Slide'
export const layoutDescription = 'A slide layout showcasing team members with photos, names, positions, and descriptions alongside company information.'

const teamMemberSchema = z.object({
    name: z.string().min(2).max(50).meta({
        description: "Team member's full name"
    }),
    position: z.string().min(2).max(50).meta({
        description: "Job title or position"
    }),
    description: z.string().max(180).meta({
        description: "Brief description of the team member (around 100 characters)"
    }),
    image: ImageSchema
});

const teamSlideSchema = z.object({
    title: z.string().min(3).max(40).default('Our Team Members').meta({
        description: "Main title of the slide",
    }),
    companyDescription: z.string().min(10).max(180).default('Ginyard International Co. is a leading provider of innovative digital solutions tailored for businesses. Our mission is to empower organizations to achieve their goals through cutting-edge technology and strategic partnerships.').meta({
        description: "Company description or team introduction text",
    }),
    teamMembers: z.array(teamMemberSchema).min(1).max(4).default([
        {
            name: 'Juliana Silva',
            position: 'CEO',
            description: 'Strategic leader with 15+ years experience in digital transformation and business growth.',
            image: {
                __image_url__: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
                __image_prompt__: 'Professional businesswoman CEO headshot'
            }
        },
        {
            name: 'Daniel Gallego',
            position: 'CTO',
            description: 'Technology expert specializing in scalable solutions and innovative software architecture.',
            image: {
                __image_url__: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
                __image_prompt__: 'Professional businessman CTO headshot'
            }
        },
        {
            name: 'Ketut Susilo',
            position: 'COO',
            description: 'Operations leader focused on efficiency, process optimization, and team development.',
            image: {
                __image_url__: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
                __image_prompt__: 'Professional businessman COO headshot'
            }
        },
        {
            name: 'Anna Robertson',
            position: 'CMO',
            description: 'Marketing strategist with expertise in brand development and customer engagement.',
            image: {
                __image_url__: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
                __image_prompt__: 'Professional businesswoman CMO headshot'
            }
        }
    ]).meta({
        description: "List of team members with their information",
    })
})

export const Schema = teamSlideSchema

export type TeamSlideData = z.infer<typeof teamSlideSchema>

interface TeamSlideLayoutProps {
    data?: Partial<TeamSlideData>
}

const TeamSlideLayout: React.FC<TeamSlideLayoutProps> = ({ data: slideData }) => {
    const teamMembers = (slideData?.teamMembers || []).slice(0, 4)
    const photoSize = getTeamPhotoSize(teamMembers.length)
    const gridCols = getTeamGridCols(teamMembers.length)

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

                <div className="absolute bottom-0 left-0 w-80 h-40 opacity-10 overflow-hidden pointer-events-none">
                    <svg className="w-full h-full" viewBox="0 0 300 150" fill="none">
                        <path d="M0 75C75 50 150 100 225 75C262.5 62.5 300 75 300 75V150H0V75Z" fill="#8b5cf6" opacity="0.3" />
                        <path d="M0 100C100 125 200 75 300 100V125C225 112.5 150 125 75 112.5L0 100Z" fill="#8b5cf6" opacity="0.2" />
                    </svg>
                </div>

                <div className="relative z-10 flex h-full px-8 sm:px-12 lg:px-20 pt-10 pb-6 items-center gap-8">
                    <div className="flex-1 flex flex-col justify-center min-w-0 space-y-4">
                        <h1
                            style={{ color: "var(--text-heading-color,#111827)" }}
                            className={SLIDE_TITLE}
                        >
                            {slideData?.title || 'Our Team Members'}
                        </h1>
                        <div
                            style={{ background: "var(--primary-accent-color,#9333ea)" }}
                            className={SLIDE_ACCENT_LINE}
                        />
                        <p
                            style={{ color: "var(--text-body-color,#4b5563)" }}
                            className={SLIDE_BODY}
                        >
                            {slideData?.companyDescription || 'Ginyard International Co. is a leading provider of innovative digital solutions tailored for businesses. Our mission is to empower organizations to achieve their goals through cutting-edge technology and strategic partnerships.'}
                        </p>
                    </div>

                    <div className={`flex-1 flex items-center justify-center ${teamMembers.length === 1 ? 'max-w-sm mx-auto' : ''}`}>
                        <div className={`grid ${gridCols} gap-4 w-full max-w-2xl`}>
                            {teamMembers.map((member, index) => (
                                <div key={index} className="text-center space-y-2">
                                    <div
                                        className={`${photoSize} mx-auto rounded-lg overflow-hidden shadow-md`}
                                        style={{ background: "var(--tertiary-accent-color,#e5e7eb)" }}
                                    >
                                        <img
                                            src={member.image.__image_url__ || ''}
                                            alt={member.image.__image_prompt__ || member.name}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                    <div>
                                        <h3
                                            style={{ color: "var(--text-heading-color,#111827)" }}
                                            className="text-base font-semibold line-clamp-1"
                                        >
                                            {member.name}
                                        </h3>
                                        <p
                                            style={{ color: "var(--text-body-color,#4b5563)" }}
                                            className="text-sm font-medium italic mb-1 line-clamp-1"
                                        >
                                            {member.position}
                                        </p>
                                        <p
                                            style={{ color: "var(--text-body-color,#4b5563)" }}
                                            className="text-sm leading-relaxed line-clamp-3 px-1"
                                        >
                                            {member.description}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default TeamSlideLayout
