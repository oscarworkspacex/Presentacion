"use client";
import React, { useState } from "react";
import { X, Play } from "lucide-react";

interface VideoEmbedProps {
  url: string;
  onRemove?: () => void;
  isAdmin?: boolean;
}

function getEmbedUrl(url: string): { embedUrl: string; type: "youtube" | "tiktok" | null } {
  if (!url) return { embedUrl: "", type: null };

  // YouTube: watch?v=ID, youtu.be/ID, youtube.com/shorts/ID, youtube.com/embed/ID
  const ytPatterns = [
    /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/shorts\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
  ];
  for (const pattern of ytPatterns) {
    const match = url.match(pattern);
    if (match) {
      return {
        embedUrl: `https://www.youtube.com/embed/${match[1]}?autoplay=0&rel=0`,
        type: "youtube",
      };
    }
  }

  // TikTok: tiktok.com/@user/video/ID or vm.tiktok.com/CODE
  const ttMatch = url.match(/tiktok\.com\/@[^/]+\/video\/(\d+)/);
  if (ttMatch) {
    return {
      embedUrl: `https://www.tiktok.com/embed/v2/${ttMatch[1]}`,
      type: "tiktok",
    };
  }

  // vm.tiktok.com short links can't be embedded directly, show unsupported
  return { embedUrl: "", type: null };
}

const VideoEmbed: React.FC<VideoEmbedProps> = ({ url, onRemove, isAdmin }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const { embedUrl, type } = getEmbedUrl(url);

  if (!embedUrl) return null;

  const isTikTok = type === "tiktok";

  return (
    <div
      className={`absolute inset-0 z-30 flex items-center justify-center bg-black/60 backdrop-blur-[2px] transition-all duration-300 ${
        isMinimized ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      onClick={(e) => {
        if (e.target === e.currentTarget) setIsMinimized(true);
      }}
    >
      <div
        className={`relative bg-black rounded-xl shadow-2xl overflow-hidden flex flex-col ${
          isTikTok
            ? "w-[38%] max-w-[340px] aspect-[9/16]"
            : "w-[80%] max-w-[800px] aspect-video"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Controls bar */}
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-3 py-2 bg-gradient-to-b from-black/70 to-transparent">
          <span className="text-white text-xs font-medium opacity-80">
            {type === "youtube" ? "YouTube" : "TikTok"}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(true)}
              className="text-white/70 hover:text-white transition-colors p-1 rounded"
              title="Minimizar"
            >
              <span className="text-xs font-bold leading-none">—</span>
            </button>
            {isAdmin && onRemove && (
              <button
                onClick={onRemove}
                className="text-white/70 hover:text-red-400 transition-colors p-1 rounded"
                title="Eliminar video"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        <iframe
          src={embedUrl}
          className="w-full h-full border-0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          title="Video embebido"
        />
      </div>

      {/* Minimized badge */}
      {isMinimized && (
        <div
          onClick={() => setIsMinimized(false)}
          className="absolute bottom-4 right-4 bg-black/80 hover:bg-black text-white rounded-full px-3 py-1.5 flex items-center gap-1.5 cursor-pointer text-xs font-medium shadow-lg transition-all"
        >
          <Play className="w-3 h-3 fill-white" />
          Ver video
        </div>
      )}
    </div>
  );
};

export default VideoEmbed;
