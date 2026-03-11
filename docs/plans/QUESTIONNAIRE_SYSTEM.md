# Questionnaire System Implementation

## Overview
This document describes the questionnaire system implementation for Praestara, which allows users to complete psychological surveys using Likert scales, with questionnaires assigned upon registration and before appointments.

## Completed Backend Implementation

### 1. Database Models (backend/app/models.py)
✅ **Enums:**
- `ScaleType`: LIKERT_5, LIKERT_7, YES_NO
- `AppointmentStatus`: SCHEDULED, COMPLETED, CANCELLED
- `AssignmentStatus`: PENDING, COMPLETED, OVERDUE

✅ **Models:**
- `QuestionnaireTemplate`: Admin-created questionnaire templates
- `Question`: Individual questions with scale types
- `Appointment`: User appointments with providers
- `QuestionnaireAssignment`: Links questionnaires to users/appointments
- `QuestionnaireResponse`: User's completed questionnaire
- `Answer`: Individual question responses

### 2. Database Migration
✅ Migration file: `e3f102a658cd_add_questionnaire_system.py`
✅ Successfully applied to database

### 3. CRUD Operations (backend/app/crud.py)
✅ `create_questionnaire_template()`: Create questionnaire with questions
✅ `update_questionnaire_template()`: Update questionnaire and questions
✅ `create_appointment()`: Create user appointments
✅ `create_questionnaire_assignment()`: Assign questionnaire to user
✅ `create_questionnaire_response()`: Submit questionnaire with automatic scoring

### 4. API Endpoints (backend/app/api/routes/questionnaires.py)

#### Admin Endpoints:
- `GET /api/v1/questionnaires/templates` - List all templates
- `POST /api/v1/questionnaires/templates` - Create template
- `GET /api/v1/questionnaires/templates/{id}` - Get template
- `PATCH /api/v1/questionnaires/templates/{id}` - Update template
- `DELETE /api/v1/questionnaires/templates/{id}` - Delete template
- `POST /api/v1/questionnaires/assignments` - Assign questionnaire to user
- `POST /api/v1/questionnaires/appointments` - Create appointment
- `PATCH /api/v1/questionnaires/appointments/{id}` - Update appointment
- `DELETE /api/v1/questionnaires/appointments/{id}` - Delete appointment
- `PATCH /api/v1/questionnaires/responses/{id}` - Override response score

#### User Endpoints:
- `GET /api/v1/questionnaires/assignments/me` - Get my assignments
- `GET /api/v1/questionnaires/assignments/{id}` - Get assignment details
- `POST /api/v1/questionnaires/responses` - Submit questionnaire
- `GET /api/v1/questionnaires/responses/me` - Get my responses
- `GET /api/v1/questionnaires/responses/{id}` - View specific response
- `GET /api/v1/questionnaires/appointments` - View appointments

## Frontend Implementation Needed

### Phase 1: Admin Questionnaire Management UI

#### Components to Create:

1. **frontend/src/components/Questionnaires/QuestionnaireList.tsx**
   - Display all questionnaire templates
   - Add/Edit/Delete actions
   - Active/Inactive toggle

2. **frontend/src/components/Questionnaires/AddQuestionnaire.tsx**
   - Form to create new questionnaire
   - Question builder with drag-and-drop ordering
   - Scale type selector (Likert 5, Likert 7, Yes/No)
   - Add/Remove questions dynamically

3. **frontend/src/components/Questionnaires/EditQuestionnaire.tsx**
   - Edit existing questionnaire
   - Modify questions
   - Update questionnaire details

4. **frontend/src/components/Questionnaires/QuestionBuilder.tsx**
   - Reusable component for building questions
   - Question text input
   - Scale type dropdown
   - Required checkbox
   - Order management

5. **frontend/src/components/Questionnaires/AssignQuestionnaire.tsx**
   - Select users to assign questionnaire
   - Optional appointment selection
   - Set due date
   - Bulk assignment capability

6. **frontend/src/components/Questionnaires/ResponseViewer.tsx**
   - View user responses
   - Display scores (total and manual override)
   - Filter by user, date, questionnaire
   - Export functionality

#### Routes to Create:
- `/admin/questionnaires` - Main questionnaire management
- `/admin/questionnaires/new` - Create questionnaire
- `/admin/questionnaires/{id}/edit` - Edit questionnaire
- `/admin/questionnaires/{id}/responses` - View responses
- `/admin/appointments` - Appointment management

### Phase 2: User Questionnaire Taking UI

#### Components to Create:

1. **frontend/src/components/Questionnaires/PendingQuestionnaires.tsx**
   - Dashboard widget showing pending questionnaires
   - Due date countdown
   - Quick access to take questionnaire

2. **frontend/src/components/Questionnaires/QuestionnaireForm.tsx**
   - Main questionnaire taking interface
   - Progress indicator
   - Question navigation
   - Submit button

3. **frontend/src/components/Questionnaires/LikertScaleQuestion.tsx**
   - Radio button group for Likert scales
   - Visual scale representation
   - Labels (Strongly Disagree → Strongly Agree)

4. **frontend/src/components/Questionnaires/QuestionnaireHistory.tsx**
   - List of completed questionnaires
   - View past responses (read-only)
   - Date completed
   - Associated appointment (if any)

5. **frontend/src/components/Appointments/AppointmentList.tsx**
   - Upcoming appointments
   - Associated questionnaires
   - Status indicators

#### Routes to Create:
- `/questionnaires` - List pending/completed questionnaires
- `/questionnaires/{assignmentId}/take` - Take questionnaire
- `/questionnaires/history` - View completed questionnaires
- `/appointments` - View appointments

### Phase 3: Registration Integration

#### Modification Needed:

**frontend/src/routes/signup.tsx**
- After successful registration, check for default questionnaire
- If exists, redirect to questionnaire or show notification
- Store assignment ID for later completion

**backend/app/api/routes/users.py - register_user()**
- After creating user, check for "Initial Assessment" questionnaire
- If exists, create assignment automatically
- Return assignment info in response

### Phase 4: Email Notifications

#### Email Templates to Create:

1. **backend/app/email-templates/src/questionnaire_assigned.mjml**
   ```mjml
   Subject: New Questionnaire Assigned
   - Questionnaire title
   - Due date (if applicable)
   - Link to complete questionnaire
   ```

2. **backend/app/email-templates/src/questionnaire_reminder.mjml**
   ```mjml
   Subject: Reminder: Complete Your Questionnaire
   - Questionnaire title
   - Appointment date/time
   - Hours remaining
   - Link to complete
   ```

3. **backend/app/email-templates/src/appointment_scheduled.mjml**
   ```mjml
   Subject: Appointment Scheduled
   - Appointment details
   - Associated questionnaire (if any)
   - Reminder to complete 24 hours before
   ```

#### Email Utility Functions:

**backend/app/utils.py** - Add functions:
- `generate_questionnaire_assigned_email()`
- `generate_questionnaire_reminder_email()`
- `generate_appointment_scheduled_email()`

### Phase 5: Reminder System (Cron-based)

#### Endpoint to Create:

**backend/app/api/routes/questionnaires.py**
```python
@router.post("/internal/process-reminders")
def process_reminders(session: SessionDep, internal_token: str):
    """
    Process questionnaire reminders (called by cron job).
    Protected by internal token.
    """
    # Check token matches environment variable
    # Find appointments in next 24 hours
    # Find assignments with status PENDING
    # Send reminder emails
    # Mark reminder_sent = True
    # Mark OVERDUE if past due date
```

#### Cron Job Setup:
```bash
# Add to crontab (runs every hour)
0 * * * * curl -X POST http://localhost:8000/api/v1/questionnaires/internal/process-reminders \
  -H "Authorization: Bearer ${INTERNAL_TOKEN}"
```

### Phase 6: Sidebar Navigation Updates

**frontend/src/components/Common/SidebarItems.tsx**

Add for regular users:
```typescript
{
  title: "Questionnaires",
  icon: FiClipboard,
  path: "/questionnaires",
}
{
  title: "Appointments",
  icon: FiCalendar,
  path: "/appointments",
}
```

Add for admins:
```typescript
{
  title: "Questionnaires",
  icon: FiClipboard,
  path: "/admin/questionnaires",
}
{
  title: "Appointments",
  icon: FiCalendar,
  path: "/admin/appointments",
}
```

## Sample Questionnaire Data

### Initial Assessment Questionnaire (Placeholder)

```json
{
  "title": "Initial Wellness Assessment",
  "description": "A brief assessment to understand your current wellness state",
  "is_active": true,
  "questions": [
    {
      "question_text": "I feel optimistic about my future",
      "order": 0,
      "is_required": true,
      "scale_type": "LIKERT_5"
    },
    {
      "question_text": "I have clear goals for what I want to achieve",
      "order": 1,
      "is_required": true,
      "scale_type": "LIKERT_5"
    },
    {
      "question_text": "I feel satisfied with my current life direction",
      "order": 2,
      "is_required": true,
      "scale_type": "LIKERT_5"
    },
    {
      "question_text": "I have supportive relationships in my life",
      "order": 3,
      "is_required": true,
      "scale_type": "LIKERT_5"
    },
    {
      "question_text": "I feel capable of handling challenges that come my way",
      "order": 4,
      "is_required": true,
      "scale_type": "LIKERT_5"
    }
  ]
}
```

## Testing Checklist

### Backend Testing:
- [ ] Create questionnaire template via API
- [ ] Update questionnaire template
- [ ] Delete questionnaire template
- [ ] Create appointment
- [ ] Assign questionnaire to user
- [ ] Submit questionnaire response
- [ ] Verify automatic scoring
- [ ] Test manual score override
- [ ] Verify cascade deletes work correctly

### Frontend Testing:
- [ ] Admin can create questionnaire
- [ ] Admin can edit questionnaire
- [ ] Admin can assign questionnaire to users
- [ ] User sees pending questionnaires
- [ ] User can complete questionnaire
- [ ] User can view past responses
- [ ] Likert scale renders correctly
- [ ] Progress indicator works
- [ ] Form validation works
- [ ] Submission success/error handling

### Integration Testing:
- [ ] New user registration triggers questionnaire assignment
- [ ] Appointment creation triggers questionnaire assignment
- [ ] Email notifications sent correctly
- [ ] Reminder system marks assignments as overdue
- [ ] Calendar integration (future)

## Security Considerations

1. **Authorization:**
   - Only admins can create/edit questionnaires
   - Users can only view their own assignments/responses
   - Admins can view all responses

2. **Validation:**
   - Verify assignment belongs to user before submission
   - Prevent duplicate responses
   - Validate Likert values are within range
   - Ensure all required questions are answered

3. **Data Privacy:**
   - Users cannot see other users' responses
   - Scores are only visible to admins
   - Manual score overrides are audit-logged

## Future Enhancements

1. **Advanced Features:**
   - Conditional questions (skip logic)
   - Multiple question types (text, multiple choice)
   - Question branching
   - Questionnaire versioning
   - Response analytics dashboard

2. **Calendar Integration:**
   - Google Calendar sync
   - Outlook Calendar sync
   - Automatic appointment import
   - Two-way sync

3. **Reporting:**
   - Score trends over time
   - Comparative analytics
   - Export to PDF
   - Data visualization

4. **Notifications:**
   - In-app notifications
   - SMS reminders
   - Push notifications
   - Customizable reminder schedules

## API Usage Examples

### Create Questionnaire (Admin):
```typescript
const questionnaire = await QuestionnairesService.createQuestionnaireTemplate({
  title: "PHQ-9 Depression Scale",
  description: "Patient Health Questionnaire",
  is_active: true,
  questions: [
    {
      question_text: "Little interest or pleasure in doing things",
      order: 0,
      is_required: true,
      scale_type: "LIKERT_5"
    }
    // ... more questions
  ]
});
```

### Assign Questionnaire (Admin):
```typescript
const assignment = await QuestionnairesService.createAssignment({
  questionnaire_id: questionnaireId,
  user_id: userId,
  appointment_id: appointmentId, // optional
  due_date: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours from now
});
```

### Get My Assignments (User):
```typescript
const assignments = await QuestionnairesService.readMyAssignments({
  skip: 0,
  limit: 10
});
```

### Submit Response (User):
```typescript
const response = await QuestionnairesService.createResponse({
  assignment_id: assignmentId,
  answers: [
    {
      question_id: question1Id,
      likert_value: 4
    },
    {
      question_id: question2Id,
      likert_value: 3
    }
    // ... more answers
  ]
});
```

## Database Schema Diagram

```
User
├── created_questionnaires (QuestionnaireTemplate)
├── appointments (Appointment)
├── questionnaire_assignments (QuestionnaireAssignment)
└── questionnaire_responses (QuestionnaireResponse)

QuestionnaireTemplate
├── questions (Question)
└── assignments (QuestionnaireAssignment)

Appointment
└── questionnaire_assignments (QuestionnaireAssignment)

QuestionnaireAssignment
├── questionnaire (QuestionnaireTemplate)
├── user (User)
├── appointment (Appointment)
└── response (QuestionnaireResponse)

QuestionnaireResponse
├── assignment (QuestionnaireAssignment)
├── user (User)
└── answers (Answer)

Question
└── answers (Answer)

Answer
├── response (QuestionnaireResponse)
└── question (Question)
```

## Next Steps

1. **Immediate (Core Functionality):**
   - Create admin questionnaire management UI
   - Create user questionnaire taking UI
   - Add questionnaire assignment on registration
   - Update sidebar navigation

2. **Short-term (Essential Features):**
   - Create email templates
   - Implement reminder cron endpoint
   - Add appointment management UI
   - Create initial assessment questionnaire

3. **Medium-term (Enhanced Features):**
   - Add response analytics for admins
   - Implement calendar integration
   - Add bulk assignment features
   - Create reporting dashboard

4. **Long-term (Advanced Features):**
   - Conditional question logic
   - Multiple question types
   - Advanced analytics
   - Mobile app integration
