# 🚀 Deploy EDU AI to Render.com

Complete guide to deploy your EDU AI Flask app to Render.com

## 📋 Prerequisites

1. **GitHub Account** - Render connects via GitHub
2. **Render Account** - Sign up at https://render.com (free tier available)
3. **Your code pushed to GitHub** - Make sure your code is in a GitHub repository

## 🚀 Quick Deploy Steps

### Step 1: Push to GitHub

If you haven't already, push your code to GitHub:

```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Ready for Render deployment"

# Add your GitHub remote
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Sign up or log in

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub account (if not already)
   - Select your repository

3. **Configure Service**
   - **Name**: `edu-ai` (or your preferred name)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (or `.` if needed)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

4. **Set Environment Variables**
   Click "Advanced" → "Add Environment Variable" and add:

   **Required (at least one AI provider):**
   ```
   GROQ_API_KEY=your-groq-api-key
   ```

   **Optional:**
   ```
   OPENAI_API_KEY=your-openai-key
   TAVILY_API_KEY=your-tavily-key
   SUPABASE_URL=your-supabase-url
   SUPABASE_ANON_KEY=your-supabase-key
   AI_TEMPERATURE=0.65
   ENABLE_WEB_SEARCH=true
   GROQ_MODEL=llama-3.1-70b-versatile
   OPENAI_MODEL=gpt-4o-mini
   ```

5. **Choose Plan**
   - **Free**: Good for testing (spins down after inactivity)
   - **Starter ($7/month)**: Always on, better performance

6. **Deploy!**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes first time)
   - Your app will be live at `https://your-app-name.onrender.com`

## 🔧 Configuration Details

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

### Port Configuration
Render automatically sets `$PORT` - your app will use it automatically.

## 📁 File Structure

Your project should have:
```
AI/
├── app.py                 # Main Flask app
├── requirements.txt       # Python dependencies
├── Procfile              # Render start command
├── render.yaml           # Optional: Infrastructure as code
├── templates/
│   └── index.html        # Frontend
├── static/               # Static files (icons, manifest)
└── uploads/              # User uploads (create if needed)
```

## 🔐 Environment Variables

### Required (at least one):
- `GROQ_API_KEY` - Get free key: https://console.groq.com

### Optional:
- `OPENAI_API_KEY` - For OpenAI models
- `TAVILY_API_KEY` - For better web search
- `SUPABASE_URL` - For authentication
- `SUPABASE_ANON_KEY` - For authentication
- `AI_TEMPERATURE` - Default: 0.65
- `ENABLE_WEB_SEARCH` - Default: true
- `GROQ_MODEL` - Default: llama-3.1-70b-versatile
- `OPENAI_MODEL` - Default: gpt-4o-mini

## 🗂️ Static Files & Uploads

### Static Files
Your `static/` folder (icons, manifest) will be served automatically by Flask.

### Uploads Folder
Render's filesystem is ephemeral. For production:
- **Option 1**: Use cloud storage (AWS S3, Cloudinary, etc.)
- **Option 2**: Use Render's disk (persists but limited on free tier)
- **Option 3**: Store in database (Supabase, PostgreSQL)

## 🐛 Troubleshooting

### Build Fails
- Check `requirements.txt` has all dependencies
- Verify Python version (3.11 recommended)
- Check build logs in Render dashboard

### App Crashes
- Check logs: Render Dashboard → Your Service → Logs
- Verify environment variables are set
- Check if port is correctly configured

### Static Files Not Loading
- Ensure `static/` folder is in root directory
- Check Flask static folder configuration
- Verify file paths in templates

### Timeout Issues
- Increase timeout in start command: `--timeout 300`
- Check if web search is taking too long
- Optimize AI provider calls

### Free Tier Spins Down
- Free tier spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- Upgrade to Starter plan ($7/month) for always-on

## 📊 Monitoring

- **Logs**: View in Render Dashboard → Your Service → Logs
- **Metrics**: Available on paid plans
- **Health Checks**: Automatic on Render

## 🔄 Updates

To update your app:
1. Push changes to GitHub
2. Render automatically detects and redeploys
3. Or manually trigger: Dashboard → Your Service → Manual Deploy

## 💡 Tips

1. **Use Free Tier for Testing**: Test thoroughly before upgrading
2. **Monitor Logs**: Check logs regularly for errors
3. **Set All Environment Variables**: Don't forget API keys
4. **Test After Deploy**: Verify all features work
5. **Backup Your .env**: Keep a copy of environment variables

## 🎉 You're Done!

Your EDU AI app is now live on Render!

**Your app URL**: `https://your-app-name.onrender.com`

Share it with users and enjoy! 🚀

---

**Need Help?**
- Render Docs: https://render.com/docs
- Render Support: support@render.com
- Check logs in Render Dashboard

