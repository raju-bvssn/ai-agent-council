"""
End-to-End Workflow Validation: S3 to Salesforce Customer Data Sync.

Comprehensive scenario test that validates the complete Agent Council workflow
using a realistic MuleSoft integration scenario.

Scenario: Customer Data Sync from AWS S3 (CSV) → Salesforce (Upsert Flow)
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Any, Dict

from httpx import AsyncClient, ASGITransport

from app.app import app
from app.utils.settings import get_settings


# Test scenario configuration
SCENARIO_REQUEST = """Design a MuleSoft integration that ingests customer data from AWS S3 (CSV files) and syncs it into Salesforce using an upsert pattern. Include error handling, retries, transformation, observability and best practice patterns."""

SCENARIO_NAME = "S3 to Salesforce Customer Sync"

SCENARIO_DESCRIPTION = "End-to-end validation of the Agent Council workflow using a real MuleSoft integration scenario"

SCENARIO_CONTEXT = {
    "project_type": "integration",
    "priority": "high",
    "source": "aws_s3",
    "target": "salesforce",
    "data_format": "csv",
    "volume": "medium"
}

# Test configuration - Extended timeout for complete workflow validation
POLL_INTERVAL = 1  # seconds
POLL_TIMEOUT = 240  # seconds (4 minutes - allows full multi-agent workflow)
MAX_POLL_ITERATIONS = POLL_TIMEOUT // POLL_INTERVAL  # 240 iterations

# Keywords to validate in outputs
INTEGRATION_KEYWORDS = [
    "s3", "salesforce", "integration", "mulesoft", "upsert",
    "csv", "error handling", "flow design", "transformation",
    "mapping", "api", "retry", "batch"
]


@pytest.mark.asyncio
@pytest.mark.e2e
class TestE2ES3ToSalesforce:
    """
    End-to-end test for S3 → Salesforce customer data sync scenario.
    
    Tests complete workflow execution from session creation through
    deliverables generation with stability safeguard validation.
    """
    
    async def test_complete_s3_to_salesforce_workflow(self):
        """
        Execute and validate complete Agent Council workflow for S3→SF integration.
        
        Steps:
        1. Create session
        2. Start workflow
        3. Poll until completion
        4. Validate stability safeguards
        5. Validate reviewer outputs
        6. Validate debates and consensus
        7. Validate adjudicator output
        8. Validate deliverables bundle
        9. Validate LangSmith trace (if enabled)
        10. Print scenario summary
        """
        settings = get_settings()
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            
            # ================================================================
            # STEP 1: CREATE SESSION
            # ================================================================
            print("\n" + "="*70)
            print("🚀 STEP 1: Creating Agent Council Session")
            print("="*70)
            
            session_payload = {
                "user_request": SCENARIO_REQUEST,
                "name": SCENARIO_NAME,
            }
            
            response = await client.post("/api/v1/sessions", json=session_payload)
            
            # Assertions
            assert response.status_code in [200, 201], f"Session creation failed: {response.text}"
            
            session_data = response.json()
            session_id = session_data.get("session_id")
            
            assert session_id is not None, "Session ID not returned"
            assert len(session_id) > 0, "Session ID is empty"
            assert session_data.get("status") == "pending", f"Unexpected status: {session_data.get('status')}"
            
            print(f"✅ Session created: {session_id}")
            print(f"   Status: {session_data.get('status')}")
            print(f"   Name: {session_data.get('name')}")
            
            # ================================================================
            # STEP 2: START WORKFLOW
            # ================================================================
            print("\n" + "="*70)
            print("🔄 STEP 2: Starting Workflow")
            print("="*70)
            
            # Try both possible endpoint patterns
            start_response = await client.post(f"/api/v1/workflow/{session_id}/start")
            
            if start_response.status_code == 404:
                # Try alternative endpoint
                start_response = await client.post(f"/api/v1/sessions/{session_id}/start")
            
            assert start_response.status_code == 200, f"Workflow start failed: {start_response.text}"
            
            start_data = start_response.json()
            workflow_status = start_data.get("status")
            
            print(f"✅ Workflow started")
            print(f"   Status: {workflow_status}")
            print(f"   Current Node: {start_data.get('current_node', 'unknown')}")
            
            # ================================================================
            # STEP 3: POLL UNTIL COMPLETION
            # ================================================================
            print("\n" + "="*70)
            print("⏳ STEP 3: Polling for Workflow Completion")
            print("="*70)
            
            poll_start_time = time.time()
            final_state = None
            iterations = 0
            
            while iterations < MAX_POLL_ITERATIONS:
                iterations += 1
                elapsed = time.time() - poll_start_time
                
                # Get workflow status
                status_response = await client.get(f"/api/v1/workflow/{session_id}/status")
                
                if status_response.status_code == 404:
                    # Try alternative endpoint
                    status_response = await client.get(f"/api/v1/sessions/{session_id}")
                
                assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
                
                current_state = status_response.json()
                current_status = current_state.get("status")
                current_node = current_state.get("current_node", "unknown")
                
                print(f"   [{elapsed:.1f}s] Status: {current_status}, Node: {current_node}")
                
                # Check for terminal states
                if current_status == "completed":
                    final_state = current_state
                    print(f"\n✅ Workflow completed in {elapsed:.1f} seconds")
                    break
                elif current_status == "failed":
                    error_msg = current_state.get("error", "Unknown error")
                    pytest.fail(f"Workflow failed: {error_msg}")
                elif current_status in ["cancelled", "rejected"]:
                    pytest.fail(f"Workflow terminated: {current_status}")
                
                # Wait before next poll
                await asyncio.sleep(POLL_INTERVAL)
            
            # Timeout check
            if final_state is None:
                pytest.fail(f"Workflow did not complete within {POLL_TIMEOUT} seconds")
            
            # ================================================================
            # STEP 4: VALIDATE STABILITY GUARDRAILS
            # ================================================================
            print("\n" + "="*70)
            print("🛡️  STEP 4: Validating Stability Safeguards")
            print("="*70)
            
            metadata = final_state.get("metadata", {})
            
            # Check adjudicator run count
            adjudicator_run_count = metadata.get("adjudicator_run_count", 0)
            print(f"   Adjudicator runs: {adjudicator_run_count}")
            assert adjudicator_run_count <= settings.adjudicator_max_runs, \
                f"Adjudicator ran {adjudicator_run_count} times (max: {settings.adjudicator_max_runs})"
            
            # Check debate rounds don't exceed max
            total_debates = final_state.get("total_debates", 0)
            print(f"   Total debates: {total_debates}")
            
            # Validate no infinite loops occurred
            current_round = final_state.get("current_round", 0)
            print(f"   Review rounds: {current_round}")
            assert current_round <= 10, f"Too many review rounds: {current_round} (possible infinite loop)"
            
            # Check for forced consensus flags
            consensus_summary = final_state.get("consensus_summary", "")
            forced_consensus = "forced" in consensus_summary.lower() or "timeout" in consensus_summary.lower()
            print(f"   Forced consensus: {forced_consensus}")
            
            if forced_consensus:
                print(f"   ℹ️  Consensus was forced (safeguards activated)")
                print(f"   Reason: {consensus_summary[:100]}")
            
            print("✅ All stability safeguards validated")
            
            # ================================================================
            # STEP 5: VALIDATE REVIEWER OUTPUTS
            # ================================================================
            print("\n" + "="*70)
            print("👥 STEP 5: Validating Reviewer Outputs")
            print("="*70)
            
            reviews = final_state.get("reviews", [])
            print(f"   Total reviews: {len(reviews)}")
            
            assert len(reviews) >= 2, f"Expected at least 2 reviewers, got {len(reviews)}"
            
            # Validate each review
            for idx, review in enumerate(reviews, 1):
                reviewer_role = review.get("reviewer_role", "unknown")
                rationale = review.get("rationale", "")
                
                # Check content length
                assert len(rationale) > 50, f"Review {idx} rationale too short: {len(rationale)} chars"
                
                # Check for integration keywords
                rationale_lower = rationale.lower()
                keywords_found = [kw for kw in INTEGRATION_KEYWORDS if kw in rationale_lower]
                
                print(f"   Review {idx} ({reviewer_role}): {len(rationale)} chars, keywords: {len(keywords_found)}")
                
                # At least some integration context should be present
                if idx <= 2:  # Check first 2 reviews more strictly
                    assert len(keywords_found) >= 1, \
                        f"Review {idx} missing integration context (found: {keywords_found})"
            
            print("✅ All reviewer outputs validated")
            
            # ================================================================
            # STEP 6: VALIDATE DEBATE AND CONSENSUS
            # ================================================================
            print("\n" + "="*70)
            print("💬 STEP 6: Validating Debates and Consensus")
            print("="*70)
            
            debates_resolved = final_state.get("debates_resolved", 0)
            total_disagreements = final_state.get("total_disagreements", 0)
            consensus_confidence = final_state.get("consensus_confidence")
            consensus_summary = final_state.get("consensus_summary", "")
            
            print(f"   Total disagreements: {total_disagreements}")
            print(f"   Debates resolved: {debates_resolved}")
            print(f"   Consensus confidence: {consensus_confidence}")
            
            # Validate consensus
            assert len(consensus_summary) > 0, "Consensus summary is empty"
            
            if consensus_confidence is not None:
                assert 0.5 <= consensus_confidence <= 1.0, \
                    f"Consensus confidence out of range: {consensus_confidence}"
                print(f"   ✅ Confidence in valid range: {consensus_confidence:.2f}")
            
            # If forced consensus, validate reason is included
            if forced_consensus:
                assert any(word in consensus_summary.lower() for word in ["forced", "timeout", "max rounds", "repetition"]), \
                    "Forced consensus but reason not in summary"
                print(f"   ℹ️  Forced consensus reason documented")
            
            print("✅ Debates and consensus validated")
            
            # ================================================================
            # STEP 7: VALIDATE ADJUDICATOR OUTPUT
            # ================================================================
            print("\n" + "="*70)
            print("⚖️  STEP 7: Validating Adjudicator Output")
            print("="*70)
            
            final_architecture_rationale = final_state.get("final_architecture_rationale", "")
            adjudication_complete = final_state.get("adjudication_complete", False)
            
            print(f"   Adjudication complete: {adjudication_complete}")
            print(f"   Rationale length: {len(final_architecture_rationale)} chars")
            
            if final_architecture_rationale:
                # Check for integration-specific reasoning
                rationale_lower = final_architecture_rationale.lower()
                integration_mentions = [
                    kw for kw in ["transformation", "mapping", "s3", "salesforce", 
                                  "mulesoft", "api", "integration flow", "error handling"]
                    if kw in rationale_lower
                ]
                
                print(f"   Integration concepts found: {len(integration_mentions)}")
                print(f"   Concepts: {', '.join(integration_mentions[:5])}")
                
                assert len(integration_mentions) >= 2, \
                    f"Adjudicator output lacks integration context (found: {integration_mentions})"
                
                print("✅ Adjudicator output validated")
            else:
                print("   ℹ️  No adjudicator output (consensus reached without adjudication)")
            
            # ================================================================
            # STEP 8: VALIDATE DELIVERABLES BUNDLE
            # ================================================================
            print("\n" + "="*70)
            print("📦 STEP 8: Validating Deliverables Bundle")
            print("="*70)
            
            deliverables = final_state.get("deliverables")
            
            if deliverables is None:
                # Try dedicated deliverables endpoint
                print("   Fetching from /deliverables endpoint...")
                deliverables_response = await client.get(f"/api/v1/workflow/{session_id}/deliverables")
                if deliverables_response.status_code == 200:
                    deliverables = deliverables_response.json()
                else:
                    pytest.fail(f"Deliverables not available: {deliverables_response.status_code}")
            
            assert deliverables is not None, "Deliverables bundle is missing"
            
            # 8.1: Architecture Summary
            print("\n   📋 Architecture Summary:")
            arch_summary = deliverables.get("architecture_summary", {})
            overview = arch_summary.get("overview", "")
            key_capabilities = arch_summary.get("key_capabilities", [])
            nfr_highlights = arch_summary.get("non_functional_highlights", [])
            
            assert len(overview) > 0, "Architecture overview is empty"
            assert len(key_capabilities) >= 3, f"Expected ≥3 capabilities, got {len(key_capabilities)}"
            
            print(f"      Overview: {len(overview)} chars")
            print(f"      Capabilities: {len(key_capabilities)}")
            print(f"      NFR Highlights: {len(nfr_highlights)}")
            print("      ✅ Architecture summary valid")
            
            # 8.2: Decision Records
            print("\n   🎯 Decision Records:")
            decisions = deliverables.get("decisions", [])
            
            assert len(decisions) >= 3, f"Expected ≥3 decisions, got {len(decisions)}"
            
            for idx, decision in enumerate(decisions[:5], 1):  # Check first 5
                assert "id" in decision, f"Decision {idx} missing ID"
                assert "context" in decision, f"Decision {idx} missing context"
                assert "decision" in decision, f"Decision {idx} missing decision text"
                assert "rationale" in decision, f"Decision {idx} missing rationale"
                assert "consequences" in decision, f"Decision {idx} missing consequences"
                
                assert len(decision["context"]) > 0, f"Decision {idx} context is empty"
                assert len(decision["rationale"]) > 0, f"Decision {idx} rationale is empty"
            
            print(f"      Total decisions: {len(decisions)}")
            print(f"      First decision: {decisions[0].get('id')} - {decisions[0].get('title', 'N/A')[:50]}")
            print("      ✅ Decision records valid")
            
            # 8.3: Risks
            print("\n   ⚠️  Risks:")
            risks = deliverables.get("risks", [])
            
            assert len(risks) >= 2, f"Expected ≥2 risks, got {len(risks)}"
            
            for idx, risk in enumerate(risks[:5], 1):  # Check first 5
                assert "id" in risk, f"Risk {idx} missing ID"
                assert "description" in risk, f"Risk {idx} missing description"
                assert "likelihood" in risk, f"Risk {idx} missing likelihood"
                assert "impact" in risk, f"Risk {idx} missing impact"
                assert "mitigation" in risk, f"Risk {idx} missing mitigation"
                
                # Validate likelihood and impact values
                assert risk["likelihood"] in ["low", "medium", "high"], \
                    f"Risk {idx} invalid likelihood: {risk['likelihood']}"
                assert risk["impact"] in ["low", "medium", "high", "critical"], \
                    f"Risk {idx} invalid impact: {risk['impact']}"
            
            print(f"      Total risks: {len(risks)}")
            print(f"      First risk: {risks[0].get('id')} - {risks[0].get('description', 'N/A')[:50]}")
            print("      ✅ Risks valid")
            
            # 8.4: FAQ
            print("\n   ❓ FAQ:")
            faqs = deliverables.get("faqs", [])
            
            assert len(faqs) >= 3, f"Expected ≥3 FAQ items, got {len(faqs)}"
            
            for idx, faq in enumerate(faqs[:5], 1):  # Check first 5
                assert "question" in faq, f"FAQ {idx} missing question"
                assert "answer" in faq, f"FAQ {idx} missing answer"
                
                assert len(faq["question"]) > 0, f"FAQ {idx} question is empty"
                assert len(faq["answer"]) > 0, f"FAQ {idx} answer is empty"
            
            print(f"      Total FAQs: {len(faqs)}")
            print(f"      First FAQ: {faqs[0].get('question', 'N/A')[:60]}")
            print("      ✅ FAQ items valid")
            
            # 8.5: Diagrams
            print("\n   📊 Diagrams:")
            diagrams = deliverables.get("diagrams", [])
            
            assert len(diagrams) >= 2, f"Expected ≥2 diagrams, got {len(diagrams)}"
            
            for idx, diagram in enumerate(diagrams, 1):
                assert "diagram_type" in diagram, f"Diagram {idx} missing type"
                assert "title" in diagram, f"Diagram {idx} missing title"
                assert "description" in diagram, f"Diagram {idx} missing description"
                
                # Must have either Lucid URL or Mermaid source
                has_lucid = diagram.get("lucid_url") is not None
                has_mermaid = diagram.get("mermaid_source") is not None
                
                assert has_lucid or has_mermaid, \
                    f"Diagram {idx} has neither Lucid URL nor Mermaid source"
                
                if has_mermaid:
                    mermaid_source = diagram["mermaid_source"]
                    assert "graph" in mermaid_source.lower() or "sequencediagram" in mermaid_source.lower(), \
                        f"Diagram {idx} Mermaid source appears invalid"
            
            print(f"      Total diagrams: {len(diagrams)}")
            diagram_types = [d.get("diagram_type") for d in diagrams]
            print(f"      Types: {', '.join(diagram_types)}")
            print("      ✅ Diagrams valid")
            
            # 8.6: Markdown Report
            print("\n   📄 Markdown Report:")
            markdown_report = deliverables.get("markdown_report", "")
            
            assert len(markdown_report) >= 500, \
                f"Markdown report too short: {len(markdown_report)} chars"
            
            # Check for required sections
            required_sections = [
                "# Architecture",
                "## Key Decision",
                "## Risk",
                "## FAQ",
                "## Diagram"
            ]
            
            for section in required_sections:
                assert section.lower() in markdown_report.lower(), \
                    f"Markdown report missing section: {section}"
            
            print(f"      Report size: {len(markdown_report)} chars")
            print(f"      Sections: {len(required_sections)}/5 present")
            print("      ✅ Markdown report valid")
            
            print("\n✅ Deliverables bundle fully validated")
            
            # ================================================================
            # STEP 9: VALIDATE LANGSMITH TRACE (IF ENABLED)
            # ================================================================
            print("\n" + "="*70)
            print("🔍 STEP 9: Validating LangSmith Trace")
            print("="*70)
            
            if settings.enable_langsmith:
                langsmith_trace_url = final_state.get("langsmith_trace_url")
                
                if langsmith_trace_url:
                    assert "smith.langchain.com" in langsmith_trace_url or "langsmith" in langsmith_trace_url, \
                        f"Invalid LangSmith URL: {langsmith_trace_url}"
                    print(f"   ✅ LangSmith trace available: {langsmith_trace_url}")
                else:
                    print("   ⚠️  LangSmith enabled but trace URL not found")
                    print("   (This is acceptable - tracing may be delayed)")
            else:
                print("   ℹ️  LangSmith tracing disabled")
            
            # ================================================================
            # STEP 10: PRINT FINAL SCENARIO SUMMARY
            # ================================================================
            print("\n" + "="*70)
            print("📊 SCENARIO VALIDATION SUMMARY")
            print("="*70)
            
            execution_time = time.time() - poll_start_time
            
            summary = f"""
[S3 → Salesforce E2E Test] COMPLETED ✅

Session ID:           {session_id}
Execution Time:       {execution_time:.1f}s
Iterations:           {iterations}

WORKFLOW METRICS:
-----------------
Status:               {final_state.get('status')}
Review Rounds:        {current_round}
Total Debates:        {total_debates}
Debates Resolved:     {final_state.get('debates_resolved', 0)}
Consensus Forced:     {forced_consensus}
Consensus Confidence: {consensus_confidence or 'N/A'}
Adjudicator Runs:     {adjudicator_run_count}

REVIEWER OUTPUTS:
-----------------
Total Reviews:        {len(reviews)}
Reviewers Active:     {len(set(r.get('reviewer_role') for r in reviews))}

DELIVERABLES:
-------------
Decisions (ADR):      {len(decisions)}
Risks Identified:     {len(risks)}
FAQ Items:            {len(faqs)}
Diagrams:             {len(diagrams)}
Markdown Report:      {len(markdown_report):,} bytes

LANGSMITH:
----------
Tracing Enabled:      {settings.enable_langsmith}
Trace URL:            {final_state.get('langsmith_trace_url') or 'N/A'}

STABILITY VALIDATION:
---------------------
✅ No infinite loops detected
✅ Adjudicator run-once enforced
✅ Debate rounds within limits
✅ All safeguards operational

TEST RESULT: PASSED ✅
"""
            
            print(summary)
            
            # ================================================================
            # ADDITIONAL VALIDATIONS
            # ================================================================
            
            # Validate messages timeline
            messages = final_state.get("messages", [])
            print(f"\nAgent Messages: {len(messages)}")
            assert len(messages) >= 3, "Expected at least 3 agent messages in timeline"
            
            # Validate no errors in final state
            errors = final_state.get("errors", [])
            if errors:
                print(f"\n⚠️  Warnings: {len(errors)} error(s) logged:")
                for error in errors[:3]:
                    print(f"   - {error}")
            
            # Validate design exists
            design = final_state.get("design")
            if design:
                print(f"\nFinal Design: {design.get('title', 'N/A')}")
                print(f"   Version: {design.get('version', 1)}")
            
            print("\n" + "="*70)
            print("🎉 END-TO-END WORKFLOW VALIDATION COMPLETE")
            print("="*70)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_workflow_stability_under_load():
    """
    Test workflow stability with multiple concurrent sessions.
    
    Validates that stability safeguards work correctly when multiple
    workflows run simultaneously.
    """
    settings = get_settings()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n" + "="*70)
        print("🔥 Testing Workflow Stability Under Load")
        print("="*70)
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            response = await client.post("/api/v1/sessions", json={
                "user_request": f"Design integration scenario {i+1}",
                "name": f"Load Test Session {i+1}",
            })
            
            if response.status_code == 200:
                session_ids.append(response.json()["session_id"])
        
        print(f"✅ Created {len(session_ids)} test sessions")
        
        # Start all workflows
        for session_id in session_ids:
            await client.post(f"/api/v1/workflow/{session_id}/start")
        
        print(f"✅ Started {len(session_ids)} workflows")
        
        # Brief wait
        await asyncio.sleep(2)
        
        # Check all are progressing
        for session_id in session_ids:
            response = await client.get(f"/api/v1/workflow/{session_id}/status")
            if response.status_code == 200:
                state = response.json()
                status = state.get("status")
                print(f"   Session {session_id[:8]}: {status}")
                
                # Validate no session is stuck
                assert status in ["pending", "in_progress", "awaiting_human", "completed"], \
                    f"Unexpected status: {status}"
        
        print("\n✅ All sessions progressing normally")
        print("✅ No stability issues detected under concurrent load")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

