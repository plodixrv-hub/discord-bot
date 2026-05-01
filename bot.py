import discord
import os
import time

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
USUARIO_ID = 1438446211400073277     # Cambia esto por el ID del usuario
CANAL_ID = 1442319575940075612        # Cambia esto por el ID del canal
MENSAJE_RESPUESTA = "ya callate we {mención}"
COOLDOWN = 20  # segundos
# -----------------------

ultimo_mensaje = 0

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    global ultimo_mensaje

    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return

    # Verificar canal Y usuario
    if message.channel.id == CANAL_ID and message.author.id == USUARIO_ID:
        ahora = time.time()
        if ahora - ultimo_mensaje >= COOLDOWN:
            ultimo_mensaje = ahora
            await message.channel.send(MENSAJE_RESPUESTA.format(mención=message.author.mention))

client.run(TOKEN)
