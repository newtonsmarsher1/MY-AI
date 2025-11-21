# 🆓 Free AI Setup Guide

Your app now supports **100% FREE** AI providers! No credit card needed.

## Option 1: Ollama (Recommended - 100% Free) ⭐

Ollama runs AI models locally on your computer - completely free, no API keys, no limits!

### Setup Steps:

1. **Download Ollama**
   - Visit: https://ollama.ai
   - Download and install for Windows

2. **Pull a Model** (choose one):
   ```powershell
   ollama pull llama2
   # OR
   ollama pull mistral
   # OR
   ollama pull llama3
   ```

3. **Start Ollama** (it runs automatically after installation)

4. **That's it!** Your app will automatically detect and use Ollama.

### Available Models:
- `llama2` - Good general purpose
- `mistral` - Fast and efficient
- `llama3` - Latest and most capable
- `phi` - Small and fast

---

## Option 2: Groq (Free API Tier) 🚀

Groq offers a free API tier with very fast responses!

### Setup Steps:

1. **Get Free API Key**
   - Visit: https://console.groq.com
   - Sign up (free, no credit card)
   - Go to API Keys section
   - Create a new API key

2. **Add to .env file**
   ```powershell
   cd C:\Users\PC\Desktop\AI
   # Edit .env file and add:
   GROQ_API_KEY=your-groq-api-key-here
   ```

3. **Restart the app** - It will automatically use Groq!

### Benefits:
- ✅ Very fast responses
- ✅ Free tier with generous limits
- ✅ No local installation needed
- ✅ Works immediately

---

## Option 3: OpenAI (Paid) 💳

If you have OpenAI credits, it will work automatically with your existing API key.

---

## How It Works

The app automatically tries providers in this order:
1. **Ollama** (if running) - 100% free
2. **Groq** (if API key set) - Free tier
3. **OpenAI** (if API key set) - Paid

If one fails, it automatically tries the next one!

---

## Quick Start (Ollama)

```powershell
# 1. Install Ollama from https://ollama.ai

# 2. Pull a model
ollama pull llama2

# 3. Start your app
cd C:\Users\PC\Desktop\AI
python app.py

# 4. Open http://localhost:5000
```

That's it! You now have a completely free AI assistant! 🎉

---

## Troubleshooting

**Ollama not detected?**
- Make sure Ollama is running
- Check: `ollama list` should show your models
- Restart your Flask app

**Groq not working?**
- Verify your API key in `.env` file
- Check: https://console.groq.com for API status
- Make sure you've added `GROQ_API_KEY=...` to `.env`

**Want to switch providers?**
- Just restart the app - it auto-detects!
- Ollama takes priority if running
- You can stop Ollama to use Groq instead

---

Enjoy your free AI assistant! 🚀








