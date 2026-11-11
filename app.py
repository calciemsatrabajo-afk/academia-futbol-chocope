import base64
import html
from pathlib import Path
from urllib.parse import quote
import streamlit as st
from config import ACADEMIA, WHATSAPP, TIKTOK, YOUTUBE, DIRECCION, HORARIOS

ROOT = Path(__file__).parent
st.set_page_config(page_title='Academia Fútbol Chocope | Formando grandes talentos', page_icon='⚽', layout='wide', initial_sidebar_state='collapsed')
def image(name):
    path = ROOT/'assets'/name
    if not path.exists(): return ''
    return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode()
def esc(s): return html.escape(str(s), quote=True)
def wa(msg): return f'https://wa.me/{WHATSAPP}?text={quote(msg)}'
reg = wa('Hola, quiero registrarme en la Academia Fútbol Chocope. Deseo información sobre categorías, horarios, costos y requisitos de inscripción.')
logo = image('escudo.jpeg')
photos = [image('foto_0%d.jpg'%i) for i in range(1,6)]
hero = image('portada.jpg')
css = (ROOT/'styles.css').read_text(encoding='utf-8')
st.markdown('<style>'+css+'</style>', unsafe_allow_html=True)
nav = f'''<header class="top"><div class="wrap nav"><a href="#inicio" class="brand"><img src="{logo}" alt="Escudo"><span>ACADEMIA DE FÚTBOL <b>CHOCOPE</b></span></a><nav class="navlinks"><a href="#inicio">Inicio</a><a href="#nosotros">Nosotros</a><a href="#programas">Programas</a><a href="#cursos">Cursos</a><a href="#galeria">Galería</a><a href="#pagos">Yape</a><a href="?vista=registrar_pago">Registrar pago</a><a href="?vista=administracion">Administración</a><a href="#contacto">Contacto</a></nav><div class="nav-actions"><a class="join" href="{reg}" target="_blank">INSCRÍBETE ↗</a></div></div></header>'''
from pagos import mostrar_registro, mostrar_administracion
vista = st.query_params.get("vista", "inicio")
if vista == "registrar_pago":
    mostrar_registro()
elif vista == "administracion":
    mostrar_administracion()
else:
    st.markdown(nav, unsafe_allow_html=True)
    st.markdown(f'''<section id="inicio" class="hero" style="--photo:url('{hero}')"><div class="wrap hero-grid"><div class="hero-text"><span class="eyebrow">ACADEMIA DE FÚTBOL · CHOCOPE</span><h1>FORMANDO<br><span>GRANDES TALENTOS</span></h1><h3>DISCIPLINA <i>•</i> TRABAJO <i>•</i> VALORES <i>•</i> FUTURO</h3><p>Formamos niños y jóvenes con pasión por el fútbol, promoviendo su desarrollo deportivo, personal y social. Un lugar donde el talento se descubre y se fortalece.</p><a class="btn green" href="{reg}" target="_blank">QUIERO INSCRIBIRME <span>↗</span></a><a class="btn ghost" href="#nosotros">CONOCE MÁS ↓</a></div></div></section>''', unsafe_allow_html=True)
    st.markdown('''<section class="benefits"><div class="wrap benefit-grid"><div><span>⚽</span><b>Entrenadores<br>comprometidos</b></div><div><span>♧</span><b>Formación integral<br>del jugador</b></div><div><span>🏆</span><b>Competencias<br>y torneos</b></div><div><span>♢</span><b>Disciplina<br>y valores</b></div><div><span>☆</span><b>Desarrollo<br>de talento</b></div></div></section>''', unsafe_allow_html=True)
    st.markdown(f'''<section class="white-section" id="nosotros"><div class="wrap about-grid"><div class="about-copy"><span class="overline">— SOBRE NOSOTROS</span><h2>Nuestra Academia</h2><p><b>Somos una academia comprometida con la formación de niños y jóvenes en Chocope.</b> Impulsamos el aprendizaje del fútbol con un enfoque en la técnica, la disciplina y los valores, para que cada jugador desarrolle su máximo potencial dentro y fuera de la cancha.</p><a class="btn green" href="#programas">NUESTROS PROGRAMAS ↗</a></div><div class="about-image"><img src="{photos[0]}" alt="Academia de fútbol en entrenamiento"><span>EL FÚTBOL<br>TAMBIÉN EDUCA.</span></div></div></section>''', unsafe_allow_html=True)
    categories=[('NIÑOS','6 – 9 años',photos[1]),('PRE INFANTIL','10 – 12 años',photos[2]),('JUVENIL','13 – 16 años',photos[3]),('ENTRENAMIENTO PERSONALIZADO','Sesiones adaptadas a cada jugador',photos[4])]
    items=''.join(f'''<article class="cat-card"><img src="{p}" alt="Categoría {esc(n)}"><div class="cat-body"><div class="cat-title"><span>⚽</span><div><h3>{n}</h3><small>{age}</small></div></div><a href="{wa('Hola, quiero información sobre la categoría '+n+' de la Academia Fútbol Chocope.') }" target="_blank">CONSULTAR ↗</a></div></article>''' for n,age,p in categories)
    st.markdown(f'''<section id="programas" class="programs" style="--photo:url('{hero}')"><div class="wrap"><div class="center-heading"><span>— NUESTROS PROGRAMAS —</span><h2>Categorías y Entrenamiento Personalizado</h2><p>Formación por etapas y entrenamiento personalizado. Edades referenciales sujetas a confirmación.</p></div><div class="categories">{items}</div></div></section>''', unsafe_allow_html=True)
    st.markdown(f'''<section id="cursos" class="white-section"><div class="wrap"><div class="section-heading"><span class="overline">— ENTRENAMIENTO A TU MEDIDA</span><h2>Desarrolla tu mejor versión</h2><p>Entrenamiento personalizado, formación técnica y preparación competitiva para cada etapa.</p></div><div class="course-grid"><article class="course"><img src="{photos[0]}"><div><span>01 / FUNDAMENTOS</span><h3>Entrenamiento personalizado</h3><p>Sesiones adaptadas al nivel, objetivos y ritmo de cada jugador: técnica, control y dominio del balón.</p><a href="{reg}" target="_blank">SOLICITAR INFORMACIÓN ↗</a></div></article><article class="course"><img src="{photos[2]}"><div><span>02 / RENDIMIENTO</span><h3>Preparación física</h3><p>Coordinación, agilidad y desarrollo según la edad.</p><a href="{reg}" target="_blank">SOLICITAR INFORMACIÓN ↗</a></div></article><article class="course"><img src="{photos[3]}"><div><span>03 / EQUIPO</span><h3>Formación competitiva</h3><p>Juego colectivo, toma de decisiones y torneos.</p><a href="{reg}" target="_blank">SOLICITAR INFORMACIÓN ↗</a></div></article></div></div></section>''', unsafe_allow_html=True)
    gallery=''.join(f'<img loading="lazy" src="{p}" alt="Fotografía de Academia Fútbol Chocope">' for p in photos)
    st.markdown(f'''<section id="galeria" class="gallery-section"><div class="wrap"><div class="section-heading"><span class="overline">— NUESTRA COMUNIDAD</span><h2>Momentos que nos unen</h2><p>Entrenamientos, compañerismo y pasión por el fútbol.</p></div><div class="gallery-grid">{gallery}</div></div></section>''', unsafe_allow_html=True)
    st.markdown(f'''<section class="social-band"><div class="wrap social-inner"><div><span>CONÉCTATE CON LA ACADEMIA</span><h2>Vive el fútbol con nosotros.</h2></div><div class="social-buttons"><a href="{esc(TIKTOK)}" target="_blank">TIKTOK ↗</a><a href="{esc(YOUTUBE)}" target="_blank">YOUTUBE ↗</a><a href="{reg}" target="_blank">WHATSAPP ↗</a></div></div></section>''', unsafe_allow_html=True)
    # Pagos Yape: el QR proviene de la imagen proporcionada por la academia.
    # Sin base de datos ni integración bancaria, la validación es MANUAL.
    yape_img = image('yape_qr.png')
    yape_consulta = wa('Hola, Academia Fútbol Chocope. Quiero reportar un pago por Yape. Indicaré el nombre del alumno, concepto, monto, fecha y número de operación; adjuntaré mi comprobante para su verificación.')
    st.markdown(f'''<section id="pagos" class="yape-section"><div class="wrap"><div class="center-heading"><span>— PAGOS DE LA ACADEMIA —</span><h2>Paga fácilmente con Yape</h2><p>Escanea el código QR oficial y comunica tu pago para su validación.</p></div><div class="yape-layout"><div class="yape-qr-card"><img src="{yape_img}" alt="Código QR Yape de Isaac Joel Vasquez Zambrano"><p><strong>Titular:</strong> Isaac Joel Vasquez Zambrano</p><span>Verifica que el titular coincida antes de pagar.</span></div><div class="yape-steps"><span class="overline">— PASO A PASO</span><h3>Registra tu mensualidad</h3><ol><li>Abre Yape y escanea el QR de la academia.</li><li>Verifica el titular y realiza el pago del monto acordado.</li><li>Conserva tu comprobante o número de operación.</li><li>Ingresa a Registrar pago, completa tus datos y adjunta tu comprobante.</li></ol><a class="btn green" href="?vista=registrar_pago">REGISTRAR PAGO EN LA WEB ↗</a><p class="yape-note">Importante: reportar un pago no significa que esté aprobado. La academia verificará el ingreso en Yape antes de marcar la mensualidad como pagada. El registro quedará pendiente hasta que el administrador verifique el abono en Yape.</p></div></div></div></section>''', unsafe_allow_html=True)
    st.markdown('''<section id="contacto" class="white-section"><div class="wrap"><div class="section-heading"><span class="overline">— CONTACTO E INSCRIPCIONES</span><h2>Empieza tu historia con nosotros</h2><p>Completa los datos y envía tu consulta directamente por WhatsApp. Esta página no guarda información personal.</p></div></div></section>''', unsafe_allow_html=True)
    left,right=st.columns([1.4,1],gap='large')
    with left:
        # Formulario HTML: abre WhatsApp directamente con el texto completado.
        # No envía datos a servidores propios ni los almacena.
        import streamlit.components.v1 as components
        from string import Template
        form_html = Template(r"""
    <!doctype html><html lang="es"><head><meta charset="utf-8">
    <style>
    *{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#092336;background:transparent}
    form{padding:22px;background:#f5f8f9;border:1px solid #dce6e9;border-radius:13px}
    label{display:block;font-size:14px;font-weight:600;margin:0 0 8px}
    input,select,textarea{display:block;width:100%;padding:12px 13px;margin:0 0 18px;border:1px solid #cbd9df;border-radius:8px;background:white;font:15px Arial;color:#092336}
    textarea{min-height:95px;resize:vertical}button{width:100%;background:#08bd45;color:white;border:0;border-radius:8px;padding:15px 10px;font-size:14px;font-weight:800;cursor:pointer}
    button:hover{background:#079e3b}.hint{font-size:12px;color:#47606a;margin-top:12px;line-height:1.5}
    </style></head><body>
    <form id="inscripcion">
    <label for="nombre">Nombre del padre, madre o apoderado *</label>
    <input id="nombre" required minlength="3" autocomplete="name" placeholder="Nombre completo">
    <label for="telefono">Número de contacto *</label>
    <input id="telefono" required inputmode="tel" pattern="[0-9+ ()-]{7,18}" placeholder="Ej.: 916582419">
    <label for="categoria">Categoría de interés</label>
    <select id="categoria"><option>NIÑOS</option><option>PRE INFANTIL</option><option>JUVENIL</option><option>ENTRENAMIENTO PERSONALIZADO</option><option>Deseo orientación</option></select>
    <label for="consulta">Consulta adicional</label>
    <textarea id="consulta" placeholder="Horarios, costos, vacantes..."></textarea>
    <button type="submit">ENVIAR INSCRIPCIÓN POR WHATSAPP ↗</button>
    <div class="hint">Se abrirá WhatsApp con tus datos. Revisa el mensaje y pulsa Enviar para completar la consulta.</div>
    </form>
    <script>
    document.getElementById('inscripcion').addEventListener('submit',function(e){
     e.preventDefault();
     const nombre=document.getElementById('nombre').value.trim();
     const telefono=document.getElementById('telefono').value.trim();
     const categoria=document.getElementById('categoria').value;
     const consulta=document.getElementById('consulta').value.trim() || 'Deseo conocer horarios, costos y requisitos.';
     const mensaje='Hola, quiero registrarme en la Academia Fútbol Chocope.\nApoderado: '+nombre+'\nTeléfono: '+telefono+'\nCategoría: '+categoria+'\nConsulta: '+consulta;
     const url='https://wa.me/$phone?text='+encodeURIComponent(mensaje);
     window.open(url,'_blank','noopener,noreferrer');
    });
    </script></body></html>
    """).substitute(phone=WHATSAPP)
        components.html(form_html, height=565, scrolling=False)
    with right:
        st.markdown(f'''<div class="contact-card"><span>INFORMACIÓN OFICIAL</span><h3>¡Te esperamos en la cancha!</h3><p>Consulta los horarios, cupos y requisitos de inscripción directamente con nuestro equipo.</p><hr><b>WHATSAPP</b><p>+51 916 582 419</p><b>UBICACIÓN</b><p>{esc(DIRECCION or 'Chocope, La Libertad, Perú · sede por confirmar')}</p><b>HORARIOS</b><p>{esc(HORARIOS or 'Consultar con la academia')}</p></div>''',unsafe_allow_html=True)
    st.markdown(f'''<footer><div class="wrap foot"><div class="foot-brand"><img src="{logo}" alt="Escudo"><div><b>ACADEMIA FÚTBOL CHOCOPE</b><p>Disciplina · Trabajo · Valores · Futuro</p></div></div><div class="foot-links"><a href="#inicio">Inicio</a><a href="#programas">Programas</a><a href="{esc(TIKTOK)}" target="_blank">TikTok</a><a href="{esc(YOUTUBE)}" target="_blank">YouTube</a><a href="{reg}" target="_blank">WhatsApp</a></div></div><div class="wrap copyright">© 2026 Academia Fútbol Chocope. Todos los derechos reservados.</div></footer><a class="floating-wa" href="{reg}" target="_blank">✆ &nbsp; INSCRÍBETE POR WHATSAPP</a>''',unsafe_allow_html=True)
