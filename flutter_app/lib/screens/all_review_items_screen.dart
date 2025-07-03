import 'package:flutter/material.dart';
import '../widgets/coming_soon_widget.dart';

class AllReviewItemsScreen extends StatelessWidget {
  const AllReviewItemsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonWidget(featureName: "All Review Items"),
    );
  }
}
