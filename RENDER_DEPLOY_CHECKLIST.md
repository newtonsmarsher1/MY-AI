# ✅ Render Deployment Checklist

Quick checklist to deploy your EDU AI to Render.com

## 📝 Pre-Deployment

- [x] ✅ `Procfile` created with gunicorn command
- [x] ✅ `requirements.txt` includes gunicorn
- [x] ✅ `render.yaml` created (optional)
- [x] ✅ `runtime.txt` specifies Python 3.11
- [x] ✅ Code pushed to GitHub

## 🚀 Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Create Render Account
- [ ] Sign up at https://render.com
- [ ] Verify email

### 3. Connect GitHub
- [ ] Connect GitHub account in Render
- [ ] Authorize Render to access repositories

### 4. Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Select your repository
- [ ] Configure:
  - Name: `edu-ai`
  - Region: Choose closest
  - Branch: `main`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

### 5. Set Environment Variables
Add in Render Dashboard → Environment:
- [ ] `GROQ_API_KEY` (required - get from https://console.groq.com)
- [ ] `OPENAI_API_KEY` (optional)
- [ ] `TAVILY_API_KEY` (optional)
- [ ] `SUPABASE_URL` (optional)
- [ ] `SUPABASE_ANON_KEY` (optional)
- [ ] `ENABLE_WEB_SEARCH=true` (optional)
- [ ] `AI_TEMPERATURE=0.65` (optional)

### 6. Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for build (5-10 minutes)
- [ ] Check logs for errors
- [ ] Test your app URL

## 🧪 Post-Deployment Testing

- [ ] App loads correctly
- [ ] Can ask questions
- [ ] AI responses work
- [ ] Streaming works
- [ ] File uploads work (if enabled)
- [ ] Authentication works (if enabled)

## 📊 Your App URL

After deployment, your app will be at:
```
https://your-app-name.onrender.com
```

## ⚠️ Important Notes

1. **Free Tier**: Spins down after 15 min inactivity (first request takes ~30s)
2. **Uploads**: Files are ephemeral on free tier - use cloud storage for production
3. **Environment Variables**: Set all API keys in Render dashboard
4. **Logs**: Check Render dashboard → Logs for debugging

## 🆘 Troubleshooting

- **Build fails**: Check `requirements.txt` and build logs
- **App crashes**: Check environment variables and logs
- **Timeout**: Increase timeout in start command
- **Static files**: Verify `static/` folder is in repo

## ✅ Done!

Once all checked, your app is live! 🎉

---

**Quick Deploy Command Reference:**
```bash
# Build Command
pip install -r requirements.txt

# Start Command  
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

