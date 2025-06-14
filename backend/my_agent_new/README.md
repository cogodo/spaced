# Spaced Repetition Learning Agent

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

This is a sophisticated spaced repetition learning agent built with [LangGraph](https://github.com/langchain-ai/langgraph), designed for personalized learning experiences and intelligent conversation management.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

## Features

### Core Learning Engine
- **Adaptive Conversation AI**: Sophisticated conversation management with pedagogical awareness
- **Spaced Repetition Integration**: FSRS-compatible task scheduling and review optimization
- **Real-time Learning Analytics**: Live analysis of user responses for adaptive difficulty adjustment
- **Multi-topic Session Management**: Intelligent topic progression and evaluation

### Advanced Capabilities
- **Adaptive Intelligence**: Real-time performance analysis and learning style detection
- **Firebase Integration**: Comprehensive user data, task management, and analytics storage
- **Question Generation**: Dynamic question creation and management system
- **Session Analytics**: Detailed performance tracking and learning insights

## Architecture

### LangGraph Structure
The core logic is defined in `src/agent/graph.py`, showcasing a multi-node application that manages:
- Session initialization and topic setup
- Dynamic conversation flow with AI-driven topic management
- Topic evaluation and scoring
- Session completion with comprehensive analytics

### Key Components
```
src/agent/
├── graph.py              # Main LangGraph definition
├── state.py              # GraphState schema
├── nodes.py              # LangGraph node implementations
├── tools.py              # Utility functions and AI integration
└── utils/
    ├── firebase_service.py      # Firebase/Firestore integration
    ├── adaptive_intelligence.py # Real-time learning analysis
    └── adaptive_state_integration.py # State management
```

## Getting Started

1. Install dependencies, along with the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/):

```bash
cd backend/my_agent_new
pip install -e . "langgraph-cli[inmem]"
```

2. Set up environment variables:

```bash
cp .env.example .env
```

Required environment variables:
```env
# OpenAI API (for AI conversation and analysis)
OPENAI_API_KEY=your_openai_api_key

# Firebase Configuration (choose one method)
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
# OR
FIREBASE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}

# Optional: LangSmith for tracing
LANGSMITH_API_KEY=lsv2...
```

3. Configure Firebase:
   - Place your Firebase service account file in the backend directory as `firebase-service-account.json`, OR
   - Set the `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable with the JSON content

4. Start the LangGraph Server:

```shell
langgraph dev
```

## Usage

### Session Types
The agent supports two main session types:

1. **Due Items Sessions**: Reviews tasks that are due based on FSRS spaced repetition scheduling
2. **Custom Topics Sessions**: Explores user-defined topics with adaptive conversation

### Core Workflow
1. **Session Initialization**: Welcome message and topic setup
2. **Dynamic Conversation**: AI-driven learning conversation with real-time adaptation
3. **Topic Evaluation**: Comprehensive assessment of understanding
4. **Session Completion**: Summary with scores and learning analytics

### State Management
The `GraphState` schema manages:
- Session metadata (ID, type, user, settings)
- Topic progression and scoring
- Conversation history and analysis
- Adaptive learning metrics
- Firebase task integration

## Development

### Graph Visualization
Use LangGraph Studio to visualize and debug the conversation flow. The graph shows:
- Session initialization entry point
- Conversation loops with conditional routing
- Topic evaluation branching
- Session completion endpoints

### Key Features for Development
- **Hot Reload**: Local changes automatically applied
- **State Debugging**: Edit past state and rerun from previous states
- **Thread Management**: Create new threads or extend existing conversations
- **LangSmith Integration**: Advanced tracing and collaboration

### Extending the Agent

1. **Add New Node Types**: Implement additional learning strategies in `nodes.py`
2. **Custom Question Types**: Extend question generation in the tools module
3. **Analytics Enhancement**: Add new metrics in the adaptive intelligence module
4. **Integration Expansion**: Connect to additional learning platforms

## Configuration

The agent can be configured through:
- Environment variables for API keys and Firebase
- State initialization for session parameters
- Topic sources for content customization
- Adaptive settings for personalization parameters

## Architecture Notes

### Migration from FastAPI Integration
This project represents a migration from a combined FastAPI/LangGraph structure to a pure LangGraph implementation, following LangGraph best practices:
- Clean separation of graph logic from API concerns
- Proper LangGraph state management
- Standard LangGraph project structure
- LangGraph Server compatibility

### Firebase Integration
Comprehensive integration with Firebase/Firestore for:
- User authentication and profiles
- FSRS task scheduling and storage
- Session analytics and metrics
- Learning insights and recommendations

For more information on LangGraph development, refer to the [LangGraph documentation](https://langchain-ai.github.io/langgraph/).
