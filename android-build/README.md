# EDU AI Android APK Build Guide

This guide will help you build an Android APK from the EDU AI web app.

## Method 1: Using Capacitor (Recommended)

### Prerequisites
- Node.js (v14 or higher)
- Android Studio
- Java JDK 11 or higher

### Steps

1. **Install Capacitor CLI globally:**
```bash
npm install -g @capacitor/cli
```

2. **Initialize Capacitor in your project:**
```bash
cd C:\Users\PC\Desktop\AI
npm init -y
npm install @capacitor/core @capacitor/cli
npx cap init
```

When prompted:
- App name: `EDU AI`
- App ID: `com.eduai.app`
- Web dir: `templates` (or create a `dist` folder)

3. **Add Android platform:**
```bash
npm install @capacitor/android
npx cap add android
```

4. **Configure your Flask server URL:**
Edit `android/app/src/main/java/com/eduai/app/MainActivity.java` and set your server URL.

5. **Build the APK:**
```bash
npx cap sync
npx cap open android
```

6. **In Android Studio:**
- Wait for Gradle sync to complete
- Go to Build > Generate Signed Bundle / APK
- Select APK
- Create a keystore (or use existing)
- Build the APK

## Method 2: Using PWA Builder (Easiest)

1. Visit https://www.pwabuilder.com/
2. Enter your deployed web app URL
3. Click "Start" and follow the wizard
4. Download the generated Android project
5. Open in Android Studio and build

## Method 3: Manual WebView Wrapper

See `android-webview/` folder for a simple WebView Android project.

### Quick Build Steps:

1. Open `android-webview/` in Android Studio
2. Update `MainActivity.java` with your server URL
3. Build > Build Bundle(s) / APK(s) > Build APK(s)

## Deploying Your Backend

Before building the APK, make sure your Flask app is deployed and accessible:

- **Option A:** Deploy to a cloud service (Vercel, Render, Heroku)
- **Option B:** Use ngrok for local testing: `ngrok http 5000`
- **Option C:** Use a VPS with a public IP

Update the URL in the Android app to point to your deployed backend.

## Testing

1. Install the APK on an Android device
2. Enable "Install from Unknown Sources" if needed
3. Open the app and test all features

## Notes

- The app requires internet connection to communicate with your Flask backend
- For offline support, implement more caching in the service worker
- Update app icons in `android/app/src/main/res/` folders

