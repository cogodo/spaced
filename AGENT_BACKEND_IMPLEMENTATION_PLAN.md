# 🤖 Agent Backend Implementation Plan

## 📋 Overview
Integrate the chat system with the spaced repetition review system, creating an intelligent agent that:
1. Asks active recall questions based on due review items from FSRS algorithm
2. Adapts question difficulty based on FSRS difficulty levels
3. Evaluates user responses and updates review schedules via frontend FSRS
4. Provides contextual follow-up questions and tie-ins
5. Offers choice between reviewing due items or custom topics

---

## 🎯 Current State Analysis

### ✅ Already Implemented
- **Basic Chat Flow**: LangGraph with respond_node and evaluate_node
- **Question Generation**: AI generates questions for user-provided topics
- **Session Management**: Backend tracks sessions and Q&A history
- **Score Evaluation**: Evaluator assigns 0-5 scores per topic
- **Frontend Integration**: Chat UI with session persistence
- **FSRS Algorithm**: Frontend has existing FSRS implementation for task updates

### 🔄 What Needs Enhancement
- **Firebase Integration**: Connect to user's review tasks
- **Difficulty-Based Questions**: Adapt questions based on FSRS difficulty
- **Review Schedule Updates**: Pass scores to frontend FSRS algorithm
- **Active Recall Focus**: Better prompting with detailed question types
- **Session Type Selection**: Choice between due items vs custom topics

---

## 📊 FSRS Task Structure
```javascript
// Located at: users/{userId}/tasks/{taskName}
{
  "task": "sleep stuff",                    // Task name/topic
  "difficulty": 0.285,                      // FSRS difficulty (0.0-1.0)
  "lastReviewDate": "2025-06-08T00:00:00.000",
  "nextReviewDate": "2025-06-14T00:00:00.000", 
  "previousInterval": 6,                    // Days since last review
  "repetition": 1,                          // Number of times reviewed
  "stability": 1.5,                         // FSRS stability factor
  "daysSinceInit": 0                        // Days since task creation
}
```

### FSRS Integration Notes
- **Difficulty Range**: 0.0 (easy) to 1.0 (very difficult)
- **Due Items**: Tasks where `nextReviewDate <= today`
- **Score Mapping**: Chat scores (0-5) → FSRS grades → Updated schedule
- **Frontend Algorithm**: Existing FSRS implementation handles schedule updates

---

## 🏗️ Architecture Components

### 1. **Review Task Service**
```python
class ReviewTaskService:
    async def get_due_tasks(user_id: str) -> List[Task]
    async def get_all_tasks(user_id: str) -> List[Task]
    def filter_due_tasks(tasks: List[Task]) -> List[Task]
    def prioritize_tasks(tasks: List[Task]) -> List[Task]  # By difficulty, overdue days
```

### 2. **Enhanced Question Generator**
```python
class QuestionGenerator:
    def generate_question(task_name: str, difficulty: float, question_type: str) -> str
    def get_followup_question(task_name: str, user_answer: str, context: str) -> str
    def select_question_type(difficulty: float) -> str  # Based on FSRS difficulty
```

### 3. **Session Evaluator**
```python
class SessionEvaluator:
    def evaluate_responses(qa_history: List[QA]) -> Dict[str, int]  # Returns 0-5 scores
    def format_scores_for_frontend(scores: Dict[str, int]) -> Dict  # For FSRS update
```

---

## 📊 Data Flow

### Session Start Options
1. **Check Due Tasks**: Fetch tasks where `nextReviewDate <= today`
2. **Present Choice**: 
   - If due tasks exist: "Review Due Items" vs "Custom Topics"
   - If no due tasks: "All caught up! Try custom topics?"
3. **Initialize Session**: Based on user choice

### Due Items Session Flow
1. **Fetch Due Tasks**: Get overdue/due tasks from Firebase
2. **Prioritize**: Order by difficulty (hardest first) and days overdue
3. **Generate Questions**: Adapt to FSRS difficulty level
4. **Track Progress**: Monitor per-task understanding

### Custom Topics Session Flow
1. **User Input**: Manual topic entry (existing flow)
2. **Question Generation**: Standard difficulty progression
3. **Evaluation**: Standard scoring without FSRS updates

### Session End (Due Items)
1. **Evaluate Responses**: Score each task 0-5
2. **Return to Frontend**: Pass scores for FSRS algorithm
3. **Update Tasks**: Frontend handles FSRS schedule updates
4. **Session Summary**: Show progress and next review dates

---

## 🎯 Question Types & Active Recall Techniques

### System Prompt Definitions:
```
1. **FREE RECALL**: "Tell me everything you know about [topic]"
   - Open-ended, no hints
   - Tests comprehensive understanding
   - Example: "Explain the concept of machine learning"

2. **CUED RECALL**: Provide context, ask for specific details
   - Guided retrieval with prompts
   - Example: "In Python, when you use a 'with' statement, what happens to the file?"

3. **RECOGNITION**: Multiple choice or true/false
   - Easier for high-difficulty items
   - Example: "Which of these is a Python data type: A) list B) array C) vector"

4. **APPLICATION**: Real-world scenario questions
   - Tests practical understanding
   - Example: "You need to store user data that persists. What would you use?"

5. **CONNECTION**: Relate topics to each other
   - Tests deeper understanding
   - Example: "How does recursion relate to the concept of divide-and-conquer?"

6. **ELABORATION**: Build on previous answers
   - Follow-up questions
   - Example: "You mentioned X. Can you explain why that works?"

**Difficulty Adaptation**:
- High difficulty (0.7-1.0): More recognition, cued recall, multiple choice
- Medium difficulty (0.3-0.7): Mix of all types
- Low difficulty (0.0-0.3): More free recall, application, connection questions
```

---

## 🔧 Implementation Phases

### Phase 1: Firebase Integration & Task Fetching
- [ ] Add Firebase Admin SDK to backend
- [ ] Implement ReviewTaskService for task CRUD operations
- [ ] Create authentication middleware for user context
- [ ] Test fetching due tasks from `users/{userId}/tasks/`

### Phase 2: Session Flow Enhancement
- [ ] Add session type selection (due items vs custom)
- [ ] Implement due task detection and prioritization
- [ ] Update start_session endpoint to handle both modes
- [ ] Add "no due items" messaging

### Phase 3: Difficulty-Adaptive Question Generation
- [ ] Update prompts with detailed question type definitions
- [ ] Implement difficulty-based question type selection
- [ ] Add follow-up question generation based on user responses
- [ ] Test question variety and appropriateness

### Phase 4: Evaluation & FSRS Integration
- [ ] Enhance evaluator with task-specific scoring
- [ ] Format scores for frontend FSRS algorithm consumption
- [ ] Test score accuracy and consistency
- [ ] Validate integration with existing frontend FSRS

### Phase 5: Advanced Features
- [ ] Multi-task tie-ins and connections
- [ ] Adaptive session length based on performance
- [ ] Progress analytics and session summaries
- [ ] Performance optimization and caching

---

## 🔐 Authentication & Security

### User Authentication Flow
1. **Frontend**: Pass Firebase ID token or user ID with chat requests
2. **Backend**: Validate token using Firebase Admin SDK
3. **User Context**: Extract user_id for Firestore queries
4. **Security**: Ensure users can only access their own tasks

### Implementation Options
```python
# Option 1: ID Token Validation
async def verify_token(id_token: str) -> str:
    decoded_token = auth.verify_id_token(id_token)
    return decoded_token['uid']

# Option 2: User ID with validation
async def validate_user_session(user_id: str, session_context: dict) -> bool:
    # Validate user owns the chat session
    return True
```

---

## 🎯 API Updates

### Enhanced Start Session
```python
@app.post("/start_session")
async def start_session(payload: StartSessionPayload):
    # NEW: Support both session types
    {
        "session_type": "due_items" | "custom_topics",
        "user_id": "firebase_user_id",  # NEW
        "topics": ["topic1", "topic2"],  # Optional for custom
        "max_topics": 3,
        "max_questions": 7
    }
    
    # Returns:
    {
        "session_id": "uuid",
        "session_type": "due_items",
        "next_question": "question text",
        "due_tasks_count": 5,  # NEW
        "current_task": "task_name"  # NEW for due_items
    }
```

### Enhanced Answer Endpoint
```python
# Response includes task context for due_items sessions
{
    "next_question": "question text",
    "current_task": "task_name",
    "progress": "2/5 tasks completed"  # NEW
}
```

### New Session Completion
```python
@app.post("/complete_session")  # NEW endpoint
async def complete_session(session_id: str):
    # Returns scores formatted for frontend FSRS
    {
        "scores": {
            "task_name_1": 4,
            "task_name_2": 2
        },
        "session_summary": "Completed 5 tasks, average score: 3.2",
        "tasks_for_fsrs_update": [...]  # Formatted for frontend
    }
```

---

## 🚀 Success Metrics

### User Experience
- [ ] Clear choice between due items and custom topics
- [ ] Appropriate question difficulty for FSRS difficulty levels
- [ ] Engaging variety of question types
- [ ] Smooth integration with existing FSRS workflow

### System Performance
- [ ] Fast Firebase task fetching (<1s)
- [ ] Accurate question difficulty adaptation
- [ ] Reliable score evaluation and formatting
- [ ] Secure user authentication and data isolation

### Learning Outcomes
- [ ] Improved task completion rates
- [ ] Better retention with adaptive questioning
- [ ] Effective FSRS schedule optimization
- [ ] Measurable learning progress over time

---

## 📝 Next Steps

1. **Set up Firebase Admin SDK** in backend with service account
2. **Implement task fetching** and due item detection logic
3. **Update session flow** with type selection
4. **Enhance question generation** with difficulty adaptation
5. **Test end-to-end** with real FSRS tasks
6. **Integrate with frontend** FSRS algorithm

---

*This enhanced plan creates a seamless bridge between the chat system and your existing FSRS-based spaced repetition workflow, providing adaptive learning experiences based on individual task difficulty.* 🎓 