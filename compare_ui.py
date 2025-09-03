#!/usr/bin/env python3
"""
UI Comparison Tool
Quick script to test both UI versions side by side
"""

import os
import sys
import threading
import time
from typing import Optional

def run_original_ui(port: int = 7860):
    """Run the original UI version."""
    os.environ["USE_SIMPLIFIED_UI"] = "false"
    print(f"Starting ORIGINAL UI on port {port}...")
    
    # Import after setting env var
    from ui import create_ui
    import gradio as gr
    
    demo = create_ui()
    demo.queue(max_size=20).launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_api=False,
        quiet=True
    )

def run_simplified_ui(port: int = 7861):
    """Run the simplified UI version."""
    os.environ["USE_SIMPLIFIED_UI"] = "true"
    print(f"Starting SIMPLIFIED UI on port {port}...")
    
    # Import after setting env var
    from ui_simplified import create_ui
    import gradio as gr
    
    demo = create_ui()
    demo.queue(max_size=20).launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_api=False,
        quiet=True
    )

def run_comparison(original_port: int = 7860, simplified_port: int = 7861):
    """Run both UIs side by side for comparison."""
    print("=" * 60)
    print("UI COMPARISON TOOL")
    print("=" * 60)
    print(f"Original UI:   http://localhost:{original_port}")
    print(f"Simplified UI: http://localhost:{simplified_port}")
    print("=" * 60)
    print("Press Ctrl+C to stop both servers")
    print("=" * 60)
    
    # Start both UIs in separate threads
    original_thread = threading.Thread(
        target=run_original_ui, 
        args=(original_port,),
        daemon=True
    )
    simplified_thread = threading.Thread(
        target=run_simplified_ui,
        args=(simplified_port,),
        daemon=True
    )
    
    original_thread.start()
    time.sleep(2)  # Give the first one time to start
    simplified_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down both UIs...")
        sys.exit(0)

def run_single(ui_type: str = "simplified", port: int = 7860):
    """Run a single UI version."""
    if ui_type.lower() == "original":
        run_original_ui(port)
    else:
        run_simplified_ui(port)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare UI versions")
    parser.add_argument(
        "--mode", 
        choices=["compare", "original", "simplified"],
        default="compare",
        help="Which mode to run (default: compare)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port for single mode (default: 7860)"
    )
    parser.add_argument(
        "--original-port",
        type=int,
        default=7860,
        help="Port for original UI in compare mode (default: 7860)"
    )
    parser.add_argument(
        "--simplified-port",
        type=int,
        default=7861,
        help="Port for simplified UI in compare mode (default: 7861)"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check for required dependencies
    try:
        import gradio
        from config import config
        if not config.validate():
            print("❌ Configuration validation failed!")
            print("Make sure OPENAI_API_KEY is set")
            sys.exit(1)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run the appropriate mode
    if args.mode == "compare":
        run_comparison(args.original_port, args.simplified_port)
    elif args.mode == "original":
        run_original_ui(args.port)
    else:  # simplified
        run_simplified_ui(args.port)
