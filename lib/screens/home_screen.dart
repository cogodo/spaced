import 'package:flutter/material.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  final List<String> reviewItems;

  const HomeScreen({Key? key, required this.reviewItems}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Today's Reviews"),
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: () {
              // Settings navigation can still use a normal push since it's a modal route.
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: ListView.builder(
        itemCount: widget.reviewItems.length,
        itemBuilder: (context, index) {
          return CheckboxListTile(
            title: Text(widget.reviewItems[index]),
            value: false,
            onChanged: (bool? newValue) {
              // Remove the task once it is checked off.
              setState(() {
                widget.reviewItems.removeAt(index);
              });
            },
          );
        },
      ),
    );
  }
}
