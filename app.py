#!/usr/bin/env python3
"""
OCR Processor - Simplified Version
Vision-first OCR with intelligent corruption detection
"""

import os
import sys
import traceback
import gradio as gr
from config import config  # This loads .env first

# Use main UI
from ui import create_ui

def main():
    """Kickoff DI processor."""
    print("Document Ingestion 5.0 (Simplified)")
    print("=" * 50)
    
    # Validate environment
    if not config.validate():
        print("❌ Configuration validation failed!")
        print("Make sure OPENAI_API_KEY is set in Space secrets")
        # Create a simple error interface
        with gr.Blocks() as error_demo:
            gr.Markdown("""
            # ❌ Configuration Error
            
            **OPENAI_API_KEY not found**
            """)
        return error_demo
    
    print(f"📋 Vision threshold: {config.vision_corruption_threshold}")
    print(f"🔧 Max vision calls: {config.max_vision_calls_per_doc}")
    print(f"🖼️  DPI: {config.dpi}")
    print(f"🤖 Vision model: {config.vision_model}")
    print(f"📝 Temperature: {config.temperature}")
    print("💡 Focus: Vision OCR priority, accuracy, speed")
    # Using main UI interface
    print("=" * 50)
    
    try:
        demo = create_ui()
        return demo
        
    except Exception as e:
        print(f"❌ Interface creation failed: {e}")
        traceback.print_exc()
        
        with gr.Blocks() as error_demo:
            gr.Markdown(f"""
            # ❌ Application Error
            
            **Failed to start OCR Processor:**
            
            ```
            {str(e)}
            ```
            
            Please check the logs for more details.
            """)
        return error_demo

def running_on_spaces() -> bool:
    """Check if the app is running on Spaces."""
    return any(os.getenv(k) for k in ["SPACE_ID", "SPACE_REPO", "HF_SPACE", "SPACE_NAME"])

if __name__ == "__main__":
    demo = main()
    if demo is None:
        sys.exit(1)

    # Launch the app
    launch_kwargs = {}

    # Pass css/js to launch() (Gradio 6.0+)
    if hasattr(demo, '_custom_css'):
        launch_kwargs["css"] = demo._custom_css
    if hasattr(demo, '_custom_js'):
        launch_kwargs["js"] = demo._custom_js

    if running_on_spaces():
        pass
    else:
        # Always use share link for local development to fix download blocking issues
        launch_kwargs.update({"server_name": "0.0.0.0", "server_port": 7860, "share": True})

    demo.queue(max_size=20).launch(**launch_kwargs)
