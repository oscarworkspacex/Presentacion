'use client'
import { useEffect, useRef, useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { PresentationGenerationApi } from '../../services/api/presentation-generation';
import { addToHistory } from '@/store/slices/undoRedoSlice';

interface UseAutoSaveOptions {
    debounceMs?: number;
    enabled?: boolean;
}

const pendingSaveTimeoutRef: { current: ReturnType<typeof setTimeout> | null } = {
    current: null,
};
let skipAutoSaveFlag = false;

export function cancelPendingAutoSave() {
    if (pendingSaveTimeoutRef.current) {
        clearTimeout(pendingSaveTimeoutRef.current);
        pendingSaveTimeoutRef.current = null;
    }
}

export function setSkipAutoSave(skip: boolean) {
    skipAutoSaveFlag = skip;
}

export const useAutoSave = ({
    debounceMs = 1000,
    enabled = true,
}: UseAutoSaveOptions = {}) => {
   
    const dispatch = useDispatch();
    const { presentationData, isStreaming, isLoading, isLayoutLoading } = useSelector(
        (state: RootState) => state.presentationGeneration
    );

    const lastSavedDataRef = useRef<string>('');
    const [isSaving, setIsSaving] = useState<boolean>(false);
 

    const debouncedSave = useCallback(async (data: unknown) => {
        cancelPendingAutoSave();

        pendingSaveTimeoutRef.current = setTimeout(async () => {
            if (!data || isSaving || skipAutoSaveFlag) return;

            const currentDataString = JSON.stringify(data);

            if (currentDataString === lastSavedDataRef.current) {
                return;
            }

            try {
                setIsSaving(true);
                console.log('🔄 Auto-saving presentation data...');

                await PresentationGenerationApi.updatePresentationContent(data);

                lastSavedDataRef.current = currentDataString;

                console.log('✅ Auto-save successful');

            } catch (error) {
                console.error('❌ Auto-save failed:', error);

            } finally {
                setIsSaving(false);
            }
        }, debounceMs);
    }, [debounceMs, isSaving]);

    useEffect(() => {
        if (!enabled || !presentationData || isStreaming || isLoading || isLayoutLoading || skipAutoSaveFlag) return;
        
        dispatch(addToHistory({
            slides: presentationData.slides,
            actionType: "AUTO_SAVE"
        }));
        debouncedSave(presentationData);
       
        return () => {
            cancelPendingAutoSave();
        };
    }, [presentationData, enabled, debouncedSave, isLoading, isStreaming, isLayoutLoading, dispatch]);
    
    return {
        isSaving,
        cancelPendingAutoSave,
    };
};
