"""
Base Agent Architecture for OCR Pipeline
Provides foundation for specialized OCR agents with state management and reasoning
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import time
from datetime import datetime
import openai
from logger import ProcessingLogger


@dataclass
class AgentState:
    """Represents the current state of an agent."""
    agent_id: str
    session_id: str
    task_context: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    error_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Standardized response from agents."""
    success: bool
    content: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    reasoning_steps: List[str] = field(default_factory=list)
    tokens_used: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """Base class for OCR pipeline agents."""
    
    def __init__(self, agent_id: str, logger: ProcessingLogger, api_key: str):
        self.agent_id = agent_id
        self.logger = logger
        
        # Initialize OpenAI client with explicit parameters only
        if api_key and api_key.strip():
            self.client = openai.OpenAI(
                api_key=api_key,
                timeout=30.0,
                max_retries=2
            )
        else:
            self.client = None
        self.state = AgentState(
            agent_id=agent_id,
            session_id=f"session_{int(time.time())}"
        )
        
    @abstractmethod
    def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResponse:
        """Process input and return structured response."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def update_state(self, key: str, value: Any) -> None:
        """Update agent state."""
        self.state.task_context[key] = value
        self.state.last_updated = datetime.now()
    
    def add_memory(self, event: str, data: Dict[str, Any]) -> None:
        """Add event to agent memory."""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        }
        self.state.memory.append(memory_entry)
        
        # Keep only last 50 memory entries
        if len(self.state.memory) > 50:
            self.state.memory = self.state.memory[-50:]
    
    def calculate_confidence(self, response_text: str, context: Dict[str, Any]) -> float:
        """Calculate confidence score for the response."""
        # Base confidence calculation - can be overridden by subclasses
        base_confidence = 0.8
        
        # Adjust based on response length
        if len(response_text) < 10:
            base_confidence -= 0.3
        elif len(response_text) > 1000:
            base_confidence += 0.1
            
        # Adjust based on context
        if context.get("retry_count", 0) > 0:
            base_confidence -= (context["retry_count"] * 0.1)
            
        return max(0.0, min(1.0, base_confidence))
    
    def make_api_call(self, messages: List[Dict[str, Any]], model: str = "gpt-4o", 
                     temperature: float = 0.1, max_tokens: int = None) -> Tuple[str, int]:
        """Make API call with error handling and token tracking."""
        if not self.client:
            raise ValueError("OpenAI client not initialized - API key may be missing")
            
        try:
            # Use config max_tokens if not specified
            if max_tokens is None:
                from config import config
                max_tokens = config.max_output_tokens
                
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return content, tokens_used
            
        except Exception as e:
            error_msg = str(e)
            # More specific error logging
            if "timeout" in error_msg.lower():
                self.logger.log_error(f"Agent {self.agent_id} API call timed out (30s limit)")
            elif "rate" in error_msg.lower():
                self.logger.log_error(f"Agent {self.agent_id} rate limited")
            else:
                self.logger.log_error(f"Agent {self.agent_id} API call failed: {e}")
            self.state.error_history.append(error_msg)
            raise
    
    def retry_with_fallback(self, input_data: Any, context: Dict[str, Any], 
                           max_retries: int = 2) -> AgentResponse:
        """Retry processing with fallback strategies."""
        for attempt in range(max_retries + 1):
            try:
                context["retry_count"] = attempt
                response = self.process(input_data, context)
                if response.success:
                    return response
                    
            except Exception as e:
                self.logger.log_warning(f"Agent {self.agent_id} attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    return AgentResponse(
                        success=False,
                        content="",
                        confidence=0.0,
                        error_message=f"Failed after {max_retries + 1} attempts: {str(e)}"
                    )
        
        return AgentResponse(
            success=False,
            content="",
            confidence=0.0,
            error_message="Max retries exceeded"
        )
    
    def get_reasoning_context(self) -> str:
        """Get formatted context for reasoning."""
        recent_memory = self.state.memory[-50:] if self.state.memory else []
        context_parts = []
        
        if recent_memory:
            context_parts.append("Recent context:")
            for entry in recent_memory:
                context_parts.append(f"- {entry['event']}: {entry['data'].get('summary', 'No summary')}")
        
        if self.state.confidence_scores:
            avg_confidence = sum(self.state.confidence_scores.values()) / len(self.state.confidence_scores)
            context_parts.append(f"Average confidence: {avg_confidence:.2f}")
            
        return "\n".join(context_parts) if context_parts else "No previous context"


class AgentOrchestrator:
    """Coordinates multiple agents in the OCR pipeline."""
    
    def __init__(self, logger: ProcessingLogger):
        self.logger = logger
        self.agents: Dict[str, BaseAgent] = {}
        self.pipeline_state = {
            "current_stage": None,
            "completed_stages": [],
            "stage_results": {}
        }
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_id] = agent
        self.logger.log_step(f"Registered agent: {agent.agent_id}")
    
    def execute_pipeline(self, input_data: Any, agent_sequence: List[str], 
                        context: Dict[str, Any] = None) -> Dict[str, AgentResponse]:
        """Execute a sequence of agents."""
        results = {}
        current_data = input_data
        context = context or {}
        
        for agent_id in agent_sequence:
            if agent_id not in self.agents:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            self.pipeline_state["current_stage"] = agent_id
            self.logger.log_step(f"Executing agent: {agent_id}")
            
            agent = self.agents[agent_id]
            
            # Add previous results to context
            context["pipeline_results"] = results
            context["current_stage"] = agent_id
            
            # Execute agent with retry capability
            response = agent.retry_with_fallback(current_data, context)
            results[agent_id] = response
            
            self.pipeline_state["stage_results"][agent_id] = response
            self.pipeline_state["completed_stages"].append(agent_id)
            
            if response.success:
                current_data = response.content  # Pass output to next agent
                self.logger.log_success(f"Agent {agent_id} completed successfully (confidence: {response.confidence:.2f})")
            else:
                self.logger.log_error(f"Agent {agent_id} failed: {response.error_message}")
                break
        
        return results
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of pipeline execution."""
        return {
            "completed_stages": self.pipeline_state["completed_stages"],
            "total_agents": len(self.agents),
            "success_rate": len(self.pipeline_state["completed_stages"]) / len(self.agents) if self.agents else 0,
            "stage_results": {
                stage: {
                    "success": result.success,
                    "confidence": result.confidence,
                    "tokens_used": result.tokens_used,
                    "processing_time": result.processing_time
                }
                for stage, result in self.pipeline_state["stage_results"].items()
            }
        }