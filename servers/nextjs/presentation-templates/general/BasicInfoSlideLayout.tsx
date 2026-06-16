import React from 'react'
import * as z from "zod";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';
import {
    SLIDE_CONTAINER,
    SLIDE_TITLE,
    SLIDE_BODY,
    SLIDE_ACCENT_LINE,
    SLIDE_IMAGE_SIDE,
} from '@/presentation-templates/slideLayoutUtils';

export const layoutId = 'basic-info-slide'
export const layoutName = 'Basic Info'
export const layoutDescription = 'A clean slide layout with title, description text, and a supporting image.'

const basicInfoSlideSchema = z.object({
    title: z.string().min(3).max(40).default('Product Overview').meta({
        description: "Main title of the slide",
    }),
    description: z.string().min(10).max(200).default('Our product offers customizable dashboards for real-time reporting and data-driven decisions. It integrates with third-party tools to enhance operations and scales with business growth for improved efficiency.').meta({
        description: "Main description text content",
    }),
    image: ImageSchema.default({
        __image_url__: 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80',
        __image_prompt__: 'Business team in meeting room discussing product features and solutions'
    }).meta({
        description: "Supporting image for the slide",
    })
})

export const Schema = basicInfoSlideSchema

export type BasicInfoSlideData = z.infer<typeof basicInfoSlideSchema>

interface BasicInfoSlideLayoutProps {
    data?: Partial<BasicInfoSlideData>
}

const BasicInfoSlideLayout: React.FC<BasicInfoSlideLayoutProps> = ({ data: slideData }) => {


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


                {/* Main Content */}
                <div className="relative z-10 flex h-full px-8 sm:px-12 lg:px-20 pt-10 pb-6 items-center gap-8">
                    <div className="flex-1 flex items-center justify-center">
                        <div className="w-full max-w-lg rounded-2xl overflow-hidden shadow-lg">
                            <img
                                src={slideData?.image?.__image_url__ || ''}
                                alt={slideData?.image?.__image_prompt__ || slideData?.title || ''}
                                className={SLIDE_IMAGE_SIDE}
                            />
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col justify-center min-w-0 space-y-4">
                        <h1 style={{ color: "var(--text-heading-color,#111827)" }} className={SLIDE_TITLE}>
                            {slideData?.title || 'Product Overview'}
                        </h1>
                        <div style={{background:"var(--primary-accent-color,#9333ea)"}} className={SLIDE_ACCENT_LINE}></div>
                        <p style={{color:"var(--text-body-color,#4b5563)"}} className={SLIDE_BODY}>
                            {slideData?.description || 'Our product offers customizable dashboards for real-time reporting and data-driven decisions. It integrates with third-party tools to enhance operations and scales with business growth for improved efficiency.'}
                        </p>


                    </div>
                   
              
  
                </div>
               
            </div>
        </>
    )
}

export default BasicInfoSlideLayout 