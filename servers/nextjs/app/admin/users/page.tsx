"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUserRole } from "@/hooks/useUserRole";
import { Loader2, Plus, Pencil, Trash2, Shield, User, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import { ApiKeyGuard } from "@/components/ApiKeyGuard";

interface UserData {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export default function UsersAdminPage() {
  const router = useRouter();
  const { isAdmin, loading: authLoading } = useUserRole();
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "user",
    is_active: true,
  });

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.push("/dashboard");
    }
  }, [isAdmin, authLoading, router]);

  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
    }
  }, [isAdmin]);

  const fetchUsers = async () => {
    try {
      const response = await fetch("/api/v1/admin/users", {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        toast.error("Error al cargar usuarios");
      }
    } catch (error) {
      console.error("Error fetching users:", error);
      toast.error("Error al conectar con el servidor");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!formData.username || !formData.password) {
      toast.error("Usuario y contraseña son requeridos");
      return;
    }

    if (formData.password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }

    try {
      const response = await fetch("/api/v1/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Usuario creado exitosamente");
        setShowCreateModal(false);
        setFormData({ username: "", password: "", role: "user", is_active: true });
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Error al crear usuario");
      }
    } catch (error) {
      toast.error("Error al conectar con el servidor");
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;

    try {
      const updateData: any = {
        role: formData.role,
        is_active: formData.is_active,
      };

      if (formData.password) {
        if (formData.password.length < 6) {
          toast.error("La contraseña debe tener al menos 6 caracteres");
          return;
        }
        updateData.password = formData.password;
      }

      const response = await fetch(`/api/v1/admin/users/${editingUser.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        toast.success("Usuario actualizado exitosamente");
        setEditingUser(null);
        setFormData({ username: "", password: "", role: "user", is_active: true });
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Error al actualizar usuario");
      }
    } catch (error) {
      toast.error("Error al conectar con el servidor");
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!confirm(`¿Estás seguro de eliminar al usuario "${username}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok || response.status === 204) {
        toast.success("Usuario eliminado exitosamente");
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Error al eliminar usuario");
      }
    } catch (error) {
      toast.error("Error al conectar con el servidor");
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <ApiKeyGuard>
      <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Gestión de Usuarios</h1>
            <p className="text-gray-600">Administra los usuarios del sistema</p>
          </div>
          <button
            onClick={() => {
              setShowCreateModal(true);
              setFormData({ username: "", password: "", role: "user", is_active: true });
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Nuevo Usuario
          </button>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuario
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último acceso
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        {user.role === "admin" ? (
                          <Shield className="w-5 h-5 text-blue-600" />
                        ) : (
                          <User className="w-5 h-5 text-gray-600" />
                        )}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                        <div className="text-sm text-gray-500">ID: {user.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.role === "admin"
                          ? "bg-purple-100 text-purple-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {user.role === "admin" ? "Administrador" : "Usuario"}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {user.is_active ? (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                          <span className="text-sm text-gray-900">Activo</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-5 h-5 text-red-500 mr-2" />
                          <span className="text-sm text-gray-900">Inactivo</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleString()
                      : "Nunca"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => {
                        setEditingUser(user);
                        setFormData({
                          username: user.username,
                          password: "",
                          role: user.role,
                          is_active: user.is_active,
                        });
                      }}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      <Pencil className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id, user.username)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Create/Edit Modal */}
        {(showCreateModal || editingUser) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
              <h2 className="text-2xl font-bold mb-6">
                {editingUser ? "Editar Usuario" : "Nuevo Usuario"}
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Usuario
                  </label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    disabled={!!editingUser}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="nombre_usuario"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contraseña {editingUser && "(dejar vacío para no cambiar)"}
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="••••••"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rol
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="user">Usuario</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>

                {editingUser && (
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                      Usuario activo
                    </label>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingUser(null);
                    setFormData({ username: "", password: "", role: "user", is_active: true });
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={editingUser ? handleUpdateUser : handleCreateUser}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingUser ? "Actualizar" : "Crear"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    </ApiKeyGuard>
  );
}
