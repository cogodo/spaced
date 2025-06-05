# 🔥 **Firebase & Authentication Implementation Plan**
## Complete Setup Guide for Spaced Repetition App

---

## 📋 **Phase 1: Firebase Project Setup**

### **1.1 Firebase Console Configuration**
- [ ] Create new Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
- [ ] Enable Google Analytics (optional but recommended)
- [ ] Configure project settings (name: "spaced-repetition-app")
- [ ] Set up billing account for production features

### **1.2 Firebase Services Activation**
- [ ] **Authentication**
  - [ ] Enable Email/Password provider
  - [ ] Enable Google Sign-In provider  
  - [ ] Enable Anonymous Sign-In provider
  - [ ] Configure authorized domains
- [ ] **Firestore Database**
  - [ ] Create database in production mode
  - [ ] Choose multi-region location (nam5 for North America)
  - [ ] Set up initial security rules
- [ ] **Firebase Storage** (for future file uploads)
  - [ ] Enable with default settings
- [ ] **Firebase Hosting** (for web deployment)
  - [ ] Enable for Flutter web hosting

### **1.3 Platform Registration**
- [ ] **Android App Registration**
  - [ ] Add Android app with package name: `com.example.spaced_repetition`
  - [ ] Download `google-services.json`
  - [ ] Configure SHA-1 fingerprints for Google Sign-In
- [ ] **iOS App Registration**
  - [ ] Add iOS app with bundle ID: `com.example.spacedRepetition`
  - [ ] Download `GoogleService-Info.plist`
  - [ ] Configure URL schemes
- [ ] **Web App Registration**
  - [ ] Add web app with name: "Spaced Repetition Web"
  - [ ] Copy Firebase config object

---

## 📋 **Phase 2: Flutter Firebase Integration**

### **2.1 Dependencies Setup**
```yaml
# pubspec.yaml additions
dependencies:
  # Firebase Core
  firebase_core: ^2.24.2
  
  # Authentication
  firebase_auth: ^4.15.3
  google_sign_in: ^6.1.6
  
  # Firestore
  cloud_firestore: ^4.13.6
  
  # UI Components
  firebase_ui_auth: ^1.9.4
  firebase_ui_firestore: ^1.5.10
  
  # State Management
  provider: ^6.1.1
  shared_preferences: ^2.2.2

dev_dependencies:
  # Firebase testing
  fake_cloud_firestore: ^2.4.9
  firebase_auth_mocks: ^0.13.0
```

### **2.2 Platform Configuration**

#### **Android Setup**
```gradle
// android/app/build.gradle
android {
    compileSdkVersion 34
    defaultConfig {
        minSdkVersion 21  // Required for Firebase
        targetSdkVersion 34
        multiDexEnabled true  // For large apps
    }
}

dependencies {
    implementation 'androidx.multidex:multidex:2.0.1'
}
```

```gradle
// android/build.gradle
dependencies {
    classpath 'com.google.gms:google-services:4.4.0'
}
```

```gradle
// android/app/build.gradle (bottom)
apply plugin: 'com.google.gms.google-services'
```

#### **iOS Setup**
```xml
<!-- ios/Runner/Info.plist -->
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLName</key>
        <string>REVERSED_CLIENT_ID</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>YOUR_REVERSED_CLIENT_ID</string>
        </array>
    </dict>
</array>
```

#### **Web Setup**
```html
<!-- web/index.html -->
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-firestore-compat.js"></script>
```

### **2.3 Firebase Initialization**
```dart
// lib/firebase_options.dart (auto-generated)
// Run: flutter packages pub run flutterfire_cli:flutterfire configure

// lib/main.dart
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  runApp(MyApp());
}
```

---

## 📋 **Phase 3: Authentication System Implementation**

### **3.1 Authentication Service**
```dart
// lib/services/auth_service.dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  // Current user stream
  Stream<User?> get authStateChanges => _auth.authStateChanges();
  
  // Current user
  User? get currentUser => _auth.currentUser;
  
  // Email & Password Sign Up
  Future<UserCredential?> signUpWithEmail(String email, String password) async {
    try {
      UserCredential result = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Send email verification
      await result.user?.sendEmailVerification();
      
      return result;
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }
  
  // Email & Password Sign In
  Future<UserCredential?> signInWithEmail(String email, String password) async {
    try {
      return await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }
  
  // Google Sign In
  Future<UserCredential?> signInWithGoogle() async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;
      
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );
      
      return await _auth.signInWithCredential(credential);
    } catch (e) {
      throw Exception('Google sign-in failed: $e');
    }
  }
  
  // Anonymous Sign In
  Future<UserCredential?> signInAnonymously() async {
    try {
      return await _auth.signInAnonymously();
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }
  
  // Password Reset
  Future<void> resetPassword(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }
  
  // Sign Out
  Future<void> signOut() async {
    await Future.wait([
      _auth.signOut(),
      _googleSignIn.signOut(),
    ]);
  }
  
  // Delete Account
  Future<void> deleteAccount() async {
    final user = currentUser;
    if (user != null) {
      await user.delete();
    }
  }
  
  // Handle Firebase Auth Exceptions
  String _handleAuthException(FirebaseAuthException e) {
    switch (e.code) {
      case 'weak-password':
        return 'The password provided is too weak.';
      case 'email-already-in-use':
        return 'An account already exists for that email.';
      case 'user-not-found':
        return 'No user found for that email.';
      case 'wrong-password':
        return 'Wrong password provided.';
      case 'invalid-email':
        return 'The email address is not valid.';
      case 'user-disabled':
        return 'This user account has been disabled.';
      case 'too-many-requests':
        return 'Too many failed attempts. Please try again later.';
      default:
        return 'An error occurred. Please try again.';
    }
  }
}
```

### **3.2 User Model & Firestore Integration**
```dart
// lib/models/user_model.dart
import 'package:cloud_firestore/cloud_firestore.dart';

class UserModel {
  final String uid;
  final String email;
  final String? displayName;
  final String? photoURL;
  final DateTime createdAt;
  final DateTime lastActive;
  final bool isAnonymous;

  UserModel({
    required this.uid,
    required this.email,
    this.displayName,
    this.photoURL,
    required this.createdAt,
    required this.lastActive,
    required this.isAnonymous,
  });

  factory UserModel.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return UserModel(
      uid: doc.id,
      email: data['email'] ?? '',
      displayName: data['displayName'],
      photoURL: data['photoURL'],
      createdAt: (data['createdAt'] as Timestamp).toDate(),
      lastActive: (data['lastActive'] as Timestamp).toDate(),
      isAnonymous: data['isAnonymous'] ?? false,
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'email': email,
      'displayName': displayName,
      'photoURL': photoURL,
      'createdAt': Timestamp.fromDate(createdAt),
      'lastActive': Timestamp.fromDate(lastActive),
      'isAnonymous': isAnonymous,
    };
  }
}
```

### **3.3 Authentication Screens**

#### **Login Screen**
```dart
// lib/screens/auth/login_screen.dart
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _authService = AuthService();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // App Logo/Title
              Text(
                'Spaced Repetition',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              SizedBox(height: 48),
              
              // Email/Password Form
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    TextFormField(
                      controller: _emailController,
                      decoration: InputDecoration(
                        labelText: 'Email',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value?.isEmpty ?? true) return 'Email required';
                        if (!value!.contains('@')) return 'Invalid email';
                        return null;
                      },
                    ),
                    SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                      validator: (value) {
                        if (value?.isEmpty ?? true) return 'Password required';
                        if (value!.length < 6) return 'Password too short';
                        return null;
                      },
                    ),
                  ],
                ),
              ),
              
              SizedBox(height: 24),
              
              // Sign In Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _signInWithEmail,
                  child: _isLoading 
                    ? CircularProgressIndicator()
                    : Text('Sign In'),
                ),
              ),
              
              SizedBox(height: 16),
              
              // Google Sign In
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _isLoading ? null : _signInWithGoogle,
                  icon: Icon(Icons.login),
                  label: Text('Sign in with Google'),
                ),
              ),
              
              SizedBox(height: 16),
              
              // Anonymous Sign In
              TextButton(
                onPressed: _isLoading ? null : _signInAnonymously,
                child: Text('Continue as Guest'),
              ),
              
              SizedBox(height: 16),
              
              // Navigation to Sign Up
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("Don't have an account? "),
                  TextButton(
                    onPressed: () => Navigator.pushNamed(context, '/signup'),
                    child: Text('Sign Up'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _signInWithEmail() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      await _authService.signInWithEmail(
        _emailController.text.trim(),
        _passwordController.text,
      );
      // Navigation handled by AuthWrapper
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    setState(() => _isLoading = true);
    
    try {
      await _authService.signInWithGoogle();
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _signInAnonymously() async {
    setState(() => _isLoading = true);
    
    try {
      await _authService.signInAnonymously();
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}
```

### **3.4 Authentication Wrapper**
```dart
// lib/widgets/auth_wrapper.dart
class AuthWrapper extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: AuthService().authStateChanges,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return LoadingScreen();
        }
        
        if (snapshot.hasData) {
          return HomeScreen(); // or your main app screen
        }
        
        return LoginScreen();
      },
    );
  }
}
```

---

## 📋 **Phase 4: Backend Firebase Integration**

### **4.1 Python Dependencies**
```txt
# requirements.txt additions
firebase-admin==6.4.0
python-jose[cryptography]==3.3.0
```

### **4.2 Firebase Admin Setup**
```python
# backend/services/firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from typing import Optional
import json

class FirebaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            # For production, use service account key
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
            
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
            else:
                # For development, use default credentials
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
    
    async def verify_token(self, id_token: str) -> Optional[dict]:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    async def get_user_by_uid(self, uid: str) -> Optional[dict]:
        """Get user document from Firestore"""
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    async def create_user_document(self, uid: str, user_data: dict) -> bool:
        """Create user document in Firestore"""
        try:
            self.db.collection('users').document(uid).set(user_data)
            return True
        except Exception as e:
            print(f"Error creating user document: {e}")
            return False
    
    async def update_user_last_active(self, uid: str) -> bool:
        """Update user's last active timestamp"""
        try:
            self.db.collection('users').document(uid).update({
                'lastActive': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error updating last active: {e}")
            return False
```

### **4.3 Authentication Middleware**
```python
# backend/middleware/auth_middleware.py
from fastapi import HTTPException, Depends, Header
from typing import Optional
from services.firebase_service import FirebaseService

firebase_service = FirebaseService()

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # Verify token
        user_info = await firebase_service.verify_token(token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Update last active
        await firebase_service.update_user_last_active(user_info['uid'])
        
        return user_info
    
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Optional user authentication (allows anonymous access)"""
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
```

### **4.4 Updated API Endpoints**
```python
# backend/my_agent/agent.py
from middleware.auth_middleware import get_current_user, get_optional_user

@app.post("/start_session")
async def start_session(
    payload: StartPayload,
    current_user: dict = Depends(get_current_user)
):
    # Now we have authenticated user info
    user_id = current_user['uid']
    
    # Initialize a fresh GraphState with user info
    state: GraphState = {
        "user_id": user_id,
        "topics": payload.topics,
        "current_topic_index": 0,
        "question_count": 0,
        "history": [],
        "user_input": None,
        "next_question": None,
        "done": False,
        "scores": None,
        "max_topics": payload.max_topics,
        "max_questions": payload.max_questions
    }

    # Create and store session
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = state

    # Run the graph
    updated = compiled_graph.invoke(state)
    SESSIONS[session_id] = updated

    return {"session_id": session_id, "next_question": updated["next_question"]}

@app.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile information"""
    firebase_service = FirebaseService()
    user_data = await firebase_service.get_user_by_uid(current_user['uid'])
    
    if not user_data:
        # Create user document if it doesn't exist
        user_data = {
            'email': current_user.get('email', ''),
            'displayName': current_user.get('name', ''),
            'photoURL': current_user.get('picture', ''),
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastActive': firestore.SERVER_TIMESTAMP,
            'isAnonymous': current_user.get('firebase', {}).get('sign_in_provider') == 'anonymous'
        }
        await firebase_service.create_user_document(current_user['uid'], user_data)
    
    return user_data

@app.post("/user/update-profile")
async def update_user_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    firebase_service = FirebaseService()
    
    # Update user document
    try:
        firebase_service.db.collection('users').document(current_user['uid']).update(profile_data)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
```

---

## 📋 **Phase 5: Security Rules & Configuration**

### **5.1 Firestore Security Rules**
```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      // Learning items subcollection
      match /learningItems/{itemId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      
      // Sessions subcollection
      match /sessions/{sessionId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
    
    // Public collections (if any)
    match /public/{document=**} {
      allow read: if true;
      allow write: if false; // Only admins can write (via backend)
    }
  }
}
```

### **5.2 Firebase Storage Rules**
```javascript
// storage.rules
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // User profile images
    match /users/{userId}/profile/{fileName} {
      allow read, write: if request.auth != null && request.auth.uid == userId
        && resource.size < 5 * 1024 * 1024; // 5MB limit
    }
  }
}
```

### **5.3 Environment Configuration**
```bash
# .env file for backend
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_WEB_API_KEY=your-web-api-key
```

---

## 📋 **Phase 6: Testing & Validation**

### **6.1 Unit Tests**
```dart
// test/auth_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:firebase_auth_mocks/firebase_auth_mocks.dart';
import '../lib/services/auth_service.dart';

void main() {
  group('AuthService Tests', () {
    late AuthService authService;
    late MockFirebaseAuth mockAuth;

    setUp(() {
      mockAuth = MockFirebaseAuth();
      authService = AuthService();
    });

    test('should sign in with email and password', () async {
      final user = MockUser(
        isAnonymous: false,
        uid: 'test-uid',
        email: 'test@example.com',
        displayName: 'Test User',
      );
      
      when(mockAuth.signInWithEmailAndPassword(
        email: 'test@example.com',
        password: 'password123',
      )).thenAnswer((_) async => MockUserCredential(false, user));

      final result = await authService.signInWithEmail(
        'test@example.com',
        'password123',
      );

      expect(result?.user?.email, 'test@example.com');
    });
  });
}
```

### **6.2 Integration Tests**
```python
# backend/tests/test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_protected_endpoint_without_auth():
    response = client.post("/start_session", json={
        "topics": ["test"],
        "max_topics": 1,
        "max_questions": 1
    })
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token():
    # Mock Firebase token verification
    headers = {"Authorization": "Bearer valid-token"}
    response = client.post("/start_session", 
        json={"topics": ["test"], "max_topics": 1, "max_questions": 1},
        headers=headers
    )
    # Should work with proper mocking
    assert response.status_code in [200, 401]  # Depends on mocking setup
```

---

## 📋 **Phase 7: Deployment & Production Setup**

### **7.1 Environment Setup**
- [ ] **Development Environment**
  - [ ] Local Firebase emulator setup
  - [ ] Test Firebase project
  - [ ] Development service account
- [ ] **Production Environment**
  - [ ] Production Firebase project
  - [ ] Production service account with minimal permissions
  - [ ] Environment-specific configuration

### **7.2 CI/CD Pipeline**
```yaml
# .github/workflows/deploy.yml
name: Deploy App
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        
      - name: Install dependencies
        run: flutter pub get
        
      - name: Run tests
        run: flutter test
        
      - name: Build web
        run: flutter build web
        
      - name: Deploy to Firebase Hosting
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          projectId: your-project-id
```

---

## 🎯 **Implementation Timeline**

### **Week 1: Foundation**
- [ ] Firebase project setup and configuration
- [ ] Platform registration (Android, iOS, Web)
- [ ] Flutter dependencies and basic integration

### **Week 2: Authentication**
- [ ] AuthService implementation
- [ ] Login/Signup UI screens
- [ ] Authentication wrapper and routing

### **Week 3: Backend Integration**
- [ ] Firebase Admin SDK setup
- [ ] Authentication middleware
- [ ] API endpoint protection

### **Week 4: Security & Testing**
- [ ] Firestore security rules
- [ ] Unit and integration tests
- [ ] Error handling and validation

### **Week 5: Production Deployment**
- [ ] Environment configuration
- [ ] CI/CD pipeline setup
- [ ] Production testing and monitoring

---

## 🔧 **Best Practices & Considerations**

### **Security**
- Never store API keys in code repository
- Use environment variables for sensitive configuration
- Implement proper token refresh logic
- Validate all user inputs on backend
- Use least-privilege principle for service accounts

### **Performance**
- Implement offline persistence for Firestore
- Cache user authentication state
- Use connection pooling for backend Firebase connections
- Implement proper loading states in UI

### **User Experience**
- Graceful handling of network failures
- Clear error messages for authentication failures
- Remember user login state across app restarts
- Provide easy account recovery options

---

## 📱 **Future Enhancements**
- [ ] Biometric authentication (fingerprint, face ID)
- [ ] Multi-factor authentication (2FA)
- [ ] Social login providers (Apple, Facebook, Twitter)
- [ ] Account linking (merge anonymous with permanent accounts)
- [ ] Admin dashboard for user management
- [ ] Advanced security monitoring and alerting

---

**Last Updated**: December 2024  
**Project**: Spaced Repetition Learning App  
**Status**: Implementation Ready  
**Estimated Duration**: 5 weeks 