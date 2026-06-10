"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthType } from "@/hooks/useAuthType";

export function ApiKeyGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isApiUser } = useAuthType();

  useEffect(() => {
    // Si el usuario está autenticado con API key, redirigir al dashboard
    if (isApiUser) {
      router.push("/dashboard");
    }
  }, [isApiUser, router]);

  // Si es usuario API, no renderizar nada (ya que se redirige)
  if (isApiUser) {
    return null;
  }

  return <>{children}</>;
}
