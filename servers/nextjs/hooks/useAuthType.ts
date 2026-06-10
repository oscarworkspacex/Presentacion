"use client";

import { useState, useEffect } from "react";

export interface AuthTypeInfo {
  authType: "jwt" | "api_key" | null;
  isApiUser: boolean;
  apiKeyName?: string;
}

export function useAuthType(): AuthTypeInfo {
  const [authInfo, setAuthInfo] = useState<AuthTypeInfo>({
    authType: null,
    isApiUser: false,
  });

  useEffect(() => {
    // Verificar el tipo de autenticación
    const authType = sessionStorage.getItem("auth_type");
    const apiKeyName = sessionStorage.getItem("api_key_name");

    if (authType === "api_key") {
      setAuthInfo({
        authType: "api_key",
        isApiUser: true,
        apiKeyName: apiKeyName || undefined,
      });
    } else {
      setAuthInfo({
        authType: "jwt",
        isApiUser: false,
      });
    }
  }, []);

  return authInfo;
}
