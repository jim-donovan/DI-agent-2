"""
OCR Processor Logging System
Clean, timestamp-based logging with multiple output options
"""

import time
from typing import List, Callable

class ProcessingLogger:
    """Simple, efficient logger for OCR processing."""
    
    def __init__(self):
        self.logs: List[str] = []
        self.callbacks: List[Callable[[str], None]] = []
    
    def log(self, message: str) -> None:
        """Log a message with timestamp."""
        timestamp = time.strftime('%H:%M:%S')
        formatted = f"[{timestamp}] {message}"
        
        self.logs.append(formatted)
        
        print(formatted)
        
        for callback in self.callbacks:
            try:
                callback(formatted)
            except Exception as e:
                print(f"[{timestamp}] Logger callback error: {e}")
    
    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback for real-time log updates."""
        self.callbacks.append(callback)
    
    def get_logs(self) -> str:
        """Get all logs as a single string."""
        return "\n".join(self.logs)
    
    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()
    
    def get_recent_logs(self, count: int = 10) -> str:
        """Get the most recent N log entries."""
        return "\n".join(self.logs[-count:])
    
    def log_section(self, title: str) -> None:
        """Log a section header for better organization."""
        separator = "=" * 50
        self.log(f"\n{separator}")
        self.log(f"📋 {title}")
        self.log(separator)
    
    def log_step(self, step: str, detail: str = "") -> None:
        """Log a processing step with optional detail."""
        if detail:
            self.log(f"🔄 {step}: {detail}")
        else:
            self.log(f"🔄 {step}")
    
    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.log(f"✅ {message}")
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.log(f"⚠️  {message}")
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.log(f"❌ {message}")
    
    def log_metric(self, name: str, value: any) -> None:
        """Log a metric value."""
        self.log(f"📊 {name}: {value}")
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.log(f"ℹ️  {message}")
    
    def warning(self, message: str) -> None:
        """Log a warning message (alias for log_warning)."""
        self.log_warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message (alias for log_error)."""
        self.log_error(message)
    
    def log_page_processed(self, page_num: int, method: str, processing_time: float, from_cache: bool = False) -> None:
        """Log page processing completion."""
        cache_indicator = " (cached)" if from_cache else ""
        self.log(f"📄 Page {page_num} processed using {method} in {processing_time:.2f}s{cache_indicator}")