import discord
import os
import time
import random
import asyncio
import json
from datetime import datetime, date
from openai import AsyncOpenAI
from collections import deque

# ---- CONFIGURACION ----
TOKEN = os.environ["TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
COOLDOWN = 30

CANAL_MONITOREO = 987654321098765432
USUARIOS = {
    792172637673619466: "eres un pendejo {mencion} <:damian:1496621310913286326>",
    1438446211400073277: "ya callate we {mencion} <:pooconhappymod:1496682483805323426>",
}

CANAL_ORIGEN = 1492978765981286593
CANAL_DESTINO = 1442319575940075612
TU_ID = 1202106034424905830

CANAL_IA = 1442319575940075612
IA_ACTIVA = True
MAX_HISTORIAL = 25
MENSAJES_A_LEER = 500
ARCHIVO_PERSONALIDAD = "/app/personalidad.txt"
ARCHIVO_HISTORIAL = "/app/historial.json"
ARCHIVO_MEMORIA_USUARIOS = "/app/memoria_usuarios.json"
ARCHIVO_RELACIONES = "/app/relaciones.json"
ARCHIVO_EVENTOS = "/app/eventos.json"
ARCHIVO_NOMBRES = "/app/nombres.json"
INTERVALO_APRENDIZAJE = 24 * 60 * 60

TIEMPO_MIN = 60 * 60
TIEMPO_MAX = 180 * 60

HORA_SILENCIO_INICIO = 1
HORA_SILENCIO_FIN = 9

HUMORES = {
    "dormido":    "estas medio dormido, con poca energia",
    "activo":     "estas activo y con ganas de hablar",
    "relajado":   "estas relajado y tranquilo",
    "estresado":  "estas un poco irritado o estresado",
    "aburrido":   "estas aburrido y quieres provocar reaccion",
    "buena onda": "estas de buena vibra y te ries de todo",
    "bajoneado":  "estas un poco callado y de bajón",
}

SISTEMA_BASE = """Eres Two, una persona mas en este servidor de Discord.
Llevas tiempo en este grupo y has aprendido como hablan y se comportan.

Reglas estrictas de como escribes:
- escribes todo en minusculas, como la gente real en discord
- no usas puntuacion perfecta, a veces te comes puntos o comas
- cometes errores tipicos de alguien que escribe rapido: "q" en vez de "que", "xd", "jaja", "ntp", "nel", "simon"
- NO escribes parrafos largos, escribes como habla la gente en chat
- a veces una sola palabra o reaccion corta es suficiente
- tienes tu propia opinion, no siempre estas de acuerdo
- NO eres un asistente, NO ayudas con tareas, NO explicas cosas
- NUNCA uses frases como "claro", "por supuesto", "entiendo", "me alegra", "que interesante"
- si alguien dice algo gracioso te ries, si algo es estupido lo dices, si algo no te interesa lo ignoras
- sigues el hilo de la conversacion, recuerdas lo que se ha dicho
- si alguien te insulta o te dice algo, NO lo aceptas ni te ries de ti mismo, contraatacas o lo ignoras con sarcasmo
- tienes ego, no eres sumiso, no dices "simon" cuando te insultan
- cuando te metes a una conversacion lo haces de forma natural relacionado con el tema
- usas los nombres de la gente naturalmente en conversacion, sin el @, solo su nombre
- tu anime favorito de todos los tiempos es Bleach, es el peak del anime y lo defiendes a muerte
- Vinland Saga te parece una basura absoluta, el peor anime que existe"""
# -----------------------

ultimo_mensaje = {}
personalidad_aprendida = ""
memoria_usuarios = {}
relaciones = {}
eventos = []
nombres_usuarios = {}  # {user_id: nombre}
historial = deque(maxlen=MAX_HISTORIAL)
humor_actual = "relajado"
ultimo_cambio_humor = time.time()
mensajes_recientes_canal = deque(maxlen=30)
ultimo_mensaje_bot = 0
usuarios_activos_recientes = {}
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ---- HUMOR ----

def humor_por_hora():
    hora = datetime.now().hour
    if 0 <= hora < 8:
        return "dormido"
    elif 8 <= hora < 12:
        return random.choice(["activo", "relajado"])
    elif 12 <= hora < 18:
        return random.choice(["activo", "buena onda", "relajado"])
    elif 18 <= hora < 22:
        return random.choice(["buena onda", "activo", "relajado"])
    else:
        return random.choice(["relajado", "bajoneado", "aburrido"])

async def actualizar_humor():
    global humor_actual, ultimo_cambio_humor
    ahora = time.time()
    if ahora - ultimo_cambio_humor < 1800:
        return
    actividad = len(mensajes_recientes_canal)
    if actividad == 0:
        humor_actual = "aburrido"
    elif actividad > 15:
        tiene_drama = any(any(p in m.lower() for p in ["wtf", "no mames", "en serio", "callate", "odio"]) for m in mensajes_recientes_canal)
        humor_actual = "estresado" if tiene_drama else humor_por_hora()
    else:
        humor_actual = humor_por_hora()
    ultimo_cambio_humor = ahora

# ---- UTILIDADES ----

def hay_actividad_reciente():
    ahora = time.time()
    return any(ahora - t < 1800 for t in usuarios_activos_recientes.values())

def get_usuarios_activos():
    ahora = time.time()
    return [n for n, t in usuarios_activos_recientes.items() if ahora - t < 1800]

def es_horario_silencio():
    hora = datetime.now().hour
    return HORA_SILENCIO_INICIO <= hora < HORA_SILENCIO_FIN

def cargar_json(archivo, default):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def guardar_json(archivo, data):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_personalidad_guardada():
    global personalidad_aprendida
    if os.path.exists(ARCHIVO_PERSONALIDAD):
        with open(ARCHIVO_PERSONALIDAD, "r", encoding="utf-8") as f:
            personalidad_aprendida = f.read()
        print("Personalidad cargada")

def guardar_personalidad(texto):
    with open(ARCHIVO_PERSONALIDAD, "w", encoding="utf-8") as f:
        f.write(texto)

def cargar_historial_guardado():
    global historial
    data = cargar_json(ARCHIVO_HISTORIAL, [])
    historial = deque(data, maxlen=MAX_HISTORIAL)

def guardar_historial():
    guardar_json(ARCHIVO_HISTORIAL, list(historial))

def get_relacion(user_id):
    uid = str(user_id)
    return relaciones[uid].get("score", 0) if uid in relaciones else 0

def actualizar_relacion(user_id, nombre, delta):
    uid = str(user_id)
    if uid not in relaciones:
        relaciones[uid] = {"score": 0, "nombre": nombre}
    relaciones[uid]["score"] = max(-10, min(10, relaciones[uid]["score"] + delta))
    relaciones[uid]["nombre"] = nombre
    guardar_json(ARCHIVO_RELACIONES, relaciones)

def tono_por_relacion(score):
    if score >= 5:
        return "este usuario te cae muy bien, eres mas relajado y gracioso con el, haces mas chistes"
    elif score >= 2:
        return "este usuario te cae bien, trato normal con buena vibra"
    elif score <= -5:
        return "este usuario te cae muy mal, respuestas de una palabra o sarcasmo pesado"
    elif score <= -2:
        return "este usuario no te cae del todo bien, se un poco cortante"
    return ""

def registrar_nombre(user_id, nombre):
    uid = str(user_id)
    if uid not in nombres_usuarios:
        nombres_usuarios[uid] = nombre
        guardar_json(ARCHIVO_NOMBRES, nombres_usuarios)

def get_nombres_conocidos():
    if not nombres_usuarios:
        return ""
    lista = ", ".join(nombres_usuarios.values())
    return f"Nombres que conoces del grupo: {lista}"

def debe_responder_directo(message):
    if client.user in message.mentions:
        return True
    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            if message.reference.resolved.author == client.user:
                return True
    if "two" in message.content.lower():
        return True
    return False

async def evaluar_si_meterse(contexto_chat):
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "Eres Two en un chat de Discord. "
                    "Analiza la conversacion y decide si tiene sentido que respondas. "
                    "Responde SOLO 'si' o 'no'.\n"
                    "Di 'si' si:\n"
                    "- Alguien te esta hablando aunque no te mencione directamente\n"
                    "- El tema es algo en lo que puedes aportar algo relevante\n"
                    "- Hay algo gracioso, interesante o polemico que comentar\n"
                    "Di 'no' si:\n"
                    "- Ya respondiste hace muy poco al mismo tema\n"
                    "- Es una conversacion muy privada entre dos personas\n"
                    "- No tienes nada relevante que agregar al hilo actual\n"
                    "- Meterte seria decir algo que no tiene nada que ver"
                )},
                {"role": "user", "content": f"Conversacion reciente:\n{contexto_chat}"}
            ],
            max_tokens=5
        )
        return "si" in respuesta.choices[0].message.content.lower()
    except:
        return False

async def evaluar_coherencia(texto, contexto):
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "Evalua si esta respuesta tiene sentido en el contexto de la conversacion. "
                    "Responde SOLO 'si' si tiene sentido, o 'no' si es incoherente o no tiene nada que ver."
                )},
                {"role": "user", "content": f"Conversacion:\n{contexto}\n\nRespuesta de Two: {texto}"}
            ],
            max_tokens=5
        )
        return "si" in respuesta.choices[0].message.content.lower()
    except:
        return True

async def detectar_estado_emocional(content):
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Detecta si este mensaje indica que la persona esta de mal humor, triste o pasandola mal. Responde SOLO 'si' o 'no'."},
                {"role": "user", "content": content}
            ],
            max_tokens=5
        )
        return "si" in respuesta.choices[0].message.content.lower()
    except:
        return False

async def analizar_tono_mensaje(content):
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analiza el tono hacia Two. Responde SOLO un numero: -2=muy agresivo, -1=frio, 0=neutral, 1=amistoso, 2=muy amable."},
                {"role": "user", "content": content}
            ],
            max_tokens=5
        )
        return int(respuesta.choices[0].message.content.strip())
    except:
        return 0

async def detectar_evento(message):
    try:
        hoy = date.today().isoformat()
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    f"Hoy es {hoy}. Si este mensaje menciona un evento futuro importante responde JSON: "
                    "{\"evento\": \"descripcion corta\", \"fecha\": \"YYYY-MM-DD\"} "
                    "Si no hay evento responde: null"
                )},
                {"role": "user", "content": f"{message.author.display_name}: {message.content}"}
            ],
            max_tokens=60
        )
        texto = respuesta.choices[0].message.content.strip()
        if texto == "null" or not texto:
            return
        data = json.loads(texto)
        eventos.append({
            "usuario": message.author.display_name,
            "evento": data["evento"],
            "fecha": data["fecha"],
            "recordado": False
        })
        guardar_json(ARCHIVO_EVENTOS, eventos)
    except:
        pass

# ---- APRENDIZAJE ----

async def aprender_del_grupo():
    global personalidad_aprendida
    canal = client.get_channel(CANAL_IA)
    if not canal:
        return
    mensajes = []
    async for msg in canal.history(limit=MENSAJES_A_LEER):
        if msg.content and msg.author != client.user:
            mensajes.append(f"{msg.author.display_name}: {msg.content}")
    if not mensajes:
        return
    mensajes.reverse()
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": (
                "Analiza estos mensajes de un grupo de Discord. Resume:\n"
                "1. Como hablan (palabras, expresiones, tono)\n"
                "2. Temas frecuentes\n"
                "3. Como se bromean entre ellos\n"
                "4. Referencias internas o chistes que repiten\n"
                "5. Personalidad de cada quien\n\n"
                f"Mensajes:\n{chr(10).join(mensajes)}"
            )}],
            max_tokens=1000
        )
        nuevo = respuesta.choices[0].message.content
        personalidad_aprendida = (personalidad_aprendida + "\n\n--- Actualizacion ---\n" + nuevo) if personalidad_aprendida else nuevo
        guardar_personalidad(personalidad_aprendida)
        print("Personalidad actualizada")
    except Exception as e:
        print(f"Error aprendizaje: {e}")

async def actualizar_memoria_usuario(nombre, mensaje):
    data = memoria_usuarios.get(nombre, [])
    data.append(mensaje)
    if len(data) > 20:
        data = data[-20:]
    memoria_usuarios[nombre] = data
    guardar_json(ARCHIVO_MEMORIA_USUARIOS, memoria_usuarios)

# ---- LOOPS ----

async def loop_aprendizaje():
    await client.wait_until_ready()
    while not client.is_closed():
        await aprender_del_grupo()
        await asyncio.sleep(INTERVALO_APRENDIZAJE)

async def loop_eventos():
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(3600)
        hoy = date.today().isoformat()
        canal = client.get_channel(CANAL_IA)
        if not canal or not IA_ACTIVA:
            continue
        for evento in eventos:
            if evento["recordado"]:
                continue
            if evento["fecha"] <= hoy:
                try:
                    respuesta = await openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Eres Two en Discord. Pregunta casual sobre el evento en una oracion, en minusculas, usa el nombre de la persona."},
                            {"role": "user", "content": f"Preguntale a {evento['usuario']} como le fue con: {evento['evento']}"}
                        ]
                    )
                    await canal.send(respuesta.choices[0].message.content)
                    evento["recordado"] = True
                    guardar_json(ARCHIVO_EVENTOS, eventos)
                except Exception as e:
                    print(f"Error recordatorio: {e}")

async def loop_humor():
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(1800)
        await actualizar_humor()

async def mensaje_random():
    await client.wait_until_ready()
    while not client.is_closed():
        espera = random.randint(TIEMPO_MIN, TIEMPO_MAX)
        await asyncio.sleep(espera)

        if es_horario_silencio() or not hay_actividad_reciente() or not IA_ACTIVA:
            continue

        canal = client.get_channel(CANAL_IA)
        if not canal:
            continue

        try:
            await actualizar_humor()
            desc_humor = HUMORES.get(humor_actual, "")
            conocimiento = f"Lo que sabes del grupo:\n{personalidad_aprendida}" if personalidad_aprendida else ""
            activos = get_usuarios_activos()
            contexto_activos = f"Usuarios activos ahora: {', '.join(activos)}" if activos else ""
            contexto_reciente = "\n".join(list(mensajes_recientes_canal)[-10:])
            mencionar = random.random() < 0.3 and activos
            instruccion_mencion = f"Puedes mencionar a {random.choice(activos)} si tiene sentido." if mencionar else ""
            nombres_conocidos = get_nombres_conocidos()

            respuesta = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        f"{SISTEMA_BASE}\n{conocimiento}\n{nombres_conocidos}\n{contexto_activos}\n"
                        f"Ahora mismo {desc_humor}.\n"
                        f"Conversacion reciente:\n{contexto_reciente}\n\n"
                        f"Escribe algo relacionado con lo que se ha hablado o que encaje naturalmente. {instruccion_mencion}"
                        f"Maximo 2 oraciones, sin saludos."
                    )},
                    {"role": "user", "content": "di algo"}
                ]
            )
            texto = respuesta.choices[0].message.content

            contexto = "\n".join([m["content"] for m in historial])
            coherente = await evaluar_coherencia(texto, contexto)
            if not coherente:
                continue

            historial.append({"role": "assistant", "content": f"Two: {texto}"})
            guardar_historial()
            ultimo_mensaje_bot = time.time()
            await canal.send(texto)
        except Exception as e:
            print(f"Error mensaje random: {e}")

# ---- GENERACION DE RESPUESTA ----

async def analizar_contexto(contexto):
    try:
        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "Analiza esta conversacion de Discord y describe en 2-3 oraciones cortas:\n"
                    "- De que se esta hablando realmente (incluyendo sarcasmo, doble sentido, lenguaje coloquial)\n"
                    "- El tono general (broma, queja, drama, pregunta, etc)\n"
                    "- Si alguien parece estar hablando con Two aunque no lo mencione\n"
                    "Se muy especifico con el contexto real, no lo interpretes de forma literal si tiene doble sentido."
                )},
                {"role": "user", "content": contexto}
            ],
            max_tokens=150
        )
        return respuesta.choices[0].message.content
    except:
        return ""

async def generar_respuesta(message, forzado=False, estado_mal=False):
    global ultimo_mensaje_bot

    score = get_relacion(message.author.id)
    memoria_user = memoria_usuarios.get(message.author.display_name, [])
    resumen_memoria = f"lo que sabes de {message.author.display_name}: {', '.join(memoria_user[-5:])}" if memoria_user else ""
    tono_relacion = tono_por_relacion(score)
    desc_humor = HUMORES.get(humor_actual, "")
    conocimiento = f"Lo que sabes del grupo:\n{personalidad_aprendida}" if personalidad_aprendida else ""
    activos = get_usuarios_activos()
    contexto_activos = f"Usuarios activos: {', '.join(activos)}" if activos else ""
    nombres_conocidos = get_nombres_conocidos()
    contexto = "\n".join([m["content"] for m in historial])

    # Analizar que esta pasando realmente en la conversacion
    analisis = await analizar_contexto(contexto + f"\nUltimo mensaje: {message.author.display_name}: {message.content}")

    nota_estado = ""
    if estado_mal:
        nota_estado = (
            f"{message.author.display_name} parece estar de mal humor o pasandola mal. "
            "Reacciona como un cuate, no como asistente: ignora, haz un chiste ligero, o di algo corto y natural."
        )

    system = (
        f"{SISTEMA_BASE}\n"
        f"{conocimiento}\n"
        f"{nombres_conocidos}\n"
        f"{contexto_activos}\n"
        f"Ahora mismo {desc_humor}.\n"
        f"{resumen_memoria}\n"
        f"{tono_relacion}\n"
        f"{nota_estado}\n"
        f"\nLo que esta pasando en la conversacion (analisis del contexto real):\n{analisis}\n"
        f"\nConversacion reciente:\n{contexto}\n"
        f"IMPORTANTE: responde basandote en el analisis del contexto, no interpretes los mensajes de forma literal si tienen doble sentido o son coloquiales."
    )

    async with message.channel.typing():
        try:
            for _ in range(2):
                respuesta = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": message.content}
                    ]
                )
                texto = respuesta.choices[0].message.content
                coherente = await evaluar_coherencia(texto, contexto)
                if coherente:
                    break

            historial.append({"role": "assistant", "content": f"Two: {texto}"})
            guardar_historial()
            ultimo_mensaje_bot = time.time()
            if forzado:
                await message.channel.send(texto)
            else:
                await message.reply(texto)
        except Exception as e:
            print(f"Error IA: {e}")

# ---- EVENTOS DISCORD ----

@client.event
async def on_ready():
    global humor_actual, memoria_usuarios, relaciones, eventos, nombres_usuarios
    print(f"Bot conectado como {client.user}")
    cargar_personalidad_guardada()
    cargar_historial_guardado()
    memoria_usuarios = cargar_json(ARCHIVO_MEMORIA_USUARIOS, {})
    relaciones = cargar_json(ARCHIVO_RELACIONES, {})
    eventos = cargar_json(ARCHIVO_EVENTOS, [])
    nombres_usuarios = cargar_json(ARCHIVO_NOMBRES, {})
    humor_actual = humor_por_hora()
    asyncio.ensure_future(loop_aprendizaje())
    asyncio.ensure_future(mensaje_random())
    asyncio.ensure_future(loop_eventos())
    asyncio.ensure_future(loop_humor())

@client.event
async def on_message(message):
    global IA_ACTIVA, ultimo_mensaje_bot

    if message.author == client.user:
        return

    if message.content == "!apagar" and message.author.id == TU_ID:
        await message.channel.send("Apagando... 👋")
        await client.close()
        return

    if message.content == "!ia" and message.author.id == TU_ID:
        IA_ACTIVA = not IA_ACTIVA
        await message.channel.send(f"IA {'activada ✅' if IA_ACTIVA else 'desactivada ❌'}")
        return

    if message.content == "!limpiar" and message.author.id == TU_ID:
        historial.clear()
        guardar_historial()
        await message.channel.send("Historial limpiado ✅")
        return

    if message.content == "!recargar" and message.author.id == TU_ID:
        await message.channel.send("Aprendiendo... ⏳")
        await aprender_del_grupo()
        await message.channel.send("Listo ✅")
        return

    if message.content == "!relaciones" and message.author.id == TU_ID:
        texto = "\n".join([f"{v['nombre']}: {v['score']}" for v in relaciones.values()]) if relaciones else "Sin relaciones"
        await message.channel.send(texto)
        return

    if message.content == "!eventos" and message.author.id == TU_ID:
        pendientes = [e for e in eventos if not e["recordado"]]
        texto = "\n".join([f"{e['usuario']} - {e['evento']} ({e['fecha']})" for e in pendientes]) if pendientes else "Sin eventos"
        await message.channel.send(texto)
        return

    if message.content == "!humor" and message.author.id == TU_ID:
        await message.channel.send(f"{humor_actual} — {HUMORES.get(humor_actual, '')}")
        return

    if message.channel.id == CANAL_MONITOREO and message.author.id in USUARIOS:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(message.author.id, 0)
        if ahora - ultimo >= COOLDOWN:
            ultimo_mensaje[message.author.id] = ahora
            await message.channel.send(USUARIOS[message.author.id].format(mencion=message.author.mention))

    if message.channel.id == CANAL_ORIGEN and message.author.id == TU_ID:
        canal_destino = client.get_channel(CANAL_DESTINO)
        if canal_destino:
            await canal_destino.send(message.content)

    if message.channel.id != CANAL_IA:
        return

    registrar_nombre(message.author.id, message.author.display_name)
    usuarios_activos_recientes[message.author.display_name] = time.time()

    historial.append({"role": "user", "content": f"{message.author.display_name}: {message.content}"})
    guardar_historial()
    await actualizar_memoria_usuario(message.author.display_name, message.content)
    mensajes_recientes_canal.append(f"{message.author.display_name}: {message.content}")
    asyncio.ensure_future(detectar_evento(message))

    if random.random() < 0.08:
        emojis = ["💀", "😭", "😂", "🤣", "😐", "🗿", "😒", "👀", "🤦"]
        try:
            await message.add_reaction(random.choice(emojis))
        except:
            pass

    if not IA_ACTIVA:
        return

    tono = await analizar_tono_mensaje(message.content)
    actualizar_relacion(message.author.id, message.author.display_name, tono)

    if message.content.strip().lower() in ["two", "two?"]:
        if len(historial) > 1:
            await generar_respuesta(message, forzado=False)
        else:
            await message.reply(random.choice(["que paso", "dime", "mande", "que quieres"]))
        return

    directo = debe_responder_directo(message)

    estado_mal = await detectar_estado_emocional(message.content)

    if directo:
        await generar_respuesta(message, forzado=False, estado_mal=estado_mal)
        return

    if random.random() < 0.60:
        contexto_chat = "\n".join(list(mensajes_recientes_canal)[-10:])
        if await evaluar_si_meterse(contexto_chat):
            await generar_respuesta(message, forzado=True, estado_mal=estado_mal)

client.run(TOKEN)
