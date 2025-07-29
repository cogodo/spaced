# Question Management Implementation Plan

## Overview
This plan outlines the implementation of question management functionality for the "All Reviews" screen, allowing users to view, add, and delete questions within topics.

## Current State Analysis

### Frontend (Flutter)
- **All Review Items Screen**: `flutter_app/lib/screens/all_review_items_screen.dart`
  - Currently displays topics with review status
  - Has delete topic functionality
  - Uses `ChatProvider` to fetch due topics
- **API Service**: `flutter_app/lib/services/session_api.dart`
  - Has topic management endpoints
  - No direct question management endpoints
- **Models**: Questions are not directly exposed in frontend models

### Backend (Python/FastAPI)
- **Question Service**: `src/backend/core/services/question_service.py`
  - Has methods for getting, creating, and deleting questions
  - Supports question generation
- **Question Repository**: `src/backend/core/repositories/question_repository.py`
  - CRUD operations for questions in Firestore
- **API Endpoints**: `src/backend/api/v1/endpoints/topics.py`
  - Has topic management but no direct question endpoints

## Implementation Plan

### Phase 1: Backend API Endpoints

#### 1.1 Create Question Management Endpoints
**File**: `src/backend/api/v1/endpoints/questions.py` (new file)

```python
@router.get("/topics/{topic_id}/questions")
async def get_topic_questions(topic_id: str, current_user: dict = Depends(get_current_user))

@router.post("/topics/{topic_id}/questions")
async def create_questions(topic_id: str, questions: List[CreateQuestionRequest], current_user: dict = Depends(get_current_user))

@router.delete("/topics/{topic_id}/questions/{question_id}")
async def delete_question(topic_id: str, question_id: str, current_user: dict = Depends(get_current_user))

@router.put("/topics/{topic_id}/questions/{question_id}")
async def update_question(topic_id: str, question_id: str, question: UpdateQuestionRequest, current_user: dict = Depends(get_current_user))
```

#### 1.2 Add Request/Response Models
**File**: `src/backend/core/models/question.py` (extend existing)

```python
class CreateQuestionRequest(BaseModel):
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int = 1

class UpdateQuestionRequest(BaseModel):
    text: str
    type: Literal["multiple_choice", "short_answer", "explanation"]
    difficulty: int
```

#### 1.3 Update Router Configuration
**File**: `src/backend/api/v1/router.py`
- Add questions router to main API router

### Phase 2: Frontend API Service Updates

#### 2.1 Extend ApiService
**File**: `flutter_app/lib/services/session_api.dart`

Add new methods:
```dart
Future<List<Question>> getTopicQuestions(String topicId)
Future<void> createQuestions(String topicId, List<CreateQuestionRequest> questions)
Future<void> deleteQuestion(String topicId, String questionId)
Future<void> updateQuestion(String topicId, String questionId, UpdateQuestionRequest question)
```

#### 2.2 Add Question Models
**File**: `flutter_app/lib/models/question.dart` (new file)

```dart
class Question {
  final String id;
  final String topicId;
  final String text;
  final String type;
  final int difficulty;
  final Map<String, dynamic> metadata;
  
  // ... constructor, fromJson, toJson methods
}

class CreateQuestionRequest {
  final String text;
  final String type;
  final int difficulty;
  
  // ... constructor, toJson methods
}
```

### Phase 3: Frontend UI Components

#### 3.1 Create Question Management Dialog
**File**: `flutter_app/lib/widgets/question_management_dialog.dart` (new file)

Features:
- Display topic information
- List existing questions with delete functionality
- Add new questions (single or bulk)
- Question type selection (multiple choice, short answer, explanation)
- Difficulty level selection
- Bulk question input with text area
- Validation and error handling

#### 3.2 Create Question List Widget
**File**: `flutter_app/lib/widgets/question_list_widget.dart` (new file)

Features:
- Scrollable list of questions
- Question type indicators
- Difficulty level display
- Delete buttons for each question
- Loading states

#### 3.3 Create Question Input Widget
**File**: `flutter_app/lib/widgets/question_input_widget.dart` (new file)

Features:
- Single question input form
- Bulk question input (multiple questions in text area)
- Question type dropdown
- Difficulty slider
- Validation

### Phase 4: Update All Review Items Screen

#### 4.1 Modify AllReviewItemsScreen
**File**: `flutter_app/lib/screens/all_review_items_screen.dart`

Changes:
- Add tap handler to topic cards
- Show question management dialog on tap
- Add loading states for question operations
- Handle errors gracefully

#### 4.2 Update ChatProvider
**File**: `flutter_app/lib/providers/chat_provider.dart`

Add methods:
```dart
Future<List<Question>> getTopicQuestions(String topicId)
Future<void> createQuestions(String topicId, List<CreateQuestionRequest> questions)
Future<void> deleteQuestion(String topicId, String questionId)
Future<void> updateQuestion(String topicId, String questionId, UpdateQuestionRequest question)
```

### Phase 5: User Experience Enhancements

#### 5.1 Add Confirmation Dialogs
- Delete question confirmation
- Bulk operations confirmation
- Unsaved changes warning

#### 5.2 Add Loading States
- Question loading indicators
- Save/delete operation feedback
- Error state handling

#### 5.3 Add Success Feedback
- Toast messages for successful operations
- Visual feedback for changes
- Auto-refresh topic list after changes

## Implementation Details

### Backend Implementation Order
1. Create question models and endpoints
2. Add authentication and authorization
3. Implement CRUD operations
4. Add error handling and validation
5. Update router configuration
6. Test endpoints

### Frontend Implementation Order
1. Create question models
2. Extend API service
3. Create UI components
4. Update ChatProvider
5. Modify AllReviewItemsScreen
6. Add error handling and loading states
7. Test functionality

### Database Schema
Questions are stored in Firestore:
```
users/{userId}/topics/{topicId}/questions/{questionId}
```

Question document structure:
```json
{
  "id": "question_id",
  "topicId": "topic_id",
  "text": "Question text",
  "type": "multiple_choice|short_answer|explanation",
  "difficulty": 1-3,
  "metadata": {
    "generated_by": "user|openai",
    "created_at": "timestamp"
  }
}
```

## Testing Strategy

### Backend Testing
1. Unit tests for question service methods
2. Integration tests for API endpoints
3. Authentication and authorization tests
4. Error handling tests

### Frontend Testing
1. Widget tests for UI components
2. Integration tests for API calls
3. User interaction tests
4. Error state tests

## Security Considerations

1. **Authentication**: All endpoints require valid Firebase auth token
2. **Authorization**: Users can only access their own topics and questions
3. **Input Validation**: Validate question text, type, and difficulty
4. **Rate Limiting**: Prevent abuse of question creation endpoints
5. **Data Sanitization**: Sanitize user input to prevent XSS

## Performance Considerations

1. **Pagination**: Implement pagination for large question lists
2. **Caching**: Cache frequently accessed questions
3. **Optimistic Updates**: Update UI immediately, sync with backend
4. **Debouncing**: Debounce bulk question input
5. **Lazy Loading**: Load questions only when dialog opens

## Future Enhancements

1. **Question Templates**: Pre-defined question templates
2. **Question Import/Export**: CSV/JSON import/export functionality
3. **Question Analytics**: Usage statistics and performance metrics
4. **Question Sharing**: Share questions between users
5. **Advanced Question Types**: Support for more complex question formats

## Timeline Estimate

- **Phase 1 (Backend)**: 2-3 days
- **Phase 2 (Frontend API)**: 1-2 days
- **Phase 3 (UI Components)**: 3-4 days
- **Phase 4 (Integration)**: 2-3 days
- **Phase 5 (UX Enhancements)**: 1-2 days
- **Testing and Bug Fixes**: 2-3 days

**Total Estimated Time**: 11-17 days

## Risk Assessment

### High Risk
- Complex UI state management for bulk operations
- Performance with large question lists
- Data consistency during concurrent operations

### Medium Risk
- API endpoint design complexity
- Error handling edge cases
- User experience with bulk input

### Low Risk
- Basic CRUD operations
- Authentication integration
- Database schema changes

## Success Criteria

1. Users can view all questions for a topic
2. Users can add single or multiple questions
3. Users can delete individual questions
4. Users can edit existing questions
5. All operations provide appropriate feedback
6. Error states are handled gracefully
7. Performance is acceptable with 100+ questions
8. Security requirements are met 