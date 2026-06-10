# 🔑 Guía de Integración - Sistema de API Keys

## 📋 Resumen Ejecutivo

Este documento explica **cómo integrar tu sitio web externo con Presenton** para que tus usuarios puedan crear presentaciones sin necesidad de hacer login. Solo necesitas un enlace con una API key especial.

---

## 🎯 ¿Qué Hace Este Sistema?

Permite que desde **TU página web** los usuarios hagan clic en un botón/enlace y sean llevados directamente a Presenton para crear presentaciones **sin pedir usuario ni contraseña**.

### Flujo Simple:
```
Tu Página Web → Click en botón → Presenton con API key → Usuario crea presentación
```

---

## 🚀 Pasos para Integrar (Lado de Presenton)

### Paso 1: Crear tu API Key

**Opción A: Desde la Interfaz Web (Recomendado para principiantes)**

1. Entra a Presenton con tu cuenta de **administrador**
2. Ve al menú **"Usuarios"** o **"Admin"**
3. Busca la sección **"API Keys"** (nueva sección)
4. Haz clic en **"Crear Nueva API Key"**
5. Dale un nombre (ejemplo: "Integración Mi Sitio Web")
6. **IMPORTANTE:** Copia la API key que se genera, se ve así:
   ```
   sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx
   ```
7. **⚠️ GUÁRDALA EN UN LUGAR SEGURO** - Solo se muestra una vez

**Opción B: Crear API Key Desde el Terminal (Para desarrolladores)**

Si tienes acceso al servidor de Presenton:

```bash
# Navega al directorio del proyecto
cd /var/www/html/presenton

# Ejecuta el script
python create_test_api_key.py
```

El script te mostrará algo como esto:
```
================================================================================
✅ API Key de prueba creada exitosamente!
================================================================================

ID: abc-123-def-456
Nombre: Test API Key - Demo
API Key: sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx
Activa: True
Creada: 2024-01-01 00:00:00
Expira: 2024-12-31 23:59:59

================================================================================
🔗 URL de prueba:
================================================================================

http://localhost:5000/?api_key=sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx
```

**Copia la API key que empieza con `sk_`**

---

## 💻 Cómo Integrar en TU Sitio Web

### Método 1: Enlace Simple (El Más Fácil) ⭐ RECOMENDADO

Simplemente crea un enlace HTML con la API key en la URL:

```html
<!-- Reemplaza TU_DOMINIO y TU_API_KEY -->
<a href="https://TU_DOMINIO/?api_key=sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx" 
   target="_blank"
   class="btn btn-primary">
  Crear Presentación Ahora
</a>
```

**Ejemplo Real:**
```html
<a href="https://presenton.miempresa.com/?api_key=sk_xyzABC123..." 
   target="_blank"
   style="background-color: #4CAF50; color: white; padding: 15px 32px; text-decoration: none; display: inline-block;">
  🎨 Crear Mi Presentación
</a>
```

### Método 2: Botón con JavaScript

Si quieres más control o necesitas lógica adicional:

```html
<button onclick="crearPresentacion()" class="btn-crear">
  Crear Presentación
</button>

<script>
function crearPresentacion() {
  // Tu API key (reemplázala)
  const API_KEY = "sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx";
  
  // Tu dominio de Presenton (reemplázalo)
  const PRESENTON_URL = "https://presenton.miempresa.com";
  
  // Construye la URL completa
  const url = `${PRESENTON_URL}/?api_key=${API_KEY}`;
  
  // Abre en nueva pestaña
  window.open(url, '_blank');
}
</script>
```

### Método 3: Formulario con Datos Adicionales (Avanzado)

Si quieres pasar datos adicionales del usuario:

```html
<form id="formPresentacion">
  <input type="text" id="nombreUsuario" placeholder="Tu nombre" required>
  <button type="submit">Crear Presentación</button>
</form>

<script>
document.getElementById('formPresentacion').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const API_KEY = "sk_abcd1234efgh5678...";
  const PRESENTON_URL = "https://presenton.miempresa.com";
  const nombreUsuario = document.getElementById('nombreUsuario').value;
  
  // Puedes agregar parámetros adicionales (opcional)
  const url = `${PRESENTON_URL}/?api_key=${API_KEY}&nombre=${encodeURIComponent(nombreUsuario)}`;
  
  window.open(url, '_blank');
});
</script>
```

### Método 4: Integración en React/Vue/Angular

**React:**
```jsx
import React from 'react';

function BotonPresentacion() {
  const API_KEY = "sk_abcd1234efgh5678...";
  const PRESENTON_URL = "https://presenton.miempresa.com";
  
  const handleClick = () => {
    window.open(`${PRESENTON_URL}/?api_key=${API_KEY}`, '_blank');
  };
  
  return (
    <button onClick={handleClick} className="btn-presentacion">
      Crear Presentación
    </button>
  );
}

export default BotonPresentacion;
```

**Vue:**
```vue
<template>
  <button @click="crearPresentacion" class="btn-presentacion">
    Crear Presentación
  </button>
</template>

<script>
export default {
  data() {
    return {
      apiKey: 'sk_abcd1234efgh5678...',
      presentonUrl: 'https://presenton.miempresa.com'
    }
  },
  methods: {
    crearPresentacion() {
      window.open(`${this.presentonUrl}/?api_key=${this.apiKey}`, '_blank');
    }
  }
}
</script>
```

**Angular:**
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-boton-presentacion',
  template: `
    <button (click)="crearPresentacion()" class="btn-presentacion">
      Crear Presentación
    </button>
  `
})
export class BotonPresentacionComponent {
  apiKey = 'sk_abcd1234efgh5678...';
  presentonUrl = 'https://presenton.miempresa.com';
  
  crearPresentacion() {
    window.open(`${this.presentonUrl}/?api_key=${this.apiKey}`, '_blank');
  }
}
```

---

## 🔒 Seguridad - MUY IMPORTANTE

### ❌ NO Hagas Esto:

```javascript
// MAL - La API key visible en el código del cliente
const API_KEY = "sk_abcd1234..."; // Cualquiera puede verla
```

### ✅ Haz Esto en Producción:

**Opción A: API Key en el Backend (RECOMENDADO)**

```javascript
// Frontend - No expones la API key
async function crearPresentacion() {
  // Llama a TU backend primero
  const response = await fetch('/api/generar-url-presenton', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  const data = await response.json();
  // Tu backend te devuelve la URL completa con la API key
  window.open(data.url, '_blank');
}
```

```python
# Backend (Python/Flask ejemplo) - La API key está aquí
from flask import Flask, jsonify

app = Flask(__name__)

# La API key está en tu backend, no en el cliente
API_KEY = "sk_abcd1234..."  # O mejor, en variable de entorno
PRESENTON_URL = "https://presenton.miempresa.com"

@app.route('/api/generar-url-presenton', methods=['POST'])
def generar_url():
    url = f"{PRESENTON_URL}/?api_key={API_KEY}"
    return jsonify({"url": url})
```

**Opción B: Variables de Entorno**

```javascript
// En tu .env (nunca en el repositorio)
VITE_PRESENTON_API_KEY=sk_abcd1234...
VITE_PRESENTON_URL=https://presenton.miempresa.com

// En tu código
const apiKey = import.meta.env.VITE_PRESENTON_API_KEY;
const url = `${import.meta.env.VITE_PRESENTON_URL}/?api_key=${apiKey}`;
```

---

## 🧪 Cómo Probar que Funciona

### Paso 1: Crea un archivo HTML de prueba

Crea un archivo llamado `test-presenton.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prueba Integración Presenton</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            text-align: center;
        }
        .btn-test {
            background-color: #4CAF50;
            color: white;
            padding: 15px 32px;
            text-decoration: none;
            font-size: 16px;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        .btn-test:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>🎨 Prueba de Integración Presenton</h1>
    <p>Haz clic en el botón para ir a Presenton:</p>
    
    <button onclick="irAPresenton()" class="btn-test">
        Crear Presentación Ahora
    </button>
    
    <script>
        function irAPresenton() {
            // ⚠️ IMPORTANTE: Reemplaza estos valores con los tuyos
            const API_KEY = "sk_XXXXXXXX"; // Tu API key aquí
            const PRESENTON_URL = "http://localhost:5000"; // O tu dominio
            
            if (API_KEY === "sk_XXXXXXXX") {
                alert("⚠️ Por favor, reemplaza API_KEY con tu API key real");
                return;
            }
            
            const url = `${PRESENTON_URL}/?api_key=${API_KEY}`;
            console.log("Abriendo:", url);
            window.open(url, '_blank');
        }
    </script>
</body>
</html>
```

### Paso 2: Prueba el archivo

1. Reemplaza `sk_XXXXXXXX` con tu API key real
2. Reemplaza la URL con tu dominio de Presenton
3. Abre el archivo `test-presenton.html` en tu navegador
4. Haz clic en el botón

### Paso 3: Verifica que funciona

**✅ Si todo funciona correctamente:**
- Se abre una nueva pestaña con Presenton
- **NO te pide login**
- Ves el dashboard directamente
- **NO ves** el botón de "Settings"
- **NO ves** el botón de "Admin" o "Usuarios"
- **SÍ ves** el botón "+" para crear presentación

**❌ Si algo sale mal:**
- Te redirige al login → La API key no es válida
- Error 401 → La API key está inactiva o expiró
- No carga nada → URL incorrecta

---

## 📊 ¿Qué Puede Hacer el Usuario con API Key?

### ✅ Permitido:
- ✅ Ver el dashboard
- ✅ Crear nuevas presentaciones
- ✅ Ver presentaciones existentes
- ✅ Editar presentaciones
- ✅ Exportar presentaciones (PDF/PPTX)

### ❌ Bloqueado:
- ❌ Acceder a Settings (configuración)
- ❌ Acceder al panel de administración
- ❌ Gestionar usuarios
- ❌ Gestionar otras API keys
- ❌ Eliminar presentaciones (puede ser configurado)

---

## 🛠️ Configuración Avanzada

### Gestionar API Keys Programáticamente

Si necesitas crear/gestionar API keys desde tu sistema:

```javascript
// Crear nueva API key (requiere token de admin)
async function crearAPIKey(nombre, adminToken) {
  const response = await fetch('https://presenton.miempresa.com/api/v1/admin/api-keys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${adminToken}`
    },
    body: JSON.stringify({
      name: nombre,
      expires_at: "2025-12-31T23:59:59Z" // Opcional
    })
  });
  
  const data = await response.json();
  return data.key; // Guarda esta API key
}

// Listar todas las API keys
async function listarAPIKeys(adminToken) {
  const response = await fetch('https://presenton.miempresa.com/api/v1/admin/api-keys', {
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  });
  
  return await response.json();
}

// Desactivar una API key
async function desactivarAPIKey(apiKeyId, adminToken) {
  await fetch(`https://presenton.miempresa.com/api/v1/admin/api-keys/${apiKeyId}/toggle`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  });
}
```

### Usar API Key en Llamadas Directas a la API

Si necesitas hacer llamadas directas a la API (no solo el navegador):

```javascript
// Ejemplo: Crear presentación programáticamente
async function crearPresentacionAPI(tema, apiKey) {
  const response = await fetch('https://presenton.miempresa.com/api/v1/ppt/presentation/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey  // La API key va en el header
    },
    body: JSON.stringify({
      content: tema,
      n_slides: 10,
      language: "es"
    })
  });
  
  return await response.json();
}

// Uso
const resultado = await crearPresentacionAPI(
  "Historia de la Inteligencia Artificial",
  "sk_abcd1234..."
);
console.log("Presentación creada:", resultado.id);
```

---

## 🔍 Solución de Problemas Comunes

### Problema 1: "Me redirige al login"
**Causa:** La API key no es válida
**Solución:**
1. Verifica que copiaste la API key completa (empieza con `sk_`)
2. Revisa que la API key esté activa en el panel de admin
3. Verifica que no haya expirado

### Problema 2: "Veo botones de Settings/Admin"
**Causa:** No estás usando API key, estás logueado normal
**Solución:**
1. Cierra sesión
2. Limpia las cookies del navegador
3. Usa una ventana de incógnito para probar

### Problema 3: "Error 403 - Forbidden"
**Causa:** Intentas acceder a algo no permitido con API key
**Solución:** Las API keys solo pueden crear/leer presentaciones, no hacer operaciones administrativas

### Problema 4: "No funciona en producción"
**Causa:** CORS o configuración de dominio
**Solución:**
1. Asegúrate de usar HTTPS en producción
2. Verifica que tu dominio esté configurado correctamente
3. Revisa los logs del servidor

---

## 📞 Soporte y Contacto

Si tienes problemas:

1. **Revisa los logs del navegador:**
   - Abre DevTools (F12)
   - Ve a la pestaña "Console"
   - Ve a la pestaña "Network"
   - Busca errores en rojo

2. **Revisa los logs del servidor:**
   ```bash
   # Si usas Docker
   docker-compose logs -f production
   
   # Si es local
   tail -f servers/fastapi/logs/app.log
   ```

3. **Verifica la API key:**
   ```bash
   curl "https://presenton.miempresa.com/api/v1/auth/verify-api-key?api_key=sk_tu_api_key"
   ```
   
   Debería responder:
   ```json
   {
     "valid": true,
     "name": "Nombre de tu API key",
     "id": "abc-123"
   }
   ```

---

## 📝 Checklist de Implementación

Usa esta lista para asegurarte de que todo está configurado:

- [ ] ✅ API key creada en Presenton
- [ ] ✅ API key copiada y guardada de forma segura
- [ ] ✅ Código de integración añadido a tu sitio
- [ ] ✅ Probado en local (localhost)
- [ ] ✅ Probado en incógnito (sin cookies)
- [ ] ✅ Verificado que NO pide login
- [ ] ✅ Verificado que NO se ven botones de Settings/Admin
- [ ] ✅ Probada la creación de presentaciones
- [ ] ✅ API key protegida (no visible en el código cliente en producción)
- [ ] ✅ Documentación interna creada para tu equipo
- [ ] ✅ Configurado HTTPS en producción
- [ ] ✅ Probado en producción

---

## 🎉 Ejemplo Completo Funcional

Aquí un ejemplo completo que puedes usar directamente:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mi Sistema - Integración Presenton</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            margin-bottom: 30px;
        }
        .btn-presenton {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            font-size: 18px;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: transform 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-presonton:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 5px;
            font-size: 14px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Creador de Presentaciones</h1>
        <p>Crea presentaciones profesionales con IA en segundos</p>
        
        <button onclick="abrirPresenton()" class="btn-presenton">
            ✨ Crear Mi Presentación
        </button>
        
        <div class="info">
            <strong>✓</strong> Sin registro<br>
            <strong>✓</strong> Sin login<br>
            <strong>✓</strong> Gratis
        </div>
    </div>
    
    <script>
        function abrirPresenton() {
            // CONFIGURACIÓN - Reemplaza estos valores
            const CONFIG = {
                apiKey: "sk_XXXXXXXX",  // ⚠️ Reemplaza con tu API key
                url: "http://localhost:5000"  // ⚠️ Reemplaza con tu URL
            };
            
            // Validación
            if (CONFIG.apiKey === "sk_XXXXXXXX") {
                alert("⚠️ Configura tu API key en el código");
                return;
            }
            
            // Construir URL
            const urlCompleta = `${CONFIG.url}/?api_key=${CONFIG.apiKey}`;
            
            // Abrir en nueva pestaña
            const ventana = window.open(urlCompleta, '_blank');
            
            // Opcional: Detectar si se bloqueó el popup
            if (!ventana || ventana.closed || typeof ventana.closed === 'undefined') {
                alert('⚠️ Por favor, permite popups para este sitio');
            }
        }
    </script>
</body>
</html>
```

---

## 🎓 Conceptos Clave para Entender

### ¿Qué es una API Key?
Es como una "contraseña especial" que identificaen lugar de usar usuario y contraseña normal. En este caso:
- Formato: `sk_` + 43 caracteres aleatorios
- Ejemplo: `sk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx`

### ¿Cómo funciona internamente?
1. Tu página envía al usuario a Presenton con `?api_key=sk_...` en la URL
2. Presenton recibe la URL y extrae la API key
3. Verifica en la base de datos si la key es válida y está activa
4. Si es válida, crea una "sesión limitada" (solo puede crear presentaciones)
5. Redirige al usuario al dashboard
6. El usuario trabaja normalmente, pero con permisos limitados

### ¿Dónde se guarda la sesión?
- En `sessionStorage` del navegador (se borra al cerrar la pestaña)
- NO se guarda en cookies
- NO se guarda en localStorage
- Es temporal y solo para esa sesión

---

## ✅ Resumen Rápido

1. **Crea una API key** en el panel de admin de Presenton
2. **Copia la API key** (empieza con `sk_`)
3. **Crea un enlace** en tu sitio: `https://tu-presenton.com/?api_key=sk_...`
4. **Listo** - Tus usuarios pueden crear presentaciones sin login

**Eso es todo. Realmente es así de simple.**

---

*Documento creado: 2024 | Versión 1.0*
