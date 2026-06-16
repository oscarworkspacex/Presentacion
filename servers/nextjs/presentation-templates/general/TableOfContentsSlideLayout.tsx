import React from 'react'
import * as z from "zod";
import { SLIDE_CONTAINER, SLIDE_TITLE } from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'table-of-contents-slide'
export const layoutName = 'Table of Contents'
export const layoutDescription = 'A professional table of contents layout with numbered sections, and page references. This should be right after introduction slide if ever used.'

const tableOfContentsSlideSchema = z.object({
    sections: z.array(z.object({
        number: z.number().min(1).meta({
            description: "Section number"
        }),
        title: z.string().min(1).max(50).meta({
            description: "Section title"
        }),
        pageNumber: z.string().min(1).max(10).meta({
            description: "Page number for this section"
        })
    })).min(1).max(10).default([
        { number: 1, title: "Problem", pageNumber: "03" },
        { number: 2, title: "Solution", pageNumber: "04" },
        { number: 3, title: "Product Overview", pageNumber: "05" },
        { number: 4, title: "Market Size", pageNumber: "06" },
        { number: 5, title: "Market Validation", pageNumber: "07" },
        { number: 6, title: "Company Traction", pageNumber: "08" },
        { number: 7, title: "Product Performance", pageNumber: "09" },
        { number: 8, title: "Business Model", pageNumber: "10" },
        { number: 9, title: "Competitive Advantage", pageNumber: "11" },
        { number: 10, title: "Team Member", pageNumber: "12" }
    ]).meta({
        description: "List of table of contents sections",
    })
})

export const Schema = tableOfContentsSlideSchema

export type TableOfContentsSlideData = z.infer<typeof tableOfContentsSlideSchema>

interface TableOfContentsSlideLayoutProps {
    data?: Partial<TableOfContentsSlideData>
}

const TableOfContentsSlideLayout: React.FC<TableOfContentsSlideLayoutProps> = ({ data: slideData }) => {
    const sections = (slideData?.sections || []).slice(0, 10)
    const midPoint = Math.ceil(sections.length / 2)
    const leftSections = sections.slice(0, midPoint)
    const rightSections = sections.slice(midPoint)

    const renderSection = (section: typeof sections[number]) => (
        <div key={section.number} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3 min-w-0">
                <div
                    style={{ background: "var(--primary-accent-color,#9333ea)", color: "var(--text-heading-color,#ffffff)" }}
                    className="w-9 h-9 flex-shrink-0 rounded-lg flex items-center justify-center font-bold text-sm"
                >
                    {section.number}
                </div>
                <span
                    style={{ color: "var(--text-heading-color,#111827)" }}
                    className="text-sm font-medium line-clamp-1"
                >
                    {section.title}
                </span>
            </div>
            <span
                style={{ color: "var(--text-body-color,#4b5563)" }}
                className="text-sm flex-shrink-0"
            >
                {section.pageNumber}
            </span>
        </div>
    )

    return (
        <>
            <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
                rel="stylesheet"
            />

            <div
                className={`${SLIDE_CONTAINER} bg-white px-8 sm:px-12 lg:px-20 py-6`}
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

                <div className="flex flex-col h-full pt-6 min-h-0">
                    <div className="text-center mb-6">
                        <h1 style={{ color: "var(--text-heading-color,#111827)" }} className={SLIDE_TITLE}>
                            Table of Contents
                        </h1>
                        <div className="flex justify-center mt-2">
                            <svg width="60" height="16" viewBox="0 0 80 20" style={{ color: "var(--primary-accent-color,#9333ea)" }}>
                                <path
                                    d="M0 10 Q20 0 40 10 T80 10"
                                    stroke="currentColor"
                                    strokeWidth="3"
                                    fill="none"
                                />
                            </svg>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-x-8 gap-y-3 flex-1 min-h-0 content-start overflow-hidden">
                        <div className="space-y-3">
                            {leftSections.map(renderSection)}
                        </div>
                        <div className="space-y-3">
                            {rightSections.map(renderSection)}
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default TableOfContentsSlideLayout
