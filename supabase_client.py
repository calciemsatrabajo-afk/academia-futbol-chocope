
"""
ACADEMIA FÚTBOL CHOCOPE
Autenticación con Supabase.

Funciones:
- cliente()
- sesion()
- cerrar()
- acceso()

Nunca utilizar service_role en esta aplicación.
"""

import logging
import re

import streamlit as st
from supabase import create_client
from supabase_auth.errors import AuthApiError

logger = logging.getLogger(__name__)


# =====================================================
# CONFIGURACIÓN
# =====================================================

def limpiar_sesion():
    """Elimina las credenciales locales."""

    for campo in (
        "usuario_id",
        "access_token",
        "refresh_token",
        "correo",
    ):
        st.session_state.pop(campo, None)


def configuracion():
    """Obtiene y valida las credenciales públicas."""

    url = str(
        st.secrets.get("SUPABASE_URL", "")
    ).strip().rstrip("/")

    key = str(
        st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "")
    ).strip()

    if not url or not key:
        st.error(
            "Faltan SUPABASE_URL o "
            "SUPABASE_PUBLISHABLE_KEY en "
            ".streamlit/secrets.toml."
        )
        st.stop()

    # El SDK necesita la URL base, no /rest/v1.
    if url.endswith("/rest/v1"):
        url = url[:-8].rstrip("/")

    if not (
        url.startswith("https://")
        and url.endswith(".supabase.co")
    ):
        st.error(
            "SUPABASE_URL no tiene un formato válido. "
            "Debe ser https://TU-PROYECTO.supabase.co"
        )
        st.stop()

    return url, key


# =====================================================
# CLIENTE SUPABASE
# =====================================================

def cliente():
    """
    Crea un cliente Supabase para la ejecución actual.

    Si existe una sesión, intenta restaurarla.
    """

    url, key = configuracion()

    try:
        sb = create_client(url, key)

    except Exception as error:
        logger.exception(
            "No se pudo crear el cliente Supabase"
        )

        st.error(
            "No se pudo conectar con Supabase. "
            "Verifica la URL y la clave pública."
        )

        st.stop()

    token = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")

    if token and refresh:

        try:
            respuesta = sb.auth.set_session(
                token,
                refresh
            )

            if respuesta.session:

                st.session_state["access_token"] = (
                    respuesta.session.access_token
                )

                st.session_state["refresh_token"] = (
                    respuesta.session.refresh_token
                )

                if respuesta.user:
                    st.session_state["usuario_id"] = (
                        str(respuesta.user.id)
                    )

            else:
                limpiar_sesion()

        except Exception:
            logger.exception(
                "No se pudo restaurar la sesión"
            )

            limpiar_sesion()

    return sb


# =====================================================
# ESTADO DE SESIÓN
# =====================================================

def sesion():
    """Comprueba si hay credenciales locales."""

    return bool(
        st.session_state.get("usuario_id")
        and st.session_state.get("access_token")
        and st.session_state.get("refresh_token")
    )


# =====================================================
# CERRAR SESIÓN
# =====================================================

def cerrar():
    """Cierra sesión en Supabase y Streamlit."""

    try:
        if sesion():
            sb = cliente()
            sb.auth.sign_out()

    except Exception:
        logger.exception(
            "Error durante el cierre de sesión"
        )

    finally:
        limpiar_sesion()
        st.rerun()


# =====================================================
# VALIDACIONES
# =====================================================

def correo_valido(email):
    """Validación básica del correo."""

    patron = (
        r"^[A-Za-z0-9._%+\-]+@"
        r"[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    )

    return bool(re.fullmatch(patron, email))


def mostrar_error(error):
    """
    Traduce errores comunes de Supabase.

    El detalle técnico se registra en la terminal,
    sin mostrar información sensible al usuario.
    """

    mensaje = str(error).lower()

    logger.error(
        "Error Supabase (%s): %s",
        type(error).__name__,
        str(error),
    )

    if "invalid login credentials" in mensaje:

        st.error(
            "Correo electrónico o contraseña incorrectos."
        )

    elif "email not confirmed" in mensaje:

        st.warning(
            "Tu correo todavía no está confirmado. "
            "Revisa tu bandeja de entrada."
        )

    elif (
        "invalid api key" in mensaje
        or "invalid_api_key" in mensaje
    ):

        st.error(
            "La clave pública de Supabase no es válida."
        )

    elif (
        "signup is disabled" in mensaje
        or "signups not allowed" in mensaje
        or "signup_disabled" in mensaje
    ):

        st.error(
            "El registro de usuarios está deshabilitado "
            "en Supabase Authentication."
        )

    elif (
        "rate limit" in mensaje
        or "email rate limit" in mensaje
        or "over_email_send_rate_limit" in mensaje
    ):

        st.warning(
            "Se alcanzó el límite de solicitudes. "
            "Espera antes de volver a intentarlo."
        )

    elif (
        "database error saving new user" in mensaje
        or "database error" in mensaje
    ):

        st.error(
            "Supabase presentó un error al guardar "
            "el usuario en la base de datos. "
            "Revisa los triggers y las políticas "
            "de la tabla perfiles."
        )

    elif (
        "user already registered" in mensaje
        or "already been registered" in mensaje
    ):

        st.warning(
            "Este correo podría estar registrado. "
            "Prueba iniciar sesión o recuperar "
            "tu contraseña."
        )

    elif "password" in mensaje:

        st.error(
            "Supabase rechazó la contraseña. "
            "Utiliza una contraseña más segura."
        )

    elif (
        "connection" in mensaje
        or "timeout" in mensaje
    ):

        st.error(
            "No se pudo establecer comunicación "
            "con Supabase. Revisa tu conexión."
        )

    else:

        st.error(
            "No se pudo completar la operación. "
            "Consulta el error técnico en la "
            "terminal de Visual Studio Code."
        )


# =====================================================
# FORMULARIO DE ACCESO
# =====================================================

def acceso():
    """
    Gestiona:
    - Inicio de sesión
    - Registro de apoderados
    - Recuperación de contraseña
    """

    st.subheader("Acceso a la academia")

    # ---------------------------------------------
    # USUARIO CON SESIÓN
    # ---------------------------------------------

    if sesion():

        st.success(
            "Sesión iniciada: "
            + st.session_state.get(
                "correo",
                "Usuario"
            )
        )

        if st.button(
            "Cerrar sesión",
            key="logout"
        ):
            cerrar()

        return cliente()

    # ---------------------------------------------
    # OPCIONES DE ACCESO
    # ---------------------------------------------

    opcion = st.radio(
        "Acceso",
        [
            "Iniciar sesión",
            "Crear cuenta de apoderado",
            "Recuperar contraseña",
        ],
        horizontal=True,
        key="opcion_acceso",
    )

    # ---------------------------------------------
    # FORMULARIO
    # ---------------------------------------------

    with st.form("auth_form"):

        email = st.text_input(
            "Correo electrónico",
            placeholder="ejemplo@gmail.com"
        ).strip().lower()

        password = ""

        if opcion != "Recuperar contraseña":

            password = st.text_input(
                "Contraseña",
                type="password"
            )

        nombre = ""

        if opcion == "Crear cuenta de apoderado":

            nombre = st.text_input(
                "Nombre completo",
                placeholder="Nombres y apellidos"
            )

        enviar = st.form_submit_button(
            "Continuar",
            type="primary"
        )

    if not enviar:
        return None

    # ---------------------------------------------
    # VALIDACIÓN DEL CORREO
    # ---------------------------------------------

    if not correo_valido(email):

        st.warning(
            "Ingresa un correo electrónico válido."
        )

        return None

    # ---------------------------------------------
    # VALIDACIONES SEGÚN OPERACIÓN
    # ---------------------------------------------

    if opcion == "Iniciar sesión" and not password:

        st.warning(
            "Ingresa tu contraseña."
        )

        return None

    if opcion == "Crear cuenta de apoderado":

        if not nombre.strip():

            st.warning(
                "Ingresa el nombre completo del apoderado."
            )

            return None

        if len(password) < 10:

            st.warning(
                "La contraseña debe tener al menos "
                "10 caracteres."
            )

            return None

    # ---------------------------------------------
    # OPERACIONES SUPABASE
    # ---------------------------------------------

    try:

        sb = cliente()

        # =========================================
        # INICIAR SESIÓN
        # =========================================

        if opcion == "Iniciar sesión":

            respuesta = sb.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            if not respuesta.session or not respuesta.user:

                st.warning(
                    "No se recibió una sesión válida. "
                    "Comprueba que tu correo esté confirmado."
                )

                return None

            st.session_state["access_token"] = (
                respuesta.session.access_token
            )

            st.session_state["refresh_token"] = (
                respuesta.session.refresh_token
            )

            st.session_state["usuario_id"] = (
                str(respuesta.user.id)
            )

            st.session_state["correo"] = email

            st.rerun()

        # =========================================
        # REGISTRAR APODERADO
        # =========================================

        elif opcion == "Crear cuenta de apoderado":

            respuesta = sb.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "nombre": nombre.strip()
                        }
                    },
                }
            )

            if respuesta.user:

                st.success(
                    "Solicitud de registro procesada. "
                    "Si corresponde, recibirás un correo "
                    "de confirmación. Revisa también spam."
                )

                st.info(
                    "Después de confirmar tu correo, "
                    "selecciona Iniciar sesión. "
                    "La academia deberá vincular "
                    "a tu hijo con tu cuenta."
                )

            else:

                st.info(
                    "Si el registro es válido, "
                    "recibirás instrucciones "
                    "en tu correo electrónico."
                )

        # =========================================
        # RECUPERAR CONTRASEÑA
        # =========================================

        elif opcion == "Recuperar contraseña":

            sb.auth.reset_password_email(email)

            st.success(
                "Si el correo está registrado, "
                "recibirás instrucciones para "
                "recuperar tu contraseña."
            )

            st.caption(
                "Para completar la recuperación, "
                "configura una URL de redirección "
                "y una pantalla de actualización "
                "de contraseña en tu aplicación."
            )

    except AuthApiError as error:

        mostrar_error(error)

    except Exception as error:

        logger.exception(
            "Fallo inesperado en autenticación"
        )

        mostrar_error(error)

    return None
