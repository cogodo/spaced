import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import '../screens/chat_screen.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final String Function(DateTime) formatTimestamp;

  const ChatBubble({
    Key? key,
    required this.message,
    required this.formatTimestamp,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            // AI avatar
            Container(
              width: 32,
              height: 32,
              margin: const EdgeInsets.only(right: 12),
              decoration: BoxDecoration(
                color:
                    message.isSystem
                        ? theme.colorScheme.secondaryContainer
                        : theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                message.isSystem ? Icons.info : Icons.smart_toy,
                size: 18,
                color:
                    message.isSystem
                        ? theme.colorScheme.onSecondaryContainer
                        : theme.colorScheme.onPrimaryContainer,
              ),
            ),
          ],
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              child:
                  isUser
                      ? _buildUserBubble(context, theme)
                      : _buildAiBubble(context, theme),
            ),
          ),
          if (isUser) ...[
            // User avatar
            Container(
              width: 32,
              height: 32,
              margin: const EdgeInsets.only(left: 12),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                Icons.person,
                size: 18,
                color: theme.colorScheme.onPrimary,
              ),
            ),
          ],
        ],
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
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Markdown content for user messages
          _buildMarkdownContent(context, theme, TextAlign.right, isUser: true),
          const SizedBox(height: 4),
          // Timestamp
          Text(
            formatTimestamp(message.timestamp),
            style: theme.textTheme.bodySmall?.copyWith(letterSpacing: 0.3),
            textAlign: TextAlign.right,
          ),
        ],
      ),
    );
  }

  Widget _buildAiBubble(BuildContext context, ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Markdown content for AI messages
        _buildMarkdownContent(context, theme, TextAlign.left, isUser: false),
        const SizedBox(height: 4),
        // Timestamp
        Text(
          formatTimestamp(message.timestamp),
          style: theme.textTheme.bodySmall?.copyWith(letterSpacing: 0.3),
          textAlign: TextAlign.left,
        ),
      ],
    );
  }

  Widget _buildMarkdownContent(
    BuildContext context,
    ThemeData theme,
    TextAlign textAlign, {
    required bool isUser,
  }) {
    // Custom markdown style sheet for user vs AI messages
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
          data: message.text,
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
                  Clipboard.setData(ClipboardData(text: message.text));
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
                  final plainText = _stripMarkdown(message.text);
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

  // Helper method to strip markdown formatting for plain text copy
  String _stripMarkdown(String markdown) {
    return markdown
        // Remove bold/italic markers
        .replaceAll(RegExp(r'\*\*(.*?)\*\*'), r'$1')
        .replaceAll(RegExp(r'\*(.*?)\*'), r'$1')
        .replaceAll(RegExp(r'__(.*?)__'), r'$1')
        .replaceAll(RegExp(r'_(.*?)_'), r'$1')
        // Remove code markers
        .replaceAll(RegExp(r'`(.*?)`'), r'$1')
        .replaceAll(RegExp(r'```[\s\S]*?```'), '')
        // Remove links but keep text
        .replaceAll(RegExp(r'\[([^\]]*)\]\([^)]*\)'), r'$1')
        // Remove headers
        .replaceAll(RegExp(r'^#+\s*', multiLine: true), '')
        // Remove blockquotes
        .replaceAll(RegExp(r'^>\s*', multiLine: true), '')
        // Clean up extra whitespace
        .replaceAll(RegExp(r'\n{3,}'), '\n\n')
        .trim();
  }
}
