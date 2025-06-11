import 'package:flutter/material.dart';
import '../widgets/top_navigation_bar.dart';

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

    return Scaffold(
      // Use the new top navigation bar
      appBar: const TopNavigationBar(),

      // Simplified body - just the child content
      body: Container(
        padding: EdgeInsets.symmetric(
          horizontal: isDesktop ? 40 : 20,
          vertical: 20,
        ),
        child: widget.child, // Router provides the child
      ),
    );
  }
}
