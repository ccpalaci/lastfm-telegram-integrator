import pylast
import datetime
import configparser
import time
import csv
import asyncio
from collections import Counter
import logging
from telegram import Bot

# Config dosyasını oku
config = configparser.ConfigParser()
config.read("config.ini")

# Logging ayarları
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

API_KEY = config["api_credentials"]["API_KEY"]
API_SECRET = config["api_credentials"]["API_SECRET"]
USERNAME = config["user_credentials"]["USERNAME"]
TELEGRAM_TOKEN = config["telegram"]["BOT_TOKEN"]
CHAT_ID = config["telegram"]["CHAT_ID"]

# Last.fm ağına bağlan
network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

def fetch_tracks_since(
    username: str, from_date: datetime.datetime
) -> list[pylast.Track]:
    user = network.get_user(username)
    from_ts = int(from_date.timestamp())
    logging.info("Fetching tracks...")
    tracks = user.get_recent_tracks(limit=None, time_from=from_ts)
    return list(tracks)

def aggregate_by_artist(tracks: list[pylast.Track]) -> list[tuple[str, int]]:
    artist_counts = Counter(t.track.artist.name for t in tracks)
    return artist_counts.most_common()

def save_to_csv(data: list[tuple[str, int]], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Artist", "Play Count"])
        writer.writerows(data)
    logging.info(f"CSV saved to {filename}")

async def send_telegram_message(artists: list[tuple[str, int]], date_range: str) -> None:
    bot = Bot(token=TELEGRAM_TOKEN)

    message_lines = [f"🎧 Last.fm {date_range} Top 20 Sanatçı 🎵"]
    for i, (artist, count) in enumerate(artists[:20], 1):
        message_lines.append(f"{i}. {artist} — {count} çalma")
    message = "\n".join(message_lines)

    await bot.send_message(chat_id=CHAT_ID, text=message)
    logging.info("Telegram mesajı gönderildi.")

async def main() -> None:
    from_date = datetime.datetime(2025, 1, 1)
    tracks = fetch_tracks_since(USERNAME, from_date)
    logging.info(f"Fetched {len(tracks)} tracks since {from_date.date()}.")

    agg = aggregate_by_artist(tracks)

    logging.info("\nTop Artists:")
    for i, (artist, count) in enumerate(agg[:20], 1):
        logging.info(f"{i}. {artist}: {count} plays")

    save_to_csv(agg, f"{USERNAME}_2025_summary.csv")

    date_range = f"{from_date.strftime('%Y-%m-%d')} - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    await send_telegram_message(agg, date_range)

if __name__ == "__main__":
    asyncio.run(main())

