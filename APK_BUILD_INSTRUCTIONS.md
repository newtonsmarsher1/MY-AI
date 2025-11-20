# 📱 Build EDU AI Android APK - Complete Guide

## 🚀 Quick Start (Easiest Method)

### Method 1: PWA Builder (Recommended for Beginners)

**This is the easiest way - no coding required!**

1. **Deploy your Flask app first:**
   ```bash
   # Deploy to Vercel (if not already done)
   vercel --prod
   
   # Or deploy to Render, Heroku, etc.
   # Get your public URL, e.g., https://my-edu-ai.vercel.app
   ```

2. **Visit PWA Builder:**
   - Go to https://www.pwabuilder.com/
   - Paste your deployed URL
   - Click "Start"

3. **Generate Android Package:**
   - Click the "Android" tab
   - Click "Generate Package"
   - Download the ZIP file

4. **Build APK in Android Studio:**
   - Extract the downloaded ZIP
   - Open the folder in Android Studio
   - Wait for Gradle sync
   - **Build > Generate Signed Bundle / APK**
   - Select "APK"
   - Create a new keystore (first time) or use existing
   - Build and download your APK!

5. **Install on Android:**
   - Transfer APK to your Android device
   - Enable "Install from Unknown Sources" in settings
   - Install and enjoy!

---

## 🛠️ Method 2: Using Capacitor (For Developers)

### Prerequisites:
- Node.js (v14+)
- Android Studio
- Java JDK 11+

### Steps:

```bash
# 1. Initialize npm (if not done)
cd C:\Users\PC\Desktop\AI
npm init -y

# 2. Install Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/android

# 3. Initialize Capacitor
npx cap init "EDU AI" "com.eduai.app"

# When prompted:
# - Web dir: templates (or create a 'dist' folder)
# - Package ID: com.eduai.app

# 4. Add Android platform
npx cap add android

# 5. Sync your web assets
npx cap sync

# 6. Open in Android Studio
npx cap open android
```

**In Android Studio:**
- Wait for Gradle sync
- **Build > Build Bundle(s) / APK(s) > Build APK(s)**
- APK will be in `android/app/build/outputs/apk/`

---

## 📦 Method 3: Manual WebView Wrapper

Use the provided `android-webview/` project:

1. **Open in Android Studio:**
   - File > Open > Select `android-webview/` folder

2. **Update the URL:**
   - Edit `app/src/main/java/com/eduai/app/MainActivity.java`
   - Replace `APP_URL` with your deployed Flask app URL:
   ```java
   private static final String APP_URL = "https://your-app.vercel.app";
   ```

3. **Build APK:**
   - **Build > Build Bundle(s) / APK(s)**
   - Select "APK"
   - Build

---

## 🎨 Generate App Icons

Before building, create app icons:

```bash
# Option 1: Use the Python script
python generate_icons.py

# Option 2: Create manually
# Create icon-192.png (192x192) and icon-512.png (512x512)
# Place them in static/ folder
```

**Online icon generators:**
- https://www.favicon-generator.org/
- https://realfavicongenerator.net/
- https://realfavicongenerator.net/favicon_generator

---

## 🌐 Deploy Your Backend First

**Important:** Your Flask app must be deployed and publicly accessible!

### Option A: Deploy to Vercel
```bash
vercel --prod
```

### Option B: Deploy to Render
1. Connect your GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Deploy

### Option C: Use ngrok for Testing
```bash
# Install ngrok
npm install -g ngrok

# Start Flask
python app.py

# In another terminal
ngrok http 5000

# Use the ngrok URL in your Android app
```

---

## ✅ Testing Checklist

Before publishing:

- [ ] App loads correctly on Android device
- [ ] All features work (chat, uploads, auth)
- [ ] Internet connection required message shows when offline
- [ ] App icon displays correctly
- [ ] App name shows as "EDU AI"
- [ ] Back button works correctly
- [ ] No crashes or errors in logcat

---

## 🐛 Troubleshooting

### App shows blank screen
- ✅ Check your Flask app URL is correct in MainActivity.java
- ✅ Verify your backend is deployed and accessible
- ✅ Check Android logcat: `adb logcat | grep WebView`

### Can't connect to server
- ✅ Test URL in browser first
- ✅ Check internet permissions in AndroidManifest.xml
- ✅ Verify CORS is enabled on Flask backend

### Build errors
- ✅ Update Android Studio
- ✅ Sync Gradle: File > Sync Project with Gradle Files
- ✅ Clean project: Build > Clean Project
- ✅ Invalidate caches: File > Invalidate Caches / Restart

### Icons not showing
- ✅ Ensure icons are in `static/` folder
- ✅ Check manifest.json paths are correct
- ✅ Clear app cache and reinstall

---

## 📱 Publishing to Google Play Store

1. **Create Google Play Developer Account:**
   - Visit https://play.google.com/console
   - Pay $25 one-time fee

2. **Build Signed APK/AAB:**
   - **Build > Generate Signed Bundle / APK**
   - Select "Android App Bundle" (recommended) or "APK"
   - Create keystore (save it securely!)
   - Build

3. **Upload to Play Console:**
   - Create new app
   - Upload AAB/APK
   - Fill store listing (description, screenshots, etc.)
   - Set pricing (Free)
   - Submit for review

---

## 📝 Important Notes

- **Internet Required:** The app needs internet to connect to your Flask backend
- **Update URL:** Always update `APP_URL` in MainActivity.java with your production URL
- **Test First:** Test thoroughly on real devices before publishing
- **Keystore:** Save your keystore file securely - you'll need it for updates!

---

## 🎉 You're Done!

Your EDU AI app is now ready as an Android APK! 

**Next Steps:**
1. Test on multiple Android devices
2. Get user feedback
3. Publish to Google Play Store
4. Share with users!

For questions, check the main `BUILD_APK.md` file or the Android project README.

