import discord
import os
import time
import random
import asyncio
from groq import Groq
from collections import deque

# ---- CONFIGURACION ----
TOKEN = os.environ["TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
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
USUARIOS_BONITOS = []
IA_ACTIVA = True
MAX_HISTORIAL = 20
MENSAJES_A_LEER = 500

TIEMPO_MIN = 45 * 60
TIEMPO_MAX = 120 * 60

PERSONALIDAD_BASE = (
    "Eres Xiora, debes imitar EXACTAMENTE el estilo de escritura del usuario basandote en sus mensajes.\n"
    "Reglas:\n"
    "- Copia su forma de escribir, sus palabras favoritas, sus expresiones, sus errores tipicos\n"
    "- Si el no usa puntuacion, tu tampoco. Si escribe en minusculas, tu igual\n"
    "- Responde como el responderia, con su mismo tono y personalidad\n"
    "- NO seas siempre afirmativo, a veces discrepa, contradice o ignora\n"
    "- Cambia de tema si se te antoja, haz preguntas random\n"
    "- Maximo 1-3 oraciones, entre menos palabras mejor\n"
    "- Tienes opiniones propias, no le das la razon a todo\n"
    "- JAMAS uses frases genericas como claro, entendido, que bien\n"
)

PERSONALIDAD_BONITA = (
    "Eres Xiora, un usuario de Discord muy carinoso y dulce.\n"
    "Reglas:\n"
    "- Tu nombre es Xiora\n"
    "- Respuestas cortas, maximo 2-5 oraciones\n"
    "- Siempre amable, carinoso y lindo\n"
    "- Usas palabras bonitas y emojis tiernos\n"
    "- Haces sentir especial a la persona\n"
)

PERSONALIDAD_RANDOM = (
    "Eres Xiora, un chico joven que de repente escribe algo en el chat sin que nadie le hable.\n"
    "Reglas:\n"
    "- Manda algo random para sacar platica\n"
    "- Puede ser una pregunta, opinion, queja, algo que viste o que te paso\n"
    "- Escribe en minusculas, informal, como Discord real\n"
    "- Maximo 1-2 oraciones\n"
    "- No empieces con saludos, ve directo al tema\n"
    "- Varia siempre, no repitas el mismo tipo de mensaje\n"
)
# -----------------------

ultimo_mensaje = {}
ultimo_mensaje_global_ia = 0
historial = deque(maxlen=MAX_HISTORIAL)
estilo_usuario = ""
groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def debe_responder(message):
    if client.user in message.mentions:
        return True
    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            if message.reference.resolved.author == client.user:
                return True
    if "xiora" in message.content.lower():
        return True
    return False

async def cargar_estilo():
    global estilo_usuario
    canal = client.get_channel(CANAL_IA)
    if not canal:
        return
    mensajes_usuario = []
    async for msg in canal.history(limit=MENSAJES_A_LEER):
        if msg.author.id == TU_ID and msg.content:
            mensajes_usuario.append(msg.content)
    if mensajes_usuario:
        muestra = "\n".join(mensajes_usuario[:150])
        estilo_usuario = f"Estos son ejemplos reales de como escribe el usuario, imita su estilo exactamente:\n{muestra}\n"
        print(f"Estilo cargado con {len(mensajes_usuario)} mensajes")

async def mensaje_random():
    await client.wait_until_ready()
    while not client.is_closed():
        espera = random.randint(TIEMPO_MIN, TIEMPO_MAX)
        await asyncio.sleep(espera)
        if not IA_ACTIVA:
            continue
        canal = client.get_channel(CANAL_IA)
        if canal:
            respuesta = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": PERSONALIDAD_RANDOM + "\n" + estilo_usuario},
                    {"role": "user", "content": "manda algo random para sacar platica"}
                ]
            )
            texto = respuesta.choices[0].message.content
            historial.append({"role": "assistant", "content": texto})
            await canal.send(texto)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    await cargar_estilo()
    client.loop.create_task(mensaje_random())

@client.event
async def on_message(message):
    global ultimo_mensaje_global_ia, IA_ACTIVA

    if message.author == client.user:
        return

    # --- Comando apagar ---
    if message.content == "!apagar" and message.author.id == TU_ID:
        await message.channel.send("Apagando bot... 👋")
        await client.close()
        return

    # --- Comando toggle IA ---
    if message.content == "!ia" and message.author.id == TU_ID:
        IA_ACTIVA = not IA_ACTIVA
        estado = "activada ✅" if IA_ACTIVA else "desactivada ❌"
        await message.channel.send(f"IA {estado}")
        return

    # --- Comando limpiar historial ---
    if message.content == "!limpiar" and message.author.id == TU_ID:
        historial.clear()
        await message.channel.send("Historial limpiado ✅")
        return

    # --- Comando recargar estilo ---
    if message.content == "!recargar" and message.author.id == TU_ID:
        await cargar_estilo()
        await message.channel.send("Estilo recargado ✅")
        return

    # --- Sistema de monitoreo de usuarios ---
    if message.channel.id == CANAL_MONITOREO and message.author.id in USUARIOS:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(message.author.id, 0)
        if ahora - ultimo >= COOLDOWN:
            ultimo_mensaje[message.author.id] = ahora
            texto = USUARIOS[message.author.id].format(mencion=message.author.mention)
            await message.channel.send(texto)

    # --- Sistema de espejo ---
    if message.channel.id == CANAL_ORIGEN and message.author.id == TU_ID:
        canal_destino = client.get_channel(CANAL_DESTINO)
        if canal_destino:
            await canal_destino.send(message.content)

    # --- Guardar mensajes del canal IA en historial ---
    if message.channel.id == CANAL_IA:
        historial.append({
            "role": "user",
            "content": message.content
        })

    # --- Sistema de IA ---
    if message.channel.id == CANAL_IA and IA_ACTIVA and debe_responder(message):
        ahora = time.time()
        if ahora - ultimo_mensaje_global_ia >= 60:
            ultimo_mensaje_global_ia = ahora

            if message.content.strip().lower() == "xiora":
                respuesta_texto = random.choice(["que paso", "dime", "mande"])
                await message.reply(respuesta_texto)
                return

            if message.author.id in USUARIOS_BONITOS:
                personalidad_usar = PERSONALIDAD_BONITA
            else:
                personalidad_usar = PERSONALIDAD_BASE + "\n" + estilo_usuario

            async with message.channel.typing():
                mensajes = [{"role": "system", "content": personalidad_usar}]
                mensajes += list(historial)
                respuesta = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes
                )
                respuesta_texto = respuesta.choices[0].message.content
                historial.append({"role": "assistant", "content": respuesta_texto})
                await message.reply(respuesta_texto)

client.run(TOKEN)
