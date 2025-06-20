import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../models/chat_session.dart';
import '../providers/chat_provider.dart';

class SessionItem extends StatefulWidget {
  final ChatSessionSummary session;
  final bool isSelected;

  const SessionItem({
    super.key,
    required this.session,
    required this.isSelected,
  });

  @override
  State<SessionItem> createState() => _SessionItemState();
}

class _SessionItemState extends State<SessionItem> {
  bool _isHovered = false;
  bool _isEditing = false;
  final TextEditingController _nameController = TextEditingController();
  final FocusNode _nameFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    _nameController.text = widget.session.displayName;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _nameFocus.dispose();
    super.dispose();
  }

  void _startEditing() {
    setState(() {
      _isEditing = true;
      _nameController.text = widget.session.displayName;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _nameFocus.requestFocus();
      _nameController.selection = TextSelection(
        baseOffset: 0,
        extentOffset: _nameController.text.length,
      );
    });
  }

  Future<void> _saveEdit() async {
    final newName = _nameController.text.trim();
    if (newName.isNotEmpty && newName != widget.session.displayName) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      await chatProvider.renameSession(widget.session.id, newName);
    }
    setState(() {
      _isEditing = false;
    });
  }

  void _cancelEdit() {
    setState(() {
      _isEditing = false;
      _nameController.text = widget.session.displayName;
    });
  }

  Future<void> _deleteSession() async {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    // Store session info for potential undo
    final sessionId = widget.session.id;
    final sessionName = widget.session.displayName;

    // Delete immediately
    try {
      await chatProvider.deleteSession(sessionId);

      // Show undo snackbar
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Deleted "$sessionName"'),
            duration: const Duration(seconds: 4),
            action: SnackBarAction(
              label: 'Undo',
              onPressed: () {
                // Note: For now, just show a message.
                // Full undo would require backend support for session restoration
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'Undo not yet supported. Session permanently deleted.',
                    ),
                    duration: Duration(seconds: 2),
                  ),
                );
              },
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to delete session: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  Future<void> _copySessionUrl() async {
    final url = 'https://yourapp.com${widget.session.sessionUrl}';
    await Clipboard.setData(ClipboardData(text: url));

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Session URL copied to clipboard'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  void _showContextMenu(BuildContext context, Offset position) {
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        position.dx - 120, // Move closer to the left
        position.dy - 10, // Move slightly up
        position.dx - 50, // Smaller width
        position.dy + 10, // Smaller height
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8), // Rounded edges
      ),
      constraints: const BoxConstraints(
        minWidth: 120, // Smaller minimum width
        maxWidth: 150, // Smaller maximum width
      ),
      items: [
        PopupMenuItem<String>(
          value: 'rename',
          height: 36, // Smaller height
          child: Row(
            children: [
              Icon(Icons.edit, size: 14), // Smaller icon
              const SizedBox(width: 8),
              Text('Rename', style: TextStyle(fontSize: 13)), // Smaller text
            ],
          ),
        ),
        PopupMenuItem<String>(
          value: 'copy_url',
          height: 36, // Smaller height
          child: Row(
            children: [
              Icon(Icons.link, size: 14), // Smaller icon
              const SizedBox(width: 8),
              Text('Copy URL', style: TextStyle(fontSize: 13)), // Smaller text
            ],
          ),
        ),
        PopupMenuItem<String>(
          value: 'delete',
          height: 36, // Smaller height
          child: Row(
            children: [
              Icon(Icons.delete, size: 14, color: Colors.red), // Smaller icon
              const SizedBox(width: 8),
              Text(
                'Delete',
                style: TextStyle(fontSize: 13, color: Colors.red),
              ), // Smaller text
            ],
          ),
        ),
      ],
    ).then((value) {
      switch (value) {
        case 'rename':
          _startEditing();
          break;
        case 'copy_url':
          _copySessionUrl();
          break;
        case 'delete':
          _deleteSession();
          break;
      }
    });
  }

  Color _getStatusColor(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    switch (widget.session.statusColorType) {
      case 'progress':
        return Colors.blue;
      case 'success':
        return Colors.green;
      case 'error':
        return colorScheme.error;
      case 'warning':
        return Colors.orange;
      case 'neutral':
      default:
        return colorScheme.outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: () {
          if (!_isEditing) {
            context.go(widget.session.sessionUrl);
          }
        },
        onSecondaryTapDown: (details) {
          _showContextMenu(context, details.globalPosition);
        },
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color:
                widget.isSelected
                    ? colorScheme.primaryContainer.withOpacity(0.3)
                    : _isHovered
                    ? colorScheme.surface
                    : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border:
                widget.isSelected
                    ? Border.all(
                      color: colorScheme.primary.withOpacity(0.3),
                      width: 1,
                    )
                    : null,
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Session name (editable or display)
                if (_isEditing)
                  TextField(
                    controller: _nameController,
                    focusNode: _nameFocus,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                    decoration: const InputDecoration(
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 4,
                        vertical: 2,
                      ),
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _saveEdit(),
                    onTapOutside: (_) => _cancelEdit(),
                    maxLines: 1,
                  )
                else
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          widget.session.displayName,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color:
                                widget.isSelected
                                    ? colorScheme.primary
                                    : colorScheme.onSurface,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (_isHovered)
                        GestureDetector(
                          onTap: () {
                            // Get the position of the three dots relative to the widget
                            final RenderBox renderBox =
                                context.findRenderObject() as RenderBox;
                            final position = renderBox.localToGlobal(
                              Offset.zero,
                            );
                            _showContextMenu(
                              context,
                              Offset(
                                position.dx + renderBox.size.width,
                                position.dy,
                              ),
                            );
                          },
                          child: Icon(
                            Icons.more_horiz,
                            size: 16,
                            color: colorScheme.outline,
                          ),
                        ),
                    ],
                  ),

                const SizedBox(height: 4),

                // Topics preview
                if (widget.session.topics.isNotEmpty)
                  Text(
                    widget.session.topics.take(2).join(', '),
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onSurface.withOpacity(0.7),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                const SizedBox(height: 6),

                // Status row (no time display)
                Row(
                  children: [
                    // Status indicator
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: _getStatusColor(context),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      widget.session.statusText,
                      style: TextStyle(
                        fontSize: 11,
                        color: colorScheme.onSurface.withOpacity(0.6),
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ],
                ),

                // Message count
                if (widget.session.messageCount > 0) ...[
                  const SizedBox(height: 4),
                  Text(
                    '${widget.session.messageCount} messages',
                    style: TextStyle(
                      fontSize: 11,
                      color: colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
