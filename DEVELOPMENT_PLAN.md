# 🚀 **Spaced Repetition Evolution Plan**
## From Manual Topics to Intelligent Daily Reviews

---

## 📋 **Phase 1: Firebase Foundation**
### **1.1 Authentication Setup**
- [ ] Add Firebase Auth to Flutter app
- [ ] Implement sign-in/sign-up UI screens
- [ ] Add anonymous auth as fallback option
- [ ] Handle auth state changes in app routing

### **1.2 Firestore Database Design**
```json
// Users collection
users/{userId} = {
  "createdAt": timestamp,
  "displayName": string,
  "email": string
}

// User's learning items
users/{userId}/learningItems/{itemId} = {
  "topic": string,
  "createdAt": timestamp,
  "lastReviewed": timestamp,
  "nextReview": timestamp,
  "fsrsData": {
    "stability": number,
    "difficulty": number,
    "retrievability": number,
    "reviews": number
  },
  "currentScore": number, // 0-5
  "history": [
    {
      "sessionId": string,
      "timestamp": timestamp,
      "questions": [
        {
          "question": string,
          "answer": string,
          "score": number
        }
      ]
    }
  ]
}

// Active sessions
users/{userId}/sessions/{sessionId} = {
  "type": "review" | "newTopics",
  "createdAt": timestamp,
  "items": array of itemIds,
  "currentIndex": number,
  "completed": boolean
}
```

### **1.3 Backend Firebase Integration**
- [ ] Add Firebase Admin SDK to Python backend
- [ ] Create Firestore service module
- [ ] Add authentication middleware to FastAPI
- [ ] Update API endpoints to require auth tokens

---

## 📋 **Phase 2: FSRS Integration & Review Logic**

### **2.1 FSRS Service Implementation**
```python
# backend/my_agent/services/fsrs_service.py
class FSRSService:
    def calculate_next_review(item_data, score):
        # Calculate based on FSRS algorithm
        pass
    
    def get_items_due_for_review(user_id):
        # Query Firestore for items due today
        pass
    
    def update_item_after_review(item_id, score, session_data):
        # Update FSRS data and schedule next review
        pass
```

### **2.2 Review Scheduling Logic**
- [ ] Daily review calculator (items due today)
- [ ] FSRS interval calculation integration
- [ ] Batch review session creator
- [ ] Review completion tracker

---

## 📋 **Phase 3: Enhanced LangGraph System**

### **3.1 New Session Types**
```python
# Update GraphState
class GraphState(TypedDict):
    session_type: str  # "review" | "newTopics" | "mixed"
    user_id: str
    review_items: List[Dict]  # Items due for review
    new_topics: List[str]     # Newly added topics
    current_item_index: int
    # ... existing fields
```

### **3.2 New Node Functions**
```python
# my_agent/utils/nodes.py
def review_scheduler_node(state):
    """Gets items due for review for user"""
    pass

def new_topic_collector_node(state):
    """Handles adding new topics before reviews"""
    pass

def smart_question_generator_node(state):
    """Generates questions based on item history"""
    pass

def fsrs_evaluator_node(state):
    """Updates FSRS data after review"""
    pass
```

### **3.3 Updated Graph Flow**
```
Entry → Auth Check → Review Scheduler → New Topic Collector → 
Review Session → FSRS Evaluator → Session Complete
```

---

## 📋 **Phase 4: Flutter App Evolution**

### **4.1 New UI Screens**
- [ ] **Login/Signup Screen** - Firebase auth
- [ ] **Dashboard Screen** - Shows review counts, streaks
- [ ] **Add Topics Screen** - Pre-review topic addition
- [ ] **Review Session Screen** - Enhanced chat for reviews
- [ ] **Progress Screen** - FSRS analytics, upcoming reviews

### **4.2 State Management Updates**
```dart
// New app states
enum AppState {
  unauthenticated,
  loading,
  dashboardReady,
  addingTopics,
  reviewSession,
  noReviewsDue
}

// New session flow
enum ReviewSessionState {
  checkingDueItems,
  addingNewTopics,
  activeReview,
  completed,
  error
}
```

### **4.3 Enhanced Chat Screen**
- [ ] Review-specific messaging (e.g., "Question 3 of 7 for Flutter")
- [ ] Progress indicators for current review session
- [ ] Item context display (last reviewed, current score)
- [ ] Smart completion messages with next review dates

---

## 📋 **Phase 5: API Endpoint Evolution**

### **5.1 New Endpoints**
```python
@app.post("/start_review_session")
async def start_review_session(user_token: str):
    # Get items due for review, create session
    pass

@app.post("/add_new_topics")
async def add_new_topics(user_token: str, topics: List[str]):
    # Add topics to user's learning items
    pass

@app.post("/complete_review")
async def complete_review(session_id: str, item_scores: Dict):
    # Update FSRS data, schedule next reviews
    pass

@app.get("/user_dashboard")
async def get_dashboard(user_token: str):
    # Get review counts, streaks, progress data
    pass
```

### **5.2 Enhanced LLM Integration**
```python
def generate_review_question(item_data, user_history):
    """Generate contextual questions based on item history"""
    prompt = f"""
    Generate a question for: {item_data['topic']}
    Last score: {item_data['currentScore']}/5
    Times reviewed: {len(item_data['history'])}
    Previous questions: {get_previous_questions(item_data)}
    
    Make the question appropriately challenging based on their history.
    """
```

---

## 📋 **Phase 6: Migration & Deployment**

### **6.1 Data Migration Strategy**
- [ ] Backup existing session data
- [ ] Create migration scripts for any existing users
- [ ] Implement graceful fallback to manual topics
- [ ] Add feature flags for gradual rollout

### **6.2 Testing Strategy**
- [ ] Unit tests for FSRS calculations
- [ ] Integration tests for Firebase operations
- [ ] E2E tests for complete review flow
- [ ] Performance tests for large user datasets

---

## 🎯 **Implementation Priority Order**

1. **Week 1-2**: Phase 1 (Firebase setup)
2. **Week 3**: Phase 2 (FSRS integration)
3. **Week 4-5**: Phase 3 (LangGraph enhancement)
4. **Week 6-7**: Phase 4 (Flutter UI updates)
5. **Week 8**: Phase 5 (API completion)
6. **Week 9**: Phase 6 (Testing & deployment)

---

## 🔧 **Technical Considerations**

### **Database Optimization**
- Index on `nextReview` field for efficient due-item queries
- Batch operations for multiple item updates
- Pagination for users with many learning items

### **Security**
- Firebase security rules for user data isolation
- API rate limiting for review sessions
- Input validation for all user-generated content

### **Performance**
- Cache user's due items in memory during session
- Batch Firestore writes for session completion
- Optimize LLM prompts for faster generation

---

## 📱 **Future Enhancements** *(Phase 7+)*
- [ ] Spaced repetition analytics dashboard
- [ ] Social features (study streaks, leaderboards)
- [ ] Import/export learning data
- [ ] Offline review capability
- [ ] Multi-device sync optimization
- [ ] Advanced FSRS algorithm customization

---

## 📝 **Development Notes**

### **Current System**
- Manual topic input via chat interface
- In-memory session storage
- Mock LLM responses
- Basic Q&A flow with completion scoring

### **Target System**
- Firebase authentication and data persistence
- Intelligent daily review scheduling
- FSRS-powered spaced repetition
- Two-stage interaction: new topics → reviews
- Enhanced LLM context with user history

### **Key Design Decisions**
1. **Firebase as primary data layer** - Handles auth, real-time data, scaling
2. **Maintain existing chat interface** - Familiar user experience
3. **Gradual migration strategy** - Keep fallback options during transition
4. **FSRS integration with existing algorithm** - Leverage proven spaced repetition science
5. **Two-stage daily flow** - New topics first, then reviews (later implementation)

---

## 🎯 **Success Metrics**
- User retention and daily active usage
- Review completion rates
- FSRS algorithm effectiveness (memory retention)
- User satisfaction with question quality
- System performance under load

---

**Last Updated**: December 2024  
**Project**: Spaced Repetition Learning App  
**Status**: Planning Phase 