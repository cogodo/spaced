import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Import for MaxLengthEnforcement
// import 'package:lr_scheduler/models/task_holder.dart'; // No longer needed here

class AdderScreen extends StatefulWidget {
  // Change callback signature to expect Future<bool>
  final Future<bool> Function(String) onAddTask;

  AdderScreen({required this.onAddTask});

  @override
  _AdderScreenState createState() => _AdderScreenState();
}

// Add TickerProviderStateMixin for animation controller
class _AdderScreenState extends State<AdderScreen>
    with TickerProviderStateMixin {
  final _taskController = TextEditingController();
  bool _isAdding = false; // Prevent double submission

  // Animation controller and tween for shake animation
  late AnimationController _shakeController;
  late Animation<Offset> _shakeAnimation;

  @override
  void initState() {
    super.initState();
    _shakeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400), // Adjust duration
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
  }

  @override
  void dispose() {
    _taskController.dispose();
    _shakeController.dispose(); // Dispose animation controller
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: GestureDetector(
        onTap: () {
          FocusScope.of(context).unfocus();
        },
        // Wrap with SingleChildScrollView to prevent overflow
        child: SingleChildScrollView(
          physics:
              const ClampingScrollPhysics(), // Prevent bouncing effect when content fits
          child: Container(
            // Ensure the scrollable area takes at least the screen height
            // for proper centering when content is small
            height:
                MediaQuery.of(context).size.height -
                MediaQuery.of(context).padding.top -
                MediaQuery.of(context).padding.bottom,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SlideTransition(
                      position: _shakeAnimation,
                      child: TextField(
                        controller: _taskController,
                        maxLines: null,
                        keyboardType: TextInputType.multiline,
                        textInputAction: TextInputAction.newline,
                        maxLength: 400,
                        maxLengthEnforcement: MaxLengthEnforcement.enforced,
                        buildCounter:
                            (
                              context, {
                              required currentLength,
                              required isFocused,
                              maxLength,
                            }) => null,
                        // Set explicit larger font size
                        style: TextStyle(fontSize: 36.0),
                        decoration: InputDecoration(
                          hintText: 'input',
                          // Adjust hint style to match input size
                          hintStyle: TextStyle(
                            fontSize: 36.0,
                            color: Theme.of(context).hintColor,
                          ),
                        ),
                        onChanged: (value) {
                          // Check if the last character is a newline
                          if (value.endsWith('\n')) {
                            // Remove the newline character itself
                            final textWithoutNewline = value.substring(
                              0,
                              value.length - 1,
                            );
                            // Update the controller without triggering onChanged again
                            // and place cursor at the end
                            _taskController.value = _taskController.value
                                .copyWith(
                                  text: textWithoutNewline,
                                  selection: TextSelection.collapsed(
                                    offset: textWithoutNewline.length,
                                  ),
                                );

                            // Trigger submission if not already adding
                            if (!_isAdding) {
                              _submitTask();
                              FocusScope.of(
                                context,
                              ).unfocus(); // Dismiss keyboard
                            }
                            return; // Don't process length check if newline submitted
                          }

                          // --- Character Limit Check ---
                          if (value.length >= 400) {
                            // Trigger shake animation
                            _shakeController.forward(from: 0.0);
                            // Show local SnackBar when limit is hit
                            ScaffoldMessenger.of(
                              context,
                            ).removeCurrentSnackBar(); // Remove previous messages
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('ERROR: len() > 400'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                          }
                        },
                        onSubmitted: (value) {
                          // Keep onSubmitted as a fallback for keyboards
                          // with a distinct submit action
                          if (!_isAdding) {
                            _submitTask();
                          }
                          FocusScope.of(context).unfocus();
                        },
                      ),
                    ),
                    SizedBox(height: 24),
                    ElevatedButton(
                      onPressed:
                          _isAdding
                              ? null
                              : () {
                                _submitTask();
                                FocusScope.of(context).unfocus();
                              },
                      child:
                          _isAdding
                              ? SizedBox(
                                height: 20.0,
                                width: 20.0,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.0,
                                  color:
                                      Theme.of(
                                        context,
                                      ).progressIndicatorTheme.color ??
                                      Theme.of(context).colorScheme.onPrimary,
                                ),
                              )
                              : Text('Add'),
                    ),
                  ],
                ),
              ),
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
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('ERROR: no input.')));
      return;
    }

    // Prevent multiple submissions while waiting
    setState(() {
      _isAdding = true;
    });

    try {
      final bool success = await widget.onAddTask(taskDescription);

      // Check the result from the callback
      if (success) {
        _taskController.clear();
        // Confirmation is handled by SwipeNavigationScreen's bottom sheet now
        // ScaffoldMessenger.of(context).showSnackBar(
        //   SnackBar(content: Text('Task "$taskDescription" added!')),
        // );
      } else {
        // Error (duplicate) is handled by SwipeNavigationScreen's bottom sheet now
        // ScaffoldMessenger.of(context).showSnackBar(
        //   SnackBar(
        //     content: Text(
        //       'Task "$taskDescription" already exists or could not be added.',
        //     ),
        //   ),
        // );
      }
    } finally {
      // Always re-enable the button
      if (mounted) {
        // Check if the widget is still in the tree
        setState(() {
          _isAdding = false;
        });
      }
    }
  }
}
