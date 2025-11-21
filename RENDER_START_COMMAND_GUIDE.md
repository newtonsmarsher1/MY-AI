# 📍 Where to Enter Start Command in Render

## Step-by-Step: Where to Put the Start Command

### 1. Go to Render Dashboard
- Visit: https://dashboard.render.com
- Log in to your account

### 2. Create New Web Service
- Click the **"New +"** button (top right)
- Select **"Web Service"**

### 3. Connect Your Repository
- Connect GitHub (if not already connected)
- Select your repository: `newtonsmarsher1/MY-AI`
- Click **"Connect"**

### 4. Configure Your Service

You'll see a form with these fields:

#### **Name**
```
edu-ai
```
(or any name you prefer)

#### **Region**
Choose the closest region to you (e.g., "Oregon (US West)")

#### **Branch**
```
main
```

#### **Root Directory**
Leave **empty** (or put `.` if needed)

#### **Runtime**
Select: **Python 3**

#### **Build Command** ⬅️ HERE
```
pip install -r requirements.txt
```

#### **Start Command** ⬅️ HERE (THIS IS WHERE!)
```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

#### **Instance Type**
- **Free** (for testing)
- **Starter** ($7/month - always on)

### 5. Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these one by one:
- Key: `GROQ_API_KEY` → Value: `your-groq-key`
- Key: `OPENAI_API_KEY` → Value: `your-openai-key` (optional)
- Key: `ENABLE_WEB_SEARCH` → Value: `true` (optional)

### 6. Deploy!

Click the **"Create Web Service"** button at the bottom.

---

## 🎯 Visual Guide

```
Render Dashboard
└── New + → Web Service
    └── Repository: newtonsmarsher1/MY-AI
        └── Configuration Form
            ├── Name: edu-ai
            ├── Region: [Select]
            ├── Branch: main
            ├── Root Directory: [empty]
            ├── Runtime: Python 3
            ├── Build Command: pip install -r requirements.txt  ⬅️
            ├── Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120  ⬅️
            └── Instance Type: Free
```

---

## 📋 Copy-Paste Ready Commands

### Build Command:
```bash
pip install -r requirements.txt
```

### Start Command:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

---

## ⚠️ Important Notes

1. **$PORT is automatic** - Render sets this automatically, don't change it
2. **Copy exactly** - Make sure there are no extra spaces
3. **Case sensitive** - Commands are case-sensitive
4. **No quotes needed** - Don't wrap commands in quotes

---

## 🔍 Can't Find It?

If you don't see the fields:
1. Make sure you selected **"Web Service"** (not Static Site)
2. Make sure you selected **Python 3** as runtime
3. Scroll down - the form might be long

---

## ✅ After Entering Commands

1. Add environment variables (click "Advanced")
2. Choose your plan (Free or Starter)
3. Click **"Create Web Service"**
4. Wait 5-10 minutes for build
5. Your app will be live!

---

**Your app URL will be**: `https://your-app-name.onrender.com`

Need help? Check the full guide in `DEPLOY_RENDER.md`






