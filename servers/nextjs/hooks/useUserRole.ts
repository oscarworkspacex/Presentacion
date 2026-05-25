"use client";

import { useState, useEffect } from "react";

export interface UserInfo {
  username: string;
  role: "admin" | "user";
  authenticated: boolean;
}

export function useUserRole() {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const response = await fetch("/api/v1/auth/me", {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setUserInfo({
            username: data.username,
            role: data.role || "user",
            authenticated: true,
          });
          
          // Guardar en localStorage
          localStorage.setItem("user_role", data.role || "user");
          localStorage.setItem("username", data.username);
        } else {
          setUserInfo(null);
          localStorage.removeItem("user_role");
          localStorage.removeItem("username");
        }
      } catch (error) {
        console.error("Error fetching user info:", error);
        setUserInfo(null);
      } finally {
        setLoading(false);
      }
    };

    // Intentar cargar desde localStorage primero
    const storedRole = localStorage.getItem("user_role");
    const storedUsername = localStorage.getItem("username");

    if (storedRole && storedUsername) {
      setUserInfo({
        username: storedUsername,
        role: storedRole as "admin" | "user",
        authenticated: true,
      });
      setLoading(false);
    }

    // Luego verificar con el servidor
    fetchUserInfo();
  }, []);

  const isAdmin = userInfo?.role === "admin";
  const isUser = userInfo?.role === "user";

  return {
    userInfo,
    isAdmin,
    isUser,
    loading,
  };
}
