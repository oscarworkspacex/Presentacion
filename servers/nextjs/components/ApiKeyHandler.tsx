"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export function ApiKeyHandler({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Verificar si hay un api_key en los query params
    const apiKey = searchParams?.get("api_key");

    if (apiKey && !isProcessing) {
      setIsProcessing(true);
      handleApiKey(apiKey);
    }
  }, [searchParams]);

  const handleApiKey = async (apiKey: string) => {
    try {
      // Verificar la API key contra el backend
      const response = await fetch(
        `/api/v1/auth/verify-api-key?api_key=${encodeURIComponent(apiKey)}`
      );

      if (!response.ok) {
        console.error("Error verifying API key");
        router.push("/login");
        return;
      }

      const data = await response.json();

      if (data.valid) {
        // API key válida - guardar en sessionStorage
        sessionStorage.setItem("api_key", apiKey);
        sessionStorage.setItem("api_key_name", data.name || "API User");
        sessionStorage.setItem("auth_type", "api_key");

        // Redirigir al dashboard (sin el parámetro api_key en la URL)
        router.push("/dashboard");
      } else {
        // API key inválida - redirigir a login
        console.error("Invalid API key:", data.reason);
        router.push("/login");
      }
    } catch (error) {
      console.error("Error handling API key:", error);
      router.push("/login");
    }
  };

  return <>{children}</>;
}
