import 'package:flutter/material.dart';
import '../widgets/coming_soon_widget.dart';

class TodaysReviewsScreen extends StatelessWidget {
  const TodaysReviewsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonWidget(featureName: "Today's Reviews"),
    );
  }
}
