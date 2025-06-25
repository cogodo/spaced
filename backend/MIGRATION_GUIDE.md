# Firestore Structure Migration Guide

## Overview

The application has been upgraded from a flat Firestore structure to a user-centric nested structure for improved security, performance, and data organization.

## What Changed

### Old Structure (Flat)
```
/sessions/{sessionId}
/topics/{topicId}
/questions/{questionId}
```

### New Structure (User-Centric)
```
/users/{userId}/sessions/{sessionId}
/users/{userId}/topics/{topicId}
/users/{userId}/topics/{topicId}/questions/{questionId}
/users/{userId}/sessions/{sessionId}/messages/{messageId}
```

## Key Benefits

1. **Security**: Path-based Firestore rules (no `get()` calls needed)
2. **Performance**: More efficient queries and pagination
3. **Data Organization**: User data is logically grouped
4. **Scalability**: Better isolation and cleanup capabilities

## Breaking Changes

### Backend Models
- **New**: `Message` model replaces embedded `Response` arrays
- **Updated**: All repository methods now require `user_uid` parameter
- **Updated**: All service methods now require `user_uid` parameter
- **Updated**: All API endpoints now pass `user_uid` to services

### API Changes
All endpoints now use the user authentication context to determine data paths. No breaking changes to frontend API contracts.

### Database Schema
- Sessions no longer embed `responses` arrays
- Session responses are now separate `Message` documents in subcollections
- Questions include embedded `questionText` in messages for efficiency

## Migration Steps

### For Existing Applications with Data

1. **Backup your Firestore data** (recommended):
   ```bash
   # Using gcloud CLI
   gcloud firestore export gs://your-backup-bucket/backup-$(date +%Y%m%d)
   ```

2. **Run the migration script**:
   ```bash
   cd backend
   python scripts/migrate_firestore_structure.py
   ```

3. **The script will**:
   - Run a dry-run first to show what will be migrated
   - Ask for confirmation before making changes
   - Migrate all data to the new structure
   - Optionally clean up old data

4. **Test your application** thoroughly after migration

5. **Update Firestore rules** if you have custom rules

### For New Applications

No migration needed. The new structure will be used from the start.

## Security Rules Update

The new Firestore rules are path-based and more efficient:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User subcollections - path-based security
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Backward compatibility for transition period (optional)
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userUid;
    }
    match /topics/{topicId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.ownerUid;
    }
    match /questions/{questionId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## Troubleshooting

### Migration Issues

1. **"Migration script fails"**:
   - Check Firebase credentials
   - Ensure proper permissions
   - Review logs for specific errors

2. **"Data missing after migration"**:
   - Check if dry-run showed all expected data
   - Verify user IDs are consistent
   - Check Firestore rules allow access

3. **"Application errors after migration"**:
   - Ensure all services are updated
   - Check API endpoint parameter passing
   - Verify frontend authentication

### Performance Issues

1. **Slow queries**:
   - Ensure proper indexing on new paths
   - Use pagination for large datasets
   - Consider composite indexes for complex queries

2. **Security rule errors**:
   - Verify user authentication context
   - Check path-based rule coverage
   - Monitor Firestore security logs

## Development Notes

### Testing the Migration

1. Create test data in old structure
2. Run migration script in dry-run mode
3. Verify expected output
4. Run actual migration
5. Test application functionality
6. Compare data integrity

### Rolling Back

If issues occur:

1. **Before cleanup**: Old data still exists, can revert code changes
2. **After cleanup**: Restore from backup and revert code changes

## Support

If you encounter issues:

1. Check the logs in the migration script output
2. Verify Firestore rules are updated
3. Ensure all dependencies are current
4. Test with a clean user account

## Technical Details

### Message Embedding

Questions texts are embedded in messages for efficiency:
- Reduces read operations (no need to fetch question separately)
- Improves performance for message lists
- Maintains data consistency

### Pagination Strategy

New structure supports efficient pagination:
- 5 questions per session
- 5 messages per page in history
- User-scoped collections for better performance

### Migration Script Details

The migration script:
1. Preserves all existing data
2. Maintains referential integrity
3. Handles edge cases (missing fields, orphaned data)
4. Provides dry-run mode for safety
5. Includes cleanup functionality 