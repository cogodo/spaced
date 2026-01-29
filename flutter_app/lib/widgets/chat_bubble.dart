import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import '../screens/chat_screen.dart';

class ChatBubble extends StatefulWidget {
  final ChatMessage message;
  final String Function(DateTime) formatTimestamp;
  final bool isStreaming;

  const ChatBubble({
    super.key,
    required this.message,
    required this.formatTimestamp,
    this.isStreaming = false,
  });

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble>
    with SingleTickerProviderStateMixin {
  late AnimationController _fadeController;
  String _previousText = '';

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 100),
      vsync: this,
    );
    _previousText = widget.message.text;
    _fadeController.value = 1.0;
  }

  @override
  void didUpdateWidget(ChatBubble oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Trigger subtle animation when text updates during streaming
    if (widget.isStreaming && widget.message.text != _previousText) {
      _previousText = widget.message.text;
      // Quick pulse for smooth streaming effect
      _fadeController.forward(from: 0.9);
    }
  }

  @override
  void dispose() {
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isUser = widget.message.isUser;
    final theme = Theme.of(context);

    return Align(
      alignment: widget.message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.symmetric(horizontal: 80),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final horizontalGutter = 16.0;
            final availableWidth =
                constraints.maxWidth - (horizontalGutter * 2);
            final userMaxWidth = availableWidth * 0.7;
            final userIndent = availableWidth * 0.33;
            return Row(
              mainAxisAlignment:
                  isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(width: horizontalGutter),
                Flexible(
                  child: Container(
                    constraints: BoxConstraints(
                      maxWidth: isUser ? userMaxWidth : availableWidth,
                    ),
                    margin:
                        isUser
                            ? EdgeInsets.only(left: userIndent)
                            : EdgeInsets.zero,
                    child:
                        isUser
                            ? _buildUserBubble(context, theme)
                            : _buildAiBubble(context, theme),
                  ),
                ),
                SizedBox(width: horizontalGutter),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildUserBubble(BuildContext context, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildMarkdownContent(context, theme, TextAlign.left, isUser: true),
          const SizedBox(height: 4),
          Text(
            widget.formatTimestamp(widget.message.timestamp),
            style: theme.textTheme.bodySmall?.copyWith(letterSpacing: 0.3),
            textAlign: TextAlign.left,
          ),
        ],
      ),
    );
  }

  Widget _buildAiBubble(BuildContext context, ThemeData theme) {
    // Wrap in FadeTransition for smooth streaming animation
    Widget content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildMarkdownContent(context, theme, TextAlign.left, isUser: false),
        const SizedBox(height: 4),
        Text(
          widget.formatTimestamp(widget.message.timestamp),
          style: theme.textTheme.bodySmall?.copyWith(letterSpacing: 0.3),
          textAlign: TextAlign.left,
        ),
      ],
    );

    // Apply subtle fade animation during streaming
    if (widget.isStreaming) {
      return FadeTransition(
        opacity: _fadeController,
        child: content,
      );
    }

    return content;
  }

  Widget _buildMarkdownContent(
    BuildContext context,
    ThemeData theme,
    TextAlign textAlign, {
    required bool isUser,
  }) {
    final markdownStyleSheet = MarkdownStyleSheet(
      p: theme.textTheme.bodyLarge?.copyWith(
        height: 1.5,
        letterSpacing: 0.2,
        color:
            isUser
                ? theme.textTheme.bodyLarge?.color
                : theme.textTheme.bodyLarge?.color,
      ),
      h1: theme.textTheme.headlineSmall?.copyWith(
        fontWeight: FontWeight.bold,
        color: isUser ? theme.colorScheme.onSurface : theme.colorScheme.primary,
      ),
      h2: theme.textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.bold,
        color: isUser ? theme.colorScheme.onSurface : theme.colorScheme.primary,
      ),
      h3: theme.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: isUser ? theme.colorScheme.onSurface : theme.colorScheme.primary,
      ),
      strong: theme.textTheme.bodyLarge?.copyWith(
        fontWeight: FontWeight.bold,
        height: 1.5,
        letterSpacing: 0.2,
      ),
      em: theme.textTheme.bodyLarge?.copyWith(
        fontStyle: FontStyle.italic,
        height: 1.5,
        letterSpacing: 0.2,
      ),
      code: theme.textTheme.bodyMedium?.copyWith(
        fontFamily: 'Courier',
        backgroundColor:
            isUser
                ? theme.colorScheme.surface.withValues(alpha: 0.3)
                : theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
        color:
            isUser
                ? theme.colorScheme.onSurface
                : theme.colorScheme.onPrimaryContainer,
      ),
      codeblockDecoration: BoxDecoration(
        color:
            isUser
                ? theme.colorScheme.surface.withValues(alpha: 0.5)
                : theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      codeblockPadding: const EdgeInsets.all(12),
      blockquote: theme.textTheme.bodyLarge?.copyWith(
        fontStyle: FontStyle.italic,
        color: theme.textTheme.bodyLarge?.color?.withValues(alpha: 0.8),
      ),
      blockquoteDecoration: BoxDecoration(
        border: Border(
          left: BorderSide(
            color:
                isUser ? theme.colorScheme.outline : theme.colorScheme.primary,
            width: 3,
          ),
        ),
      ),
      blockquotePadding: const EdgeInsets.only(left: 12),
      a: TextStyle(
        color: theme.colorScheme.primary,
        decoration: TextDecoration.underline,
      ),
      listBullet: theme.textTheme.bodyLarge?.copyWith(
        height: 1.5,
        letterSpacing: 0.2,
      ),
      tableHead: theme.textTheme.bodyMedium?.copyWith(
        fontWeight: FontWeight.bold,
      ),
      tableBody: theme.textTheme.bodyMedium,
      tableBorder: TableBorder.all(
        color: theme.colorScheme.outline.withValues(alpha: 0.3),
        width: 1,
      ),
      textAlign:
          textAlign == TextAlign.right
              ? WrapAlignment.end
              : WrapAlignment.start,
    );

    return GestureDetector(
      onLongPress: () => _showCopyMenu(context),
      child: SelectionArea(
        child: MarkdownBody(
          data: widget.message.text,
          styleSheet: markdownStyleSheet,
          selectable: true,
          onTapLink: (text, href, title) async {
            if (href != null) {
              final uri = Uri.tryParse(href);
              if (uri != null && await canLaunchUrl(uri)) {
                await launchUrl(uri, mode: LaunchMode.externalApplication);
              }
            }
          },
        ),
      ),
    );
  }

  void _showCopyMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.copy),
                title: const Text('Copy Message'),
                onTap: () {
                  Clipboard.setData(ClipboardData(text: widget.message.text));
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Message copied to clipboard'),
                      duration: Duration(seconds: 2),
                    ),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.text_fields),
                title: const Text('Copy as Plain Text'),
                onTap: () {
                  final plainText = _stripMarkdown(widget.message.text);
                  Clipboard.setData(ClipboardData(text: plainText));
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Plain text copied to clipboard'),
                      duration: Duration(seconds: 2),
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }

  String _stripMarkdown(String markdown) {
    return markdown
        .replaceAll(RegExp(r'\*\*(.*?)\*\*'), r'$1')
        .replaceAll(RegExp(r'\*(.*?)\*'), r'$1')
        .replaceAll(RegExp(r'__(.*?)__'), r'$1')
        .replaceAll(RegExp(r'_(.*?)_'), r'$1')
        .replaceAll(RegExp(r'`(.*?)`'), r'$1')
        .replaceAll(RegExp(r'```[\s\S]*?```'), '')
        .replaceAll(RegExp(r'\[([^\]]*)\]\([^)]*\)'), r'$1')
        .replaceAll(RegExp(r'^#+\s*', multiLine: true), '')
        .replaceAll(RegExp(r'^>\s*', multiLine: true), '')
        .replaceAll(RegExp(r'\n{3,}'), '\n\n')
        .trim();
  }
}
