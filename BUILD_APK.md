# Build EDU AI Android APK

## Quick Start (Easiest Method)

### Option 1: Use PWA Builder (No coding required)

1. **Deploy your Flask app** to a public URL (Vercel, Render, etc.)
2. Visit https://www.pwabuilder.com/
3. Enter your deployed URL
4. Click "Start" → "Android" → Download
5. Open the downloaded project in Android Studio
6. Build > Generate Signed Bundle / APK

### Option 2: Use Capacitor (Recommended for developers)

```bash
# Install Node.js dependencies
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialize Capacitor
npx cap init "EDU AI" "com.eduai.app"

# Add Android platform
npx cap add android

# Sync web assets
npx cap sync

# Open in Android Studio
npx cap open android
```

Then in Android Studio: **Build > Build Bundle(s) / APK(s)**

### Option 3: Use the WebView wrapper

1. Open `android-webview/` folder in Android Studio
2. Edit `MainActivity.java` - replace `APP_URL` with your deployed URL
3. Build the APK

## Prerequisites

- **Android Studio** (latest version)
- **Java JDK 11+**
- **Your Flask app deployed** to a public URL

## Step-by-Step: PWA Builder Method

1. **Deploy your app:**
   ```bash
   # If using Vercel
   vercel --prod
   
   # Or deploy to Render, Heroku, etc.
   ```

2. **Get your public URL:**
   - Example: `https://my-edu-ai.vercel.app`

3. **Visit PWA Builder:**
   - Go to https://www.pwabuilder.com/
   - Paste your URL
   - Click "Start"

4. **Generate Android package:**
   - Click "Android" tab
   - Click "Generate Package"
   - Download the ZIP file

5. **Build in Android Studio:**
   - Extract the ZIP
   - Open the folder in Android Studio
   - Wait for Gradle sync
   - Build > Generate Signed Bundle / APK
   - Create keystore (first time only)
   - Build APK

6. **Install on device:**
   - Transfer APK to Android device
   - Enable "Install from Unknown Sources"
   - Install and test

## Creating App Icons

Create these icon files in `static/` folder:
- `icon-192.png` (192x192 pixels)
- `icon-512.png` (512x512 pixels)

You can use online tools like:
- https://www.favicon-generator.org/
- https://realfavicongenerator.net/

## Troubleshooting

**Issue: App shows blank screen**
- Check that your Flask app URL is correct
- Ensure CORS is enabled on your backend
- Check Android logcat for errors

**Issue: Can't connect to server**
- Verify your app is deployed and accessible
- Check internet permissions in AndroidManifest.xml
- Test URL in browser first

**Issue: Build errors**
- Update Android Studio to latest version
- Sync Gradle files: File > Sync Project with Gradle Files
- Clean project: Build > Clean Project

## Testing Locally

For local testing, use ngrok:

```bash
# Install ngrok
npm install -g ngrok

# Start Flask app
python app.py

# In another terminal, expose it
ngrok http 5000

# Use the ngrok URL in your Android app
```

## Publishing to Google Play

1. Create a Google Play Developer account ($25 one-time fee)
2. Build a signed APK or AAB (Android App Bundle)
3. Upload to Google Play Console
4. Fill in store listing, screenshots, etc.
5. Submit for review

## Notes

- The app requires internet connection
- All API calls go to your Flask backend
- Update `APP_URL` in MainActivity.java with your production URL
- Test thoroughly on real devices before publishing

