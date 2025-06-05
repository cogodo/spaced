import 'package:flutter/material.dart';
import '../models/task_holder.dart';

class QualitySelectorScreen extends StatelessWidget {
  final Task task;

  QualitySelectorScreen({super.key, required this.task});

  final Map<int, String> _qualityDescriptions = {
    5: 'Perfect recall',
    4: 'Correct after hesitation',
    3: 'Correct with difficulty',
    2: 'Wrong, but recognized the answer',
    1: 'Wrong, seemed familiar',
    0: 'Complete blackout',
  };

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 600;

    return Scaffold(
      appBar: AppBar(
        title: Text('Rate Your Recall'),
        leading: IconButton(
          icon: Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'How well did you remember:',
                  style: TextStyle(fontSize: 18),
                ),
                SizedBox(height: 8),
                Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      task.task,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              children:
                  _qualityDescriptions.entries.map((entry) {
                    return Card(
                      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: InkWell(
                        onTap: () => Navigator.of(context).pop(entry.key),
                        child: Padding(
                          padding: EdgeInsets.all(isDesktop ? 20 : 16),
                          child: Row(
                            children: [
                              Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  color: _getQualityColor(entry.key),
                                  shape: BoxShape.circle,
                                ),
                                child: Center(
                                  child: Text(
                                    '${entry.key}',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 18,
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: 16),
                              Expanded(
                                child: Text(
                                  entry.value,
                                  style: TextStyle(
                                    fontSize: isDesktop ? 18 : 16,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Color _getQualityColor(int quality) {
    switch (quality) {
      case 5:
        return Colors.green;
      case 4:
        return Colors.lightGreen;
      case 3:
        return Colors.amber;
      case 2:
        return Colors.orange;
      case 1:
        return Colors.deepOrange;
      case 0:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
