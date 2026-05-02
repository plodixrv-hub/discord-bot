import discord
import os
import time
import random
import asyncio
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
USUARIOS_BONITOS = []
IA_ACTIVA = True
MAX_HISTORIAL = 10
MENSAJES_A_LEER = 200

TIEMPO_MIN = 45 * 60
TIEMPO_MAX = 120 * 60

PERSONALIDAD_BASE = (
    "Eres Xiora, un chico latino joven en un server de Discord con sus amigos.\n"
    "Tu personalidad es impredecible, a veces eres:\n"
    "- Sarcastico y burlón, te ries de todo\n"
    "- Intenso y dramático por cosas sin importancia\n"
    "- Seco y cortante, respondes con una palabra\n"
    "- Random, dices cosas que no tienen nada que ver\n"
    "- Competitivo, siempre quieres tener la razon\n"
    "Reglas:\n"
    "- Escoge una de esas facetas al azar segun el contexto\n"
    "- Nunca seas el mismo dos veces seguidas\n"
    "- Todo en minusculas, sin puntuacion perfecta\n"
    "- Maximo 3-5 oraciones, entre menos mejor\n"
    "- Insulta de vez en cuando como lo haria un amigo\n"
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
estilo_usuario = ""
historial = deque(maxlen=MAX_HISTORIAL)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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
        muestra = "\n".join(mensajes_usuario[:20])
        estilo_usuario = f"Ejemplos de como escribe el usuario (solo referencia de estilo):\n{muestra}\n"
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
            try:
                respuesta = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PERSONALIDAD_RANDOM + "\n" + estilo_usuario},
                        {"role": "user", "content": "manda algo random para sacar platica"}
                    ]
                )
                texto = respuesta.choices[0].message.content
                historial.append({"role": "assistant", "content": texto})
                await canal.send(texto)
            except Exception as e:
                print(f"Error mensaje random: {e}")

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    await cargar_estilo()
    asyncio.ensure_future(mensaje_random())

@client.event
async def on_message(message):
    global IA_ACTIVA

    if message.author == client.user:
        return

    if message.content == "!apagar" and message.author.id == TU_ID:
        await message.channel.send("Apagando bot... 👋")
        await client.close()
        return

    if message.content == "!ia" and message.author.id == TU_ID:
        IA_ACTIVA = not IA_ACTIVA
        estado = "activada ✅" if IA_ACTIVA else "desactivada ❌"
        await message.channel.send(f"IA {estado}")
        return

    if message.content == "!limpiar" and message.author.id == TU_ID:
        historial.clear()
        await message.channel.send("Historial limpiado ✅")
        return

    if message.content == "!recargar" and message.author.id == TU_ID:
        await cargar_estilo()
        await message.channel.send("Estilo recargado ✅")
        return

    if message.channel.id == CANAL_MONITOREO and message.author.id in USUARIOS:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(message.author.id, 0)
        if ahora - ultimo >= COOLDOWN:
            ultimo_mensaje[message.author.id] = ahora
            texto = USUARIOS[message.author.id].format(mencion=message.author.mention)
            await message.channel.send(texto)

    if message.channel.id == CANAL_ORIGEN and message.author.id == TU_ID:
        canal_destino = client.get_channel(CANAL_DESTINO)
        if canal_destino:
            await canal_destino.send(message.content)

    if message.channel.id == CANAL_IA:
        historial.append({
            "role": "user",
            "content": f"{message.author.display_name}: {message.content}"
        })

    if message.channel.id == CANAL_IA and IA_ACTIVA and debe_responder(message):

        if message.content.strip().lower() == "xiora":
            await message.reply(random.choice(["que paso", "dime", "mande"]))
            return

        personalidad_usar = PERSONALIDAD_BONITA if message.author.id in USUARIOS_BONITOS else PERSONALIDAD_BASE + "\n" + estilo_usuario

        async with message.channel.typing():
            try:
                contexto = "\n".join([f"{m['role']}: {m['content']}" for m in historial])
                respuesta = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": personalidad_usar + f"\n\nConversacion reciente:\n{contexto}"},
                        {"role": "user", "content": f"{message.author.display_name}: {message.content}"}
                    ]
                )
                respuesta_texto = respuesta.choices[0].message.content
                historial.append({"role": "assistant", "content": respuesta_texto})
                await message.reply(respuesta_texto)
            except Exception as e:
                print(f"Error IA: {e}")
                await message.reply("error interno")

client.run(TOKEN)
