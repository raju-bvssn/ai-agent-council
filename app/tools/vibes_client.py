"""
MuleSoft Vibes client for best practice analysis.

Vibes provides:
- RAML/OAS specification validation
- MuleSoft best practice recommendations
- Error handling pattern suggestions
- Integration style guidance

This client uses Gemini as an analysis engine when Vibes official API
is unavailable (prototype/demo mode).
"""

import os
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, with_timeout, with_retry
from app.tools.schemas import ToolResult
from app.llm.factory import get_llm_provider
from app.utils.settings import get_settings

# LangSmith tracing (optional)
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])


class VibesClient(BaseTool):
    """
    Client for MuleSoft Vibes integration analysis.
    
    Provides best practice validation and recommendations for
    MuleSoft integration patterns.
    """
    
    @property
    def name(self) -> str:
        return "vibes"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Vibes client.
        
        Args:
            config: Optional configuration including API keys and endpoints
        """
        super().__init__(config)
        settings = get_settings()
        
        self.api_key = self.config.get("api_key") or os.getenv("VIBES_API_KEY")
        self.endpoint = self.config.get("endpoint") or os.getenv("VIBES_ENDPOINT")
        
        # Use mock mode if DEMO_MODE is enabled or no API key
        self.use_mock = settings.demo_mode or not self.api_key
        
        if self.use_mock:
            reason = "DEMO_MODE enabled" if settings.demo_mode else "No API key found"
            self.logger.warning("vibes_mock_mode", reason=f"{reason}, using Gemini fallback")
    
    @with_timeout(seconds=45)
    @with_retry(max_attempts=3)
    @traceable(name="vibes_execute")
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute Vibes operation.
        
        Operations:
        - analyze_api_spec: Validate API specification
        - recommend_patterns: Suggest integration patterns
        - review_error_handling: Check error handling strategy
        - validate_nfrs: Validate non-functional requirements
        """
        if operation == "analyze_api_spec":
            return await self._analyze_api_spec(
                parameters.get("spec_text"),
                parameters.get("spec_type", "raml")
            )
        elif operation == "recommend_patterns":
            return await self._recommend_patterns(parameters.get("description"))
        elif operation == "review_error_handling":
            return await self._review_error_handling(parameters.get("design"))
        elif operation == "validate_nfrs":
            return await self._validate_nfrs(parameters.get("requirements"))
        else:
            return self._create_error_result(
                f"Unknown operation: {operation}",
                error_type="InvalidOperation"
            )
    
    @traceable(name="vibes_analyze_api_spec")
    async def _analyze_api_spec(
        self,
        spec_text: Optional[str],
        spec_type: str = "raml"
    ) -> ToolResult:
        """
        Analyze an API specification for best practices.
        
        Args:
            spec_text: The API specification content
            spec_type: Type of spec ('raml', 'oas', 'openapi')
            
        Returns:
            ToolResult with analysis and recommendations
        """
        if not spec_text:
            return self._create_error_result(
                "No spec_text provided",
                error_type="InvalidParameter"
            )
        
        if self.use_mock:
            return await self._analyze_with_gemini(spec_text, spec_type)
        
        # TODO: Implement actual Vibes API call when available
        return await self._analyze_with_gemini(spec_text, spec_type)
    
    async def _analyze_with_gemini(self, spec_text: str, spec_type: str) -> ToolResult:
        """
        Use Gemini to analyze API spec (fallback/prototype mode).
        
        Args:
            spec_text: API specification content
            spec_type: Specification type
            
        Returns:
            ToolResult with Gemini-powered analysis
        """
        provider = get_llm_provider()
        
        prompt = f"""
You are a MuleSoft Vibes API design expert. Analyze this {spec_type.upper()} specification and provide:

1. **Compliance Score** (0-100): How well it follows MuleSoft best practices
2. **Strengths**: What's done well
3. **Issues**: Problems or anti-patterns found
4. **Recommendations**: Specific improvements with examples
5. **Priority**: HIGH/MEDIUM/LOW for each recommendation

API Specification:
```
{spec_text}
```

Return ONLY a JSON object with this structure:
{{
  "score": <number>,
  "strengths": ["<strength1>", "<strength2>"],
  "issues": [
    {{"severity": "HIGH|MEDIUM|LOW", "issue": "<description>", "location": "<where>"}}
  ],
  "recommendations": [
    {{"priority": "HIGH|MEDIUM|LOW", "recommendation": "<what to do>", "example": "<code example>"}}
  ],
  "summary": "<overall assessment>"
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            analysis = response  # Already parsed JSON from json_mode
            
            return self._create_success_result(
                summary=analysis.get("summary", "API specification analyzed"),
                details={
                    "score": analysis.get("score", 0),
                    "strengths": analysis.get("strengths", []),
                    "issues": analysis.get("issues", []),
                    "recommendations": analysis.get("recommendations", [])
                },
                metadata={
                    "spec_type": spec_type,
                    "analysis_engine": "gemini-vibes-fallback"
                }
            )
            
        except Exception as e:
            self.logger.error("vibes_gemini_analysis_failed", error=str(e))
            return self._create_error_result(
                f"Analysis failed: {str(e)}",
                error_type="AnalysisError"
            )
    
    @traceable(name="vibes_recommend_patterns")
    async def _recommend_patterns(self, description: Optional[str]) -> ToolResult:
        """
        Recommend integration patterns based on requirements.
        
        Args:
            description: Integration requirements description
            
        Returns:
            ToolResult with pattern recommendations
        """
        if not description:
            return self._create_error_result(
                "No description provided",
                error_type="InvalidParameter"
            )
        
        provider = get_llm_provider()
        
        prompt = f"""
You are a MuleSoft integration architect. Based on these requirements, recommend the best integration patterns:

Requirements:
{description}

Consider:
- Synchronous vs Asynchronous patterns
- API-led connectivity layers (System/Process/Experience)
- Error handling strategies
- Scalability patterns
- Security patterns

Return ONLY a JSON object:
{{
  "primary_pattern": "<pattern name>",
  "rationale": "<why this pattern>",
  "alternatives": [
    {{"pattern": "<name>", "pros": ["<pro1>"], "cons": ["<con1>"]}}
  ],
  "implementation_notes": ["<note1>", "<note2>"],
  "mulesoft_resources": ["<doc link or example>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"Recommended pattern: {response.get('primary_pattern', 'N/A')}",
                details=response,
                metadata={"analysis_engine": "gemini-vibes-fallback"}
            )
            
        except Exception as e:
            self.logger.error("vibes_pattern_recommendation_failed", error=str(e))
            return self._create_error_result(
                f"Pattern recommendation failed: {str(e)}",
                error_type="RecommendationError"
            )
    
    async def _review_error_handling(self, design: Optional[str]) -> ToolResult:
        """
        Review error handling strategy in a design.
        
        Args:
            design: Design document or architecture description
            
        Returns:
            ToolResult with error handling analysis
        """
        if not design:
            return self._create_error_result(
                "No design provided",
                error_type="InvalidParameter"
            )
        
        provider = get_llm_provider()
        
        prompt = f"""
You are a MuleSoft error handling expert. Review this design for error handling completeness:

Design:
{design}

Evaluate:
1. Is there a global error handler?
2. Are errors caught at appropriate layers?
3. Are errors logged with sufficient context?
4. Are errors transformed for consumers?
5. Are retries and circuit breakers used appropriately?

Return ONLY a JSON object:
{{
  "score": <0-100>,
  "coverage": {{"global_handler": true/false, "layer_specific": true/false, "logging": true/false}},
  "gaps": ["<gap1>", "<gap2>"],
  "recommendations": ["<recommendation1>", "<recommendation2>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"Error handling score: {response.get('score', 0)}/100",
                details=response,
                metadata={"analysis_engine": "gemini-vibes-fallback"}
            )
            
        except Exception as e:
            self.logger.error("vibes_error_handling_review_failed", error=str(e))
            return self._create_error_result(
                f"Error handling review failed: {str(e)}",
                error_type="ReviewError"
            )
    
    async def _validate_nfrs(self, requirements: Optional[str]) -> ToolResult:
        """
        Validate non-functional requirements for completeness.
        
        Args:
            requirements: NFR requirements text
            
        Returns:
            ToolResult with validation results
        """
        if not requirements:
            return self._create_error_result(
                "No requirements provided",
                error_type="InvalidParameter"
            )
        
        provider = get_llm_provider()
        
        prompt = f"""
You are a MuleSoft NFR validation expert. Check if these NFRs are complete and measurable:

Requirements:
{requirements}

Check for:
- Performance targets (throughput, latency)
- Scalability requirements
- Availability/SLA targets
- Security requirements
- Monitoring/observability

Return ONLY a JSON object:
{{
  "completeness_score": <0-100>,
  "present": ["<category1>", "<category2>"],
  "missing": ["<category1>", "<category2>"],
  "vague_requirements": ["<requirement that needs clarification>"],
  "recommendations": ["<specific recommendation>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            return self._create_success_result(
                summary=f"NFR completeness: {response.get('completeness_score', 0)}%",
                details=response,
                metadata={"analysis_engine": "gemini-vibes-fallback"}
            )
            
        except Exception as e:
            self.logger.error("vibes_nfr_validation_failed", error=str(e))
            return self._create_error_result(
                f"NFR validation failed: {str(e)}",
                error_type="ValidationError"
            )

