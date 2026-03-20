import os
import re
import asyncio
import time
import typer
from telethon import TelegramClient
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
        return "sem_titulo"

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

    return "sem_titulo"


def build_paths(base_path, message):
    title = get_file_title(message)
    file_name = f"{message.id}_{title}.mp4"

    final_path = os.path.join(base_path, file_name)
    temp_path = final_path + ".part"

    return final_path, temp_path, file_name


def format_time(seconds):
    if seconds <= 0:
        return "--:--:--"

    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def create_progress_callback(file_name):
    start_time = time.time()

    def progress(current, total):
        if total == 0:
            return

        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0

        percent = current * 100 / total
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        speed_mb = speed / (1024 * 1024)

        remaining = (total - current) / speed if speed > 0 else 0
        eta = format_time(remaining)

        print(
            f"\r{file_name} | {percent:.1f}% "
            f"({current_mb:.1f}/{total_mb:.1f} MB) "
            f"| {speed_mb:.2f} MB/s "
            f"| ETA: {eta}",
            end=""
        )

    return progress


# =============================
# CORE LOGIC
# =============================
async def login(client):
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Digite o codigo do Telegram: ")
        await client.sign_in(phone, code)


async def download_with_retry(client, message, base_path):
    final_path, temp_path, file_name = build_paths(base_path, message)

    if os.path.exists(final_path):
        print(f"\nJa existe: {file_name}")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\nBaixando {file_name} (tentativa {attempt})")

            await client.download_media(
                message,
                file=temp_path,
                progress_callback=create_progress_callback(file_name)
            )

            os.rename(temp_path, final_path)

            print("\nDownload concluido")
            return

        except Exception as e:
            print(f"\nErro: {e}")

            if attempt == MAX_RETRIES:
                print("Falhou definitivamente.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            wait = 2 * attempt
            print(f"Tentando novamente em {wait}s...")
            await asyncio.sleep(wait)


async def run_downloader(channel, output):
    base_path = os.path.join("videos", output)
    os.makedirs(base_path, exist_ok=True)

    client = TelegramClient("session", api_id, api_hash)

    print("Conectando...")
    await login(client)

    # 🔥 FIX: aceita int ou string
    try:
        entity = await client.get_entity(int(channel))
    except ValueError:
        entity = await client.get_entity(channel)

    print("Baixando videos...\n")

    async for message in client.iter_messages(entity, reverse=True):
        if message.video:
            await download_with_retry(client, message, base_path)

    await client.disconnect()
    print("\nFinalizado!")


# =============================
# CLI COMMAND
# =============================
@app.command()
def download(
    channel: str = typer.Option(..., help="ID ou link do canal"),
    output: str = typer.Option(..., help="Nome da pasta de saída"),
):
    """
    Baixa vídeos de um canal do Telegram
    """
    try:
        asyncio.run(run_downloader(channel, output))
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuario.")


if __name__ == "__main__":
    app()