import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/logger_service.dart';
import '../models/schedule_manager.dart';
import '../models/task_holder.dart';
import 'quality_selector_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _logger = getLogger('HomeScreen');
  List<Task> _todaysTasks = [];
  bool _isRefreshing = false;


  @override
  void initState() {
    super.initState();
    // Fetch tasks after the widget is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshTasks();
    });
  }

  void _refreshTasks() {
    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );
    setState(() {
      _todaysTasks = scheduleManager.getTodaysTasks();
      _isRefreshing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    // Listen to ScheduleManager changes to update the UI
    Provider.of<ScheduleManager>(context);

    if (_isRefreshing) {
      _refreshTasks();
    }

    return RefreshIndicator(
      onRefresh: () async {
        setState(() {
          _isRefreshing = true;
        });
      },
      child: _buildContent(context),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (_todaysTasks.isEmpty) {
      return _buildEmptyState(context);
    } else {
      return _buildTaskList(context);
    }
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.celebration, size: 120, color: Colors.amber),
          SizedBox(height: 32),
          Text(
            'All Caught Up!',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 16),
          Text(
            'No items to review today.',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          Text(
            'Check back tomorrow or add new items.',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildTaskList(BuildContext context) {
    return ListView.builder(
      itemCount: _todaysTasks.length,
      padding: EdgeInsets.all(16),
      itemBuilder: (context, index) {
        final task = _todaysTasks[index];
        return _buildTaskCard(context, task);
      },
    );
  }

  Widget _buildTaskCard(BuildContext context, Task task) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _showQualitySelector(context, task),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                task.task,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.replay, size: 16, color: Colors.grey[600]),
                  SizedBox(width: 4),
                  Text(
                    'Repetition: ${task.repetition}',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                  SizedBox(width: 16),
                  Icon(Icons.timeline, size: 16, color: Colors.grey[600]),
                  SizedBox(width: 4),
                  Text(
                    'E-Factor: ${task.eFactor.toStringAsFixed(2)}',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showQualitySelector(BuildContext context, Task task) async {
    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );

    final result = await Navigator.push(
      context,
      PageRouteBuilder(
        pageBuilder:
            (context, animation, secondaryAnimation) =>
                QualitySelectorScreen(task: task),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
      ),
    );

    if (result != null && result is int) {
      final selectedQuality = result;
      _logger.info("Selected quality: $selectedQuality for task: ${task.task}");
      await scheduleManager.updateTaskReview(task, selectedQuality);
      _logger.info("Task update called. List should refresh.");
      _refreshTasks();
    } else {
      _logger.info("Quality selection cancelled for task: ${task.task}");
    }
  }
}
