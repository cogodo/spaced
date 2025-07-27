import 'package:flutter/material.dart';
import '../services/stt_service.dart';

class SttButton extends StatefulWidget {
  final SttService sttService;
  final Function(String transcript) onTranscriptReceived;
  final double size;

  const SttButton({
    Key? key,
    required this.sttService,
    required this.onTranscriptReceived,
    this.size = 56.0,
  }) : super(key: key);

  @override
  State<SttButton> createState() => _SttButtonState();
}

class _SttButtonState extends State<SttButton> {
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _isRecording = widget.sttService.isRecording;
  }

  @override
  void didUpdateWidget(SttButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Sync state when service changes
    if (widget.sttService != oldWidget.sttService) {
      setState(() {
        _isRecording = widget.sttService.isRecording;
      });
    }
  }

  Future<void> _handleTap() async {
    if (_isRecording) {
      // Stop recording and get transcript
      final transcript = await widget.sttService.stopRecordingAndTranscribe();
      setState(() {
        _isRecording = false;
      });
      if (transcript != null && transcript.isNotEmpty) {
        widget.onTranscriptReceived(transcript);
      } else {
        // Show error if no transcript received
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('No audio detected. Please try again.'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } else {
      // Start recording
      final success = await widget.sttService.startRecording();
      if (success) {
        setState(() {
          _isRecording = true;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Recording started. Tap again to stop.'),
            duration: Duration(seconds: 1),
          ),
        );
      } else {
        // Show error if recording failed
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Failed to start recording. Please check microphone permissions.',
            ),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: _handleTap,
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color:
              _isRecording
                  ? theme.colorScheme.error
                  : theme.colorScheme.surfaceContainerHighest,
          boxShadow: [
            BoxShadow(
              color: theme.shadowColor.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Icon(
          _isRecording ? Icons.stop : Icons.mic,
          color:
              _isRecording
                  ? theme.colorScheme.onError
                  : theme.colorScheme.onSurface,
          size: widget.size * 0.5,
        ),
      ),
    );
  }
}
