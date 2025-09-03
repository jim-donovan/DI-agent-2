"""
Summary Agent for Benefits and Eligibility Extraction
Creates targeted summaries focused on benefits and eligibility criteria
"""

import time
from typing import Dict, Any, Optional
from agent_base import BaseAgent, AgentResponse
from config import config

class SummaryAgent(BaseAgent):
    """Agent specialized in creating benefits and eligibility summaries."""
    
    def __init__(self, logger, api_key: str):
        super().__init__("summary_agent", logger, api_key)
        self.api_key = api_key
        self.model = config.openai_model
        self.temperature = 0.1  # Low temperature for consistency
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return "You are a benefits analysis expert who creates concise, accurate summaries of benefits and eligibility information from documents."
        
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResponse:
        """Generate a focused summary of benefits and eligibility information."""
        
        try:
            document_content = input_data.get("content", "")
            document_title = input_data.get("title", "Document")
            
            if not document_content or not document_content.strip():
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="No document content provided for summarization"
                )
            
            # Create focused prompt for benefits and eligibility
            prompt = self._create_summary_prompt(document_content, document_title)
            
            # Make API call to generate summary
            start_time = time.time()
            response = self._call_openai_api(prompt)
            processing_time = time.time() - start_time
            
            if response and response.get("choices"):
                summary_content = response["choices"][0]["message"]["content"]
                
                # Calculate confidence based on content quality
                confidence = self._calculate_summary_confidence(summary_content, document_content)
                
                return AgentResponse(
                    success=True,
                    content=summary_content,
                    confidence=confidence,
                    tokens_used=response.get("usage", {}).get("total_tokens", 0),
                    processing_time=processing_time
                )
            else:
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="No valid response from OpenAI API"
                )
                
        except Exception as e:
            self.logger.log_error(f"Summary agent processing failed: {str(e)}")
            return AgentResponse(
                success=False,
                content="",
                confidence=0.0,
                error_message=str(e)
            )
    
    def _create_summary_prompt(self, content: str, title: str) -> str:
        """Create a focused prompt for benefits and eligibility extraction."""
        
        return f"""You are a benefits analysis expert. Extract and summarize benefits and eligibility data and information from this document.

DOCUMENT TITLE: {title}

DOCUMENT CONTENT:
{content}

INSTRUCTIONS:
Create a scannable, concise summary of benefits and eligibility data and information from this document.

1. **ELIGIBILITY CRITERIA**: Who can qualify for these benefits?
2. **BENEFITS OFFERED**: What specific benefits, coverage, or payments are available?
3. **BENEFIT AMOUNTS**: Dollar amounts, percentages, or coverage limits
4. **DURATION/TERMS**: How long benefits last or when they apply
5. **KEY REQUIREMENTS**: Important conditions or requirements to maintain benefits

FORMATTING REQUIREMENTS:
- Start with the document title as the main heading (# {title})
- Use clear headings with ## and ###
- Use bullet points for lists
- Include specific numbers, percentages, and dollar amounts when mentioned
- Keep descriptions brief but complete
- Only include information that is explicitly stated in the document
- If no benefits or eligibility information is found, state "No specific benefits or eligibility criteria identified in this document."

EXCLUDE:
- General company information
- Contact details
- Legal disclaimers (unless they affect eligibility)
- Technical procedures
- Administrative details not related to benefits/eligibility

Focus on what matters most to someone trying to understand what benefits they can get and how to qualify for them."""

    def _calculate_summary_confidence(self, summary: str, original_content: str) -> float:
        """Calculate confidence score for the generated summary."""
        
        if not summary or len(summary) < 50:
            return 0.1
        
        # Check for key benefit-related keywords
        benefit_keywords = [
            'benefit', 'eligible', 'coverage', 'payment', 'amount', 'qualify',
            'requirement', 'criteria', 'duration', 'limit', 'percentage', '$'
        ]
        
        summary_lower = summary.lower()
        keyword_matches = sum(1 for keyword in benefit_keywords if keyword in summary_lower)
        
        # Base confidence on keyword presence and summary length
        keyword_score = min(keyword_matches / len(benefit_keywords), 1.0)
        length_score = min(len(summary) / 500, 1.0)  # Optimal length around 500 chars
        
        # Check if summary contains structured information
        structure_score = 0.0
        if '##' in summary:  # Has headings
            structure_score += 0.3
        if '- ' in summary or '* ' in summary:  # Has bullet points  
            structure_score += 0.2
        if any(char.isdigit() for char in summary):  # Has numbers
            structure_score += 0.2
        
        # Combine scores
        confidence = (keyword_score * 0.4 + length_score * 0.3 + structure_score * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    def _call_openai_api(self, prompt: str) -> Optional[Dict]:
        """Make API call to OpenAI for summary generation."""
        
        if not self.api_key or not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000,  # Limit for concise summaries
                top_p=0.9
            )
            
            # Convert to dict format for compatibility
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.choices[0].message.content
                        }
                    }
                ],
                "usage": {
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            self.logger.log_error(f"OpenAI API call failed: {str(e)}")
            return None