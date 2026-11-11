# Academia Fútbol Chocope — Streamlit + Supabase

Conserva la portada, galería, colores, redes sociales, WhatsApp y QR Yape del proyecto recibido. El registro de pagos y administración ya no usan SQLite.

## 1. Base de datos

En tu proyecto `chocope-gestion`, las cinco tablas y el usuario administrador ya fueron creados. **NO vuelvas a crear las tablas.** En SQL Editor abre una consulta nueva, pega íntegro `sql/02_seguridad_y_pagos.sql` y pulsa Run sin seleccionar fragmentos. Este script añade políticas faltantes, perfil automático, funciones de registro/revisión y bucket privado. No contiene DROP TABLE ni elimina registros. Si muestra error, detente y comparte el error; no ejecutes fragmentos de funciones por separado.

Antes de producción, revisa todas las políticas existentes en Supabase (incluidas las que no creó este script), verifica permisos de usuarios reales y configura recuperación de contraseña, confirmación de email, controles antiabuso y protección de datos de menores.

## 2. Configuración local

En VS Code abre esta carpeta. Ejecuta:

```powershell
python -m pip install -r requirements.txt
```

Copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y coloca la URL del proyecto y **solo** la clave pública `sb_publishable_...` de Supabase. Nunca uses `service_role`, `sb_secret_...` ni la contraseña de PostgreSQL en Streamlit.

```powershell
python -m streamlit run app.py
```

El archivo `.streamlit/secrets.toml` está excluido de Git. En Streamlit Cloud pega estas variables en **App settings → Secrets**.

## 3. Uso

- `http://localhost:8501/`: portada.
- `http://localhost:8501/?vista=registrar_pago`: apoderados, cuenta y comprobante.
- `http://localhost:8501/?vista=administracion`: administrador (correo ya creado en Supabase Auth).

**Flujo:** el apoderado crea su cuenta y confirma correo; el administrador registra alumno, lo vincula con el UUID del apoderado en Authentication → Users, y crea mensualidad. El apoderado registra operación Yape y comprobante. El administrador verifica **manualmente en Yape** antes de aprobar.

El registro exige una mensualidad existente; no admite pagos de matrícula u otros conceptos hasta extender el modelo. No detecta automáticamente ingresos Yape. Las imágenes del QR y la landing siguen en `assets/`.

## 4. Importante

La aplicación no está validada aún con tu instancia real de Supabase. Prueba cuentas distintas, bloqueo RLS, comprobantes, revisión y restablecimiento de contraseña antes de abrir al público. Para despliegue de producción es recomendable agregar auditoría inmutable, políticas de retención, controles de privacidad, tratamiento de datos de menores y manejo de reembolsos. El reporte muestra hasta los últimos 1000 pagos, no un consolidado histórico ilimitado.
