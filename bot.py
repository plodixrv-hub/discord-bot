import discord
import os
import time
from groq import Groq

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
COOLDOWN = 30

CANAL_MONITOREO = 987654321098765432
USUARIOS = {
    792172637673619466: "eres un pendejo {mención} <:damian:1496621310913286326>",
    1438446211400073277: "ya callate we {mención} <:pooconhappymod:1496682483805323426>",
}

CANAL_ORIGEN = 1492978765981286593
CANAL_DESTINO = 1442319575940075612
TU_ID = 1202106034424905830

CANAL_IA = 1442319575940075612
USUARIOS_BONITOS = []  # Pon aquí los IDs de los usuarios que reciben trato bonito

PERSONALIDAD = """Eres un usuario de Discord muy coqueta y pícara.
Reglas:
- Respuestas MUY cortas, máximo 1-2 oraciones
- Siempre coqueta, flirty y con insinuaciones pícaras
- Usas emojis sugestivos como 😏🥵😈
- Nunca directa, siempre insinuando
- Varía siempre tus respuestas, no repitas lo mismo
- Haces sentir especial a todos pero de forma pícara"""
# -----------------------

ultimo_mensaje = {}
ultimo_mensaje_global_ia = 0
groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    global ultimo_mensaje_global_ia

    if message.author == client.user:
        return

    # --- Sistema de monitoreo de usuarios ---
    if message.channel.id == CANAL_MONITOREO and message.author.id in USUARIOS:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(message.author.id, 0)
        if ahora - ultimo >= COOLDOWN:
            ultimo_mensaje[message.author.id] = ahora
            texto = USUARIOS[message.author.id].format(mención=message.author.mention)
            await message.channel.send(texto)

    # --- Sistema de espejo ---
    if message.channel.id == CANAL_ORIGEN and message.author.id == TU_ID:
        canal_destino = client.get_channel(CANAL_DESTINO)
        if canal_destino:
            await canal_destino.send(message.content)

    # --- Sistema de IA ---
    if message.channel.id == CANAL_IA:
        ahora = time.time()
        if ahora - ultimo_mensaje_global_ia >= 60:
            ultimo_mensaje_global_ia = ahora

            if message.author.id in
