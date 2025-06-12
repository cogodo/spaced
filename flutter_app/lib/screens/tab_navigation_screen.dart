import 'package:flutter/material.dart';
import '../widgets/top_navigation_bar.dart';
import 'chat_screen.dart';

class TabNavigationScreen extends StatefulWidget {
  final Widget child; // Child widget from router

  const TabNavigationScreen({super.key, required this.child});

  @override
  State<TabNavigationScreen> createState() => _TabNavigationScreenState();
}

class _TabNavigationScreenState extends State<TabNavigationScreen> {
  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 800;
    final isChatScreen = widget.child is ChatScreen;

    return Scaffold(
      // Use the new top navigation bar
      appBar: const TopNavigationBar(),

      // Remove padding for chat screen, keep for others
      body:
          isChatScreen
              ? widget
                  .child // No padding for chat - let sidebar be flush
              : Container(
                padding: EdgeInsets.symmetric(
                  horizontal: isDesktop ? 40 : 20,
                  vertical: 20,
                ),
                child: widget.child,
              ),
    );
  }
}
