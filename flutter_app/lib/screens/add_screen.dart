import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Import for MaxLengthEnforcement
// import 'package:lr_scheduler/models/task_holder.dart'; // No longer needed here

class AdderScreen extends StatefulWidget {
  // Callback signature to expect Future<bool>
  final Future<bool> Function(String) onAddTask;

  const AdderScreen({super.key, required this.onAddTask});

  @override
  State<AdderScreen> createState() => _AdderScreenState();
}

// Add TickerProviderStateMixin for animation controller
class _AdderScreenState extends State<AdderScreen>
    with TickerProviderStateMixin {
  final _taskController = TextEditingController();
  bool _isAdding = false; // Prevent double submission
  final FocusNode _focusNode = FocusNode();

  // Animation controller and tween for shake animation
  late AnimationController _shakeController;
  late Animation<Offset> _shakeAnimation;

  @override
  void initState() {
    super.initState();
    _shakeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    // Define the shake sequence (left -> right -> center)
    _shakeAnimation = TweenSequence<Offset>([
      TweenSequenceItem(
        tween: Tween(begin: Offset.zero, end: Offset(-0.04, 0.0)),
        weight: 1.0,
      ),
      TweenSequenceItem(
        tween: Tween(begin: Offset(-0.04, 0.0), end: Offset(0.04, 0.0)),
        weight: 1.0,
      ),
      TweenSequenceItem(
        tween: Tween(begin: Offset(0.04, 0.0), end: Offset(-0.04, 0.0)),
        weight: 1.0,
      ),
      TweenSequenceItem(
        tween: Tween(begin: Offset(-0.04, 0.0), end: Offset.zero),
        weight: 1.0,
      ),
    ]).animate(
      CurvedAnimation(parent: _shakeController, curve: Curves.easeInOut),
    );

    // Focus on the text field when the screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _taskController.dispose();
    _shakeController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isDesktop = screenWidth > 600;
    final maxWidth = isDesktop ? 600.0 : screenWidth * 0.9;

    return SelectableRegion(
      focusNode: FocusNode(),
      selectionControls: materialTextSelectionControls,
      child: GestureDetector(
        onTap: () {
          FocusScope.of(context).unfocus();
        },
        child: Center(
          child: Container(
            width: maxWidth,
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Text field with shake animation
                SlideTransition(
                  position: _shakeAnimation,
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: Theme.of(
                          context,
                        ).colorScheme.primary.withAlpha(128),
                        width: 2,
                      ),
                    ),
                    child: TextField(
                      controller: _taskController,
                      focusNode: _focusNode,
                      maxLines: null,
                      keyboardType: TextInputType.multiline,
                      textInputAction: TextInputAction.done,
                      maxLength: 400,
                      maxLengthEnforcement: MaxLengthEnforcement.enforced,
                      buildCounter:
                          (
                            context, {
                            required currentLength,
                            required isFocused,
                            maxLength,
                          }) => Padding(
                            padding: const EdgeInsets.only(right: 16.0),
                            child: Text(
                              '$currentLength / 400',
                              style: TextStyle(
                                color:
                                    currentLength >= 400
                                        ? Colors.red
                                        : Theme.of(
                                          context,
                                        ).textTheme.bodySmall?.color,
                              ),
                            ),
                          ),
                      // Larger font size for better readability
                      style: TextStyle(fontSize: isDesktop ? 24.0 : 20.0),
                      decoration: InputDecoration(
                        hintText: 'Enter item to remember...',
                        hintStyle: TextStyle(
                          fontSize: isDesktop ? 24.0 : 20.0,
                          color: Theme.of(context).hintColor,
                        ),
                        contentPadding: EdgeInsets.all(20),
                        border: InputBorder.none,
                        // Add rounded border that matches container
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onSubmitted: (value) {
                        // Handle keyboard submission
                        if (!_isAdding) {
                          _submitTask();
                        }
                      },
                    ),
                  ),
                ),
                SizedBox(height: 32),

                // Submit button
                SizedBox(
                  width: isDesktop ? 300 : double.infinity,
                  height: 60, // Taller button for easier clicking
                  child: ElevatedButton(
                    onPressed: _isAdding ? null : _submitTask,
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child:
                        _isAdding
                            ? SizedBox(
                              height: 24.0,
                              width: 24.0,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.5,
                                color: Theme.of(context).colorScheme.onPrimary,
                              ),
                            )
                            : Text(
                              'Add Item',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                  ),
                ),

                SizedBox(height: 16),

                // Clear button
                SizedBox(
                  width: isDesktop ? 300 : double.infinity,
                  height: 60,
                  child: OutlinedButton(
                    onPressed: () {
                      _taskController.clear();
                      _focusNode.requestFocus();
                    },
                    style: OutlinedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text('Clear', style: TextStyle(fontSize: 18)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Make _submitTask async to await the callback result
  Future<void> _submitTask() async {
    final taskDescription = _taskController.text.trim();
    if (taskDescription.isEmpty) {
      // Clear any existing snackbars before showing a new one
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Please enter something to remember'),
          duration: Duration(seconds: 3),
        ),
      );
      return;
    }

    // Prevent multiple submissions while waiting
    setState(() {
      _isAdding = true;
    });

    try {
      final bool success = await widget.onAddTask(taskDescription);

      // Clear field on success
      if (success) {
        _taskController.clear();
      }
    } finally {
      // Always re-enable the button
      if (mounted) {
        setState(() {
          _isAdding = false;
        });
      }
    }
  }
}
