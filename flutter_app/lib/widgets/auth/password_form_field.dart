import 'package:flutter/material.dart';

/// Password form field widget with toggle visibility and validation
class PasswordFormField extends StatefulWidget {
  final TextEditingController controller;
  final FocusNode? focusNode;
  final bool obscureText;
  final VoidCallback? onToggleObscure;
  final ValueChanged<String>? onSubmitted;
  final bool enabled;
  final String? Function(String?)? validator;
  final String labelText;
  final String hintText;
  final bool showRequirements;

  const PasswordFormField({
    super.key,
    required this.controller,
    this.focusNode,
    this.obscureText = true,
    this.onToggleObscure,
    this.onSubmitted,
    this.enabled = true,
    this.validator,
    this.labelText = 'Password',
    this.hintText = 'Enter your password',
    this.showRequirements = false,
  });

  @override
  State<PasswordFormField> createState() => _PasswordFormFieldState();
}

class _PasswordFormFieldState extends State<PasswordFormField> {
  String _currentPassword = '';

  @override
  void initState() {
    super.initState();
    _currentPassword = widget.controller.text;
    widget.controller.addListener(_onPasswordChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onPasswordChanged);
    super.dispose();
  }

  void _onPasswordChanged() {
    if (mounted) {
      setState(() {
        _currentPassword = widget.controller.text;
      });
    }
  }



  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextFormField(
          controller: widget.controller,
          focusNode: widget.focusNode,
          enabled: widget.enabled,
          obscureText: widget.obscureText,
          textInputAction: TextInputAction.done,
          onFieldSubmitted: widget.onSubmitted,
          decoration: InputDecoration(
            labelText: widget.labelText,
            hintText: widget.hintText,
            prefixIcon: const Icon(Icons.lock_outlined),
            suffixIcon:
                widget.onToggleObscure != null
                    ? IconButton(
                      icon: Icon(
                        widget.obscureText
                            ? Icons.visibility
                            : Icons.visibility_off,
                      ),
                      onPressed: widget.onToggleObscure,
                    )
                    : null,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Theme.of(
                  context,
                ).colorScheme.outline.withValues(alpha: 0.3),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Theme.of(context).colorScheme.primary,
                width: 2,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Theme.of(context).colorScheme.error,
                width: 2,
              ),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Theme.of(context).colorScheme.error,
                width: 2,
              ),
            ),
          ),
          validator: widget.validator ?? _defaultPasswordValidator,
        ),

        // Show password requirements only when explicitly enabled via showRequirements
        if (widget.showRequirements &&
            widget.labelText.contains('Password') &&
            !widget.labelText.contains('Confirm'))
          _buildPasswordRequirements(context),
      ],
    );
  }

  Widget _buildPasswordRequirements(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(
          context,
        ).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Password requirements:',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 8),
          _buildRequirement(
            context,
            'At least 8 characters',
            _currentPassword.length >= 8,
          ),
          _buildRequirement(
            context,
            'Contains uppercase letter',
            RegExp(r'[A-Z]').hasMatch(_currentPassword),
          ),
          _buildRequirement(
            context,
            'Contains lowercase letter',
            RegExp(r'[a-z]').hasMatch(_currentPassword),
          ),
          _buildRequirement(
            context,
            'Contains number',
            RegExp(r'\d').hasMatch(_currentPassword),
          ),
        ],
      ),
    );
  }

  Widget _buildRequirement(
    BuildContext context,
    String requirement,
    bool isMet,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Icon(
            isMet ? Icons.check_circle : Icons.radio_button_unchecked,
            size: 16,
            color:
                isMet
                    ? Colors.green
                    : Theme.of(
                      context,
                    ).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          const SizedBox(width: 8),
          Text(
            requirement,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color:
                  isMet
                      ? Colors.green
                      : Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.8),
              decoration: isMet ? TextDecoration.lineThrough : null,
            ),
          ),
        ],
      ),
    );
  }

  String? _defaultPasswordValidator(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }

    if (value.length < 6) {
      return 'Password must be at least 6 characters';
    }

    return null;
  }
}
