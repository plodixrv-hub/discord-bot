import discord
import os
import time
from groq import Groq

# ---- CONFIGURACIÓN ----
TOKEN = os.environ["TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
COOLDOWN = 30  # segundos

# Usuarios a monitorear y sus mensajes
CANAL_MONITOREO = 987654321098765432
USUARIOS = {
    792172637673619466: "eres un pendejo {mención} <:damian:1496621310913286326>",   # Usuario 1
    1438446211400073277: "ya callate we {mención} <:pooconhappymod:1496682483805323426>",  # Usuario 2
}

# Canal espejo
CANAL_ORIGEN = 1492978765981286593   # canal privado donde tú escribes
CANAL_DESTINO = 1442319575940075612  # canal general donde se reenvía
TU_ID = 1202106034424905830          # tu ID de usuario

# Canal donde responde la IA
CANAL_IA = 1442319575940075612
# -----------------------

ultimo_mensaje = {}
groq_client = Groq(api_key=GROQ_API_KEY)

PERSONALIDAD = """Eres un usuario normal de Discord, hablas como un chico joven latino informal. 
Reglas:
- Respuestas MUY cortas, máximo 1-2 oraciones, como habla la gente en Discord
- Usas palabras como "bro", "wey", "xd", "lmao", "ntp", "nel", "simon"
- Eres gracioso y sarcástico naturalmente
- Si alguien te insulta o te habla mal, los insultas de vuelta sin filtro
- No eres un asistente, eres un cuate del server
- Nunca escribes párrafos largos, jamás
- A veces respondes con solo una palabra o emoji si la situación lo amerita"""

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

   # --- Sistema de IA ---
    if message.channel.id == CANAL_IA:
        ahora = time.time()
        ultimo = ultimo_mensaje.get(f"ia_{message.author.id}", 0)
        if ahora - ultimo >= 10:
            ultimo_mensaje[f"ia_{message.author.id}"] = ahora
            async with message.channel.typing():
                respuesta = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": PERSONALIDAD},
                        {"role": "user", "content": f"{message.author.name} dice: {message.content}"}
                    ]
                )
                await message.reply(respuesta.choices[0].message.content)

client.run(TOKEN)
