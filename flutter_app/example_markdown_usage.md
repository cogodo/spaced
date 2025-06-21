# Markdown Support in Chat Messages

Your Flutter chat app now supports rich Markdown formatting! Here are examples of what works:

## Text Formatting
- **Bold text** using `**bold**`
- *Italic text* using `*italic*`
- `Inline code` using backticks
- ~~Strikethrough~~ using `~~text~~`

## Code Blocks
```dart
void main() {
  print('Hello, Markdown!');
}
```

## Lists
1. Numbered lists
2. Work great
3. For instructions

- Bullet points
- Also supported
- Easy to read

## Links
[Visit Flutter.dev](https://flutter.dev)

## Blockquotes
> This is a quote or important note
> It stands out visually

## Tables
| Feature | User Messages | AI Messages |
|---------|---------------|-------------|
| Color | User theme | Primary color |
| Alignment | Right | Left |
| Copy | Yes | Yes |

## Usage
Simply type messages with Markdown syntax and they'll render beautifully:

**AI:** Here's how to use Flutter widgets:
```dart
Widget build(BuildContext context) {
  return Text('Hello!');
}
```

**User:** Thanks! How do I make it *bold*?

**AI:** Use `**bold**` syntax like this: **bold text** 