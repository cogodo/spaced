import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart';

class TopicSelectionWidget extends StatefulWidget {
  final Function(List<String>) onTopicsSelected;
  final Function(PopularTopic)? onPopularTopicSelected;

  const TopicSelectionWidget({
    Key? key,
    required this.onTopicsSelected,
    this.onPopularTopicSelected,
  }) : super(key: key);

  @override
  State<TopicSelectionWidget> createState() => _TopicSelectionWidgetState();
}

class _TopicSelectionWidgetState extends State<TopicSelectionWidget> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  List<UserTopic> _searchResults = [];
  bool _isSearching = false;
  String _searchQuery = '';

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Popular topics section
            if (chatProvider.popularTopics.isNotEmpty) ...[
              const Text(
                '🔥 Popular Topics',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children:
                    chatProvider.popularTopics.map((topic) {
                      return ActionChip(
                        label: Text(topic.name),
                        onPressed:
                            chatProvider.isStartingSession
                                ? null
                                : () {
                                  if (widget.onPopularTopicSelected != null) {
                                    widget.onPopularTopicSelected!(topic);
                                  } else {
                                    widget.onTopicsSelected([topic.name]);
                                  }
                                },
                        backgroundColor:
                            Theme.of(context).colorScheme.primaryContainer,
                        labelStyle: TextStyle(
                          color:
                              Theme.of(context).colorScheme.onPrimaryContainer,
                        ),
                      );
                    }).toList(),
              ),
              const SizedBox(height: 16),
              const Row(
                children: [
                  Expanded(child: Divider()),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text('OR'),
                  ),
                  Expanded(child: Divider()),
                ],
              ),
              const SizedBox(height: 16),
            ],

            // Custom topic input section
            const Text(
              '✍️ Enter Custom Topics',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),

            // Search/input field with autocomplete
            TextField(
              controller: _controller,
              focusNode: _focusNode,
              decoration: InputDecoration(
                hintText: 'Enter topics separated by commas...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.search),
                suffixIcon:
                    _controller.text.isNotEmpty
                        ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _controller.clear();
                            setState(() {
                              _searchResults.clear();
                              _searchQuery = '';
                            });
                          },
                        )
                        : null,
              ),
              onChanged: _onSearchChanged,
              onSubmitted: (value) {
                if (value.trim().isNotEmpty) {
                  _submitTopics();
                }
              },
              maxLines: null,
              textInputAction: TextInputAction.done,
            ),

            // Search results for autocomplete
            if (_searchResults.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(
                        'Your existing topics:',
                        style: TextStyle(
                          fontWeight: FontWeight.w500,
                          color: Colors.grey.shade700,
                        ),
                      ),
                    ),
                    const Divider(height: 1),
                    ..._searchResults.map((topic) {
                      return ListTile(
                        title: Text(topic.name),
                        subtitle:
                            topic.description.isNotEmpty
                                ? Text(
                                  topic.description,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                )
                                : null,
                        onTap: () {
                          _controller.text = topic.name;
                          setState(() {
                            _searchResults.clear();
                          });
                          widget.onTopicsSelected([topic.name]);
                        },
                        dense: true,
                      );
                    }).toList(),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Submit button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed:
                    (_controller.text.trim().isNotEmpty &&
                            !chatProvider.isStartingSession)
                        ? _submitTopics
                        : null,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child:
                    chatProvider.isStartingSession
                        ? Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Theme.of(context).colorScheme.onPrimary,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text('Starting Session...'),
                          ],
                        )
                        : const Text(
                          'Start Learning Session',
                          style: TextStyle(fontSize: 16),
                        ),
              ),
            ),

            // Loading indicator
            if (chatProvider.isLoadingPopularTopics ||
                _isSearching ||
                chatProvider.isStartingSession) ...[
              const SizedBox(height: 16),
              Center(
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    if (chatProvider.isStartingSession) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Starting your learning session...',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        );
      },
    );
  }

  void _onSearchChanged(String value) {
    setState(() {
      _searchQuery = value;
    });

    // Debounce search
    Future.delayed(const Duration(milliseconds: 500), () {
      if (_searchQuery == value && value.trim().isNotEmpty) {
        _performSearch(value);
      } else if (value.trim().isEmpty) {
        setState(() {
          _searchResults.clear();
        });
      }
    });
  }

  Future<void> _performSearch(String query) async {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    setState(() {
      _isSearching = true;
    });

    try {
      // Only search for single words to show existing topics
      final words = query
          .split(',')
          .map((w) => w.trim())
          .where((w) => w.isNotEmpty);
      if (words.length == 1) {
        final results = await chatProvider.searchTopics(words.first);
        setState(() {
          _searchResults = results;
        });
      } else {
        setState(() {
          _searchResults.clear();
        });
      }
    } catch (e) {
      // Handle search error silently
      setState(() {
        _searchResults.clear();
      });
    } finally {
      setState(() {
        _isSearching = false;
      });
    }
  }

  void _submitTopics() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final topics =
        text
            .split(',')
            .map((topic) => topic.trim())
            .where((topic) => topic.isNotEmpty)
            .toList();

    if (topics.isNotEmpty) {
      widget.onTopicsSelected(topics);
    }
  }
}
