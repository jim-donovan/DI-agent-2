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
    
    def __init__(self, logger, api_client=None):
        super().__init__("summary_agent", logger, api_client)
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

        # Truncate content to avoid token limits
        # Estimate ~4 chars per token, leave room for prompt and response
        # Anthropic has 200k limit, but we'll use 150k to be safe (600k chars)
        # OpenAI GPT-4 has 128k limit, so we'll use 100k to be safe (400k chars)
        max_content_chars = 400000  # Conservative limit for GPT-4

        if len(content) > max_content_chars:
            self.logger.log_warning(f"Content truncated from {len(content)} to {max_content_chars} characters to fit token limits")

            # For very large documents, try to extract the most relevant sections
            content = self._smart_truncate(content, max_content_chars)

        return f"""You are a benefits analysis expert. Provide a summary of benefits as defined in this document. Categorize and group in a logical way that is easy to understand.

DOCUMENT TITLE: {title}

DOCUMENT CONTENT:
{content}

Make sure to exclude the following:
- General company information
- Contact details
- Legal disclaimers (unless they affect eligibility)
- Technical procedures
- Administrative details not related to benefits/eligibility

Focus on what matters most to someone trying to understand what benefits they can get and the eligibility criteria they need to qualify for them."""

    def _smart_truncate(self, content: str, max_chars: int) -> str:
        """Intelligently truncate content by prioritizing benefit-related sections."""

        # If content fits, return as-is
        if len(content) <= max_chars:
            return content

        # Keywords that indicate important benefit sections
        priority_keywords = [
            'benefit', 'eligible', 'eligibility', 'coverage', 'payment',
            'amount', 'qualify', 'requirement', 'criteria', 'enrollment',
            'deductible', 'copay', 'premium', 'maximum', 'minimum',
            'percentage', 'duration', 'period', 'effective', 'termination'
        ]

        # Split content into paragraphs
        paragraphs = content.split('\n\n')

        # Score each paragraph based on keyword density
        scored_paragraphs = []
        for para in paragraphs:
            if not para.strip():
                continue

            para_lower = para.lower()
            score = sum(1 for keyword in priority_keywords if keyword in para_lower)
            # Boost score for paragraphs with dollar amounts
            if '$' in para:
                score += 2
            # Boost score for paragraphs with percentages
            if '%' in para:
                score += 1

            scored_paragraphs.append((score, para))

        # Sort by score (highest first)
        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)

        # Build truncated content prioritizing high-scoring paragraphs
        result = []
        result_length = 0

        for score, para in scored_paragraphs:
            para_length = len(para) + 2  # +2 for paragraph breaks
            if result_length + para_length <= max_chars:
                result.append(para)
                result_length += para_length
            elif result_length < max_chars * 0.8:  # If we have room for a partial paragraph
                remaining_space = max_chars - result_length - 50  # Leave some buffer
                if remaining_space > 100:
                    truncated_para = para[:remaining_space]
                    # Find last sentence boundary
                    last_period = truncated_para.rfind('. ')
                    if last_period > remaining_space * 0.5:
                        truncated_para = truncated_para[:last_period + 1]
                    result.append(truncated_para)
                    break

        # Join paragraphs
        truncated_content = '\n\n'.join(result)

        # Add truncation notice
        if len(truncated_content) < len(content):
            truncated_content += "\n\n[Content has been intelligently truncated to focus on benefit-related information...]"

        return truncated_content

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
        """Make API call using unified client system."""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt()
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # Use unified client through make_api_call
            response_content, tokens_used = self.make_api_call(
                messages=messages,
                task="main",  # Use main model for summaries
                temperature=self.temperature,
                max_tokens=64000  # Increased from 1000 to allow longer summaries
            )
            
            # Convert to dict format for compatibility
            return {
                "choices": [
                    {
                        "message": {
                            "content": response_content
                        }
                    }
                ],
                "usage": {
                    "total_tokens": tokens_used
                }
            }
            
        except Exception as e:
            self.logger.log_error(f"OpenAI API call failed: {str(e)}")
            return None