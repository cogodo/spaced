# FSRS Spaced Repetition System Guide

## Overview

The application now includes a comprehensive spaced repetition system using FSRS (Free Spaced Repetition Scheduler) algorithm. This system automatically schedules topic reviews based on your performance to optimize long-term memory retention.

## Key Features

### 🧠 **Smart Scheduling**
- Uses FSRS algorithm for optimal review intervals
- Adapts to your performance automatically
- Schedules reviews when you're most likely to forget

### 📊 **Review Analytics**
- Track study streaks and retention rates
- Get insights on study patterns
- Monitor topic difficulty and progress

### 🎯 **Personalized Learning**
- Each topic has individual FSRS parameters
- Performance-based difficulty adjustment
- Optimized for long-term retention

## How It Works

### 1. **Session Completion Updates FSRS**
When you complete a learning session (all 20 questions in a topic):

```python
# Session completion triggers FSRS update
overall_score = calculate_final_score(messages)
fsrs_update = await update_topic_fsrs_advanced(topic_id, overall_score, user_uid)

# Returns next review information
{
    "nextReviewAt": datetime,
    "intervalDays": 7,
    "daysUntilReview": 7,
    "stability": 3.2,
    "difficulty": 6.8
}
```

### 2. **FSRS Parameters**
Each topic maintains these parameters:

- **Ease**: How easy the topic is for you (higher = easier)
- **Interval**: Days between reviews
- **Repetition**: Number of times reviewed
- **Last Reviewed**: When you last studied this topic
- **Next Review**: When you should review it next

### 3. **Review Scheduling**
Based on performance:
- **Good performance** (4-5/5): Longer intervals
- **Average performance** (3/5): Moderate intervals  
- **Poor performance** (0-2/5): Shorter intervals or immediate review

## API Endpoints

### **Get Topics with Review Status**
```http
GET /api/v1/topics/{user_uid}/with-review-status
```

Returns topics with comprehensive review information:
```json
[
  {
    "id": "topic_id",
    "name": "Python Programming",
    "questionCount": 20,
    "isDue": true,
    "isOverdue": false,
    "daysUntilReview": 0,
    "reviewUrgency": "due_today",
    "retentionProbability": 0.75,
    "fsrsParams": {
      "ease": 2.8,
      "interval": 7,
      "repetition": 3
    }
  }
]
```

### **Get Today's Reviews**
```http
GET /api/v1/topics/{user_uid}/due-today
```

Returns topics organized by urgency:
```json
{
  "overdue": [...],           // Past due date
  "dueToday": [...],          // Due today
  "upcoming": [...],          // Due within 3 days
  "totalDue": 5,
  "totalOverdue": 2
}
```

### **Get Review Statistics**
```http
GET /api/v1/topics/{user_uid}/review-statistics
```

Returns study analytics:
```json
{
  "totalTopics": 10,
  "reviewedTopics": 8,
  "studyStreak": 5,           // Consecutive study days
  "averageRetention": 0.82,   // Overall retention rate
  "weeklyLoad": 3,            // Reviews due this week
  "overdueCount": 1,
  "insights": [
    "Consider reviewing topics more frequently to improve retention",
    "1 topics are overdue for review"
  ]
}
```

## Frontend Integration

### **All Topics Screen**
Shows topics with review status indicators:
- 🔴 Overdue (past due date)
- 🟡 Due today
- 🟢 Due soon (next 3 days)
- ⚪ Scheduled (future)
- ⚫ Not scheduled (never reviewed)

### **Today's Reviews Screen**
Prioritized list for daily study:
1. **Overdue** topics (most urgent)
2. **Due today** topics
3. **Upcoming** topics (next 3 days)

### **Session Completion**
Enhanced completion messages include FSRS info:
```
🎉 Topic Mastery Achieved!

📊 Final Session Results:
• Questions Answered: 5/5
• Session Score: 4.2/5.0 (84%)

🏆 Overall Topic Performance:
• Topic Average: 4.1/5.0 (82%)

📅 Next Review: 14 days
🧠 Memory Strength: 3.8/5.0

Outstanding! Your progress has been saved for optimal spaced repetition scheduling.
```

## FSRS Algorithm Details

### **Performance to Rating Mapping**
- Score 0-1: "Again" (review immediately)
- Score 2: "Hard" (short interval)
- Score 3-4: "Good" (normal interval)
- Score 5: "Easy" (long interval)

### **Interval Calculation**
The FSRS algorithm uses:
- Previous performance history
- Current memory stability
- Difficulty assessment
- Optimal forgetting curve

### **Fallback System**
If FSRS library unavailable, uses simple algorithm:
- Good performance: Double interval (max 30 days)
- Average: Increase by 1 day
- Poor: Reset to 1 day

## Database Schema

### **Topic Model Updates**
```python
class Topic(BaseModel):
    # ... existing fields ...
    fsrsParams: FSRSParams = FSRSParams()
    nextReviewAt: Optional[datetime] = None
    lastReviewedAt: Optional[datetime] = None
```

### **FSRS Parameters**
```python
class FSRSParams(BaseModel):
    ease: float = 2.5        # Difficulty factor
    interval: int = 1        # Days between reviews
    repetition: int = 0      # Number of reviews
```

## Configuration

### **Session Limits**
- 5 questions per session (configurable)
- FSRS updates only on topic completion (all 20 questions)
- Review dates calculated immediately after completion

### **Review Thresholds**
- Due today: Within 24 hours
- Due soon: Within 3 days
- Overdue: Past scheduled date
- High retention: > 90% probability

## Best Practices

### **For Users**
1. **Consistent Study**: Regular sessions improve scheduling accuracy
2. **Honest Performance**: Answer authentically for better intervals
3. **Review Overdue**: Prioritize overdue topics to maintain retention
4. **Track Progress**: Use statistics to optimize study habits

### **For Developers**
1. **Performance Monitoring**: Track FSRS calculation times
2. **Data Validation**: Ensure review dates are reasonable
3. **Fallback Handling**: Graceful degradation if FSRS fails
4. **User Privacy**: FSRS data is user-scoped and secure

## Troubleshooting

### **Common Issues**

1. **Reviews not scheduled**
   - Check if topic has been completed (all 20 questions)
   - Verify FSRS service is working
   - Look for errors in session completion

2. **Incorrect intervals**
   - Review FSRS parameter values
   - Check performance score calculation
   - Verify date/time handling

3. **Missing review data**
   - Ensure `lastReviewedAt` is being set
   - Check Firestore permissions for user subcollections
   - Verify topic cache invalidation

### **Monitoring**

Check these metrics:
- Topic completion rates
- FSRS calculation success rates
- Review adherence (users doing scheduled reviews)
- Average retention probabilities

## Future Enhancements

### **Planned Features**
- Custom review intervals per user
- Bulk review scheduling
- Review reminders/notifications
- Advanced analytics dashboard
- Export/import of review data

### **Optimization Opportunities**
- Machine learning for personalized FSRS parameters
- A/B testing different scheduling algorithms
- Integration with external spaced repetition tools
- Advanced retention prediction models

## Testing

Use the FSRS test script to verify functionality:
```bash
cd backend
python scripts/test_fsrs_system.py
```

This tests:
- Topic completion updates FSRS parameters
- Review date calculation
- Status endpoint functionality
- Statistics generation 