# Sistema de Roles y Permisos

## Resumen

Se ha implementado un sistema completo de autenticación basado en roles con dos niveles de acceso:

- **Admin**: Acceso completo para crear presentaciones, editar contenido, gestionar usuarios
- **Usuario**: Acceso de solo lectura para ver presentaciones

## Cambios Realizados

### Backend (FastAPI)

1. **Modelo de Usuario** (`models/sql/user.py`)
   - Agregado campo `role` (admin/user) con enum `UserRole`
   - Campo por defecto: `user`

2. **Sistema de Autenticación** (`core/auth.py`)
   - Actualizado `create_access_token` para incluir `role` en el JWT
   - Actualizado `verify_token` para retornar `role`
   - Mejorado `hash_password` para manejar límite de 72 bytes de bcrypt

3. **Endpoints de Login** (`api/v1/auth/endpoints.py`)
   - Login ahora verifica contra la base de datos (tabla `users`)
   - Retorna `role` en la respuesta del token
   - Endpoint `/api/v1/auth/me` retorna información del usuario actual (username, role)

4. **Endpoints CRUD de Usuarios** (`api/v1/admin/endpoints/users.py`)
   - `GET /api/v1/admin/users` - Listar todos los usuarios
   - `POST /api/v1/admin/users` - Crear nuevo usuario
   - `PUT /api/v1/admin/users/{id}` - Actualizar usuario (password opcional)
   - `DELETE /api/v1/admin/users/{id}` - Eliminar usuario (no permite eliminar el último admin)

5. **Middlewares de Seguridad** (`api/middlewares.py`)
   - `AuthenticationMiddleware` - Verifica JWT y agrega `user_info` (username, role) al `request.state`
   - `RoleRequiredMiddleware` - Protege rutas de admin y operaciones de escritura:
     - `/api/v1/admin/*` - Solo admin
     - `POST/PUT/PATCH/DELETE` en `/api/v1/ppt/*` - Solo admin

6. **Base de Datos** (`services/database.py`)
   - Agregada tabla `users` a la creación automática de tablas

### Frontend (Next.js)

1. **Hook de Roles** (`hooks/useUserRole.ts`)
   - Hook para obtener información del usuario actual
   - Retorna: `userInfo`, `isAdmin`, `isUser`, `loading`
   - Se sincroniza con localStorage y con el servidor

2. **Página de Login** (`app/login/page.tsx`)
   - Actualizada para guardar `role` en localStorage
   - Redirecciona al dashboard después del login

3. **Página de Administración de Usuarios** (`app/admin/users/page.tsx`)
   - Interfaz completa para gestionar usuarios (CRUD)
   - Solo visible para administradores
   - Permite crear, editar, desactivar y eliminar usuarios
   - Muestra información de último acceso y estado activo/inactivo

4. **Proxies de Next.js** (`app/api/v1/admin/*`)
   - `/api/v1/admin/users/route.ts` - Proxy para GET y POST
   - `/api/v1/admin/users/[id]/route.ts` - Proxy para PUT y DELETE

5. **Componentes de Presentación**
   - `SlideContent.tsx` - Deshabilita botones de edición (agregar, eliminar, editar slides) para usuarios no admin
   - `HeaderNav.tsx` - Muestra enlace "Usuarios" solo para admins

## Credenciales del Usuario Admin

El primer usuario administrador ha sido creado con las siguientes credenciales:

```
Usuario: zucaritas
Contraseña: g3st24mWork5
Rol: admin
```

## Uso

### Como Administrador

1. Inicia sesión con `zucaritas` / `g3st24mWork5`
2. Acceso completo:
   - Crear y editar presentaciones
   - Agregar, editar y eliminar slides
   - Acceder a la página "Usuarios" en el menú
   - Gestionar todos los usuarios del sistema

### Como Usuario Normal

1. El administrador debe crear una cuenta de usuario en `/admin/users`
2. El usuario podrá:
   - Ver presentaciones (modo lectura)
   - Ver slides (sin botones de edición)
   - Usar el modo de presentación
3. El usuario NO podrá:
   - Crear o editar presentaciones
   - Agregar o eliminar slides
   - Modificar contenido
   - Acceder a la página de gestión de usuarios

## Rutas Protegidas

### Backend
- `/api/v1/admin/*` - Solo admin
- `POST/PUT/PATCH/DELETE` en `/api/v1/ppt/*` - Solo admin
- `GET` en `/api/v1/ppt/*` - Cualquier usuario autenticado

### Frontend
- `/admin/users` - Solo admin (redirecciona a dashboard si no es admin)
- Botones de edición de slides - Solo visibles para admin

## Seguridad

- Contraseñas hasheadas con bcrypt
- JWT con expiración de 24 horas (configurable en `JWT_EXPIRE_MINUTES`)
- Secret key para JWT en `.env` (`JWT_SECRET_KEY`)
- Verificación de roles en cada petición protegida
- No se puede eliminar el último usuario admin del sistema
- Usuarios pueden ser desactivados sin eliminarlos

## Base de Datos

Tabla `users`:
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT NOW(),
    last_login DATETIME NULL
);
```

## Migración de Usuarios Existentes

Si ya tienes usuarios autenticándose con el sistema anterior (HTTP Basic Auth del `.env`), necesitarás:

1. Crear cuentas en la base de datos para cada usuario
2. Los usuarios deberán iniciar sesión con las nuevas credenciales
3. El sistema anterior de HTTP Basic Auth ya no se usa

## Extensiones Futuras

Posibles mejoras para el sistema de roles:

- [ ] Roles adicionales (editor, viewer, etc.)
- [ ] Permisos granulares por recurso
- [ ] Auditoría de acciones de usuarios
- [ ] Sistema de invitaciones por email
- [ ] Recuperación de contraseña
- [ ] Autenticación de dos factores (2FA)
- [ ] Límites de intentos de login
