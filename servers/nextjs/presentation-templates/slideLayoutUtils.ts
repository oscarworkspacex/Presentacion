export const SLIDE_CONTAINER =
    'w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video overflow-hidden flex flex-col relative z-20 mx-auto'

export const SLIDE_TITLE =
    'text-3xl lg:text-4xl font-bold leading-tight line-clamp-3 break-words'

export const SLIDE_BODY =
    'text-sm lg:text-base leading-relaxed line-clamp-[10] break-words'

export const SLIDE_SUBTITLE =
    'text-base lg:text-lg font-semibold line-clamp-3 break-words'

export const SLIDE_IMAGE_SIDE =
    'w-full h-full max-h-[420px] object-cover rounded-2xl shadow-lg'

export const SLIDE_IMAGE_COMPACT =
    'w-full h-full object-cover rounded-xl shadow-md'

export const SLIDE_ACCENT_LINE = 'w-20 h-1'

export function getBulletGridCols(count: number): string {
    if (count <= 1) return 'grid-cols-1'
    if (count === 2) return 'grid-cols-2'
    return 'grid-cols-1'
}

export function getTeamGridCols(count: number): string {
    if (count <= 1) return 'grid-cols-1'
    if (count === 2) return 'grid-cols-2'
    if (count <= 4) return 'grid-cols-2'
    return 'grid-cols-2 lg:grid-cols-3'
}

export function getTeamPhotoSize(count: number): string {
    if (count <= 1) return 'w-36 h-36'
    if (count <= 2) return 'w-32 h-32'
    return 'w-28 h-28'
}
