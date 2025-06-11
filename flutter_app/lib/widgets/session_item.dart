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
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Delete Session'),
            content: Text(
              'Are you sure you want to delete "${widget.session.displayName}"?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: TextButton.styleFrom(
                  foregroundColor: Theme.of(context).colorScheme.error,
                ),
                child: const Text('Delete'),
              ),
            ],
          ),
    );

    if (confirmed == true && mounted) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      await chatProvider.deleteSession(widget.session.id);
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
        position.dx,
        position.dy,
        position.dx + 1,
        position.dy + 1,
      ),
      items: [
        const PopupMenuItem<String>(
          value: 'rename',
          child: Row(
            children: [
              Icon(Icons.edit, size: 16),
              SizedBox(width: 8),
              Text('Rename'),
            ],
          ),
        ),
        const PopupMenuItem<String>(
          value: 'copy_url',
          child: Row(
            children: [
              Icon(Icons.link, size: 16),
              SizedBox(width: 8),
              Text('Copy URL'),
            ],
          ),
        ),
        const PopupMenuItem<String>(
          value: 'delete',
          child: Row(
            children: [
              Icon(Icons.delete, size: 16, color: Colors.red),
              SizedBox(width: 8),
              Text('Delete', style: TextStyle(color: Colors.red)),
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
                          onTap:
                              () => _showContextMenu(
                                context,
                                const Offset(200, 0),
                              ),
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
