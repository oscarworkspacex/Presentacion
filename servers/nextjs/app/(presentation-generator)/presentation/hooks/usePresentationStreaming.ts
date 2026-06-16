import { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import {
  clearPresentationData,
  setPresentationData,
  setStreaming,
} from "@/store/slices/presentationGeneration";
import { jsonrepair } from "jsonrepair";
import { toast } from "sonner";
import { MixpanelEvent, trackEvent } from "@/utils/mixpanel";

const hasPlaceholderImages = (slides: any[] | undefined): boolean => {
  if (!slides?.length) return false;

  const checkValue = (value: unknown): boolean => {
    if (typeof value === "string") {
      return value.includes("placeholder.jpg");
    }
    if (value && typeof value === "object") {
      return Object.values(value as Record<string, unknown>).some(checkValue);
    }
    return false;
  };

  return slides.some((slide) => checkValue(slide?.content));
};

const countPlaceholderImages = (slides: any[] | undefined): number => {
  if (!slides?.length) return 0;

  let count = 0;
  const checkValue = (value: unknown): void => {
    if (typeof value === "string" && value.includes("placeholder.jpg")) {
      count += 1;
      return;
    }
    if (value && typeof value === "object") {
      Object.values(value as Record<string, unknown>).forEach(checkValue);
    }
  };

  slides.forEach((slide) => checkValue(slide?.content));
  return count;
};

const countTotalImages = (slides: any[] | undefined): number => {
  if (!slides?.length) return 0;

  let count = 0;
  const checkValue = (value: unknown, key?: string): void => {
    if (key === "__image_prompt__" && typeof value === "string" && value.length > 0) {
      count += 1;
      return;
    }
    if (value && typeof value === "object") {
      Object.entries(value as Record<string, unknown>).forEach(([k, v]) =>
        checkValue(v, k)
      );
    }
  };

  slides.forEach((slide) => checkValue(slide?.content));
  return count;
};

export const usePresentationStreaming = (
  presentationId: string,
  stream: string | null,
  setLoading: (loading: boolean) => void,
  setError: (error: boolean) => void,
  fetchUserSlides: () => void
) => {
  const dispatch = useDispatch();
  const previousSlidesLength = useRef(0);
  const lastStreamDetail = useRef<string | null>(null);

  useEffect(() => {
    let eventSource: EventSource;
    let accumulatedChunks = "";

    const initializeStream = async () => {
      dispatch(setStreaming(true));
      dispatch(clearPresentationData());

      trackEvent(MixpanelEvent.Presentation_Stream_API_Call);

      eventSource = new EventSource(
        `/api/v1/ppt/presentation/stream/${presentationId}`
      );

      eventSource.addEventListener("response", (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "chunk":
            accumulatedChunks += data.chunk;
            try {
              const repairedJson = jsonrepair(accumulatedChunks);
              const partialData = JSON.parse(repairedJson);

              if (partialData.slides) {
                if (
                  partialData.slides.length !== previousSlidesLength.current &&
                  partialData.slides.length > 0
                ) {
                  dispatch(
                    setPresentationData({
                      ...partialData,
                      slides: partialData.slides,
                    })
                  );
                  previousSlidesLength.current = partialData.slides.length;
                  setLoading(false);
                }
              }
            } catch (error) {
              // JSON isn't complete yet, continue accumulating
            }
            break;

          case "complete":
            try {
              dispatch(setPresentationData(data.presentation));
              dispatch(setStreaming(false));
              setLoading(false);
              eventSource.close();

              if (hasPlaceholderImages(data.presentation?.slides)) {
                const stats = data.image_generation_stats;
                const failed =
                  stats?.failed ?? countPlaceholderImages(data.presentation?.slides);
                const total =
                  stats?.total ?? (countTotalImages(data.presentation?.slides) || failed);
                toast.warning("Algunas imágenes no se generaron", {
                  description:
                    lastStreamDetail.current ||
                    `${failed} de ${total} imágenes no se generaron. Se reintentó automáticamente; revisa OPENAI_API_KEY y Settings si persiste.`,
                });
              }

              // Remove stream parameter from URL
              const newUrl = new URL(window.location.href);
              newUrl.searchParams.delete("stream");
              window.history.replaceState({}, "", newUrl.toString());
            } catch (error) {
              eventSource.close();
              console.error("Error parsing accumulated chunks:", error);
            }
            accumulatedChunks = "";
            break;

          case "closing":
            dispatch(setPresentationData(data.presentation));
            setLoading(false);
            dispatch(setStreaming(false));
            eventSource.close();

            // Remove stream parameter from URL
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete("stream");
            window.history.replaceState({}, "", newUrl.toString());
            break;
          case "error":
            eventSource.close();
            lastStreamDetail.current =
              data.detail ||
              "Failed to connect to the server. Please try again.";
            toast.error("Error al generar la presentación", {
              description: lastStreamDetail.current,
            });
            setLoading(false);
            dispatch(setStreaming(false));
            setError(true);
            break;
        }
      });

      eventSource.onerror = (error) => {
        console.error("EventSource failed:", error);
        setLoading(false);
        dispatch(setStreaming(false));
        setError(true);
        eventSource.close();
      };
    };

    if (stream) {
      initializeStream();
    } else {
      fetchUserSlides();
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [presentationId, stream, dispatch, setLoading, setError, fetchUserSlides]);
};
