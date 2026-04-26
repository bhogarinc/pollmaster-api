# PollMaster API Specification

## Base URL
```
Production: https://pollmaster-bhogarai.azurewebsites.net/api/v1
Local: http://localhost:3000/api/v1
```

## Authentication

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "johndoe",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Validation Rules:**
- email: Valid email format, max 255 characters
- password: 8-128 characters, must contain uppercase, lowercase, number, special character
- username: 3-50 characters, alphanumeric and underscore only
- firstName: Optional, max 100 characters
- lastName: Optional, max 100 characters

**Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "firstName": "John",
      "lastName": "Doe",
      "createdAt": "2026-04-26T08:00:00.000Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIs...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
      "expiresIn": 900
    }
  }
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "email", "message": "Email already exists" },
      { "field": "password", "message": "Password must contain at least one uppercase letter" }
    ]
  }
}
```

### POST /auth/login
Authenticate user and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "firstName": "John",
      "lastName": "Doe"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIs...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
      "expiresIn": 900
    }
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 900
  }
}
```

### POST /auth/logout
Logout user and revoke refresh token.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Polls

### GET /polls
List polls with pagination and filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page (max 100) |
| search | string | | Search in title/description |
| status | string | all | Filter: active, expired, all |
| sortBy | string | created | Sort field: created, votes, title |
| sortOrder | string | desc | Sort order: asc, desc |

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "title": "Favorite Programming Language",
        "description": "Vote for your favorite language",
        "uniqueLink": "abc123xyz",
        "isActive": true,
        "isPublic": true,
        "totalVotes": 150,
        "viewCount": 500,
        "creator": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "johndoe"
        },
        "createdAt": "2026-04-26T08:00:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "totalPages": 8,
      "hasNextPage": true,
      "hasPrevPage": false
    }
  }
}
```

### POST /polls
Create a new poll.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request:**
```json
{
  "title": "Favorite Programming Language",
  "description": "Vote for your favorite programming language",
  "isPublic": true,
  "allowMultipleVotes": false,
  "allowAnonymousVotes": true,
  "showResultsBeforeVoting": false,
  "showResultsAfterVoting": true,
  "expiresAt": "2026-12-31T23:59:59.000Z",
  "questions": [
    {
      "text": "What is your favorite programming language?",
      "questionType": "single_choice",
      "isRequired": true,
      "orderIndex": 0,
      "options": [
        { "text": "JavaScript", "orderIndex": 0 },
        { "text": "Python", "orderIndex": 1 },
        { "text": "Java", "orderIndex": 2 },
        { "text": "Go", "orderIndex": 3 }
      ]
    }
  ]
}
```

**Validation Rules:**
- title: 3-255 characters, required
- description: Max 2000 characters
- questions: 1-50 questions, required
- question.text: 1-1000 characters, required
- options: 2-20 options per question, required
- option.text: 1-500 characters, required

**Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Favorite Programming Language",
    "uniqueLink": "abc123xyz",
    "shareUrl": "https://pollmaster.app/p/abc123xyz",
    "createdAt": "2026-04-26T08:00:00.000Z"
  }
}
```

### GET /polls/:id
Get poll details with questions.

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Favorite Programming Language",
    "description": "Vote for your favorite programming language",
    "uniqueLink": "abc123xyz",
    "isActive": true,
    "isPublic": true,
    "allowMultipleVotes": false,
    "allowAnonymousVotes": true,
    "showResultsBeforeVoting": false,
    "showResultsAfterVoting": true,
    "expiresAt": "2026-12-31T23:59:59.000Z",
    "totalVotes": 150,
    "viewCount": 500,
    "creator": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe"
    },
    "questions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "text": "What is your favorite programming language?",
        "questionType": "single_choice",
        "isRequired": true,
        "orderIndex": 0,
        "options": [
          { "id": "550e8400-e29b-41d4-a716-446655440003", "text": "JavaScript", "orderIndex": 0, "voteCount": 50 },
          { "id": "550e8400-e29b-41d4-a716-446655440004", "text": "Python", "orderIndex": 1, "voteCount": 45 },
          { "id": "550e8400-e29b-41d4-a716-446655440005", "text": "Java", "orderIndex": 2, "voteCount": 30 },
          { "id": "550e8400-e29b-41d4-a716-446655440006", "text": "Go", "orderIndex": 3, "voteCount": 25 }
        ]
      }
    ],
    "createdAt": "2026-04-26T08:00:00.000Z",
    "updatedAt": "2026-04-26T08:00:00.000Z"
  }
}
```

### PUT /polls/:id
Update poll details.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "isActive": false
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Updated Title",
    "description": "Updated description",
    "isActive": false,
    "updatedAt": "2026-04-26T09:00:00.000Z"
  }
}
```

### DELETE /polls/:id
Delete a poll (soft delete).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response 204 No Content**

### POST /polls/:id/duplicate
Duplicate an existing poll.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440007",
    "title": "Favorite Programming Language (Copy)",
    "uniqueLink": "def456uvw",
    "shareUrl": "https://pollmaster.app/p/def456uvw",
    "createdAt": "2026-04-26T09:00:00.000Z"
  }
}
```

## Voting

### POST /polls/:id/vote
Submit a vote for a poll.

**Request:**
```json
{
  "questionId": "550e8400-e29b-41d4-a716-446655440002",
  "optionId": "550e8400-e29b-41d4-a716-446655440003"
}
```

**Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "voteId": "550e8400-e29b-41d4-a716-446655440008",
    "message": "Vote recorded successfully",
    "resultsUrl": "/polls/550e8400-e29b-41d4-a716-446655440001/results"
  }
}
```

**Response 409 Conflict:**
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_VOTE",
    "message": "You have already voted in this poll"
  }
}
```

**Response 410 Gone:**
```json
{
  "success": false,
  "error": {
    "code": "POLL_EXPIRED",
    "message": "This poll has expired"
  }
}
```

## Results

### GET /polls/:id/results
Get poll results with vote counts and percentages.

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "pollId": "550e8400-e29b-41d4-a716-446655440001",
    "totalVotes": 150,
    "lastUpdated": "2026-04-26T08:30:00.000Z",
    "questions": [
      {
        "questionId": "550e8400-e29b-41d4-a716-446655440002",
        "questionText": "What is your favorite programming language?",
        "totalResponses": 150,
        "options": [
          { "optionId": "550e8400-e29b-41d4-a716-446655440003", "text": "JavaScript", "voteCount": 50, "percentage": 33.33 },
          { "optionId": "550e8400-e29b-41d4-a716-446655440004", "text": "Python", "voteCount": 45, "percentage": 30.00 },
          { "optionId": "550e8400-e29b-41d4-a716-446655440005", "text": "Java", "voteCount": 30, "percentage": 20.00 },
          { "optionId": "550e8400-e29b-41d4-a716-446655440006", "text": "Go", "voteCount": 25, "percentage": 16.67 }
        ]
      }
    ]
  }
}
```

### GET /polls/:id/results/stream
Server-Sent Events endpoint for real-time results.

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
```

**Event Stream Format:**
```
data: {"type":"connected","timestamp":"2026-04-26T08:00:00.000Z"}

data: {"type":"results_updated","pollId":"550e8400-e29b-41d4-a716-446655440001","totalVotes":151,"timestamp":"2026-04-26T08:00:05.000Z"}

data: {"type":"heartbeat","timestamp":"2026-04-26T08:00:30.000Z"}
```

## Templates

### GET /templates
List available poll templates.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| category | string | | Filter by category |
| isPublic | boolean | true | Show public templates |

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "name": "Customer Satisfaction Survey",
        "description": "Standard customer satisfaction template",
        "category": "business",
        "usageCount": 1250,
        "createdBy": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "pollmaster"
        }
      }
    ]
  }
}
```

### POST /templates
Create a new template from a poll.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "pollId": "550e8400-e29b-41d4-a716-446655440001",
  "name": "My Custom Template",
  "description": "Template description",
  "category": "custom",
  "isPublic": false
}
```

**Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440011",
    "name": "My Custom Template",
    "category": "custom",
    "isPublic": false,
    "createdAt": "2026-04-26T09:00:00.000Z"
  }
}
```

## User

### GET /users/me
Get current user profile.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "firstName": "John",
    "lastName": "Doe",
    "avatarUrl": null,
    "isEmailVerified": true,
    "createdAt": "2026-04-26T08:00:00.000Z"
  }
}
```

### PUT /users/me
Update user profile.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "firstName": "Johnny",
  "lastName": "Doe",
  "avatarUrl": "https://example.com/avatar.jpg"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "firstName": "Johnny",
    "lastName": "Doe",
    "avatarUrl": "https://example.com/avatar.jpg",
    "updatedAt": "2026-04-26T09:00:00.000Z"
  }
}
```

## Error Responses

All errors follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [],
    "timestamp": "2026-04-26T08:00:00.000Z",
    "path": "/api/v1/polls/123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Input validation failed |
| INVALID_CREDENTIALS | 401 | Wrong email or password |
| UNAUTHORIZED | 401 | Authentication required |
| TOKEN_EXPIRED | 401 | JWT token has expired |
| FORBIDDEN | 403 | Permission denied |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE_VOTE | 409 | User already voted |
| POLL_EXPIRED | 410 | Poll has expired |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/login | 5 | 15 minutes |
| POST /auth/register | 3 | 1 hour |
| POST /polls/:id/vote | 1 | Per poll |
| All API endpoints | 100 | 15 minutes per IP |
