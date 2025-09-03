#!/usr/bin/env python3
"""
Test Script for Simplified UI
Verifies that all features work correctly in the simplified version
"""

import sys
import os
import tempfile
from pathlib import Path

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    try:
        from ui_simplified import SimplifiedOCRInterface, create_ui
        print("✅ Simplified UI imports successful")
        
        from processor_optimized import OptimizedDocumentProcessor
        print("✅ Processor imports successful")
        
        from config import config
        print("✅ Config imports successful")
        
        from summary_generator import SummaryGenerator
        print("✅ Summary generator imports successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_interface_creation():
    """Test that the interface can be created."""
    print("\nTesting interface creation...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        
        interface = SimplifiedOCRInterface()
        print("✅ Interface instance created")
        
        # Test that key methods exist
        assert hasattr(interface, 'process_wrapper'), "Missing process_wrapper method"
        assert hasattr(interface, 'clear_all'), "Missing clear_all method"
        assert hasattr(interface, 'abort_processing'), "Missing abort_processing method"
        assert hasattr(interface, '_parse_evaluation_simple'), "Missing evaluation parser"
        print("✅ All key methods present")
        
        return True
    except Exception as e:
        print(f"❌ Interface creation failed: {e}")
        return False

def test_loading_messages():
    """Test loading messages functionality."""
    print("\nTesting loading messages...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        
        interface = SimplifiedOCRInterface()
        
        # Check that loading messages exist
        assert len(interface.LOADING_MESSAGES) > 0, "No loading messages defined"
        print(f"✅ {len(interface.LOADING_MESSAGES)} loading messages available")
        
        # Test HTML generation
        loading_html = interface._get_loading_html()
        assert loading_html, "Loading HTML is empty"
        assert "loading-spinner" in loading_html, "Missing loading spinner"
        print("✅ Loading HTML generation works")
        
        return True
    except Exception as e:
        print(f"❌ Loading messages test failed: {e}")
        return False

def test_evaluation_parser():
    """Test the simplified evaluation parser."""
    print("\nTesting evaluation parser...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        
        interface = SimplifiedOCRInterface()
        
        # Test with sample evaluation content
        sample_evaluation = """
        # Document Processing Quality Report
        
        **Overall Score:** 85.5/100
        **Recommendation:** REVIEW
        
        ## Summary
        The document was processed successfully with minor issues.
        """
        
        result = interface._parse_evaluation_simple(sample_evaluation)
        
        assert "summary" in result, "Missing summary in result"
        assert "score" in result, "Missing score in result"
        assert "recommendation" in result, "Missing recommendation in result"
        assert result["score"] == "85.5/100", f"Wrong score: {result['score']}"
        assert result["recommendation"] == "REVIEW", f"Wrong recommendation: {result['recommendation']}"
        print("✅ Evaluation parser works correctly")
        
        # Test with empty content
        empty_result = interface._parse_evaluation_simple("")
        assert empty_result["score"] == "N/A", "Empty evaluation should return N/A"
        print("✅ Handles empty evaluation correctly")
        
        return True
    except Exception as e:
        print(f"❌ Evaluation parser test failed: {e}")
        return False

def test_response_creation():
    """Test response creation method."""
    print("\nTesting response creation...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        
        interface = SimplifiedOCRInterface()
        
        # Test response creation
        response = interface._create_response(
            content="Test content",
            summary="Test summary",
            status="<div>Test status</div>"
        )
        
        assert len(response) == 11, f"Response should have 11 elements, got {len(response)}"
        assert response[0] == "Test content", "Content mismatch"
        assert response[1] == "Test summary", "Summary mismatch"
        print("✅ Response creation works correctly")
        
        # Test default values
        default_response = interface._create_response()
        assert "*" in default_response[0], "Default content should have placeholder"
        print("✅ Default response values work")
        
        return True
    except Exception as e:
        print(f"❌ Response creation test failed: {e}")
        return False

def test_css_generation():
    """Test CSS generation."""
    print("\nTesting CSS generation...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        
        interface = SimplifiedOCRInterface()
        css = interface.get_css()
        
        assert css, "CSS is empty"
        assert ".gradio-container" in css, "Missing main container styles"
        assert ".status-box" in css, "Missing status box styles"
        assert ".primary-btn" in css, "Missing button styles"
        
        # Check that CSS is simplified
        css_lines = css.split('\n')
        print(f"✅ CSS has {len(css_lines)} lines (simplified from ~800)")
        
        return True
    except Exception as e:
        print(f"❌ CSS generation test failed: {e}")
        return False

def test_file_operations():
    """Test file download operations."""
    print("\nTesting file operations...")
    try:
        from ui_simplified import SimplifiedOCRInterface
        from summary_generator import SummaryGenerator
        from logger import ProcessingLogger
        
        interface = SimplifiedOCRInterface()
        
        # Test summary download with no content
        result = interface.download_summary()
        assert hasattr(result, 'update'), "Should return gradio update"
        print("✅ Empty summary download handled")
        
        # Test evaluation download with no content  
        result = interface.download_evaluation()
        assert hasattr(result, 'update'), "Should return gradio update"
        print("✅ Empty evaluation download handled")
        
        return True
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("SIMPLIFIED UI TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Interface Creation", test_interface_creation),
        ("Loading Messages", test_loading_messages),
        ("Evaluation Parser", test_evaluation_parser),
        ("Response Creation", test_response_creation),
        ("CSS Generation", test_css_generation),
        ("File Operations", test_file_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The simplified UI is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check for config
    try:
        from config import config
        if not config.validate():
            print("⚠️  Warning: Configuration not fully set up")
            print("Some tests may fail without API keys")
    except:
        print("⚠️  Warning: Could not load config")
    
    sys.exit(run_all_tests())
