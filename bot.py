import discord
import os

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
USUARIO_ID = 792172637673619466      # Cambia esto por el ID del usuario
CANAL_ID = 441456975232897094       # Cambia esto por el ID del canal
MENSAJE_RESPUESTA = "eres un pendejo{mención}"
# -----------------------

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return

    # Verificar canal Y usuario
    if message.channel.id == CANAL_ID and message.author.id == USUARIO_ID:
        await message.channel.send(MENSAJE_RESPUESTA.format(mención=message.author.mention))

client.run(TOKEN)
