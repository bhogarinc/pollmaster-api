# PollMaster Database Schema

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │    polls    │       │  questions  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────┤ id (PK)     │◄──────┤ id (PK)     │
│ email       │       │ title       │       │ poll_id(FK) │
│ password    │       │ creator_id  │       │ text        │
│ username    │       │ unique_link │       │ type        │
└─────────────┘       │ is_active   │       └──────┬──────┘
                      │ expires_at  │              │
                      └─────────────┘              │
                           │                       │
                           │                ┌──────▼──────┐
                           │                │   options   │
                           │                ├─────────────┤
                           │                │ id (PK)     │
                           │                │ question_id │
                           │                │ text        │
                           │                │ vote_count  │
                           │                └──────┬──────┘
                           │                       │
                      ┌────▼──────┐                │
                      │   votes   │◄───────────────┘
                      ├───────────┤
                      │ id (PK)   │
                      │ poll_id   │
                      │ option_id │
                      │ voter_id  │
                      │ fingerprint
└─────────────────────┘
```

## Tables

### 1. users
Stores user account information and authentication details.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Display name |
| first_name | VARCHAR(100) | | Optional first name |
| last_name | VARCHAR(100) | | Optional last name |
| avatar_url | VARCHAR(500) | | Profile image URL |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| token_version | INTEGER | DEFAULT 1 | For token invalidation |
| last_login_at | TIMESTAMP | | Last login timestamp |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update |

### 2. polls
Stores poll metadata and configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Poll title |
| description | TEXT | | Poll description |
| creator_id | UUID | FOREIGN KEY | Poll creator |
| unique_link | VARCHAR(32) | UNIQUE, NOT NULL | Shareable link |
| is_active | BOOLEAN | DEFAULT TRUE | Poll status |
| is_public | BOOLEAN | DEFAULT TRUE | Visibility |
| allow_multiple_votes | BOOLEAN | DEFAULT FALSE | Multiple votes allowed |
| allow_anonymous_votes | BOOLEAN | DEFAULT TRUE | Anonymous voting |
| show_results_before_voting | BOOLEAN | DEFAULT FALSE | Results visibility |
| show_results_after_voting | BOOLEAN | DEFAULT TRUE | Results visibility |
| expires_at | TIMESTAMP | | Expiration date |
| total_votes | INTEGER | DEFAULT 0 | Total vote count |
| view_count | INTEGER | DEFAULT 0 | View count |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update |
| deleted_at | TIMESTAMP | | Soft delete timestamp |

### 3. questions
Stores individual questions within polls.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| poll_id | UUID | FOREIGN KEY, NOT NULL | Parent poll |
| text | TEXT | NOT NULL | Question text |
| question_type | VARCHAR(20) | DEFAULT 'single_choice' | single_choice or multiple_choice |
| is_required | BOOLEAN | DEFAULT TRUE | Required question |
| order_index | INTEGER | DEFAULT 0 | Display order |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update |

### 4. options
Stores answer options for questions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| question_id | UUID | FOREIGN KEY, NOT NULL | Parent question |
| text | TEXT | NOT NULL | Option text |
| order_index | INTEGER | DEFAULT 0 | Display order |
| vote_count | INTEGER | DEFAULT 0 | Cached vote count |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update |

### 5. votes
Stores individual vote records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| poll_id | UUID | FOREIGN KEY, NOT NULL | Voted poll |
| question_id | UUID | FOREIGN KEY, NOT NULL | Voted question |
| option_id | UUID | FOREIGN KEY, NOT NULL | Selected option |
| voter_id | UUID | FOREIGN KEY | Authenticated voter |
| voter_ip | INET | | Voter IP address |
| voter_fingerprint | VARCHAR(64) | | Browser fingerprint |
| voter_session_id | VARCHAR(64) | | Session identifier |
| user_agent | TEXT | | Browser user agent |
| created_at | TIMESTAMP | DEFAULT NOW() | Vote timestamp |

### 6. templates
Stores reusable poll templates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Template name |
| description | TEXT | | Template description |
| category | VARCHAR(50) | DEFAULT 'general' | Template category |
| structure | JSONB | NOT NULL | Poll structure JSON |
| created_by | UUID | FOREIGN KEY | Template creator |
| is_public | BOOLEAN | DEFAULT TRUE | Public visibility |
| usage_count | INTEGER | DEFAULT 0 | Usage counter |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update |

### 7. refresh_tokens
Stores JWT refresh tokens for session management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY, NOT NULL | Token owner |
| token_hash | VARCHAR(255) | NOT NULL | Hashed token |
| expires_at | TIMESTAMP | NOT NULL | Expiration |
| is_revoked | BOOLEAN | DEFAULT FALSE | Revocation status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| revoked_at | TIMESTAMP | | Revocation timestamp |

## Indexes

### Performance Indexes

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Poll queries
CREATE INDEX idx_polls_unique_link ON polls(unique_link);
CREATE INDEX idx_polls_creator_id ON polls(creator_id);
CREATE INDEX idx_polls_is_active ON polls(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_polls_expires_at ON polls(expires_at);

-- Vote aggregation
CREATE INDEX idx_votes_poll_id ON votes(poll_id);
CREATE INDEX idx_votes_option_id ON votes(option_id);
CREATE INDEX idx_votes_fingerprint ON votes(voter_fingerprint);

-- Question/Option ordering
CREATE INDEX idx_questions_poll_order ON questions(poll_id, order_index);
CREATE INDEX idx_options_question_order ON options(question_id, order_index);
```

### Unique Constraints

```sql
-- Prevent duplicate votes
CREATE UNIQUE INDEX idx_unique_vote_anon 
    ON votes(poll_id, voter_fingerprint) 
    WHERE voter_id IS NULL;
    
CREATE UNIQUE INDEX idx_unique_vote_auth 
    ON votes(poll_id, voter_id) 
    WHERE voter_id IS NOT NULL;
```

## Triggers

### Auto-update timestamps

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Vote count maintenance

```sql
CREATE OR REPLACE FUNCTION update_vote_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE options SET vote_count = vote_count + 1 WHERE id = NEW.option_id;
        UPDATE polls SET total_votes = total_votes + 1 WHERE id = NEW.poll_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE options SET vote_count = vote_count - 1 WHERE id = OLD.option_id;
        UPDATE polls SET total_votes = total_votes - 1 WHERE id = OLD.poll_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_vote_counts
    AFTER INSERT OR DELETE ON votes
    FOR EACH ROW EXECUTE FUNCTION update_vote_counts();
```
