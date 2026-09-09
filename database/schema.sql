-- ============================================================================
-- Agentic AI Smart Event Management System - Database Schema (MySQL)
-- Infosys Project Implementation Roadmap
-- ============================================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS smart_event_management;
USE smart_event_management;

-- Enable strict foreign key checks and timezone settings
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- Drop Tables (Ordered to respect foreign key constraints)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS tool_calls;
DROP TABLE IF EXISTS agent_runs;
DROP TABLE IF EXISTS agent_sessions;
DROP TABLE IF EXISTS registrations;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS knowledge_chunks;
DROP TABLE IF EXISTS knowledge_documents;
DROP TABLE IF EXISTS users;

-- ----------------------------------------------------------------------------
-- 1. Users Table
-- Purpose: Authentication, User Profiles, and Role-Based Access Control
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER', -- Options: 'ADMIN', 'USER'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Venues Table
-- Purpose: Track physical venues, capacities, and locations
-- ----------------------------------------------------------------------------
CREATE TABLE venues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity INT NOT NULL,
    location VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_venue_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Events Table
-- Purpose: Event management details, associated with a physical Venue
-- ----------------------------------------------------------------------------
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT NULL,
    date VARCHAR(50) NOT NULL, -- Format: YYYY-MM-DD
    time VARCHAR(50) NOT NULL, -- Format: HH:MM:SS or HH:MM
    venue_id INT NOT NULL,
    capacity INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED', -- Options: 'SCHEDULED', 'CANCELLED'
    created_by INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_event_title (title),
    INDEX idx_event_date (date),
    INDEX idx_event_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Registrations Table
-- Purpose: Participant event registrations. Implements duplicate checks and caps.
-- ----------------------------------------------------------------------------
CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED', -- Options: 'CONFIRMED', 'CANCELLED'
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_event (user_id, event_id), -- Prevent duplicate registration per user for a single event
    INDEX idx_reg_user (user_id),
    INDEX idx_reg_event (event_id),
    INDEX idx_reg_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 5. Agent Sessions Table
-- Purpose: Track AI agent conversations and chat context across sessions
-- ----------------------------------------------------------------------------
CREATE TABLE agent_sessions (
    id VARCHAR(100) PRIMARY KEY, -- Session ID (UUID or Token)
    user_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_session_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 6. Agent Runs Table
-- Purpose: Log each main agent request execution, intent detection, and response
-- ----------------------------------------------------------------------------
CREATE TABLE agent_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) DEFAULT NULL,
    user_id INT DEFAULT NULL,
    user_request TEXT NOT NULL,
    detected_intent VARCHAR(50) DEFAULT NULL,
    tool_selected VARCHAR(100) DEFAULT NULL,
    tool_input TEXT DEFAULT NULL,
    tool_output TEXT DEFAULT NULL,
    latency_ms FLOAT DEFAULT NULL,
    final_response TEXT DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL,
    INDEX idx_run_user (user_id),
    INDEX idx_run_session (session_id),
    INDEX idx_run_intent (detected_intent),
    INDEX idx_run_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 7. Tool Calls Table
-- Purpose: Track granular details of each individual tool invocation within an Agent Run
-- ----------------------------------------------------------------------------
CREATE TABLE tool_calls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_input TEXT DEFAULT NULL,
    tool_output TEXT DEFAULT NULL,
    latency_ms FLOAT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES agent_runs(id) ON DELETE CASCADE,
    INDEX idx_tool_run (run_id),
    INDEX idx_tool_name (tool_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 8. Knowledge Documents Table
-- Purpose: Metadata for uploaded documents used in RAG (e.g. Policies, FAQs)
-- ----------------------------------------------------------------------------
CREATE TABLE knowledge_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) DEFAULT NULL,
    file_type VARCHAR(50) DEFAULT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 9. Knowledge Chunks Table
-- Purpose: Ingested text chunks of documents with embeddings for semantic RAG
-- Note: MySQL stores vector embeddings in JSON field format (e.g., [0.12, -0.45, ...])
-- ----------------------------------------------------------------------------
CREATE TABLE knowledge_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INT NOT NULL,
    embedding JSON DEFAULT NULL, -- Float vector stored as JSON array of numbers
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    INDEX idx_chunk_doc (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 10. Audit Logs Table
-- Purpose: Track database mutations, security operations, and system events
-- ----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    action VARCHAR(100) NOT NULL, -- e.g., 'CREATE_EVENT', 'CANCEL_REGISTRATION', 'LOGIN_ATTEMPT'
    resource_type VARCHAR(100) DEFAULT NULL, -- e.g., 'users', 'events', 'registrations'
    resource_id INT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    details TEXT DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- ============================================================================
-- Seed / Sample Data
-- For testing, verification and local development
-- ============================================================================

-- 1. Insert Users
-- Note: Password hash corresponds to 'password123' (hashed using bcrypt/argon2 in real flow)
INSERT INTO users (id, name, email, password_hash, role) VALUES
(1, 'Admin User', 'admin@eventsystem.com', '$2b$12$K7v15R43W6n.fIuYgD8kueM0t4U9jBf2tZJ8RjH1Z3xO7Kqg0aUte', 'ADMIN'),
(2, 'Jane Doe', 'jane@eventsystem.com', '$2b$12$K7v15R43W6n.fIuYgD8kueM0t4U9jBf2tZJ8RjH1Z3xO7Kqg0aUte', 'USER'),
(3, 'John Smith', 'john@eventsystem.com', '$2b$12$K7v15R43W6n.fIuYgD8kueM0t4U9jBf2tZJ8RjH1Z3xO7Kqg0aUte', 'USER');

-- 2. Insert Venues
INSERT INTO venues (id, name, capacity, location) VALUES
(1, 'Grand Ballroom A', 200, 'Hotel Plaza, Floor 1'),
(2, 'Tech Innovation Hub', 50, 'Silicon Tower, Floor 4'),
(3, 'Main Amphitheater', 500, 'University Campus, Sector C');

-- 3. Insert Events
INSERT INTO events (id, title, description, date, time, venue_id, capacity, status, created_by) VALUES
(1, 'AI & Machine Learning Workshop', 'An immersive, hands-on workshop on LangGraph, LLMs, and agentic workflows.', '2026-09-12', '10:00:00', 2, 40, 'SCHEDULED', 1),
(2, 'Global Tech Summit 2026', 'Annual conference showcasing modern frontend and backend technologies.', '2026-10-15', '09:00:00', 3, 450, 'SCHEDULED', 1),
(3, 'Startup Pitch Night', 'A evening dedicated to regional startups pitching their ideas to investors.', '2026-09-15', '18:30:00', 1, 150, 'SCHEDULED', 1);

-- 4. Insert Registrations
INSERT INTO registrations (id, user_id, event_id, status) VALUES
(1, 2, 1, 'CONFIRMED'),
(2, 3, 1, 'CONFIRMED'),
(3, 2, 2, 'CONFIRMED');

-- 5. Insert Knowledge Documents
INSERT INTO knowledge_documents (id, title, file_path, file_type) VALUES
(1, 'Event Cancellation Policy', 'documents/cancellation_policy.pdf', 'PDF'),
(2, 'Registration & Attendance Policy', 'documents/registration_policy.pdf', 'PDF'),
(3, 'Frequently Asked Questions (FAQ)', 'documents/faq.pdf', 'PDF');

-- 6. Insert Knowledge Chunks
INSERT INTO knowledge_chunks (id, document_id, chunk_text, chunk_index, embedding) VALUES
(1, 1, 'Event Cancellation: Participants can cancel registrations up to 24 hours prior to the scheduled start time without any penalty. Cancel via the API or UI.', 0, '[0.11, -0.05, 0.74, -0.21]'),
(2, 1, 'Organizers reserve the right to reschedule or cancel events. If an event is cancelled, registered users will be notified automatically via email.', 1, '[0.01, -0.15, 0.34, -0.91]'),
(3, 2, 'Registration Cap: Registrations are accepted on a first-come, first-served basis up to the listed capacity of the venue. Duplicate registrations are blocked by system rules.', 0, '[0.22, 0.08, -0.14, 0.55]'),
(4, 3, 'Frequently Asked Questions: How do I access the AI Assistant? Simply go to /ai-assistant and type your query in natural language, such as "Register me for AI Workshop".', 0, '[0.02, 0.44, 0.12, -0.32]');

-- 7. Insert Agent Sessions
INSERT INTO agent_sessions (id, user_id) VALUES
('session_abc123', 2),
('session_xyz789', 3);

-- 8. Insert Agent Runs
INSERT INTO agent_runs (id, session_id, user_id, user_request, detected_intent, tool_selected, tool_input, tool_output, latency_ms, final_response) VALUES
(1, 'session_abc123', 2, 'Find an AI workshop this weekend and register me.', 'SEARCH_REGISTER', 'search_events,register_participant', '{"title": "AI Workshop"}', '{"status": "SUCCESS", "event_id": 1}', 320.5, 'I searched for an AI workshop, found the "AI & Machine Learning Workshop" on 2026-09-12, and successfully registered you!'),
(2, 'session_xyz789', 3, 'What is the cancellation policy?', 'ASK_POLICY', 'search_event_policy', '{"query": "cancellation policy"}', '{"relevant_chunk": "Participants can cancel registrations up to 24 hours prior..."}', 145.2, 'According to the cancellation policy, you can cancel your registration up to 24 hours prior to the scheduled event start time with no penalty.');

-- 9. Insert Tool Calls
INSERT INTO tool_calls (id, run_id, tool_name, tool_input, tool_output, latency_ms) VALUES
(1, 1, 'search_events', '{"title": "AI Workshop"}', '{"events": [{"id": 1, "title": "AI & Machine Learning Workshop"}]}', 110.2),
(2, 1, 'register_participant', '{"user_id": 2, "event_id": 1}', '{"status": "SUCCESS", "registration_id": 4}', 210.3),
(3, 2, 'search_event_policy', '{"query": "cancellation policy"}', '{"chunk": "Participants can cancel registrations up to 24 hours..."}', 145.2);

-- 10. Insert Audit Logs
INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, ip_address, details) VALUES
(1, 1, 'CREATE_EVENT', 'events', 1, '127.0.0.1', 'Admin created event: AI & Machine Learning Workshop'),
(2, 2, 'USER_LOGIN', 'users', 2, '192.168.1.5', 'Jane Doe logged in successfully'),
(3, 2, 'REGISTER_PARTICIPANT', 'registrations', 1, '192.168.1.5', 'Jane Doe registered for event ID 1');

