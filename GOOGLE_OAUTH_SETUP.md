# 🔑 **Google OAuth Setup for Production**

## **Domain: getspaced.app**

### **📋 Setup Checklist for Production Deployment**

#### **1. Firebase Console Configuration**
1. **Go to Firebase Console** → `spaced-b571d` project
2. **Authentication** → **Sign-in method** → **Google**
3. **Add authorized domains:**
   - `getspaced.app`
   - `www.getspaced.app`
   - Any staging domains (e.g., `staging.getspaced.app`)

#### **2. Google Cloud Console (OAuth Consent Screen)**
1. **Visit:** [Google Cloud Console](https://console.cloud.google.com/)
2. **Select project:** `spaced-b571d`
3. **APIs & Services** → **OAuth consent screen**
4. **Configure OAuth consent screen:**
   - **App name:** Spaced
   - **User support email:** Your email
   - **Developer contact information:** Your email
   - **Authorized domains:** 
     - `getspaced.app`
   - **Scopes:** Add required scopes (usually email, profile, openid)

#### **3. OAuth 2.0 Client IDs**
1. **APIs & Services** → **Credentials**
2. **Create credentials** → **OAuth 2.0 Client IDs**
3. **Web application type**
4. **Authorized redirect URIs:**
   ```
   https://getspaced.app/__/auth/handler
   https://www.getspaced.app/__/auth/handler
   ```

#### **4. Update Firebase Configuration (if needed)**
- The existing `firebase_options.dart` should work automatically
- Firebase handles OAuth flow internally

### **🧪 Testing Google OAuth**

#### **Local Development (Won't Work):**
- ❌ `localhost` not in authorized domains
- ❌ OAuth consent screen not configured for local

#### **Production (getspaced.app):**
- ✅ Should work after domain authorization
- ✅ Users can sign in with Google accounts

### **🚀 Deployment Steps**

1. **Deploy app to `getspaced.app`**
2. **Add domain to Firebase authorized domains**
3. **Configure OAuth consent screen**
4. **Test Google sign-in on production**

### **🔍 Troubleshooting**

#### **Common Issues:**
- **"redirect_uri_mismatch"** → Check authorized domains in Firebase
- **"invalid_client"** → Verify OAuth client configuration
- **"access_blocked"** → Complete OAuth consent screen setup

#### **Debug Steps:**
1. Check browser console for detailed error messages
2. Verify Firebase Auth configuration
3. Confirm domain authorization in Firebase Console
4. Test with different Google accounts

### **📝 Current Status**
- ✅ Firebase project configured (`spaced-b571d`)
- ✅ Google OAuth enabled in Firebase Auth
- ⏳ **Pending:** Domain authorization for `getspaced.app`
- ⏳ **Pending:** OAuth consent screen configuration
- ⏳ **Pending:** Production deployment

### **🔐 Security Notes**
- OAuth client secrets are managed by Firebase
- No sensitive credentials need to be stored in the app
- Firebase handles the OAuth flow securely
- API keys in `firebase_options.dart` are safe to commit (client-side only)

---

**Ready for production once deployed to `getspaced.app` and domains are authorized!** 