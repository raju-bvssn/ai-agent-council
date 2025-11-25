# Agent Council System Architecture

## Overview

The Agent Council is a multi-agent orchestration system built for Salesforce Professional Services, designed to provide collaborative architectural design review using LangGraph workflows.

## Architecture Layers

The system follows Clean Architecture principles with clear separation of concerns:

```mermaid
graph TB
    subgraph "Interface Layer"
        UI[Streamlit UI]
        API[FastAPI REST API]
    end
    
    subgraph "Application Layer"
        WF[Workflow Orchestrator]
        SM[Session Manager]
        AC[Agent Controllers]
    end
    
    subgraph "Domain Layer"
        AGENTS[Agents]
        GRAPH[LangGraph Workflow]
        STATE[State Models]
    end
    
    subgraph "Infrastructure Layer"
        LLM[LLM Provider - Gemini]
        TOOLS[External Tools]
        DB[SQLite Persistence]
    end
    
    UI --> SM
    UI --> AC
    API --> SM
    API --> AC
    
    SM --> STATE
    AC --> AGENTS
    
    AGENTS --> LLM
    AGENTS --> TOOLS
    WF --> GRAPH
    GRAPH --> STATE
    
    STATE --> DB
```

## Core Components

### 1. Interface Layer

**Streamlit UI**
- Council Setup: Create and configure sessions
- Agent Selector: Choose participating agents
- Feedback Panel: View agent outputs and reviews
- Approval Panel: Human-in-the-loop decision interface
- Final Output: Display completed designs and deliverables

**FastAPI REST API**
- Session management endpoints
- Workflow execution endpoints
- Agent execution endpoints
- Health and monitoring endpoints

### 2. Application Layer

**Session Manager**
- Session lifecycle management
- State persistence coordination
- Session CRUD operations

**Workflow Orchestrator**
- LangGraph workflow execution
- State transitions
- Agent coordination

**Agent Controllers**
- Agent instantiation
- Agent execution
- Response handling

### 3. Domain Layer

**Agents**
- Master Architect: Coordinates council and synthesizes results
- Solution Architect: Creates and updates design documents
- Reviewer Agents: Specialized critics (NFR, Security, Integration, etc.)
- FAQ Agent: Generates documentation and rationale

**LangGraph Workflow**
- Node definitions for each workflow step
- Conditional routing based on review outcomes
- Revision loop handling
- Human approval integration

**State Models**
- WorkflowState: Complete session state
- AgentMessage: Individual agent contributions
- ReviewFeedback: Structured review results
- DesignDocument: Evolving solution design

### 4. Infrastructure Layer

**LLM Provider (Google Gemini)**
- Mission Critical Data compliant
- Safety wrapper with prompt injection protection
- Retry logic and rate limiting
- JSON mode support

**External Tools**
- MuleSoft Vibes: Code generation and validation
- MCP Server: Platform metadata retrieval
- NotebookLM: Summarization and evidence extraction
- Lucid AI: Diagram generation

**Persistence**
- SQLite database for session storage
- State serialization/deserialization
- Session history tracking

## Design Principles

### SOLID Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Open/Closed**: Extensible without modification
3. **Liskov Substitution**: Implementations are interchangeable
4. **Interface Segregation**: Focused, minimal interfaces
5. **Dependency Inversion**: Depend on abstractions

### Clean Architecture

- **Independence**: Layers are independent and testable
- **Testability**: Business logic isolated from frameworks
- **Framework Independence**: Core logic doesn't depend on UI/DB
- **Database Independence**: Domain doesn't know about persistence

## Security & Compliance

### Mission Critical Data Requirements

1. **LLM Provider**: Only Google Gemini approved
2. **Prompt Injection Protection**: Safety wrapper on all inputs
3. **PII Redaction**: Automated redaction in logs
4. **No Customer Data Leakage**: Sanitized inputs to LLM
5. **Audit Logging**: All decisions tracked

### Safety Mechanisms

- Anti-prompt-injection guards on system prompts
- Input sanitization and validation
- Output validation before returning to user
- Secrets redaction in logs
- Timeout and retry wrappers for external calls

## TODO: Phase 2 Enhancements

- [ ] Add detailed component diagrams
- [ ] Document API specifications
- [ ] Add deployment architecture
- [ ] Document scaling strategies
- [ ] Add monitoring and observability architecture
- [ ] Document disaster recovery procedures

