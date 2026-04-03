import os
import re
import asyncio
import time
import typer
from telethon import TelegramClient
from telethon.errors import ChatIdInvalidError
from dotenv import load_dotenv

app = typer.Typer()

# =============================
# LOAD ENV
# =============================
load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
phone = os.getenv("TG_PHONE")

MAX_RETRIES = 10


# =============================
# UTIL
# =============================
def sanitize_filename(name):
    if not name:
        return "no_title"

    name = name.split("\n")[0]
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'[=#]', "", name)
    name = re.sub(r'\s+', " ", name).strip()
    name = name.replace(" ", "-")
    name = re.sub(r'-+', "-", name)

    return name[:60]


def get_file_title(message):
    if message.file and message.file.name:
        return sanitize_filename(message.file.name.replace(".mp4", ""))

    if message.text:
        return sanitize_filename(message.text)

    return "no_title"


def build_paths(base_path, message):
    title = get_file_title(message)
    file_name = f"{message.id}_{title}.mp4"

    final_path = os.path.join(base_path, file_name)
    temp_path = final_path + ".part"

    return final_path, temp_path, file_name


def format_time(seconds):
    if seconds <= 0:
        return "--:--:--"

    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_speed(bytes_per_sec):
    if bytes_per_sec == 0:
        return "0 KB/s"

    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    size = bytes_per_sec
    i = 0

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}" if i > 0 else f"{int(size)} {units[i]}"


def format_size(bytes_val):
    units = ["B", "KB", "MB", "GB"]
    size = bytes_val
    i = 0

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.1f} {units[i]}"


def create_progress_bar(percent, length=30):
    filled = int(length * percent / 100)
    bar = "█" * filled + "-" * (length - filled)
    return f"[{bar}]"


def create_progress_callback(file_name):
    start_time = time.time()

    def progress(current, total):
        if total == 0:
            return

        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0

        percent = current * 100 / total

        speed_str = format_speed(speed)
        current_str = format_size(current)
        total_str = format_size(total)

        remaining = (total - current) / speed if speed > 0 else 0
        eta = format_time(remaining)

        bar = create_progress_bar(percent)

        line = (
            f"{file_name} "
            f"{bar} {percent:.1f}% | "
            f"{current_str}/{total_str} | "
            f"{speed_str} | ETA: {eta}"
        )

        print(f"\r{line}", end="", flush=True)

    return progress


# =============================
# CORE LOGIC
# =============================
async def login(client):
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Enter the code received on Telegram: ")
        await client.sign_in(phone, code)


async def download_with_retry(client, message, base_path, index, total):
    final_path, temp_path, file_name = build_paths(base_path, message)

    print(f"\nDownloading {index}/{total}")

    if os.path.exists(final_path):
        print(f"Skipping (already exists): {file_name}")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Downloading {file_name} (attempt {attempt})")

            await client.download_media(
                message,
                file=temp_path,
                progress_callback=create_progress_callback(file_name)
            )

            os.rename(temp_path, final_path)

            print("\nDownload completed")
            return

        except Exception as e:
            print(f"\nError: {e}")

            if attempt == MAX_RETRIES:
                print("Failed after maximum retries. Removing incomplete file.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            wait = 2 * attempt
            print(f"Retrying in {wait} seconds...")
            await asyncio.sleep(wait)


async def run_downloader(channel, output):
    base_path = os.path.join("videos", output)
    os.makedirs(base_path, exist_ok=True)

    client = TelegramClient("session", api_id, api_hash)

    print("Connecting to Telegram...")
    await login(client)

    # ✅ Friendly validation (optional warning)
    if not (channel.startswith("-100") or channel.startswith("http")):
        print("\n⚠️ Warning: Channel format looks invalid.")

    # ✅ Safe entity resolution
    try:
        try:
            entity = await client.get_entity(int(channel))
        except ValueError:
            entity = await client.get_entity(channel)

    except ChatIdInvalidError:
        print("\n❌ Invalid channel.")
        print("Make sure you:")
        print("- Use a valid Telegram channel link (recommended)")
        print("- Or a valid channel ID starting with -100")
        print("\nExamples:")
        print("  --channel https://t.me/your_channel")
        print("  --channel -1001234567890\n")

        await client.disconnect()
        return

    print("Fetching video list...")

    messages = []
    async for message in client.iter_messages(entity, reverse=True):
        if message.video:
            messages.append(message)

    total = len(messages)
    print(f"Total videos found: {total}\n")

    for i, message in enumerate(messages, start=1):
        await download_with_retry(client, message, base_path, i, total)

    await client.disconnect()
    print("\nAll downloads completed!")


# =============================
# CLI
# =============================
@app.command()
def main(
    channel: str = typer.Option(..., help="Channel ID or public link"),
    output: str = typer.Option(..., help="Output folder name"),
):
    try:
        asyncio.run(run_downloader(channel, output))
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")


if __name__ == "__main__":
    app()