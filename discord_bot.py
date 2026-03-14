import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import json
import os
import time
import logging
from dotenv import load_dotenv

from utils.logging import setup_logging
from sources.adsbfi import fetch_adsbfi
from sources.opensky import fetch_opensky
from core.history import cleanup, flight_history
from services.geocode import geocode
from constants import SPECIAL_TARGETS
from config import CFG

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

DB_FILE = 'corvus-bot.db'

# SQLite helpers to persist per-channel subscriptions
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            channel_id INTEGER PRIMARY KEY, types TEXT, fields TEXT, training INTEGER)''')
    conn.commit()
    conn.close()

def save_subscription(channel_id, types_list, fields_list, training):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        REPLACE INTO subscriptions (channel_id, types, fields, training)
        VALUES (?, ?, ?, ?)''', (channel_id, json.dumps(types_list), json.dumps(fields_list), int(training)))
    conn.commit()
    conn.close()

def remove_subscription(channel_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM subscriptions WHERE channel_id = ?', (channel_id,))
    conn.commit()
    conn.close()

def get_all_subscriptions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT channel_id, types, fields, training FROM subscriptions')
    result = c.fetchall()
    conn.close()

    subs = {}
    for row in result:
        subs[row[0]] = {
            'types': json.loads(row[1]),
            'fields': json.loads(row[2]),
            'training': bool(row[3])
        }
    return subs

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    init_db()
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands.')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

    if not flight_scanner.is_running():
        flight_scanner.start()

@bot.tree.command(name="start", description="Start the flight scanner")
@app_commands.describe(
    types="The types of planes to track (e.g. B2, E6) or 'ALL'",
    fields="The fields to include in the response (e.g. alt,speed,hdg,squawk) or 'ALL'",
    training="True to include local training flights, False for strategic/VIP only"
)
async def start_flight_scanner(interaction: discord.Interaction, types: str = "ALL", fields: str = "ALL", training: bool = False):
    channel_id = interaction.channel.id

    types_list = [t.strip().upper() for t in types.split(",")] if types.upper() != "ALL" else ["ALL"]
    fields_list = [f.strip().lower() for f in fields.split(",")] if fields.upper() != "ALL" else ["all"]

    save_subscription(channel_id, types_list, fields_list, training)

    mode_text = "Active (Including training flights)" if training else "Inactive (Strategic/VIP only)"
    await interaction.response.send_message(
        f"✅ **Scanner activated!**\n"
        f"Tracked Types: `{', '.join(types_list)}`\n"
        f"Included Fields: `{', '.join(fields_list)}`\n"
        f"Training Mode: `{mode_text}`"
    )

@bot.tree.command(name="stop", description="Stop the flight scanner")
async def stop_flight_scanner(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    remove_subscription(channel_id)
    await interaction.response.send_message("🛑 **Scanner stopped.** This channel will no longer receive updates.")

@tasks.loop(seconds=CFG.poll_interval_sec)
async def flight_scanner():
    subscriptions = get_all_subscriptions()
    if not subscriptions:
        return

    cleanup()
    planes = {}
    planes.update(fetch_adsbfi())
    planes.update(fetch_opensky())

    for hex_code, plane in planes.items():
        try:
            raw_alt = plane.get("alt", 0)
            alt = int(raw_alt) if str(raw_alt).isdigit() else 0
            hdg = int(plane.get("hdg") or plane.get("track") or 0)
        except (ValueError, TypeError):
            continue

        current_time = time.time()

        if hex_code not in flight_history:
            flight_history[hex_code] = {"time": current_time, "last_alert": 0}

        last_alert = flight_history[hex_code].get("last_alert", 0)
        if (current_time - last_alert) <= CFG.alert_cooldown_sec:
            continue

        is_special = hex_code in SPECIAL_TARGETS
        is_strategic = (alt >= CFG.min_alt_normal_ft) and (CFG.hdg_min <= hdg <= CFG.hdg_max)

        plane_type = str(plane.get("type", "UNKNOWN")).upper()
        raw_callsign = str(plane.get("flight") or plane.get("callsign") or "").strip()
        callsign = raw_callsign if raw_callsign else "N/A"
        desc = plane.get("desc") or plane_type or "Unknown Aircraft"
        ownOp = plane.get("ownOp") or "Unknown Operator"
        reg = plane.get("r") or plane.get("reg") or "N/A"
        category = plane.get("category") or "N/A"
        squawk = plane.get("squawk") or "N/A"
        speed = plane.get("gs") or plane.get("speed") or "N/A"
        v_speed = plane.get("baro_rate") or plane.get("v_speed") or "N/A"
        emergency = plane.get("emergency") or "none"
        source = plane.get("source", "API")

        alert_sent = False

        for channel_id, sub in subscriptions.items():
            wants_training = sub["training"]

            if not (is_special or is_strategic or wants_training):
                continue

            if "ALL" not in sub["types"] and plane_type not in sub["types"]:
                continue

            channel = bot.get_channel(channel_id)
            if not channel:
                continue

            if is_special:
                prefix = "⭐ **PRIORITY ALERT: VIP TARGET** ⭐"
            elif is_strategic:
                prefix = "🚨 **STRATEGIC ALERT** 🚨"
            else:
                prefix = "🛩️ **TRAINING FLIGHT** 🛩️"

            map_link = f"https://globe.adsb.fi/?icao={hex_code}"

            msg_lines = [f"{prefix}"]

            show_all = "all" in sub["fields"]

            if show_all or "callsign" in sub["fields"]:
                msg_lines.append(f"**Callsign:** {callsign}")
            if show_all or "operator" in sub["fields"]:
                msg_lines.append(f"**Operator:** {ownOp}")

            msg_lines.append(f"**Type:** {desc} (Hex: {hex_code})")

            if show_all or "reg" in sub["fields"]:
                msg_lines.append(f"**Registration:** {reg}")
            if show_all or "category" in sub["fields"]:
                msg_lines.append(f"**Category:** {category}")
            if show_all or "squawk" in sub["fields"]:
                msg_lines.append(f"**Squawk:** {squawk}")
            if show_all or "location" in sub["fields"]:
                msg_lines.append(f"**Location:** 🗺️ {geocode(plane.get('lat'), plane.get('lon'))}")
            if show_all or "alt" in sub["fields"]:
                msg_lines.append(f"**Altitude:** `{alt} ft`")
            if show_all or "speed" in sub["fields"]:
                msg_lines.append(f"**Speed:** `{speed} kts`")
            if show_all or "v_speed" in sub["fields"]:
                msg_lines.append(f"**Vertical Speed:** `{v_speed} ft/min`")
            if show_all or "hdg" in sub["fields"]:
                msg_lines.append(f"**Heading:** `{hdg}°`")
            if show_all or "emergency" in sub["fields"]:
                msg_lines.append(f"**Emergency:** {emergency}")
            if show_all or "source" in sub["fields"]:
                msg_lines.append(f"**Source:** *{source}*")

            msg_lines.append(f"🌍 **Live Map:** {map_link}")

            bot.loop.create_task(channel.send("\n".join(msg_lines)))
            alert_sent = True

        if alert_sent:
            flight_history[hex_code]["last_alert"] = current_time

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

if __name__ == "__main__":
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        logger.error("Please set the BOT_TOKEN environment variable.")
        exit(1)
    bot.run(TOKEN)