-- Ejecutar DESPUÉS de crear las cinco tablas y asignar el primer administrador.
-- No elimina tablas ni datos. Ejecutar una sola vez en chocope-gestion.
BEGIN;

-- Perfil automático, siempre como apoderado, sin aceptar rol del usuario.
CREATE OR REPLACE FUNCTION public.chocope_crear_perfil()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $fn$
BEGIN
  INSERT INTO public.perfiles(id,nombre,rol)
  VALUES(NEW.id, COALESCE(LEFT(NEW.raw_user_meta_data->>'nombre',120),''),'apoderado')
  ON CONFLICT(id) DO NOTHING;
  RETURN NEW;
END;
$fn$;

-- El nombre del trigger es propio del proyecto. Si ya existe, no lo duplica.
DO $block$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='chocope_auth_perfil' AND tgrelid='auth.users'::regclass) THEN
   CREATE TRIGGER chocope_auth_perfil AFTER INSERT ON auth.users
   FOR EACH ROW EXECUTE FUNCTION public.chocope_crear_perfil();
 END IF;
END;
$block$;

-- Funciones ya creadas en el paso anterior, se aseguran sin cambiar roles.
CREATE OR REPLACE FUNCTION public.es_administrador()
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $fn$
 SELECT EXISTS(SELECT 1 FROM public.perfiles WHERE id=auth.uid() AND rol='administrador');
$fn$;
CREATE OR REPLACE FUNCTION public.es_apoderado_de(p_alumno uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $fn$
 SELECT EXISTS(SELECT 1 FROM public.alumno_apoderado WHERE alumno_id=p_alumno AND apoderado_id=auth.uid());
$fn$;

REVOKE ALL ON FUNCTION public.es_administrador() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.es_apoderado_de(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.es_administrador() TO authenticated;
GRANT EXECUTE ON FUNCTION public.es_apoderado_de(uuid) TO authenticated;

-- Crear políticas faltantes, sin tocar las existentes.
DO $block$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='perfiles' AND policyname='perfiles_ver') THEN
  CREATE POLICY perfiles_ver ON public.perfiles FOR SELECT TO authenticated
   USING(id=auth.uid() OR (SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alumnos' AND policyname='alumnos_ver') THEN
  CREATE POLICY alumnos_ver ON public.alumnos FOR SELECT TO authenticated
   USING((SELECT public.es_administrador()) OR public.es_apoderado_de(id));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alumnos' AND policyname='alumnos_admin_insertar') THEN
  CREATE POLICY alumnos_admin_insertar ON public.alumnos FOR INSERT TO authenticated WITH CHECK((SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alumnos' AND policyname='alumnos_admin_actualizar') THEN
  CREATE POLICY alumnos_admin_actualizar ON public.alumnos FOR UPDATE TO authenticated
   USING((SELECT public.es_administrador())) WITH CHECK((SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alumno_apoderado' AND policyname='relaciones_ver') THEN
  CREATE POLICY relaciones_ver ON public.alumno_apoderado FOR SELECT TO authenticated
   USING(apoderado_id=auth.uid() OR (SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alumno_apoderado' AND policyname='relaciones_admin_insertar') THEN
  CREATE POLICY relaciones_admin_insertar ON public.alumno_apoderado FOR INSERT TO authenticated
   WITH CHECK((SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='mensualidades' AND policyname='mensualidades_ver') THEN
  CREATE POLICY mensualidades_ver ON public.mensualidades FOR SELECT TO authenticated
   USING((SELECT public.es_administrador()) OR public.es_apoderado_de(alumno_id));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='mensualidades' AND policyname='mensualidades_admin_insertar') THEN
  CREATE POLICY mensualidades_admin_insertar ON public.mensualidades FOR INSERT TO authenticated
   WITH CHECK((SELECT public.es_administrador()));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='pagos' AND policyname='pagos_ver') THEN
  CREATE POLICY pagos_ver ON public.pagos FOR SELECT TO authenticated
   USING((SELECT public.es_administrador()) OR registrado_por=auth.uid());
 END IF;
END;
$block$;

-- Asegurar que NO haya escrituras directas a pagos desde el cliente.
REVOKE INSERT, UPDATE, DELETE ON public.pagos FROM anon, authenticated;
REVOKE UPDATE, DELETE ON public.perfiles FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.alumno_apoderado FROM anon;

-- Función transaccional: verifica cuota, relación, monto y ruta del comprobante.
CREATE OR REPLACE FUNCTION public.registrar_pago_yape(
 p_mensualidad uuid, p_operacion text, p_fecha date, p_ruta text
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $fn$
DECLARE
 v_monto numeric(10,2);
 v_alumno uuid;
 v_id uuid;
BEGIN
 IF auth.uid() IS NULL THEN RAISE EXCEPTION 'Sesión requerida'; END IF;
 IF p_operacion IS NULL OR length(trim(p_operacion)) < 4 OR length(p_operacion)>70 THEN
   RAISE EXCEPTION 'Número de operación inválido';
 END IF;
 IF p_fecha IS NULL OR p_fecha > current_date OR p_fecha < current_date - 365 THEN
   RAISE EXCEPTION 'Fecha inválida';
 END IF;
 IF p_ruta IS NULL OR p_ruta NOT LIKE auth.uid()::text || '/%' OR length(p_ruta)>250 THEN
   RAISE EXCEPTION 'Ruta del comprobante inválida';
 END IF;
 IF NOT EXISTS (SELECT 1 FROM storage.objects WHERE bucket_id='comprobantes-yape' AND name=p_ruta AND owner_id=auth.uid()::text) THEN
   RAISE EXCEPTION 'No se encontró el comprobante';
 END IF;
 SELECT m.monto, m.alumno_id INTO v_monto, v_alumno
 FROM public.mensualidades m WHERE m.id=p_mensualidad;
 IF NOT FOUND OR NOT public.es_apoderado_de(v_alumno) THEN
   RAISE EXCEPTION 'Mensualidad no autorizada';
 END IF;
 IF EXISTS(SELECT 1 FROM public.pagos WHERE mensualidad_id=p_mensualidad AND estado IN ('pendiente','aprobado')) THEN
   RAISE EXCEPTION 'La mensualidad ya tiene un pago pendiente o aprobado';
 END IF;
 INSERT INTO public.pagos(mensualidad_id,registrado_por,monto,numero_operacion,fecha_pago,comprobante_ruta,estado)
 VALUES(p_mensualidad,auth.uid(),v_monto,trim(p_operacion),p_fecha,p_ruta,'pendiente') RETURNING id INTO v_id;
 RETURN v_id;
END;
$fn$;

CREATE OR REPLACE FUNCTION public.revisar_pago_yape(
 p_pago uuid, p_estado text, p_observacion text DEFAULT ''
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $fn$
BEGIN
 IF NOT public.es_administrador() THEN RAISE EXCEPTION 'Acceso denegado'; END IF;
 IF p_estado NOT IN ('aprobado','observado','rechazado') THEN RAISE EXCEPTION 'Estado inválido'; END IF;
 IF length(COALESCE(p_observacion,''))>500 THEN RAISE EXCEPTION 'Observación demasiado larga'; END IF;
 UPDATE public.pagos SET estado=p_estado, observacion=COALESCE(p_observacion,''),
   revisado_por=auth.uid(), revisado_en=now()
 WHERE id=p_pago AND estado IN ('pendiente','observado');
 IF NOT FOUND THEN RAISE EXCEPTION 'Pago no encontrado o ya resuelto'; END IF;
END;
$fn$;

REVOKE ALL ON FUNCTION public.registrar_pago_yape(uuid,text,date,text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.revisar_pago_yape(uuid,text,text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.registrar_pago_yape(uuid,text,date,text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.revisar_pago_yape(uuid,text,text) TO authenticated;

-- Storage privado. El cliente solo sube dentro de su carpeta UUID.
INSERT INTO storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
VALUES('comprobantes-yape','comprobantes-yape',false,4194304,ARRAY['image/jpeg','image/png','application/pdf'])
ON CONFLICT(id) DO UPDATE SET public=false,file_size_limit=4194304,allowed_mime_types=EXCLUDED.allowed_mime_types;

DO $block$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='chocope_comprobantes_subir') THEN
  CREATE POLICY chocope_comprobantes_subir ON storage.objects FOR INSERT TO authenticated
   WITH CHECK(bucket_id='comprobantes-yape' AND (storage.foldername(name))[1]=auth.uid()::text);
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='chocope_comprobantes_ver') THEN
  CREATE POLICY chocope_comprobantes_ver ON storage.objects FOR SELECT TO authenticated
   USING(bucket_id='comprobantes-yape' AND ((storage.foldername(name))[1]=auth.uid()::text OR (SELECT public.es_administrador())));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='chocope_comprobantes_borrar_propios') THEN
  CREATE POLICY chocope_comprobantes_borrar_propios ON storage.objects FOR DELETE TO authenticated
   USING(bucket_id='comprobantes-yape' AND (storage.foldername(name))[1]=auth.uid()::text);
 END IF;
END;
$block$;
COMMIT;
