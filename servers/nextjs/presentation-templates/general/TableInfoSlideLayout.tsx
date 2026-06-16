import React from 'react'
import * as z from "zod";
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_BODY,
    SLIDE_ACCENT_LINE,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'table-info-slide'
export const layoutName = 'Table with Info'
export const layoutDescription = 'A slide layout with a title at the top, structured table in the middle, and descriptive text at the bottom.'

const tableInfoSlideSchema = z.object({
    title: z.string().min(3).max(40).default('Market Comparison').meta({
        description: "Main title of the slide",
    }),
    tableData: z.object({
        headers: z.array(z.string().min(1).max(30)).min(2).max(5).meta({
            description: "Table column headers"
        }),
        rows: z.array(z.array(z.string().min(1).max(50))).min(2).max(6).meta({
            description: "Table rows data - each row should match the number of headers"
        })
    }).default({
        headers: ['Company', 'Revenue', 'Growth', 'Market Share'],
        rows: [
            ['Company A', '$2.5M', '15%', '25%'],
            ['Company B', '$1.8M', '12%', '18%'],
            ['Company C', '$3.2M', '20%', '32%'],
            ['Our Company', '$1.2M', '35%', '12%']
        ]
    }).meta({
        description: "Table structure with headers and rows"
    }),
    description: z.string().min(10).max(180).default('This comparison shows our competitive position in the market. While we currently have a smaller market share, our growth rate significantly exceeds competitors, indicating strong potential for future expansion.').meta({
        description: "Descriptive text that appears below the table",
    })
})

export const Schema = tableInfoSlideSchema

export type TableInfoSlideData = z.infer<typeof tableInfoSlideSchema>

interface TableInfoSlideLayoutProps {
    data?: Partial<TableInfoSlideData>
}

const TableInfoSlideLayout: React.FC<TableInfoSlideLayoutProps> = ({ data: slideData }) => {
    const tableHeaders = slideData?.tableData?.headers || ['Company', 'Revenue', 'Growth', 'Market Share']
    const tableRows = slideData?.tableData?.rows || [
        ['Company A', '$2.5M', '15%', '25%'],
        ['Company B', '$1.8M', '12%', '18%'],
        ['Company C', '$3.2M', '20%', '32%'],
        ['Our Company', '$1.2M', '35%', '12%']
    ]

    return (
        <>
            {/* Import Google Fonts */}
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
                    <div className="absolute top-0 left-0 right-0 px-8 sm:px-12 lg:px-20 pt-4">
                        <div className="flex items-center gap-4">
                            <span className="text-sm sm:text-base font-semibold" style={{ color: 'var(--text-heading-color, #111827)' }}>
                                {(slideData as any)?.__companyName__ || 'Company Name'}
                            </span>
                            <div className="h-[2px] flex-1 opacity-70" style={{ backgroundColor: 'var(--text-heading-color, #111827)' }}></div>
                        </div>
                    </div>
                )}
                {/* Decorative Wave Patterns */}
                <div className="absolute top-0 left-0 w-64 h-full opacity-10 overflow-hidden">
                    <svg className="w-full h-full" viewBox="0 0 200 400" fill="none">
                        <path d="M0 100C50 150 100 50 150 100C175 125 200 100 200 100V0H0V100Z" fill="#8b5cf6" opacity="0.3" />
                        <path d="M0 200C75 250 125 150 200 200V150C150 175 100 150 50 175L0 200Z" fill="#8b5cf6" opacity="0.2" />
                        <path d="M0 300C100 350 150 250 200 300V250C125 275 75 250 25 275L0 300Z" fill="#8b5cf6" opacity="0.1" />
                    </svg>
                </div>

                <div className="absolute top-0 right-0 w-64 h-full opacity-10 overflow-hidden transform scale-x-[-1]">
                    <svg className="w-full h-full" viewBox="0 0 200 400" fill="none">
                        <path d="M0 100C50 150 100 50 150 100C175 125 200 100 200 100V0H0V100Z" fill="#8b5cf6" opacity="0.3" />
                        <path d="M0 200C75 250 125 150 200 200V150C150 175 100 150 50 175L0 200Z" fill="#8b5cf6" opacity="0.2" />
                        <path d="M0 300C100 350 150 250 200 300V250C125 275 75 250 25 275L0 300Z" fill="#8b5cf6" opacity="0.1" />
                    </svg>
                </div>

                {/* Main Content */}
                <div className="relative z-10 px-8 sm:px-12 lg:px-20 pt-10 pb-6 flex-1 flex flex-col justify-between min-h-0">
                    <div className="text-center space-y-2">
                        <h1 style={{ color: "var(--text-heading-color,#111827)" }} className={SLIDE_TITLE}>
                            {slideData?.title || 'Market Comparison'}
                        </h1>
                        <div style={{background:"var(--primary-accent-color,#9333ea)"}} className={`${SLIDE_ACCENT_LINE} mx-auto`}></div>
                    </div>

                    <div className="flex-1 flex items-center justify-center py-4 min-h-0">
                        <div className="w-full max-w-4xl">
                            <div style={{ background: "var(--tertiary-accent-color,#e5e7eb)", borderColor: "var(--secondary-accent-color,#e5e7eb)" }} className="bg-white rounded-lg shadow-lg border overflow-hidden">
                                <div style={{ backgroundColor: "var(--primary-accent-color,#9333ea)" }}>
                                    <div className="grid gap-px" style={{ gridTemplateColumns: `repeat(${tableHeaders.length}, 1fr)` }}>
                                        {tableHeaders.map((header, index) => (
                                            <div key={index} className="px-4 py-3 font-semibold text-center text-xs sm:text-sm" style={{color:"var(--text-heading-color,#111827)"}}>
                                                {header}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="divide-y divide-gray-200">
                                    {tableRows.map((row, rowIndex) => (
                                        <div 
                                            key={rowIndex} 
                                            className={`grid gap-px ${rowIndex % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}
                                            style={{ gridTemplateColumns: `repeat(${tableHeaders.length}, 1fr)` }}
                                        >
                                            {row.slice(0, tableHeaders.length).map((cell, cellIndex) => (
                                                <div
                                                    key={cellIndex}
                                                    className="px-4 py-3 text-center text-xs sm:text-sm line-clamp-2"
                                                    style={{
                                                        color: "var(--text-body-color,#4b5563)",
                                                        background: cellIndex % 2 === 0
                                                            ? "var(--secondary-accent-color,#e5e7eb)"
                                                            : "var(--tertiary-accent-color,#f3f4f6)",
                                                    }}
                                                >
                                                    {cell}
                                                </div>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="text-center">
                        <p style={{color:"var(--text-body-color,#4b5563)"}} className={`${SLIDE_BODY} line-clamp-3 max-w-4xl mx-auto`}>
                            {slideData?.description || 'This comparison shows our competitive position in the market. While we currently have a smaller market share, our growth rate significantly exceeds competitors, indicating strong potential for future expansion.'}
                        </p>
                    </div>
                </div>
            </div>
        </>
    )
}

export default TableInfoSlideLayout 