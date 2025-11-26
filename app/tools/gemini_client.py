"""
Gemini client wrapper for tool integration.

Provides unified access to Gemini models for:
- Long-context reasoning
- Multi-modal analysis
- Structured output generation
- Safety-wrapped generation

This wraps the existing Gemini provider from app.llm.providers
with the tool interface.
"""

from typing import Any, Dict, Optional

from app.tools.base_tool import BaseTool, with_timeout, with_retry
from app.tools.schemas import ToolResult
from app.llm.factory import get_llm_provider


class GeminiClient(BaseTool):
    """
    Tool wrapper for Gemini LLM operations.
    
    Provides agents with access to Gemini's reasoning capabilities
    through a standardized tool interface.
    """
    
    @property
    def name(self) -> str:
        return "gemini"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Gemini client.
        
        Args:
            config: Optional configuration for model selection and parameters
        """
        super().__init__(config)
        self.provider = get_llm_provider()
        self.default_model = self.config.get("model", "gemini-1.5-flash")
    
    @with_timeout(seconds=60)
    @with_retry(max_attempts=2)
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute Gemini operation.
        
        Operations:
        - generate: General text generation
        - analyze_long_context: Analyze large documents
        - structured_reasoning: Generate structured analysis
        - summarize: Summarize content
        - extract_insights: Extract key insights from text
        """
        if operation == "generate":
            return await self._generate(
                parameters.get("prompt"),
                parameters.get("model", self.default_model),
                parameters.get("json_mode", False)
            )
        elif operation == "analyze_long_context":
            return await self._analyze_long_context(parameters.get("text"))
        elif operation == "structured_reasoning":
            return await self._structured_reasoning(
                parameters.get("problem"),
                parameters.get("context")
            )
        elif operation == "summarize":
            return await self._summarize(parameters.get("text"))
        elif operation == "extract_insights":
            return await self._extract_insights(parameters.get("text"))
        else:
            return self._create_error_result(
                f"Unknown operation: {operation}",
                error_type="InvalidOperation"
            )
    
    async def _generate(
        self,
        prompt: Optional[str],
        model: str,
        json_mode: bool = False
    ) -> ToolResult:
        """
        General text generation.
        
        Args:
            prompt: The prompt text
            model: Gemini model to use
            json_mode: Whether to return JSON
            
        Returns:
            ToolResult with generated content
        """
        if not prompt:
            return self._create_error_result(
                "No prompt provided",
                error_type="InvalidParameter"
            )
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model=model,
                json_mode=json_mode
            )
            
            return self._create_success_result(
                summary="Generated response",
                details={"content": response, "model": model, "json_mode": json_mode},
                metadata={"model": model, "prompt_length": len(prompt)}
            )
            
        except Exception as e:
            self.logger.error("gemini_generate_failed", error=str(e))
            return self._create_error_result(
                f"Generation failed: {str(e)}",
                error_type="GenerationError"
            )
    
    async def _analyze_long_context(self, text: Optional[str]) -> ToolResult:
        """
        Analyze large documents with Gemini's long-context capabilities.
        
        Args:
            text: Long-form text to analyze
            
        Returns:
            ToolResult with analysis
        """
        if not text:
            return self._create_error_result(
                "No text provided",
                error_type="InvalidParameter"
            )
        
        prompt = f"""
Analyze this document and provide:
1. **Executive Summary** (2-3 sentences)
2. **Key Topics** (list of main themes)
3. **Critical Points** (most important facts/decisions)
4. **Recommendations** (actionable next steps)
5. **Risks or Concerns** (potential issues identified)

Document:
{text}

Return ONLY a JSON object with these fields.
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model="gemini-1.5-pro",  # Use Pro for long context
                json_mode=True
            )
            
            return self._create_success_result(
                summary="Long-context analysis complete",
                details=response,
                metadata={"model": "gemini-1.5-pro", "text_length": len(text)}
            )
            
        except Exception as e:
            self.logger.error("gemini_long_context_failed", error=str(e))
            return self._create_error_result(
                f"Long-context analysis failed: {str(e)}",
                error_type="AnalysisError"
            )
    
    async def _structured_reasoning(
        self,
        problem: Optional[str],
        context: Optional[str] = None
    ) -> ToolResult:
        """
        Perform structured reasoning on a problem.
        
        Args:
            problem: Problem statement
            context: Additional context
            
        Returns:
            ToolResult with reasoning steps and conclusion
        """
        if not problem:
            return self._create_error_result(
                "No problem provided",
                error_type="InvalidParameter"
            )
        
        context_section = f"\n\nContext:\n{context}" if context else ""
        
        prompt = f"""
Apply structured reasoning to solve this problem:

Problem: {problem}{context_section}

Provide:
1. **Problem Decomposition** (break into sub-problems)
2. **Analysis** (examine each sub-problem)
3. **Constraints** (limitations or requirements)
4. **Options** (possible solutions with pros/cons)
5. **Recommendation** (best solution with rationale)

Return ONLY a JSON object with these fields.
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model=self.default_model,
                json_mode=True
            )
            
            return self._create_success_result(
                summary="Structured reasoning complete",
                details=response,
                metadata={"model": self.default_model}
            )
            
        except Exception as e:
            self.logger.error("gemini_structured_reasoning_failed", error=str(e))
            return self._create_error_result(
                f"Structured reasoning failed: {str(e)}",
                error_type="ReasoningError"
            )
    
    async def _summarize(self, text: Optional[str]) -> ToolResult:
        """
        Summarize text concisely.
        
        Args:
            text: Text to summarize
            
        Returns:
            ToolResult with summary
        """
        if not text:
            return self._create_error_result(
                "No text provided",
                error_type="InvalidParameter"
            )
        
        prompt = f"""
Summarize this content in a clear, concise manner:

{text}

Provide:
1. **One-sentence summary**
2. **Key points** (3-5 bullet points)
3. **Action items** (if any)

Return ONLY a JSON object.
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model=self.default_model,
                json_mode=True
            )
            
            return self._create_success_result(
                summary=response.get("one_sentence_summary", "Summary generated"),
                details=response,
                metadata={"model": self.default_model, "text_length": len(text)}
            )
            
        except Exception as e:
            self.logger.error("gemini_summarize_failed", error=str(e))
            return self._create_error_result(
                f"Summarization failed: {str(e)}",
                error_type="SummarizationError"
            )
    
    async def _extract_insights(self, text: Optional[str]) -> ToolResult:
        """
        Extract key insights from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ToolResult with extracted insights
        """
        if not text:
            return self._create_error_result(
                "No text provided",
                error_type="InvalidParameter"
            )
        
        prompt = f"""
Extract key insights from this text:

{text}

Provide:
1. **Main Insights** (3-5 key takeaways)
2. **Patterns** (recurring themes or trends)
3. **Implications** (what this means for decision-making)
4. **Questions Raised** (unanswered questions or concerns)

Return ONLY a JSON object.
"""
        
        try:
            response = await self.provider.generate_with_safety(
                prompt,
                model=self.default_model,
                json_mode=True
            )
            
            return self._create_success_result(
                summary="Insights extracted",
                details=response,
                metadata={"model": self.default_model}
            )
            
        except Exception as e:
            self.logger.error("gemini_extract_insights_failed", error=str(e))
            return self._create_error_result(
                f"Insight extraction failed: {str(e)}",
                error_type="ExtractionError"
            )

