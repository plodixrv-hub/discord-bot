import discord
import os
import time
import random
import asyncio
import json
from openai import AsyncOpenAI
from collections import deque

# –– CONFIGURACION ––

TOKEN = os.environ[“TOKEN”]
OPENAI_API_KEY = os.environ[“OPENAI_API_KEY”]
COOLDOWN = 30

CANAL_MONITOREO = 987654321098765432
USUARIOS = {
792172637673619466: “eres un pendejo {mencion} <:damian:1496621310913286326>”,
1438446211400073277: “ya callate we {mencion} <:pooconhappymod:1496682483805323426>”,
}

CANAL_ORIGEN = 1492978765981286593
CANAL_DESTINO = 1442319575940075612
TU_ID = 1202106034424905830

CANAL_IA = 1442319575940075612
USUARIOS_BONITOS = []
IA_ACTIVA = True
MAX_HISTORIAL = 10
MENSAJES_A_LEER = 500
ARCHIVO_PERSONALIDAD = “/app/personalidad.txt”
INTERVALO_APRENDIZAJE = 24 * 60 * 60  # 24 horas

TIEMPO_MIN = 45 * 60
TIEMPO_MAX = 120 * 60

PERSONALIDAD_BONITA = (
“Eres Xiora, un usuario de Discord muy carinoso y dulce.\n”
“Reglas:\n”
“- Tu nombre es Xiora\n”
“- Respuestas cortas, maximo 2-5 oraciones\n”
“- Siempre amable, carinoso y lindo\n”
“- Usas palabras bonitas y emojis tiernos\n”
“- Haces sentir especial a la persona\n”
)

PERSONALIDAD_RANDOM = (
“Eres Xiora, parte de este grupo de amigos en Discord.\n”
“Manda algo random para sacar platica basandote en como habla el grupo.\n”
“Maximo 1-2 oraciones, sin saludos, ve directo al tema.\n”
)

PERSONALIDAD_FALLBACK = (
“Eres Xiora, un chico latino joven en un server de Discord con sus amigos.\n”
“Habla informal, en minusculas, sarcastico y natural.\n”
“Maximo 1-2 oraciones.\n”
)

# ———————–

ultimo_mensaje = {}
personalidad_aprendida = “”
historial = deque(maxlen=MAX_HISTORIAL)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def cargar_personalidad_guardada():
global personalidad_aprendida
if os.path.exists(ARCHIVO_PERSONALIDAD):
with open(ARCHIVO_PERSONALIDAD, “r”, encoding=“utf-8”) as f:
personalidad_aprendida = f.read()
print(“Personalidad guardada cargada”)

def guardar_personalidad(texto):
with open(ARCHIVO_PERSONALIDAD, “w”, encoding=“utf-8”) as f:
f.write(texto)

def debe_responder(message):
if client.user in message.mentions:
return True
if message.reference and message.reference.resolved:
if isinstance(message.reference.resolved, discord.Message):
if message.reference.resolved.author == client.user:
return True
if “xiora” in message.content.lower():
return True
return False

async def aprender_del_grupo():
global personalidad_aprendida
canal = client.get_channel(CANAL_IA)
if not canal:
return
mensajes = []
async for msg in canal.history(limit=MENSAJES_A_LEER):
if msg.content and msg.author != client.user:
mensajes.append(f”{msg.author.display_name}: {msg.content}”)
if not mensajes:
return
mensajes.reverse()
muestra = “\n”.join(mensajes)

```
prompt_analisis = (
    "Analiza estos mensajes de un grupo de amigos en Discord y genera un resumen detallado de:\n"
    "- Como hablan (tono, palabras que usan, expresiones tipicas)\n"
    "- La dinamica del grupo (quienes son los graciosos, los dramaticos, los secos)\n"
    "- Temas que sacan seguido\n"
    "- Como se insultan o se bromean entre ellos\n"
    "Sé especifico con ejemplos reales de sus palabras.\n\n"
    f"Mensajes:\n{muestra}"
)

try:
    respuesta = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_analisis}],
        max_tokens=800
    )
    nuevo_conocimiento = respuesta.choices[0].message.content

    if personalidad_aprendida:
        personalidad_aprendida = personalidad_aprendida + "\n\n--- Actualizacion ---\n" + nuevo_conocimiento
    else:
        personalidad_aprendida = nuevo_conocimiento

    guardar_personalidad(personalidad_aprendida)
    print("Personalidad actualizada y guardada")
except Exception as e:
    print(f"Error aprendizaje: {e}")
```

async def loop_aprendizaje():
await client.wait_until_ready()
while not client.is_closed():
await aprender_del_grupo()
await asyncio.sleep(INTERVALO_APRENDIZAJE)

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
personalidad = personalidad_aprendida if personalidad_aprendida else PERSONALIDAD_FALLBACK
respuesta = await openai_client.chat.completions.create(
model=“gpt-4o-mini”,
messages=[
{“role”: “system”, “content”: “Eres Xiora, parte de este grupo. Conocimiento del grupo:\n” + personalidad + “\n\n” + PERSONALIDAD_RANDOM},
{“role”: “user”, “content”: “manda algo random para sacar platica”}
]
)
texto = respuesta.choices[0].message.content
historial.append({“role”: “assistant”, “content”: texto})
await canal.send(texto)
except Exception as e:
print(f”Error mensaje random: {e}”)

@client.event
async def on_ready():
print(f”Bot conectado como {client.user}”)
cargar_personalidad_guardada()
asyncio.ensure_future(loop_aprendizaje())
asyncio.ensure_future(mensaje_random())

@client.event
async def on_message(message):
global IA_ACTIVA

```
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
    await message.channel.send("Aprendiendo del grupo... ⏳")
    await aprender_del_grupo()
    await message.channel.send("Listo, personalidad actualizada ✅")
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

    if message.author.id in USUARIOS_BONITOS:
        personalidad_usar = PERSONALIDAD_BONITA
    else:
        personalidad_usar = (
            "Eres Xiora, parte de este grupo de amigos en Discord.\n"
            "Conocimiento del grupo:\n" +
            (personalidad_aprendida if personalidad_aprendida else PERSONALIDAD_FALLBACK) +
            "\nReglas:\n"
            "- Responde natural como parte del grupo\n"
            "- Todo en minusculas, informal\n"
            "- Escribe lo que se siente natural, ni muy corto ni muy largo\n"
            "- No uses frases genericas\n"
        )

    async with message.channel.typing():
        try:
            contexto = "\n".join([f"{m['role']}: {m['content']}" for m in historial])
            respuesta = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": personalidad_usar + f"\n\nConversacion reciente:\n{contexto}"},
                    {"role": "user", "content": message.content}
                ]
            )
            respuesta_texto = respuesta.choices[0].message.content
            historial.append({"role": "assistant", "content": respuesta_texto})
            await message.reply(respuesta_texto)
        except Exception as e:
            print(f"Error IA: {e}")
            await message.reply("error interno")
```

client.run(TOKEN)