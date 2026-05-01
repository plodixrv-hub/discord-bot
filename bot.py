import discord
import os
import time

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
COOLDOWN = 120  # segundos

# Usuarios a monitorear y sus mensajes
CANAL_MONITOREO = 1442319575940075612  # canal donde monitoreas usuarios
USUARIOS = {
    792172637673619466: "eres un pendejo {mención} <:damian:1496621310913286326>",   # Usuario 1
    1438446211400073277: "ya callate we {mención} <:pooconhappymod:1496682483805323426>",  # Usuario 2
}

# Canal espejo
CANAL_ORIGEN = 1492978765981286593   # canal privado donde tú escribes
CANAL_DESTINO = 1442319575940075612  # canal general donde se reenvía
TU_ID = 1202106034424905830          # tu ID de usuario
# -----------------------

ultimo_mensaje = {}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
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

client.run(TOKEN)
