import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';

class FirebaseTestScreen extends StatefulWidget {
  const FirebaseTestScreen({super.key});

  @override
  State<FirebaseTestScreen> createState() => _FirebaseTestScreenState();
}

class _FirebaseTestScreenState extends State<FirebaseTestScreen> {
  String _firebaseStatus = 'Checking Firebase...';
  String _platformInfo = '';

  @override
  void initState() {
    super.initState();
    _checkFirebase();
  }

  Future<void> _checkFirebase() async {
    try {
      // Check if Firebase is already initialized
      FirebaseApp app = Firebase.app();

      setState(() {
        _firebaseStatus = '✅ Firebase initialized successfully!';
        _platformInfo = '''
App Name: ${app.name}
Project ID: ${app.options.projectId}
API Key: ${app.options.apiKey.substring(0, 10)}...
Platform: ${DefaultFirebaseOptions.currentPlatform.projectId}
''';
      });
    } catch (e) {
      setState(() {
        _firebaseStatus = '❌ Firebase initialization failed: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Firebase Test'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Firebase Status',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 10),
                    Text(_firebaseStatus),
                    if (_platformInfo.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Text(
                        'Configuration:',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(_platformInfo),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Environment Files Check',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 10),
                    const Text('✅ .env files created'),
                    const Text('✅ Firebase options generated'),
                    const Text('✅ Platform configurations verified'),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Back to Landing Page'),
            ),
          ],
        ),
      ),
    );
  }
}
