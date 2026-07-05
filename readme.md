# 📥 Telegram Video Downloader CLI

A simple and resilient CLI tool to download videos from Telegram channels (including private ones).

This tool uses the Telegram client API to fetch and download videos with support for:

* ✅ Private and public channels
* ✅ Automatic retry on failures
* ✅ Clean and safe filenames
* ✅ Progress display (percentage, speed, ETA)
* ✅ Organized output folders

---

## 🚀 Features

* Download all videos from a Telegram channel
* Skip already downloaded files
* Handle unstable connections with retry logic
* Prevent corrupted files using temporary `.part` files
* Display real-time download progress

---

## 🧰 Requirements

* Python 3.10+
* Telegram account

---

## 🔑 Telegram API Setup

You need to create your Telegram API credentials:

1. Go to: https://my.telegram.org
2. Log in with your phone number
3. Click on **"API development tools"**
4. Create a new application
5. Copy:

   * `api_id`
   * `api_hash`

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/marcusantonius88/telegram-ch-downloader.git
cd telegram-ch-downloader
```

---

### 2. Install dependencies

```bash
pip install telethon python-dotenv typer
```

---

### 3. Create `.env` file

Create a `.env` file in the project root:

```env
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE=+your_phone_number
```

Example:

```env
TG_API_ID=123456
TG_API_HASH=abcdef1234567890
TG_PHONE=+5511999999999
```

---

## ▶️ Usage

Run the CLI with:

```bash
python tg_downloader.py --channel <CHANNEL_ID_OR_LINK> --output <FOLDER_NAME>
```

---

### 📌 Example (Private Channel)

```bash
python tg_downloader.py --channel -1002264149640 --output sports-videos
```

---

### 📌 Example (Public Channel)

```bash
python tg_downloader.py --channel https://t.me/channelsports --output sports-videos
```

---

## 📂 Output Structure

Downloaded files will be saved in:

```
videos/<output-folder>/
```

Example:

```
videos/sports-videos/
  1_intro.mp4
  2_soccer.mp4
```

---

## 🔄 How It Works

* Files are first downloaded as `.part`
* Once completed, they are renamed to `.mp4`
* If interrupted, incomplete files are safely retried
* Already downloaded files are skipped automatically

---

## ⚠️ Notes

* You must be a member of private channels to download content
* Large files may take time depending on Telegram's bandwidth limits
* Telegram may throttle download speeds

---

## 🛑 Stop Execution

You can safely stop the script anytime using:

```bash
Ctrl + C
```

The downloader will resume correctly on the next run.

---

## 📌 Future Improvements

* Resume partial downloads (byte-level)
* Multi-thread chunk downloads
* Packaging as installable CLI (`pip install`)
* Docker support

---

## � AI-Assisted Development

This project was built using modern AI-assisted software development practices.

| Category | Tool |
| --- | --- |
| IDE/Agent | VSCode with GitHub Copilot |
| Primary Model | GPT-5.3 |
| Strategic Support | ChatGPT |
| Methodology | Iterative prototyping |

This repository is small and focused, so development followed a lightweight and iterative approach rather than formal Spec-Driven Development. The implementation was refined through direct coding, testing, and incremental improvements while keeping the scope practical for a single CLI utility.

---

## �🤝 Contributing

Feel free to open issues or submit pull requests.

---

## 📄 License

MIT License
