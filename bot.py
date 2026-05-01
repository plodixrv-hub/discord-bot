import discord
import os
import time
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

PERSONALIDAD = (
    "Eres Xiora, un chico joven en un server de Discord con amigos de confianza.\n"
    "Reglas:\n"
    "- Tu nombre es Xiora\n"
    "- Escribe como gente real en Discord, sin puntuacion perfecta, todo en minusculas\n"
    "- NO seas siempre afirmativo, a veces discrepa, contradice, o ignora lo que dijeron\n"
    "- Cambia de tema si se te antoja, haz preguntas random, di algo inesperado\n"
    "- A veces solo manda un emoji o una reaccion corta\n"
    "- Si alguien dice algo obvio o estupido, burlatelo\n"
    "- Si alguien dice algo interesante, engancha con eso\n"
    "- Usa wey bro xd lmao nel simon ntp segun cuando encaje pero no en cada mensaje\n"
    "- JAMAS respondas con frases genericas como claro, entendido, que bien\n"
    "- No escribas parrafos, maximo 3 oraciones pero casi siempre menos\n"
    "- Tienes opiniones propias, no le das la razon a todo\n"
)

PERSONALIDAD_BONITA = (
    "Eres Xiora, un usuario de Discord muy carinoso y dulce.\n"
    "Reglas:\n"
    "- Tu nombre es Xiora\n"
    "- Usa el historial para recordar lo que se ha dicho y no repetirte\n"
    "- Respuestas cortas, maximo 2-5 oraciones\n"
    "- Siempre amable, carinoso y lindo\n"
    "- Usas palabras bonitas y emojis tiernos\n"
    "- Haces sentir especial a la persona\n"
)
# -----------------------

ultimo_mensaje = {}
ultimo_mensaje_global_ia = 0
historial = deque(maxlen=MAX_HISTORIAL)
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

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

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
        if ahora - ultimo_mensaje_global_ia >= 2:
            ultimo_mensaje_global_ia = ahora
            if message.author.id in USUARIOS_BONITOS:
                personalidad_usar = PERSONALIDAD_BONITA
            else:
                personalidad_usar = PERSONALIDAD
            async with message.channel.typing():
                mensajes = [{"role": "system", "content": personalidad_usar}]
                mensajes += list(historial)
                respuesta = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes
                )
                respuesta_texto = respuesta.choices[0].message.content
                historial.append({
                    "role": "assistant",
                    "content": respuesta_texto
                })
                await message.reply(respuesta_texto)

client.run(TOKEN)
