import 'package:flutter/material.dart';
import 'design_tokens.dart';

class BrandGradientContainer extends StatelessWidget {
  final Widget child;
  final Alignment begin;
  final Alignment end;
  const BrandGradientContainer({
    super.key,
    required this.child,
    this.begin = Alignment.topLeft,
    this.end = Alignment.bottomRight,
  });

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).extension<SpacedTokens>()!;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: tokens.brandGradient(begin: begin, end: end),
      ),
      child: child,
    );
  }
}
