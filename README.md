# Pablos Telegram Bot 🤖

Pablos adalah chatbot Telegram yang santai, gaul, dan multifungsi dengan persona Indonesia yang asik. Bot ini menggunakan Gradient AI untuk chat interaktif, generate gambar, bantuan coding, dan mode curhat empatik.

## ✨ Fitur

### 💬 Chat Interaktif Multi-turn
- Percakapan natural dengan konteks berkelanjutan
- Persona "Pablos" yang super santai dan friendly dengan bahasa gaul
- Menggunakan bahasa Indonesia casual dengan kata-kata seperti "wkwkwk", "jir", "kontol", dll
- Memory per-user dengan Redis atau in-memory fallback

### 🎨 Generate Gambar
- Command: `/image <deskripsi>`
- Mengkonversi deskripsi user menjadi prompt detail
- Menggunakan Gradient AI image model
- Mengirim hasil gambar langsung ke chat

### 💻 Code Helper
- Auto-detect code blocks dalam format markdown
- Deteksi prefix `explain:` untuk analisis kode
- Memberikan penjelasan, bug findings, dan kode yang diperbaiki
- Response dalam bahasa Indonesia yang mudah dipahami

### ❤️ Curhat Mode
- Command: `/vent`
- Mode empati untuk topik emosional/personal
- Response supportif dan understanding
- Tetap dengan persona Pablos yang warm

### 📁 File & Media Storage
- Upload dan simpan foto, video, audio, dokumen
- Bot mengingat semua file yang dikirim user
- Command: `/files` untuk melihat daftar file
- Command: `/clearfiles` untuk menghapus semua file
- Metadata lengkap: nama file, ukuran, tanggal upload, caption

## 🚀 Quick Start

### Prerequisites

- Python 3.10 atau lebih tinggi
- Telegram Bot Token (dari [@BotFather](https://t.me/botfather))
- Gradient AI Access Key
- (Opsional) Redis untuk persistent memory

### Installation

1. Clone repository:
```bash
git clone <repository-url>
cd telegram-pablos-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
cp .env.example .env
# Edit .env dengan credentials Anda
```

4. Konfigurasi `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MODEL_ACCESS_KEY=your_gradient_access_key
MODEL_CHAT=anthropic-claude-opus-4
MODEL_IMAGE=stability-image-1
MAX_TOKENS=400
COOLDOWN=2

# Optional: Redis configuration
REDIS_URL=redis://:password@host:port/0
# Or individual settings:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your_password
# REDIS_USERNAME=default
```

### Running Locally

**Polling Mode (Recommended for development):**
```bash
python -m app.main
```

**Webhook Mode:**
```bash
# Set WEBHOOK_URL in .env first
export WEBHOOK_URL=https://yourdomain.com/webhook
python -m app.main
```

## 🔧 PM2 Process Management

Pablos bot includes PM2 scripts for production deployment with auto-restart and monitoring.

### Prerequisites
```bash
npm install -g pm2
```

### Quick Start with PM2

**Start the bot:**
```bash
./start.sh
```

**Restart the bot:**
```bash
./restart.sh
```

**Check status:**
```bash
./status.sh
```

**View statistics:**
```bash
./stats.sh
```

**View live logs:**
```bash
pm2 logs pablos-ai
```

**Stop the bot:**
```bash
pm2 stop pablos-ai
```

**Remove from PM2:**
```bash
pm2 delete pablos-ai
```

### PM2 Features
- ✅ Auto-restart on crash
- ✅ Process monitoring
- ✅ Log management
- ✅ Memory limit (500MB)
- ✅ Startup script support

### Setup Auto-start on Boot
```bash
pm2 startup
pm2 save
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t pablos-bot .
```

### Run Container
```bash
docker run -d \
  --name pablos-bot \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e MODEL_ACCESS_KEY=your_key \
  -e REDIS_URL=redis://your_redis_url \
  pablos-bot
```

### Using Docker Compose
```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MODEL_ACCESS_KEY=${MODEL_ACCESS_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 📝 Usage

### Commands

- `/start` - Mulai bot dan lihat welcome message
- `/help` - Tampilkan bantuan dan cara penggunaan
- `/image <deskripsi>` - Generate gambar dari deskripsi
- `/vent` - Masuk ke mode curhat/empati
- `/clear` - Hapus history percakapan
- `/files` - Lihat semua file yang sudah diupload
- `/clearfiles` - Hapus semua file yang tersimpan

### Examples

**Chat Biasa:**
```
User: Halo bro!
Pablos: Halo juga! Ada yang bisa gue bantuin? 😎
```

**Generate Gambar:**
```
/image sunset di pantai dengan burung camar terbang
```

**Code Help:**
````
```python
def calculate(a, b):
    return a + b
```
````

atau:
```
explain: def calculate(a, b): return a + b
```

**Curhat Mode:**
```
/vent
User: Gue lagi stress banget nih...
Pablos: Gue dengerin kok bro. Ceritain aja, apa yang bikin lu stress? 💙
```

**Upload File:**
```
[User uploads a photo]
Pablos: Oke jir, foto lu udah gue simpen! 📸
Total file lu sekarang: 1

Ketik /files buat liat semua file lu
```

**List Files:**
```
/files
Pablos: 📁 File lu (3 total):

1. 🖼️ photo_ABC123.jpg
   Type: photo | Size: 245.3 KB | 23/10/2025 14:30
   Caption: Sunset di pantai

2. 📄 document.pdf
   Type: document | Size: 1.2 MB | 23/10/2025 15:45

3. 🎥 video_XYZ789.mp4
   Type: video | Size: 5.8 MB | 23/10/2025 16:20
```

## 🏗️ Architecture

```
pablos-ai/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Entry point & bot setup
│   ├── handlers.py          # Command & message handlers
│   ├── ai_client.py         # Gradient AI wrapper
│   ├── prompts.py           # Prompt templates
│   ├── memory.py            # Conversation memory (Redis/in-memory)
│   ├── file_storage.py      # File/media storage manager
│   └── utils.py             # Utilities (chunking, rate limiting, cache)
├── tests/                   # Unit tests
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Token dari BotFather |
| `MODEL_ACCESS_KEY` | Yes | - | Gradient AI access key |
| `MODEL_CHAT` | No | `anthropic-claude-opus-4` | Chat model name |
| `MODEL_IMAGE` | No | `stability-image-1` | Image model name |
| `MAX_TOKENS` | No | `400` | Max tokens per response |
| `COOLDOWN` | No | `2` | Cooldown seconds per user |
| `REDIS_URL` | No | - | Redis connection URL |
| `WEBHOOK_URL` | No | - | Webhook URL (for webhook mode) |
| `PORT` | No | `8443` | Port for webhook server |

### Redis Configuration

Bot mendukung dua cara konfigurasi Redis:

**Option 1: Redis URL**
```env
REDIS_URL=redis://:password@host:port/0
```

**Option 2: Individual Settings**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_USERNAME=default
```

Jika Redis tidak tersedia, bot akan otomatis fallback ke in-memory storage.

## 🧪 Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📊 Monitoring & Logging

Bot menggunakan Python logging dengan output ke:
- Console (stdout)
- File: `pablos_bot.log`

Log levels:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Errors with stack traces
- DEBUG: Detailed debugging info

## 🔒 Security & Best Practices

1. **Never commit secrets**: Use `.env` file and add to `.gitignore`
2. **Rate limiting**: Built-in per-user cooldown to prevent spam
3. **Input sanitization**: All user inputs are sanitized
4. **Error handling**: Comprehensive error handling with user-friendly messages
5. **Docker security**: Runs as non-root user in container

## 🚀 Deployment Options

### DigitalOcean App Platform
1. Fork repository
2. Connect to DigitalOcean
3. Set environment variables
4. Deploy!

### Railway
```bash
railway login
railway init
railway add
# Set environment variables in dashboard
railway up
```

### Heroku
```bash
heroku create pablos-bot
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set MODEL_ACCESS_KEY=your_key
git push heroku main
```

### VPS (Manual)
```bash
# Clone and setup
git clone <repo>
cd telegram-pablos-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup systemd service
sudo nano /etc/systemd/system/pablos-bot.service
sudo systemctl enable pablos-bot
sudo systemctl start pablos-bot
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for your own purposes.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Gradient AI](https://gradient.ai/) - AI model provider
- [Redis](https://redis.io/) - In-memory data store

## 📞 Support

Jika ada pertanyaan atau issues:
1. Check existing issues
2. Create new issue dengan detail lengkap
3. Atau contact maintainer

---

Made with ❤️ by the Pablos team

