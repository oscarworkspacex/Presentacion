# Sistema de Autenticación con API Keys

Este documento describe el sistema de API keys implementado para permitir acceso directo a la funcionalidad de crear presentaciones sin requerir login tradicional.

## Características

- ✅ Autenticación mediante API key en URL o header HTTP
- ✅ Acceso limitado: solo creación y lectura de presentaciones
- ✅ Gestión completa de API keys desde el panel de administración
- ✅ Compatible con el sistema de autenticación JWT existente
- ✅ API keys con expiración opcional
- ✅ Seguimiento de uso (contador y última vez usada)

## Arquitectura

### Backend (FastAPI)

**Nuevos archivos creados:**
- `servers/fastapi/models/sql/api_key.py` - Modelo SQLAlchemy para API keys
- `servers/fastapi/models/api_key.py` - Modelos Pydantic para requests/responses
- `servers/fastapi/api/v1/admin/endpoints/api_keys.py` - Endpoints CRUD para gestión

**Archivos modificados:**
- `servers/fastapi/services/database.py` - Agregada tabla de API keys
- `servers/fastapi/api/middlewares.py` - Soporte de autenticación con API keys
- `servers/fastapi/api/v1/auth/endpoints.py` - Endpoint de verificación de API keys
- `servers/fastapi/api/v1/admin/router.py` - Router de API keys integrado

### Frontend (Next.js)

**Nuevos archivos creados:**
- `servers/nextjs/components/ApiKeyHandler.tsx` - Interceptor de API keys en URL
- `servers/nextjs/components/ApiKeyGuard.tsx` - Protección de rutas restringidas
- `servers/nextjs/hooks/useAuthType.ts` - Hook para detectar tipo de autenticación

**Archivos modificados:**
- `servers/nextjs/app/layout.tsx` - Integración de ApiKeyHandler
- `servers/nextjs/components/AuthProvider.tsx` - Soporte de API keys
- `servers/nextjs/components/HeaderNab.tsx` - Ocultar opciones según auth type
- `servers/nextjs/services/api/header.ts` - Incluir API key en requests
- `servers/nextjs/app/(presentation-generator)/settings/SettingPage.tsx` - Protegido con ApiKeyGuard
- `servers/nextjs/app/admin/users/page.tsx` - Protegido con ApiKeyGuard

## Uso

### 1. Crear una API Key (Como Administrador)

#### Opción A: Desde la interfaz web
1. Iniciar sesión como administrador
2. Ir a la sección de Administración
3. Acceder a "API Keys"
4. Hacer clic en "Nueva API Key"
5. Ingresar un nombre descriptivo
6. (Opcional) Establecer fecha de expiración
7. Copiar la API key generada (solo se muestra una vez)

#### Opción B: Usando el endpoint REST

```bash
POST /api/v1/admin/api-keys
Content-Type: application/json
Authorization: Bearer <admin_jwt_token>

{
  "name": "Mi API Key de Prueba",
  "expires_at": "2025-12-31T23:59:59Z"  // opcional
}
```

Respuesta:
```json
{
  "id": "abc-123-def-456",
  "key": "sk_abcd1234...",
  "name": "Mi API Key de Prueba",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "usage_count": 0,
  "last_used_at": null,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### 2. Usar la API Key

#### Opción A: En la URL (Para navegadores)

```
https://tudominio.com/?api_key=sk_abcd1234...
```

El usuario será automáticamente:
1. Validado contra la base de datos
2. Redirigido al dashboard
3. Limitado a crear y leer presentaciones

#### Opción B: En Header HTTP (Para API clients)

```bash
GET /api/v1/ppt/presentation/list
X-API-Key: sk_abcd1234...
```

### 3. Gestionar API Keys

**Listar todas las API keys:**
```bash
GET /api/v1/admin/api-keys
Authorization: Bearer <admin_jwt_token>
```

**Ver detalles de una API key:**
```bash
GET /api/v1/admin/api-keys/{id}
Authorization: Bearer <admin_jwt_token>
```

**Activar/Desactivar una API key:**
```bash
PATCH /api/v1/admin/api-keys/{id}/toggle
Authorization: Bearer <admin_jwt_token>
```

**Eliminar una API key:**
```bash
DELETE /api/v1/admin/api-keys/{id}
Authorization: Bearer <admin_jwt_token>
```

## Permisos

### Usuarios con API Key (rol: api_user)

**✅ Permitido:**
- `GET /api/v1/ppt/*` - Leer presentaciones y recursos
- `POST /api/v1/ppt/presentation/create` - Crear presentación
- `POST /api/v1/ppt/presentation/prepare` - Preparar presentación
- `POST /api/v1/ppt/presentation/generate` - Generar presentación
- `POST /api/v1/ppt/presentation/create-from-theme` - Crear desde tema

**❌ Bloqueado:**
- `/api/v1/admin/*` - Todas las rutas de administración
- `/api/v1/ppt/*/delete` - Operaciones destructivas
- `DELETE`, operaciones de configuración
- Acceso a `/settings` y `/admin/users` en el frontend

### Usuarios con JWT (roles: admin, user)

- Acceso normal según su rol (sin cambios)

## Testing

### 1. Iniciar el proyecto

```bash
# Opción 1: Con Docker
docker-compose up development

# Opción 2: Sin Docker (desarrollo local)
cd servers/fastapi && uvicorn api.main:app --reload --port 8000
cd servers/nextjs && npm run dev
```

### 2. Crear una API key de prueba

```bash
# Usando el script incluido
python create_test_api_key.py
```

El script generará una API key y mostrará la URL completa para probar.

### 3. Probar el flujo completo

1. **Acceso con API key:**
   - Copiar la URL generada: `http://localhost:5000/?api_key=sk_...`
   - Pegar en el navegador
   - ✅ Deberías ser redirigido al dashboard automáticamente

2. **Verificar restricciones de UI:**
   - ✅ NO deberías ver el botón de "Settings"
   - ✅ NO deberías ver el botón de "Admin/Usuarios"
   - ✅ SÍ deberías ver el dashboard y el botón "+"

3. **Crear una presentación:**
   - Hacer clic en el botón "+"
   - Ingresar un tema o subir documentos
   - ✅ La presentación debería crearse normalmente

4. **Intentar acceder a rutas prohibidas:**
   - Navegar manualmente a `/settings`
   - ✅ Deberías ser redirigido al dashboard
   - Navegar a `/admin/users`
   - ✅ Deberías ser redirigido al dashboard

5. **Verificar llamadas API:**
   - Abrir DevTools > Network
   - Crear una presentación
   - ✅ Las requests deberían incluir el header `X-API-Key`

6. **Probar login normal:**
   - Abrir una ventana de incógnito
   - Ir a `http://localhost:5000/login`
   - Iniciar sesión con usuario/contraseña
   - ✅ El flujo normal debería funcionar sin cambios

## Seguridad

- ✅ API keys son largas y aleatorias (32+ caracteres)
- ✅ Las keys se generan con `secrets.token_urlsafe()`
- ✅ Solo se muestra la key completa al momento de crearla
- ✅ En listados posteriores, la key se enmascara (`sk_abc...xyz`)
- ✅ Soporte para expiración de keys
- ✅ Seguimiento de uso (contador y timestamp)
- ⚠️ **IMPORTANTE:** Usar HTTPS en producción

## Integración con Página Externa

Para integrar desde otra página web:

```html
<!-- HTML -->
<a href="https://tudominio.com/?api_key=sk_abcd1234..." target="_blank">
  Crear Presentación
</a>

<!-- JavaScript -->
<script>
function crearPresentacion() {
  const apiKey = "sk_abcd1234...";
  window.open(`https://tudominio.com/?api_key=${apiKey}`, '_blank');
}
</script>
<button onclick="crearPresentacion()">Crear Presentación</button>
```

## Troubleshooting

**Problema:** La API key no funciona
- Verificar que la key está activa en la base de datos
- Verificar que no ha expirado
- Verificar que el servidor está ejecutándose
- Revisar logs del backend para errores

**Problema:** No se ocultan los botones de Settings/Admin
- Verificar que `sessionStorage.getItem("auth_type")` es "api_key"
- Limpiar cache del navegador
- Revisar la consola del navegador para errores

**Problema:** Las requests no incluyen la API key
- Verificar que la key está en sessionStorage
- Revisar Network tab en DevTools
- Verificar que `getHeader()` se está llamando correctamente

## Base de Datos

### Tabla: api_keys

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | ID único de la API key |
| key | String | La API key (formato: sk_...) |
| name | String | Nombre descriptivo |
| is_active | Boolean | Si la key está activa |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de última actualización |
| expires_at | DateTime | Fecha de expiración (opcional) |
| usage_count | Integer | Número de veces usada |
| last_used_at | DateTime | Última vez que se usó |

## Endpoints API

### Gestión de API Keys (Admin)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/admin/api-keys` | Listar todas las API keys |
| POST | `/api/v1/admin/api-keys` | Crear nueva API key |
| GET | `/api/v1/admin/api-keys/{id}` | Ver detalles de una key |
| DELETE | `/api/v1/admin/api-keys/{id}` | Eliminar una API key |
| PATCH | `/api/v1/admin/api-keys/{id}/toggle` | Activar/desactivar |

### Verificación (Público)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/auth/verify-api-key?api_key=xxx` | Verificar si una key es válida |

## Notas Adicionales

- Las API keys se almacenan en `sessionStorage`, no en `localStorage`
- Al cerrar el navegador, la sesión con API key se pierde
- El backend actualiza automáticamente `usage_count` y `last_used_at`
- El middleware verifica primero JWT, luego API key
- Las restricciones de permisos se aplican tanto en backend como frontend
