
"""Pagos Yape de Academia Fútbol Chocope. Requiere RLS y RPC seguras en Supabase."""
import logging
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from supabase_client import acceso, cliente, sesion

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
BUCKET = "comprobantes-yape"
MAX_BYTES = 4 * 1024 * 1024


def cabecera(titulo):
    st.markdown("""<div style="background:#061c2b;color:white;padding:20px 5%;border-bottom:3px solid #0bbf45"><h2 style="color:white;margin:0">⚽ ACADEMIA FÚTBOL CHOCOPE</h2></div>""", unsafe_allow_html=True)
    st.caption(titulo)
    if st.button("← Volver al inicio", key="volver_inicio"):
        st.query_params.clear()
        st.rerun()


def _filas(respuesta):
    return respuesta.data or []


def _archivo_valido(archivo):
    data = archivo.getvalue()
    if not data or len(data) > MAX_BYTES:
        raise ValueError("El comprobante debe pesar entre 1 byte y 4 MB.")
    ext = Path(archivo.name).suffix.lower()
    firmas = {".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".png": b"\x89PNG\r\n\x1a\n", ".pdf": b"%PDF-"}
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"}
    if ext not in firmas or not data.startswith(firmas[ext]):
        raise ValueError("El archivo debe ser un JPG, PNG o PDF válido.")
    return data, ext, mime[ext]


def _dinero(valor):
    try:
        return f"S/ {Decimal(str(valor or 0)):,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return "S/ 0.00"


def _error_admin(error, operacion):
    """Detalle para el administrador autenticado; no expone tokens ni credenciales."""
    logger.exception("Error en %s", operacion)
    codigo = getattr(error, "code", None)
    mensaje = str(getattr(error, "message", "") or error)
    st.error(f"No se pudo completar: {operacion}.")
    if codigo:
        st.code(f"Código Supabase/PostgreSQL: {codigo}")
    st.code(f"{type(error).__name__}: {mensaje}")
    if codigo == "42501" or "row-level security" in mensaje.lower():
        st.info("La operación fue bloqueada por permisos/RLS. Revisa las políticas de la tabla correspondiente; no desactives RLS.")
    elif codigo == "23502":
        st.info("Falta un valor obligatorio en la tabla. Revisa las columnas NOT NULL y sus valores predeterminados.")
    elif codigo == "23505":
        st.info("Ya existe un registro que incumple una restricción UNIQUE.")
    elif codigo == "23503":
        st.info("Hay una referencia a un registro que no existe (clave foránea).")


def _admin(sb):
    try:
        return sb.rpc("es_administrador").execute().data is True
    except Exception:
        logger.exception("No se pudo verificar rol administrador")
        return False


def mostrar_registro():
    cabecera("Registro de pagos Yape")
    st.title("Registrar mi pago")
    st.info("Realiza el Yape desde la aplicación Yape. Aquí solo reportas la operación; la academia verificará el ingreso antes de aprobarlo.")
    if not sesion():
        acceso()
        return
    sb = cliente()
    uid = str(st.session_state["usuario_id"])
    try:
        relaciones = _filas(sb.table("alumno_apoderado").select("alumno_id").eq("apoderado_id", uid).execute())
        ids = list({r["alumno_id"] for r in relaciones})
        alumnos = _filas(sb.table("alumnos").select("id,nombre,categoria").in_("id", ids).execute()) if ids else []
        cuotas = _filas(sb.table("mensualidades").select("id,alumno_id,periodo,monto,vencimiento").in_("alumno_id", ids).execute()) if ids else []
        pagos = _filas(sb.table("pagos").select("id,mensualidad_id,estado,numero_operacion,fecha_pago,monto").in_("mensualidad_id", [c["id"] for c in cuotas]).execute()) if cuotas else []
    except Exception:
        logger.exception("Error consultando mensualidades")
        st.error("No se pudieron consultar tus mensualidades. Revisa las políticas RLS de Supabase.")
        return
    if not alumnos:
        st.warning("Aún no tienes alumnos vinculados. Solicita a administración que asocie a tu hijo con tu cuenta.")
        return
    nombres = {str(a["id"]): a["nombre"] for a in alumnos}
    st.subheader("Mis alumnos")
    for alumno in alumnos:
        st.write(f"⚽ {alumno['nombre']} — {alumno.get('categoria', '')}")
    qr = ROOT / "assets" / "yape_qr.png"
    if qr.is_file():
        st.image(str(qr), width=230, caption="Escanea el QR oficial de la academia")
    else:
        st.warning("No se encontró assets/yape_qr.png. Solicita a la academia el QR oficial antes de pagar.")
    if not cuotas:
        st.warning("Todavía no tienes mensualidades asignadas. Contacta a administración.")
        return
    bloqueadas = {str(p["mensualidad_id"]) for p in pagos if p.get("estado") in ("pendiente", "aprobado")}
    disponibles = [c for c in cuotas if str(c["id"]) not in bloqueadas]
    st.subheader("Historial de pagos")
    if pagos:
        st.dataframe(pd.DataFrame([{"Alumno": nombres.get(str(next((c["alumno_id"] for c in cuotas if str(c["id"]) == str(p["mensualidad_id"])), "")), "Alumno"), "Fecha": p.get("fecha_pago"), "Operación": p.get("numero_operacion"), "Monto": _dinero(p.get("monto")), "Estado": p.get("estado")} for p in pagos]), hide_index=True, use_container_width=True)
    else:
        st.info("Todavía no has reportado pagos.")
    if not disponibles:
        st.info("No hay mensualidades disponibles para reportar. Las pendientes de verificación o aprobadas no pueden enviarse otra vez.")
        return
    disponibles.sort(key=lambda c: str(c["periodo"]), reverse=True)
    st.subheader("Reportar pago Yape")
    with st.form("registrar_pago_yape_form", clear_on_submit=False):
        cuota = st.selectbox("Mensualidad", disponibles, format_func=lambda c: f"{nombres.get(str(c['alumno_id']), 'Alumno')} · {c['periodo']} · {_dinero(c['monto'])}")
        st.caption("El monto se obtiene de la mensualidad asignada y no puede modificarse.")
        fecha = st.date_input("Fecha de operación", value=date.today(), max_value=date.today())
        operacion = st.text_input("Número de operación Yape", max_chars=70)
        archivo = st.file_uploader("Comprobante (JPG, PNG o PDF; máximo 4 MB)", type=["jpg", "jpeg", "png", "pdf"])
        permiso = st.checkbox("Confirmo que los datos son correctos y autorizo su tratamiento para verificar el pago.")
        enviar = st.form_submit_button("REGISTRAR PAGO", type="primary")
    if not enviar:
        return
    if not operacion.strip() or archivo is None or not permiso:
        st.error("Completa la operación, adjunta el comprobante y confirma la autorización.")
        return
    ruta = None
    subido = False
    try:
        data, ext, mime = _archivo_valido(archivo)
        ruta = f"{uid}/{uuid.uuid4().hex}{ext}"
        sb.storage.from_(BUCKET).upload(ruta, data, {"content-type": mime, "upsert": "false"})
        subido = True
        resultado = sb.rpc("registrar_pago_yape", {"p_mensualidad": cuota["id"], "p_operacion": operacion.strip(), "p_fecha": fecha.isoformat(), "p_ruta": ruta}).execute()
        st.success(f"Pago registrado. Estado: PENDIENTE DE VERIFICACIÓN. Referencia: {str(resultado.data or '')[:12]}")
        st.balloons()
    except ValueError as exc:
        st.error(str(exc))
    except Exception:
        logger.exception("Error al registrar pago Yape")
        st.error("No se pudo registrar el pago. Comprueba que no esté duplicado y que existan el bucket privado, las políticas RLS y la función registrar_pago_yape.")
    finally:
        if subido and ruta and not ('resultado' in locals()):
            try:
                sb.storage.from_(BUCKET).remove([ruta])
            except Exception:
                logger.warning("No se pudo limpiar comprobante huérfano")


def mostrar_administracion():
    cabecera("Administración privada")
    st.title("Panel de administración")
    if not sesion():
        acceso()
        return
    sb = cliente()
    if not _admin(sb):
        st.error("Esta cuenta no tiene permisos de administrador.")
        return
    tab1, tab2, tab3 = st.tabs(["Pagos e ingresos", "Alumnos y apoderados", "Mensualidades"])
    with tab1:
        try:
            pagos = _filas(sb.table("pagos").select("*").order("creado_en", desc=True).limit(1000).execute())
            alumnos = {str(a["id"]): a for a in _filas(sb.table("alumnos").select("id,nombre").execute())}
            cuotas = {str(c["id"]): c for c in _filas(sb.table("mensualidades").select("id,alumno_id,periodo").execute())}
        except Exception:
            logger.exception("Error leyendo pagos administrativos")
            st.error("No se pudieron leer los pagos. Comprueba las políticas RLS.")
            return
        aprobados = sum((Decimal(str(p.get("monto") or 0)) for p in pagos if p.get("estado") == "aprobado"), Decimal(0))
        pendientes = sum((Decimal(str(p.get("monto") or 0)) for p in pagos if p.get("estado") == "pendiente"), Decimal(0))
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos aprobados", _dinero(aprobados))
        c2.metric("Por verificar", _dinero(pendientes))
        c3.metric("Operaciones consultadas", len(pagos))

        def etiqueta(p):
            cuota = cuotas.get(str(p.get("mensualidad_id")), {})
            return alumnos.get(str(cuota.get("alumno_id")), {}).get("nombre", "Alumno")

        registros = [{"id": p["id"], "alumno": etiqueta(p), "periodo": cuotas.get(str(p.get("mensualidad_id")), {}).get("periodo", ""), "monto": float(p.get("monto") or 0), "fecha": p.get("fecha_pago"), "operacion": p.get("numero_operacion"), "estado": p.get("estado")} for p in pagos]
        if not registros:
            st.info("Todavía no hay operaciones registradas.")
        else:
            df = pd.DataFrame(registros)
            st.dataframe(df, hide_index=True, use_container_width=True)
            archivo = BytesIO()
            with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Pagos", index=False)
            st.download_button("Descargar reporte Excel", archivo.getvalue(), "chocope_pagos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            eleg = st.selectbox("Revisar pago", pagos, format_func=lambda p: f"{etiqueta(p)} · {_dinero(p.get('monto'))} · {p.get('estado')} · {p.get('numero_operacion')}")
            st.write("Operación:", eleg.get("numero_operacion"), "— Fecha:", eleg.get("fecha_pago"))
            ruta = eleg.get("comprobante_ruta")
            if ruta and st.button("Abrir comprobante privado"):
                try:
                    respuesta = sb.storage.from_(BUCKET).create_signed_url(ruta, 60)
                    enlace = respuesta.get("signedURL") or respuesta.get("signedUrl")
                    if enlace:
                        st.link_button("Ver comprobante (válido 60 segundos)", enlace)
                    else:
                        st.warning("No se pudo generar el enlace.")
                except Exception:
                    logger.exception("Error abriendo comprobante")
                    st.error("No se pudo acceder al comprobante.")
            if eleg.get("estado") == "aprobado":
                st.info("Este pago ya está aprobado. No se permite modificarlo desde este formulario.")
            else:
                with st.form("revisar_pago"):
                    estado = st.selectbox("Decisión", ["aprobado", "observado", "rechazado"])
                    nota = st.text_area("Observación", max_chars=500)
                    confirmar = st.checkbox("He comprobado el ingreso real en Yape (obligatorio para aprobar)")
                    if st.form_submit_button("Guardar revisión", type="primary"):
                        if estado == "aprobado" and not confirmar:
                            st.error("Antes de aprobar, verifica el ingreso real en Yape.")
                        else:
                            try:
                                sb.rpc("revisar_pago_yape", {"p_pago": eleg["id"], "p_estado": estado, "p_observacion": nota.strip()}).execute()
                                st.success("Revisión guardada.")
                                st.rerun()
                            except Exception as error:
                                _error_admin(error, "revisar pago")
    with tab2:
        st.subheader("Registrar alumno")
        with st.form("crear_alumno"):
            nombre = st.text_input("Nombre del alumno")
            categoria = st.selectbox("Categoría", ["Niños", "Pre infantil", "Juvenil", "Entrenamiento personalizado"])
            if st.form_submit_button("Guardar alumno"):
                if not nombre.strip():
                    st.warning("Ingresa el nombre del alumno.")
                else:
                    try:
                        respuesta = sb.table("alumnos").insert({"nombre": nombre.strip(), "categoria": categoria}).execute()
                        if not respuesta.data:
                            st.warning("Supabase no devolvió el alumno creado. Comprueba la tabla antes de reintentar para evitar duplicados.")
                            st.stop()
                        st.success("Alumno registrado.")
                        st.rerun()
                    except Exception as error:
                        _error_admin(error, "registrar alumno")
        st.subheader("Vincular apoderado")
        st.caption("El apoderado debe crear y confirmar su cuenta. Copia su UUID desde Supabase → Authentication → Users.")
        try:
            alumnos_lista = _filas(sb.table("alumnos").select("id,nombre").order("nombre").execute())
        except Exception:
            logger.exception("Error consultando alumnos")
            alumnos_lista = []
        if alumnos_lista:
            with st.form("vincular_apoderado"):
                alumno = st.selectbox("Alumno", alumnos_lista, format_func=lambda a: a["nombre"])
                apoderado_id = st.text_input("UUID del apoderado")
                if st.form_submit_button("Vincular"):
                    try:
                        uid = str(uuid.UUID(apoderado_id.strip()))
                        sb.table("alumno_apoderado").insert({"alumno_id": alumno["id"], "apoderado_id": uid}).execute()
                        st.success("Apoderado vinculado.")
                        st.rerun()
                    except ValueError:
                        st.error("El UUID ingresado no es válido.")
                    except Exception as error:
                        _error_admin(error, "vincular apoderado")
    with tab3:
        st.subheader("Asignar mensualidad")
        try:
            alumnos_lista = _filas(sb.table("alumnos").select("id,nombre").order("nombre").execute())
        except Exception:
            logger.exception("Error consultando alumnos para mensualidad")
            alumnos_lista = []
        if not alumnos_lista:
            st.info("Registra primero un alumno.")
        else:
            with st.form("crear_cuota"):
                alumno = st.selectbox("Alumno", alumnos_lista, format_func=lambda a: a["nombre"])
                periodo = st.date_input("Mes de la mensualidad", value=date.today().replace(day=1))
                monto = st.number_input("Monto (S/)", min_value=0.01, step=1.0, format="%.2f")
                vence = st.date_input("Vencimiento")
                if st.form_submit_button("Asignar mensualidad"):
                    try:
                        sb.table("mensualidades").insert({"alumno_id": alumno["id"], "periodo": periodo.replace(day=1).isoformat(), "monto": float(monto), "vencimiento": vence.isoformat()}).execute()
                        st.success("Mensualidad asignada.")
                        st.rerun()
                    except Exception as error:
                        _error_admin(error, "asignar mensualidad")
