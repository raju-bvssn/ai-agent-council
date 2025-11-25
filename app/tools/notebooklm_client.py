"""
NotebookLM client for grounded summaries and evidence-based analysis.

Provides:
- Document grounding with source citations
- Evidence-based answers to questions
- Multi-document synthesis
- Fact verification with references

Note: NotebookLM does not have a public API. This implementation
simulates NotebookLM behavior using Gemini with explicit instructions
for grounding and source attribution.
"""

import os
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, with_timeout, with_retry
from app.tools.schemas import ToolResult
from app.llm.providers import get_gemini_provider


class NotebookLMClient(BaseTool):
    """
    Client for NotebookLM-style grounded analysis.
    
    Provides evidence-based summaries and answers with source citations,
    mimicking NotebookLM's approach to grounded generation.
    """
    
    @property
    def name(self) -> str:
        return "notebooklm"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NotebookLM client.
        
        Args:
            config: Optional configuration
        """
        super().__init__(config)
        self.provider = get_gemini_provider()
        self.logger.warning(
            "notebooklm_simulated_mode",
            reason="NotebookLM has no public API, using Gemini-based simulation"
        )
    
    @with_timeout(seconds=60)
    @with_retry(max_attempts=2)
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute NotebookLM operation.
        
        Operations:
        - summarize_with_sources: Summarize with citations
        - answer_questions: Answer questions with evidence
        - synthesize_documents: Combine multiple documents
        - verify_claims: Verify claims against sources
        """
        if operation == "summarize_with_sources":
            return await self._summarize_with_sources(parameters.get("text"))
        elif operation == "answer_questions":
            return await self._answer_questions(
                parameters.get("text"),
                parameters.get("questions")
            )
        elif operation == "synthesize_documents":
            return await self._synthesize_documents(parameters.get("documents"))
        elif operation == "verify_claims":
            return await self._verify_claims(
                parameters.get("claims"),
                parameters.get("source_text")
            )
        else:
            return self._create_error_result(
                f"Unknown operation: {operation}",
                error_type="InvalidOperation"
            )
    
    async def _summarize_with_sources(self, text: Optional[str]) -> ToolResult:
        """
        Summarize text with source citations.
        
        Args:
            text: Text to summarize
            
        Returns:
            ToolResult with summary and citations
        """
        if not text:
            return self._create_error_result(
                "No text provided",
                error_type="InvalidParameter"
            )
        
        # Split text into numbered sections for citation
        sections = self._split_into_sections(text)
        numbered_text = "\n\n".join([f"[Section {i+1}]\n{sec}" for i, sec in enumerate(sections)])
        
        prompt = f"""
You are NotebookLM, an AI that provides grounded summaries with citations.

Your task: Summarize the following document. For EVERY statement you make, cite the source section using [Section N] notation.

Document:
{numbered_text}

Provide:
1. **Executive Summary** (2-3 sentences with citations)
2. **Key Findings** (list with citations for each)
3. **Evidence** (supporting quotes from the text)
4. **Confidence** (HIGH/MEDIUM/LOW for each finding)

Return ONLY a JSON object:
{{
  "executive_summary": "<summary with [Section N] citations>",
  "key_findings": [
    {{
      "finding": "<statement>",
      "citations": ["Section 1", "Section 3"],
      "confidence": "HIGH|MEDIUM|LOW",
      "evidence": "<direct quote>"
    }}
  ],
  "source_coverage": {{
    "sections_used": [1, 2, 3],
    "sections_unused": [4]
  }}
}}
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model="gemini-1.5-pro",
                json_mode=True
            )
            
            return self._create_success_result(
                summary="Grounded summary with citations",
                details=response,
                metadata={
                    "model": "gemini-1.5-pro",
                    "sections": len(sections),
                    "grounding_method": "section_citation"
                }
            )
            
        except Exception as e:
            self.logger.error("notebooklm_summarize_failed", error=str(e))
            return self._create_error_result(
                f"Grounded summarization failed: {str(e)}",
                error_type="SummarizationError"
            )
    
    async def _answer_questions(
        self,
        text: Optional[str],
        questions: Optional[List[str]]
    ) -> ToolResult:
        """
        Answer questions with evidence from the text.
        
        Args:
            text: Source text
            questions: List of questions to answer
            
        Returns:
            ToolResult with grounded answers
        """
        if not text or not questions:
            return self._create_error_result(
                "Both text and questions required",
                error_type="InvalidParameter"
            )
        
        sections = self._split_into_sections(text)
        numbered_text = "\n\n".join([f"[Section {i+1}]\n{sec}" for i, sec in enumerate(sections)])
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        prompt = f"""
You are NotebookLM. Answer these questions using ONLY information from the provided text.
Cite sources as [Section N]. If information is not in the text, say "Not found in sources."

Source Document:
{numbered_text}

Questions:
{questions_text}

For each question, provide:
- **Answer** (with [Section N] citations)
- **Evidence** (direct quotes)
- **Confidence** (HIGH if directly stated, MEDIUM if inferred, LOW if uncertain)

Return ONLY a JSON object:
{{
  "answers": [
    {{
      "question": "<the question>",
      "answer": "<grounded answer with citations>",
      "evidence": ["<quote1>", "<quote2>"],
      "citations": ["Section 1", "Section 3"],
      "confidence": "HIGH|MEDIUM|LOW"
    }}
  ]
}}
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model="gemini-1.5-pro",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"Answered {len(questions)} questions with evidence",
                details=response,
                metadata={
                    "model": "gemini-1.5-pro",
                    "questions_count": len(questions),
                    "sections": len(sections)
                }
            )
            
        except Exception as e:
            self.logger.error("notebooklm_answer_questions_failed", error=str(e))
            return self._create_error_result(
                f"Question answering failed: {str(e)}",
                error_type="AnsweringError"
            )
    
    async def _synthesize_documents(self, documents: Optional[List[str]]) -> ToolResult:
        """
        Synthesize insights from multiple documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            ToolResult with cross-document synthesis
        """
        if not documents or len(documents) == 0:
            return self._create_error_result(
                "No documents provided",
                error_type="InvalidParameter"
            )
        
        numbered_docs = "\n\n".join([f"[Document {i+1}]\n{doc}" for i, doc in enumerate(documents)])
        
        prompt = f"""
You are NotebookLM. Synthesize insights from these multiple documents.
Cite sources as [Document N]. Identify agreements, disagreements, and gaps.

Documents:
{numbered_docs}

Provide:
1. **Common Themes** (what all documents agree on, with citations)
2. **Contradictions** (where documents disagree, with citations)
3. **Unique Insights** (found in only one document, with citation)
4. **Gaps** (topics missing across all documents)

Return ONLY a JSON object.
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model="gemini-1.5-pro",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"Synthesized {len(documents)} documents",
                details=response,
                metadata={
                    "model": "gemini-1.5-pro",
                    "document_count": len(documents)
                }
            )
            
        except Exception as e:
            self.logger.error("notebooklm_synthesize_failed", error=str(e))
            return self._create_error_result(
                f"Document synthesis failed: {str(e)}",
                error_type="SynthesisError"
            )
    
    async def _verify_claims(
        self,
        claims: Optional[List[str]],
        source_text: Optional[str]
    ) -> ToolResult:
        """
        Verify claims against source text.
        
        Args:
            claims: List of claims to verify
            source_text: Source text for verification
            
        Returns:
            ToolResult with verification results
        """
        if not claims or not source_text:
            return self._create_error_result(
                "Both claims and source_text required",
                error_type="InvalidParameter"
            )
        
        sections = self._split_into_sections(source_text)
        numbered_text = "\n\n".join([f"[Section {i+1}]\n{sec}" for i, sec in enumerate(sections)])
        claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])
        
        prompt = f"""
You are NotebookLM. Verify each claim against the source text.

Source Text:
{numbered_text}

Claims to Verify:
{claims_text}

For each claim, determine:
- **Verified**: TRUE (directly supported), FALSE (contradicted), PARTIAL (partially supported), UNKNOWN (not mentioned)
- **Evidence**: Direct quote supporting or contradicting
- **Citation**: [Section N]
- **Confidence**: HIGH/MEDIUM/LOW

Return ONLY a JSON object:
{{
  "verifications": [
    {{
      "claim": "<the claim>",
      "verified": "TRUE|FALSE|PARTIAL|UNKNOWN",
      "evidence": "<quote>",
      "citation": "Section N",
      "confidence": "HIGH|MEDIUM|LOW",
      "explanation": "<brief explanation>"
    }}
  ]
}}
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model="gemini-1.5-pro",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"Verified {len(claims)} claims",
                details=response,
                metadata={
                    "model": "gemini-1.5-pro",
                    "claims_count": len(claims)
                }
            )
            
        except Exception as e:
            self.logger.error("notebooklm_verify_claims_failed", error=str(e))
            return self._create_error_result(
                f"Claim verification failed: {str(e)}",
                error_type="VerificationError"
            )
    
    def _split_into_sections(self, text: str, max_section_length: int = 1000) -> List[str]:
        """
        Split text into numbered sections for citation.
        
        Args:
            text: Text to split
            max_section_length: Maximum characters per section
            
        Returns:
            List of text sections
        """
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        sections = []
        current_section = ""
        
        for para in paragraphs:
            if len(current_section) + len(para) > max_section_length and current_section:
                sections.append(current_section.strip())
                current_section = para
            else:
                current_section += "\n\n" + para if current_section else para
        
        if current_section:
            sections.append(current_section.strip())
        
        return sections if sections else [text]  # Fallback to whole text if splitting fails

