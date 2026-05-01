import discord
import os
import time

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
CANAL_ID = 1442319575940075612        # Cambia esto por el ID del canal
COOLDOWN = 60  # segundos

USUARIOS = {
    1438446211400073277: "ya callate we {mención} <:pooconhappymod:1496682483805323426>",   # Usuario 1
    792172637673619466: "eres un pendejo {mención} <:damian:1496621310913286326>",  # Usuario 2
}
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

    if message.channel.id == CANAL_ID and message.author.id in USUARIOS:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(message.author.id, 0)
        if ahora - ultimo >= COOLDOWN:
            ultimo_mensaje[message.author.id] = ahora
            mensaje = USUARIOS[message.author.id].format(mención=message.author.mention)
            await message.channel.send(mensaje)

client.run(TOKEN)
