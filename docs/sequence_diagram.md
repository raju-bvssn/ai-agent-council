# Agent Council Sequence Diagram

## Complete Council Session Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant SM as Session Manager
    participant WF as Workflow Engine
    participant MA as Master Architect
    participant SA as Solution Architect
    participant R1 as NFR Reviewer
    participant R2 as Security Reviewer
    participant R3 as Integration Reviewer
    participant EV as Evaluator
    participant FA as FAQ Agent
    participant DB as Database
    
    User->>UI: Create Session
    UI->>SM: create_session(request, context)
    SM->>DB: Save initial state
    DB-->>SM: session_id
    SM-->>UI: WorkflowState
    UI-->>User: Session Created
    
    User->>UI: Start Workflow
    UI->>WF: execute_workflow(session_id)
    
    Note over WF: Phase 1: Analysis
    WF->>MA: run(input)
    MA->>MA: Analyze requirements
    MA->>MA: Generate approach
    MA-->>WF: Analysis output
    WF->>DB: Update state
    
    Note over WF: Phase 2: Design
    WF->>SA: run(master_analysis)
    SA->>SA: Create design document
    SA-->>WF: Design v1
    WF->>DB: Update state
    
    Note over WF: Phase 3: Parallel Reviews
    par NFR Review
        WF->>R1: run(design_v1)
        R1->>R1: Evaluate performance
        R1-->>WF: Review: REVISE
    and Security Review
        WF->>R2: run(design_v1)
        R2->>R2: Evaluate security
        R2-->>WF: Review: APPROVE
    and Integration Review
        WF->>R3: run(design_v1)
        R3->>R3: Evaluate integrations
        R3-->>WF: Review: APPROVE
    end
    
    WF->>DB: Update state with reviews
    
    Note over WF: Phase 4: Evaluation
    WF->>EV: determine_next_step(state)
    EV->>EV: Check reviews
    EV->>EV: Found REVISE decision
    EV-->>WF: Route to Solution Architect
    
    Note over WF: Revision Loop
    WF->>SA: run(feedback)
    SA->>SA: Incorporate feedback
    SA-->>WF: Design v2
    WF->>DB: Update state (revision=1)
    
    Note over WF: Phase 3b: Review v2
    par NFR Review
        WF->>R1: run(design_v2)
        R1-->>WF: Review: APPROVE
    and Security Review
        WF->>R2: run(design_v2)
        R2-->>WF: Review: APPROVE
    and Integration Review
        WF->>R3: run(design_v2)
        R3-->>WF: Review: APPROVE
    end
    
    WF->>DB: Update state
    
    Note over WF: Phase 4b: Evaluation
    WF->>EV: determine_next_step(state)
    EV->>EV: All reviews approved
    EV-->>WF: Route to Human Approval
    
    Note over WF: Phase 5: Human Approval
    WF->>UI: awaiting_human
    UI-->>User: Review Required
    User->>User: Review design
    User->>UI: Approve
    UI->>WF: human_decision(approve)
    WF->>DB: Update state (approved=true)
    
    Note over WF: Phase 6: FAQ Generation
    WF->>FA: run(discussion_history)
    FA->>FA: Extract FAQs
    FA->>FA: Generate rationale
    FA-->>WF: FAQ + Rationale
    WF->>DB: Update state
    
    Note over WF: Phase 7: Finalization
    WF->>WF: Generate summary
    WF->>WF: Prepare deliverables
    WF->>DB: Update state (completed)
    WF-->>UI: Workflow Complete
    
    UI-->>User: Display Final Output
    User->>UI: View Deliverables
    UI-->>User: Design + FAQ + Diagrams
```

## Key Interactions

### 1. Session Creation
- User provides requirements through UI
- Session Manager creates and persists initial state
- Returns session ID for tracking

### 2. Workflow Execution
- Workflow engine orchestrates agents sequentially and in parallel
- Each agent receives state and context
- Agents return structured outputs
- State updated after each step

### 3. Review Cycle
- Multiple reviewers evaluate design in parallel
- Reviews consolidated by evaluator
- Conditional routing based on outcomes
- Supports iterative refinement

### 4. Human Approval
- Workflow pauses for human decision
- UI displays design and reviews
- Human provides approval/rejection/feedback
- Workflow resumes based on decision

### 5. Finalization
- FAQ agent synthesizes discussion
- Final deliverables prepared
- State marked as completed
- Results displayed to user

## Error Handling Flow

```mermaid
sequenceDiagram
    participant WF as Workflow
    participant Agent
    participant EH as Error Handler
    participant DB as Database
    participant UI
    
    WF->>Agent: run(input)
    Agent->>Agent: Process
    Agent--xWF: Exception
    WF->>EH: handle_error(exception)
    EH->>EH: Log error
    EH->>EH: Determine retry
    
    alt Retryable Error
        EH->>Agent: retry(input)
        Agent-->>WF: Success
    else Non-Retryable Error
        EH->>DB: Save error state
        EH->>UI: Notify user
        UI-->>UI: Display error
    end
```

## TODO: Phase 2 Enhancements

- [ ] Add streaming sequence for real-time updates
- [ ] Document timeout handling
- [ ] Add rollback sequences
- [ ] Document concurrent execution details
- [ ] Add LangSmith tracing integration
- [ ] Document checkpoint/resume sequences

