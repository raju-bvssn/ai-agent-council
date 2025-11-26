# End-to-End Scenario Tests

This directory contains comprehensive end-to-end scenario tests that validate complete Agent Council workflows using realistic integration scenarios.

## Overview

E2E scenario tests execute the full workflow from session creation through deliverables generation, validating all system components including:

- **Session Management**: Creating and tracking sessions
- **Workflow Execution**: Multi-agent orchestration via LangGraph
- **Reviewer Agents**: Parallel agent execution and feedback collection
- **Debate & Consensus**: Multi-agent debate resolution
- **Adjudicator**: Conflict resolution by Architect Adjudicator
- **Deliverables**: Architecture summary, decisions, risks, FAQs, diagrams
- **Stability Safeguards**: Infinite loop prevention, timeout handling
- **LangSmith Integration**: Execution tracing (if enabled)

## Test Scenarios

### `test_e2e_s3_to_salesforce.py`

**Scenario**: Customer Data Sync from AWS S3 (CSV) → Salesforce (Upsert Flow)

A realistic MuleSoft integration scenario that validates the complete Agent Council workflow with:

- **Source**: AWS S3 bucket with CSV files
- **Target**: Salesforce (upsert pattern)
- **Requirements**: Error handling, retries, transformation, observability, best practices

#### Test Steps

1. **Create Session** - POST `/api/v1/sessions` with detailed requirements
2. **Start Workflow** - POST `/api/v1/workflow/{id}/start`
3. **Poll Until Completion** - GET `/api/v1/workflow/{id}/status` (120s timeout)
4. **Validate Stability Safeguards** - Check metadata for proper safeguard activation
5. **Validate Reviewer Outputs** - Verify ≥2 reviewers with integration context
6. **Validate Debates & Consensus** - Check debate resolution and confidence scores
7. **Validate Adjudicator Output** - Verify integration-specific reasoning
8. **Validate Deliverables Bundle** - Comprehensive validation of all artifacts
9. **Validate LangSmith Trace** - Check execution trace URL (if enabled)
10. **Print Scenario Summary** - Display complete execution metrics

#### Deliverables Validation

The test validates all components of the `DeliverablesBundle`:

- **Architecture Summary**
  - Overview (non-empty)
  - Key capabilities (≥3)
  - NFR highlights

- **Decision Records** (≥3)
  - ID, title, context
  - Decision, rationale, consequences

- **Risks** (≥2)
  - ID, description
  - Likelihood, impact, mitigation

- **FAQs** (≥3)
  - Question, answer
  - Source attribution

- **Diagrams** (≥2)
  - Type, title, description
  - Lucid URL or Mermaid source

- **Markdown Report** (≥500 chars)
  - All required sections present

#### Stability Validation

The test ensures all stability safeguards are operational:

- ✅ No infinite loops (review rounds ≤ 10)
- ✅ Debate rounds within limits (≤ max_debate_rounds)
- ✅ Adjudicator runs exactly once (≤ adjudicator_max_runs)
- ✅ Forced consensus documented when triggered
- ✅ Timeout handling works correctly
- ✅ Repetition detection activates appropriately

### `test_workflow_stability_under_load`

Tests workflow stability with multiple concurrent sessions to validate:

- Concurrent session creation
- Parallel workflow execution
- No resource contention issues
- All sessions progress normally
- Stability safeguards work under load

## Running the Tests

### Run All E2E Scenarios

```bash
pytest tests/scenarios/ -v -s
```

### Run Specific Scenario

```bash
pytest tests/scenarios/test_e2e_s3_to_salesforce.py::TestE2ES3ToSalesforce::test_complete_s3_to_salesforce_workflow -v -s
```

### Run With E2E Marker

```bash
pytest -m e2e -v -s
```

### Run Without Coverage (Faster)

```bash
pytest tests/scenarios/ -v -s --no-cov
```

## Configuration

E2E tests use the standard application configuration from `.env`:

```bash
# LangSmith (Optional)
ENABLE_LANGSMITH=true
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=agent-council

# Google Gemini (Required for real execution)
GOOGLE_API_KEY=your_key

# Stability Settings
MAX_DEBATE_ROUNDS=3
DEBATE_ROUND_TIMEOUT=15
ENABLE_REPETITION_DETECTION=true
ENABLE_FORCED_CONSENSUS=true
ADJUDICATOR_MAX_RUNS=1

# Demo Mode (uses mocks instead of real APIs)
DEMO_MODE=false
```

## Test Duration

- **Single E2E Test**: ~60-120 seconds
- **Load Test**: ~10-20 seconds
- **Full Suite**: ~2-3 minutes

## Expected Output

Successful E2E test produces output like:

```
======================================================================
🚀 STEP 1: Creating Agent Council Session
======================================================================
✅ Session created: 3eb92bf8-13f4-48fa-9f4e-1f6469b88b73
   Status: pending
   Name: S3 to Salesforce Customer Sync

======================================================================
🔄 STEP 2: Starting Workflow
======================================================================
✅ Workflow started
   Status: in_progress
   Current Node: generate_requirements

======================================================================
⏳ STEP 3: Polling for Workflow Completion
======================================================================
   [2.1s] Status: in_progress, Node: reviewer_round
   [8.3s] Status: in_progress, Node: debate_cycle
   [15.7s] Status: in_progress, Node: consensus_node
   [22.4s] Status: in_progress, Node: adjudication_node
   [28.9s] Status: in_progress, Node: faq_generation
   [35.2s] Status: in_progress, Node: generate_deliverables
   [42.1s] Status: completed, Node: finalize

✅ Workflow completed in 42.1 seconds

======================================================================
🛡️  STEP 4: Validating Stability Safeguards
======================================================================
   Adjudicator runs: 1
   Total debates: 2
   Review rounds: 1
   Forced consensus: False
✅ All stability safeguards validated

...

======================================================================
📊 SCENARIO VALIDATION SUMMARY
======================================================================

[S3 → Salesforce E2E Test] COMPLETED ✅

Session ID:           3eb92bf8-13f4-48fa-9f4e-1f6469b88b73
Execution Time:       42.1s
Iterations:           43

WORKFLOW METRICS:
-----------------
Status:               completed
Review Rounds:        1
Total Debates:        2
Debates Resolved:     2
Consensus Forced:     False
Consensus Confidence: 0.87
Adjudicator Runs:     1

DELIVERABLES:
-------------
Decisions (ADR):      5
Risks Identified:     4
FAQ Items:            6
Diagrams:             4
Markdown Report:      3,247 bytes

TEST RESULT: PASSED ✅
```

## Troubleshooting

### Test Times Out

- Increase `POLL_TIMEOUT` in the test (default: 120s)
- Check if API keys are configured correctly
- Enable `DEMO_MODE=true` to use mocks

### Session Creation Fails

- Verify FastAPI server is running in test mode
- Check database permissions
- Review API logs for errors

### Workflow Stuck

- Check LangSmith traces for stuck nodes
- Review stability safeguards configuration
- Ensure debate timeout is reasonable (15s)

### Deliverables Missing

- Verify workflow reaches "completed" status
- Check if `generate_deliverables` node executed
- Review workflow logs for errors

## Best Practices

1. **Run E2E tests separately** from unit tests (they're slower)
2. **Use DEMO_MODE** for CI/CD to avoid external dependencies
3. **Monitor test duration** - should complete in ~120s max
4. **Check LangSmith traces** for detailed execution analysis
5. **Review stability metrics** to ensure safeguards are working

## Future Scenarios

Additional scenarios to implement:

- **Salesforce → NetSuite Order Sync**
- **Real-time Event Processing (Kafka → MuleSoft → Salesforce)**
- **Batch File Processing (SFTP → Transform → Salesforce)**
- **API Gateway Modernization**
- **Legacy System Integration**

---

**Last Updated**: 2025-11-26  
**Test Coverage**: 100% of workflow lifecycle  
**Platforms Tested**: macOS (Python 3.9+), Linux (CI/CD)

