"""
Gradio User Interface
Clean, modern UI for the OCR processor
"""

import gradio as gr
import base64
import os
import tempfile
import random
from pathlib import Path
from datetime import datetime
from processor_optimized import OptimizedDocumentProcessor as DocumentProcessor
from config import config
from summary_generator import SummaryGenerator
from utils import extract_document_title, get_recommendation_color

class OCRInterface:
    """Gradio interface for OCR processing."""
    
    # Quirky loading messages inspired by SimCity and other games
    LOADING_MESSAGES = [
        "Reticulating splines...",
        "Generating witty dialog...",
        "Swapping time and space...",
        "Spinning violently around the y-axis...",
        "Tokenizing real life...",
        "Bending the spoon...",
        "Filtering morale...",
        "Don't think of purple hippos...",
        "We need a new fuse...",
        "Have a good day.",
        "Upgrading Windows, your PC will restart several times...",
        "640K ought to be enough for anybody",
        "The architects are still drafting...",
        "The bits are breeding...",
        "We're building the buildings as fast as we can...",
        "Would you prefer chicken, steak, or tofu?",
        "Pay no attention to the man behind the curtain...",
        "Enjoying the elevator music?",
        "Please wait while the little elves draw your map...",
        "Don't worry - a few bits tried to escape, but we caught them...",
        "And dream of faster computers...",
        "Checking the gravitational constant in your locale...",
        "Go ahead -- hold your breath!",
        "Hum something loud while others stare...",
        "You're not in Kansas anymore...",
        "The server is powered by a lemon and two electrodes...",
        "We're testing your patience...",
        "As if you had any other choice...",
        "Follow the white rabbit...",
        "Why don't you order a sandwich?",
        "While the satellite moves into position...",
        "The bits are flowing slowly today...",
        "Dig on the 'X' for buried treasure... ARRR!",
        "It's still faster than you could draw it...",
        "The last time I tried this the monkey didn't survive. Let's hope it works better this time.",
        "I should have had a V8 this morning...",
        "My other loading screen is much faster.",
        "Testing on Timmy... We're going to need another Timmy.",
        "Reconfoobling energymotron...",
        "(Insert quarter)",
        "Are we there yet?",
        "Just count to 10...",
        "Why so serious?",
        "It's not you. It's me.",
        "Counting backwards from Infinity...",
        "Don't panic...",
        "Embiggening prototypes...",
        "Do not run! We are your friends!",
        "Do you come here often?",
        "Warning: Don't set yourself on fire.",
        "We're making you a cookie.",
        "Creating time-loop inversion field...",
        "Spinning the wheel of fortune...",
        "Loading the enchanted bunny...",
        "Computing chance of success...",
        "I'm sorry Dave, I can't do that.",
        "Looking for exact change...",
        "All your web browser are belong to us...",
        "All I really need is a kilobit...",
        "I feel like im supposed to be loading something...",
        "What do you call 8 Hobbits? A Hobbyte!",
        "Should have used a compiled language...",
        "Is this Windows?",
        "Adjusting flux capacitor...",
        "Please wait until the sloth starts moving...",
        "Don't break your screen yet!",
        "I swear it's almost done.",
        "Let's take a mindfulness minute...",
        "Unicorns are at the end of this road, I promise.",
        "Listening for the sound of one hand clapping...",
        "Keeping all the 1's and removing all the 0's...",
        "Putting the icing on the cake. The cake is not a lie...",
        "Cleaning off the cobwebs...",
        "Making sure all the i's have dots...",
        "We are not liable for any broken screens as a result of waiting.",
        "We need more dilithium crystals...",
        "Where did all the internets go?",
        "Connecting Neurotoxin Storage Tank...",
        "Granting wishes...",
        "Time flies when you're having fun...",
        "Get some coffee and come back in ten minutes...",
        "Spinning the hamster wheel...",
        "99 bottles of beer on the wall...",
        "Stay awhile and listen...",
        "Be careful not to step in the git-gui...",
        "You shall not pass! Yet...",
        "Load it and they will come...",
        "Convincing AI not to turn evil...",
        "There is no spoon. Because we are not done loading it...",
        "Your left thumb prints are being processed...",
        "Shaking the snow globe...",
        "Computing the secret to life, the universe, and everything...",
        "Mining some bitcoins...",
        "Downloading more RAM...",
        "Updating to Windows Vista...",
        "Deleting System32 folder...",
        "Hiding all the passwords under the rug...",
        "Alert! User detected. Please wait...",
        "Searching for plot device...",
        "Trying to sort in O(n)...",
        "Laughing at your browser's expectations...",
        "Sending data to the NS... I mean, our servers.",
        "Looking for sense of humour, please hold on...",
        "Please wait while the intern refills his coffee...",
        "A different error message? Finally, some progress!",
        "Hold on while we wrap up our git together...sorry",
        "Please hold on as we reheat our coffee...",
        "Kindly hold on as we convert this bug to a feature...",
        "Kindly hold on as our intern quits vim...",
        "Winter is coming...",
        "Installing dependencies...",
        "Switching to the latest JS framework...",
        "Distracted by cat gifs...",
        "Finding someone to hold my beer...",
        "BRB, working on my side project...",
        "@todo Insert witty loading message...",
        "Let's hope it's worth the wait...",
        "Aw, snap! Not..",
        "Ordering 1s and 0s...",
        "Dividing by zero...",
        "If I'm not back in five minutes, just wait longer...",
        "Web developers do it with <style>",
        "Optimizing the optimizer...",
        "Debugging the debugger...",
        "Reading Terms and Conditions for you...",
        "Digesting cookies...",
        "How about this weather, eh?",
        "Building a wall...",
        "Everything in this universe is either a potato or not a potato...",
        "The severity of the itch is inversely proportional to the ability to reach it.",
        "The shortest distance between two points is under construction.",
        "Counting to 1337... 1335... 1336... 1337!",
        "I'm not slacking off. My code's compiling.",
        "Compiling the compiler...",
        "Caching the cache...",
        "Checking if 2 + 2 still equals 4...",
        "Proving P=NP...",
        "Entangling superstrings...",
        "Twiddling thumbs...",
        "Searching for Schrodinger's Cat...",
        "Attempting to lock thread, please wait...",
        "Welcome to the desert of the real...",
        "Aligning covariance matrices...",
        "Constructing additional pylons...",
        "Roping some seaturtles...",
        "Locating the required gigapixels to render...",
        "Spinning up the hamster...",
        "Shovelling coal into the server...",
        "Programming the flux capacitor...",
        "The elves are having labor troubles...",
        "How did you get here?",
        "Wait, do you smell something burning?",
        "Computing the last digit of pi...",
        "Waiting for the system admin to hit enter...",
        "All your base are belong to us...",
        "Counting the sheep in the sky...",
        "We're going to need a bigger boat...",
        "Catching em' all...",
        "Constructing additional pylons..."
    ]
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.summary_generator = SummaryGenerator(self.processor.logger)
        self.current_summary = ""
        self.current_document_title = ""
        # Debug data storage
        self.raw_ocr_output = ""
    
    def _load_animation_html(self):
        """Load the processing animation with CSS-based message cycling."""
        # Get multiple messages for CSS animation cycling
        messages_sample = random.sample(self.LOADING_MESSAGES, min(25, len(self.LOADING_MESSAGES)))
        
        # Calculate animation duration (4.3 seconds per message - the ultimate sweet spot!)
        total_duration = len(messages_sample) * 4.3
        message_show_percent = (100 / len(messages_sample)) * 0.8  # Show for 80% of each message slot
        message_hide_percent = 100 / len(messages_sample)  # Hide at start of next message slot
        
        return f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; height: 100%; padding: 40px;">
            <style>
                @keyframes orbit {{
                    0% {{ transform: rotate(0deg) translateX(80px) rotate(0deg); }}
                    100% {{ transform: rotate(360deg) translateX(80px) rotate(-360deg); }}
                }}
                @keyframes pulse {{
                    0%, 100% {{ 
                        transform: scale(1);
                        opacity: 0.8;
                    }}
                    50% {{ 
                        transform: scale(1.1);
                        opacity: 1;
                    }}
                }}
                @keyframes glow {{
                    0%, 100% {{ 
                        box-shadow: 0 0 20px rgba(6, 182, 212, 0.6),
                                    0 0 40px rgba(6, 182, 212, 0.4),
                                    0 0 60px rgba(6, 182, 212, 0.2);
                    }}
                    50% {{ 
                        box-shadow: 0 0 30px rgba(6, 182, 212, 0.8),
                                    0 0 60px rgba(6, 182, 212, 0.6),
                                    0 0 90px rgba(6, 182, 212, 0.4);
                    }}
                }}
                @keyframes messageRotate {{
                    0%, {message_show_percent:.1f}% {{ opacity: 1; }}
                    {message_hide_percent:.1f}%, 100% {{ opacity: 0; }}
                }}
                .processing-container {{
                    position: relative;
                    width: 200px;
                    height: 200px;
                    margin: 20px auto;
                }}
                .central-orb {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 120px;
                    height: 120px;
                    margin: -60px 0 0 -60px;
                    background: radial-gradient(circle at 30% 30%, #22d3ee, #0891b2);
                    border-radius: 50%;
                    animation: pulse 4.3s ease-in-out infinite, glow 4.3s ease-in-out infinite;
                    box-shadow: 0 0 40px rgba(6, 182, 212, 0.6);
                }}
                .orbit-ring {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 160px;
                    height: 160px;
                    margin: -80px 0 0 -80px;
                    border: 2px solid rgba(6, 182, 212, 0.2);
                    border-radius: 50%;
                }}
                .orbiting-dot {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 20px;
                    height: 20px;
                    margin: -10px 0 0 -10px;
                    background: #06b6d4;
                    border-radius: 50%;
                    box-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
                }}
                .orbiting-dot-1 {{
                    animation: orbit 4.3s linear infinite;
                }}
                .orbiting-dot-2 {{
                    animation: orbit 4.3s linear infinite;
                    animation-delay: -1.43s;
                }}
                .orbiting-dot-3 {{
                    animation: orbit 4.3s linear infinite;
                    animation-delay: -2.87s;
                }}
                .cycling-messages {{
                    position: relative;
                    min-height: 24px;
                    width: 100%;
                    max-width: 600px;
                }}
                .cycling-messages span {{
                    position: absolute;
                    top: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 600px;
                    text-align: center;
                    opacity: 0;
                    white-space: nowrap;
                    animation: messageRotate {total_duration}s infinite;
                }}
                {"".join(f".cycling-messages span:nth-child({i+1}) {{ animation-delay: -{total_duration * i / len(messages_sample):.1f}s; }}" for i in range(len(messages_sample)))}
            </style>
            <div class="processing-container">
                <div class="orbit-ring"></div>
                <div class="central-orb"></div>
                <div class="orbiting-dot orbiting-dot-1"></div>
                <div class="orbiting-dot orbiting-dot-2"></div>
                <div class="orbiting-dot orbiting-dot-3"></div>
            </div>
            <h3 style="color: #06b6d4; margin-top: 30px; font-family: 'Montserrat Alternates', sans-serif; text-align: center;">Processing your document...</h3>
            <div class="cycling-messages" style="color: #94a3b8; font-family: 'Montserrat Alternates', sans-serif; text-align: center;">
                {"".join(f'<span>{message}</span>' for message in messages_sample)}
            </div>
        </div>
        """
    
    def handle_web_event(self, event_data_json: str):
        """Handle web events sent from frontend JavaScript - placeholder for future analytics."""
        return ""  # Return empty string to clear the hidden input
    
    def _extract_document_title(self, filename: str) -> str:
        """Extract a clean document title from filename."""
        return extract_document_title(filename)

    def _parse_evaluation_for_comparison(self, evaluation_content: str):
        """Parse evaluation report into components for side-by-side display."""
        try:
            if not evaluation_content or evaluation_content.strip() == "*No evaluation report available*":
                return (
                    "<div class='status-box'>No evaluation comparison available</div>",
                    "*No OpenAI evaluation available*",
                    "*No Anthropic evaluation available*", 
                    "<div class='status-box'>No evaluation metrics available</div>"
                )
            
            # Check if this is a comparison report
            if "Dual Evaluation Comparison Report" in evaluation_content:
                return self._parse_dual_evaluation(evaluation_content)
            else:
                # Single evaluation - put it in Anthropic column (primary)
                return self._parse_single_evaluation(evaluation_content)
                
        except Exception as e:
            return (
                f"<div class='status-box status-error'>Error parsing evaluation: {str(e)}</div>",
                "*Error parsing evaluation*",
                "*Error parsing evaluation*",
                "<div class='status-box status-error'>Evaluation parsing failed</div>"
            )
    
    def _parse_dual_evaluation(self, evaluation_content: str):
        """Parse dual evaluation comparison report."""
        print("DEBUG: Parsing dual evaluation content...")
        print(f"DEBUG: First 500 chars of content: {evaluation_content[:500]}")
        
        lines = evaluation_content.split('\n')
        
        # Extract sections
        openai_lines = []
        anthropic_lines = []
        current_section = None
        
        for line in lines:
            if "🤖 OpenAI GPT-4V Findings" in line:
                current_section = "openai"
                openai_lines.append("## OpenAI GPT-4V Findings")
            elif "🧠 Anthropic Claude Findings" in line:
                current_section = "anthropic"
                anthropic_lines.append("## Anthropic Claude Findings")
            elif "Final Recommendation" in line:
                current_section = None
            elif current_section == "openai":
                openai_lines.append(line)
            elif current_section == "anthropic":
                anthropic_lines.append(line)
        
        # Extract scores and recommendations from the summary section
        openai_score = self._extract_score_from_summary(evaluation_content, "OpenAI")
        anthropic_score = self._extract_score_from_summary(evaluation_content, "Anthropic")
        openai_rec = self._extract_recommendation_from_summary(evaluation_content, "OpenAI")  
        anthropic_rec = self._extract_recommendation_from_summary(evaluation_content, "Anthropic")
        
        # Create comparison summary HTML
        comparison_summary_html = f"""
        <div class='status-box'>
            <h3 style='text-align: center; margin-bottom: 20px;'>📊 Evaluation Comparison</h3>
            <div style='display: flex; justify-content: space-around; margin-bottom: 15px;'>
                <div style='text-align: center; padding: 15px; background: rgba(37, 99, 235, 0.1); border-radius: 8px; flex: 1; margin-right: 10px;'>
                    <h4 style='color: #2563eb; margin: 0;'>🤖 OpenAI GPT-4V</h4>
                    <div style='font-size: 24px; font-weight: bold; margin: 5px 0;'>{openai_score}</div>
                    <div style='color: {get_recommendation_color(openai_rec)};'>{openai_rec}</div>
                </div>
                <div style='text-align: center; padding: 15px; background: rgba(124, 58, 237, 0.1); border-radius: 8px; flex: 1; margin-left: 10px;'>
                    <h4 style='color: #7c3aed; margin: 0;'>🧠 Anthropic Claude</h4>
                    <div style='font-size: 24px; font-weight: bold; margin: 5px 0;'>{anthropic_score}</div>
                    <div style='color: {get_recommendation_color(anthropic_rec)};'>{anthropic_rec}</div>
                </div>
            </div>
        </div>
        """
        
        # Create stats HTML
        evaluation_stats_html = f"""
        <div class='status-box status-success'>
            <h4>📊 Comparison Stats</h4>
            <p><strong>Agreement:</strong> {self._extract_agreement(evaluation_content)}</p>
            <p><strong>Primary:</strong> {anthropic_rec} (Anthropic)</p>
            <p><strong>Method:</strong> Dual Evaluation</p>
        </div>
        """
        
        # Convert to markdown
        openai_content = '\n'.join(openai_lines) if openai_lines else "*No OpenAI findings available*"
        anthropic_content = '\n'.join(anthropic_lines) if anthropic_lines else "*No Anthropic findings available*"
        
        return comparison_summary_html, openai_content, anthropic_content, evaluation_stats_html
    
    def _parse_single_evaluation(self, evaluation_content: str):
        """Parse single evaluation report."""
        score = self._extract_score(evaluation_content, "Overall Score")
        recommendation = self._extract_recommendation(evaluation_content, "Recommendation")
        
        comparison_summary_html = f"""
        <div class='status-box'>
            <h3 style='text-align: center; margin-bottom: 20px;'>📊 Single Evaluation</h3>
            <div style='text-align: center; padding: 20px; background: rgba(124, 58, 237, 0.1); border-radius: 8px;'>
                <h4 style='color: #7c3aed; margin: 0;'>Quality Report</h4>
                <div style='font-size: 24px; font-weight: bold; margin: 5px 0;'>{score}</div>
                <div style='color: {get_recommendation_color(recommendation)};'>{recommendation}</div>
            </div>
        </div>
        """
        
        evaluation_stats_html = f"""
        <div class='status-box status-success'>
            <h4>📊 Evaluation Metrics</h4>
            <p><strong>Score:</strong> {score}</p>
            <p><strong>Recommendation:</strong> {recommendation}</p>
            <p><strong>Method:</strong> Single Evaluation</p>
        </div>
        """
        
        return comparison_summary_html, "*Single evaluation mode*", evaluation_content, evaluation_stats_html
    
    def _extract_score(self, content: str, marker: str) -> str:
        """Extract score from evaluation content."""
        lines = content.split('\n')
        
        # Debug: log what we're looking for
        print(f"DEBUG: Looking for score with marker: '{marker}'")
        
        for line in lines:
            # More flexible score extraction patterns
            if "Score:" in line and ("OpenAI" in marker or "Anthropic" in marker or "Overall" in marker):
                try:
                    # Handle formats like "**Score:** 85.0/100"
                    if "**Score:**" in line:
                        score_part = line.split("**Score:**")[1].strip()
                        score = score_part.split('/')[0].strip()
                        return f"{score}/100"
                    # Handle formats like "Score: 85.0/100"
                    elif "Score:" in line:
                        score_part = line.split("Score:")[1].strip()
                        score = score_part.split('/')[0].strip()
                        return f"{score}/100"
                except Exception as e:
                    print(f"DEBUG: Score parsing failed for line '{line}': {e}")
                    continue
            
            # Also try pattern matching without marker for dual evaluation format
            if ("🤖 OpenAI" in line or "🧠 Anthropic" in line) and "Score:" in line:
                try:
                    score_part = line.split("Score:")[1].strip()
                    score = score_part.split(' ')[0].strip()  # Take first part before space
                    return score
                except Exception as e:
                    print(f"DEBUG: Direct score parsing failed for line '{line}': {e}")
                    continue
        
        print(f"DEBUG: No score found for marker '{marker}'")
        return "N/A"
    
    def _extract_recommendation(self, content: str, marker: str) -> str:
        """Extract recommendation from evaluation content."""
        lines = content.split('\n')
        
        # Debug: log what we're looking for  
        print(f"DEBUG: Looking for recommendation with marker: '{marker}'")
        
        for line in lines:
            # More flexible recommendation extraction patterns
            if "Recommendation:" in line and ("OpenAI" in marker or "Anthropic" in marker or "Recommendation" in marker):
                try:
                    # Handle formats like "**Recommendation:** REVIEW"
                    if "**Recommendation:**" in line:
                        rec = line.split("**Recommendation:**")[1].strip()
                        return rec
                    # Handle formats like "Recommendation: REVIEW"
                    elif "Recommendation:" in line:
                        rec = line.split("Recommendation:")[1].strip()
                        return rec
                except Exception as e:
                    print(f"DEBUG: Recommendation parsing failed for line '{line}': {e}")
                    continue
                    
            # Also try pattern matching for dual evaluation format
            if ("🤖 OpenAI" in line or "🧠 Anthropic" in line) and "Recommendation:" in line:
                try:
                    rec_part = line.split("Recommendation:")[1].strip()
                    rec = rec_part.split(' ')[0].strip()  # Take first word
                    return rec
                except Exception as e:
                    print(f"DEBUG: Direct recommendation parsing failed for line '{line}': {e}")
                    continue
        
        print(f"DEBUG: No recommendation found for marker '{marker}'")
        return "UNKNOWN"
    
    def _extract_score_from_summary(self, content: str, provider: str) -> str:
        """Extract score from evaluation comparison summary section."""
        lines = content.split('\n')
        
        # Look for the evaluation method comparison section, then find provider-specific scores
        in_comparison_section = False
        in_provider_subsection = False
        
        for line in lines:
            # Check if we're in the evaluation method comparison section
            if "Evaluation Method Comparison" in line:
                in_comparison_section = True
                continue
            elif in_comparison_section and line.startswith("## ") and "Evaluation Method Comparison" not in line:
                in_comparison_section = False
                continue
                
            # If we're in the comparison section, look for provider subsections
            if in_comparison_section:
                if f"🤖 {provider} GPT-4V Evaluation" in line or f"🧠 {provider} Claude Evaluation" in line:
                    in_provider_subsection = True
                    continue
                elif line.startswith("### ") and provider not in line:
                    in_provider_subsection = False
                    continue
                    
                # If we're in the right provider subsection, look for score
                if in_provider_subsection and ("**Score:**" in line or "Score:" in line):
                    try:
                        # Handle formats like "**Score:** 85.0/100"
                        if "**Score:**" in line:
                            score_part = line.split("**Score:**")[1].strip()
                            score = score_part.split('/')[0].strip()
                            return f"{score}/100"
                        # Handle formats like "Score: 85.0/100"
                        elif "Score:" in line:
                            score_part = line.split("Score:")[1].strip()
                            score = score_part.split('/')[0].strip()
                            return f"{score}/100"
                    except Exception as e:
                        print(f"DEBUG: Summary score parsing failed for line '{line}': {e}")
                        continue
        
        print(f"DEBUG: No summary score found for provider '{provider}' in comparison section")
        print(f"DEBUG: Content preview: {content[:500]}")
        return "N/A"
    
    def _extract_recommendation_from_summary(self, content: str, provider: str) -> str:
        """Extract recommendation from evaluation comparison summary section."""
        lines = content.split('\n')
        
        # Look for the evaluation method comparison section, then find provider-specific recommendations
        in_comparison_section = False
        in_provider_subsection = False
        
        for line in lines:
            # Check if we're in the evaluation method comparison section
            if "Evaluation Method Comparison" in line:
                in_comparison_section = True
                continue
            elif in_comparison_section and line.startswith("## ") and "Evaluation Method Comparison" not in line:
                in_comparison_section = False
                continue
                
            # If we're in the comparison section, look for provider subsections
            if in_comparison_section:
                if f"🤖 {provider} GPT-4V Evaluation" in line or f"🧠 {provider} Claude Evaluation" in line:
                    in_provider_subsection = True
                    continue
                elif line.startswith("### ") and provider not in line:
                    in_provider_subsection = False
                    continue
                    
                # If we're in the right provider subsection, look for recommendation
                if in_provider_subsection and ("**Recommendation:**" in line or "Recommendation:" in line):
                    try:
                        # Handle formats like "**Recommendation:** REVIEW"
                        if "**Recommendation:**" in line:
                            rec_part = line.split("**Recommendation:**")[1].strip()
                            # Remove any trailing text after whitespace
                            return rec_part.split()[0] if rec_part else "UNKNOWN"
                        # Handle formats like "Recommendation: REVIEW"
                        elif "Recommendation:" in line:
                            rec_part = line.split("Recommendation:")[1].strip()
                            # Remove any trailing text after whitespace
                            return rec_part.split()[0] if rec_part else "UNKNOWN"
                    except Exception as e:
                        print(f"DEBUG: Summary recommendation parsing failed for line '{line}': {e}")
                        continue
        
        print(f"DEBUG: No summary recommendation found for provider '{provider}' in comparison section")
        print(f"DEBUG: Content preview: {content[:500]}")
        return "UNKNOWN"
    
    def _extract_agreement(self, content: str) -> str:
        """Extract agreement level from comparison report."""
        lines = content.split('\n')
        for line in lines:
            if "Agreement Level:" in line:
                try:
                    agreement = line.split("Agreement Level:")[1].strip()
                    return agreement
                except:
                    pass
        return "Unknown"

    def get_css(self) -> str:
        """Get CSS styling for the interface."""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Montserrat+Alternates:wght@400;500;600;700;800&display=swap');
        
        /* Main Container with Modern Gradient Background */
        .gradio-container { 
            max-width: 100% !important; 
            margin: 0 auto !important;
            font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            background: linear-gradient(135deg, #1a1f2e 0%, #2d1b69 25%, #1a1f2e 50%, #402d8b 75%, #1a1f2e 100%) !important;
            min-height: 100vh !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* Animated Gradient Orbs for Glassmorphism Background */
        .gradio-container::before {
            content: '';
            position: absolute;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(147, 51, 234, 0.4) 0%, transparent 70%);
            top: -200px;
            right: -200px;
            animation: float 20s ease-in-out infinite;
        }
        
        .gradio-container::after {
            content: '';
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.3) 0%, transparent 70%);
            bottom: -150px;
            left: -150px;
            animation: float 15s ease-in-out infinite reverse;
        }
        
        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.05); }
            66% { transform: translate(-20px, 20px) scale(0.95); }
        }
        
        /* Glassmorphic Header */
        .main-header { 
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            padding: 2.5rem 2rem; 
            border-radius: 24px; 
            color: #F1F5F9; 
            text-align: center; 
            margin-bottom: 2rem;
            box-shadow: 
                0 8px 32px rgba(6, 182, 212, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            z-index: 10;
        }
        
        .main-header h1 {
            margin: 0 0 1rem 0;
            font-size: 2.5rem;
            font-weight: 500;
            font-family: 'Montserrat Alternates', sans-serif !important;
            background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 50%, #67e8f9 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 4px rgba(6, 182, 212, 0.3));
        }
        
        /* Glassmorphic Left Panel */
        .left-panel {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
            border-radius: 20px !important;
            padding: 1.5rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            position: relative;
            z-index: 10;
            width: 100% !important;
        }
        
        .section-header {
            font-family: 'Montserrat Alternates', sans-serif !important;
            font-size: 1.2rem;
            font-weight: 600;
            color: #f0f9ff;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(6, 182, 212, 0.3);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        /* Glassmorphic Status Box */
        .status-box { 
            background: rgba(255, 255, 255, 0.04) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 16px; 
            padding: 1rem 1.25rem; 
            margin: 1rem 0;
            font-weight: 500;
            color: #f0f9ff;
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .status-success { 
            background: rgba(16, 185, 129, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            color: #6ee7b7; 
            border-color: rgba(16, 185, 129, 0.3);
            box-shadow: 
                0 4px 16px rgba(16, 185, 129, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .status-error { 
            background: rgba(239, 68, 68, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            color: #fca5a5; 
            border-color: rgba(239, 68, 68, 0.3);
            box-shadow: 
                0 4px 16px rgba(239, 68, 68, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .status-processing { 
            background: rgba(6, 182, 212, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            color: #67e8f9; 
            border-color: rgba(6, 182, 212, 0.3);
            box-shadow: 
                0 4px 16px rgba(6, 182, 212, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }
        
        /* Glassmorphic Metric Cards */
        .metric-card {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            background: rgba(255, 255, 255, 0.05) !important;
            transform: translateY(-2px);
            box-shadow: 
                0 8px 24px rgba(6, 182, 212, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
            filter: drop-shadow(0 1px 2px rgba(6, 182, 212, 0.2));
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: #cbd5e1;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Glassmorphic Console */
        .console { 
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: #e2e8f0 !important; 
            font-family: 'Fira Code', 'Courier New', monospace !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important;
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
        }
        
        /* Glassmorphic Button Styles */
        .primary-btn, .secondary-btn {
            font-weight: 600 !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-size: 14px !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* Primary Button - Glassmorphic with Gradient */
        .primary-btn {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.9) 0%, rgba(34, 211, 238, 0.9) 100%) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 
                0 4px 16px rgba(6, 182, 212, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
        }
        
        .primary-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .primary-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 
                0 8px 24px rgba(147, 51, 234, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        }
        
        .primary-btn:hover::before {
            left: 100%;
        }
        
        .primary-btn:active {
            transform: translateY(0) !important;
            box-shadow: 
                0 2px 8px rgba(147, 51, 234, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Secondary Button - Pure Glassmorphic */
        .secondary-btn {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: #a5f3fc !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        }
        
        .secondary-btn:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(6, 182, 212, 0.3) !important;
            transform: translateY(-1px) !important;
            box-shadow: 
                0 6px 20px rgba(6, 182, 212, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            color: #67e8f9 !important;
        }
        
        .secondary-btn:active {
            transform: translateY(0) !important;
            box-shadow: 
                0 2px 8px rgba(6, 182, 212, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        }
        
        /* Disabled Button State */
        .primary-btn:disabled, .secondary-btn:disabled {
            opacity: 0.5 !important;
            cursor: not-allowed !important;
            transform: none !important;
            filter: grayscale(0.5) !important;
        }
        
        /* Button Focus States */
        .primary-btn:focus, .secondary-btn:focus {
            outline: 2px solid rgba(6, 182, 212, 0.5) !important;
            outline-offset: 2px !important;
        }
        
        /* Additional Glassmorphic Elements */
        input, textarea, select {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f0f9ff !important;
            transition: all 0.3s ease !important;
        }
        
        input:focus, textarea:focus, select:focus {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(6, 182, 212, 0.4) !important;
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
            outline: none !important;
        }
        
        /* Tabs with Glassmorphism */
        .tabs {
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border-radius: 16px !important;
            padding: 4px !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        /* Right Panel Glassmorphism */
        .gr-panel {
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 20px !important;
        }
        
        /* Markdown Content Area */
        .markdown {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
        }
        
        /* Override Gradio progress bar styling */
        .progress-container, .progress-level-inner {
            background: rgba(6, 182, 212, 0.2) !important;
            border-color: rgba(6, 182, 212, 0.3) !important;
        }
        
        .progress-text, .progress-level-inner {
            color: #67e8f9 !important;
        }
        
        /* Progress bar styling */
        .gr-progress {
            background: rgba(6, 182, 212, 0.1) !important;
            border: 1px solid rgba(6, 182, 212, 0.3) !important;
        }
        
        .gr-progress .progress-bar {
            background: linear-gradient(90deg, #06b6d4, #67e8f9) !important;
        }
        
        /* Additional Gradio progress styling overrides */
        .progress-level, .progress-level-inner, .progress-bar {
            background: linear-gradient(90deg, #06b6d4, #67e8f9) !important;
        }
        
        .progress-text, .progress-label {
            color: #67e8f9 !important;
            font-family: 'Montserrat Alternates', sans-serif !important;
        }
        
        /* Ensure all progress-related elements use blue theme */
        div[class*="progress"] {
            color: #67e8f9 !important;
        }
        """
    
    def process_wrapper(self, uploaded_file, page_ranges_str):
        """Wrapper for document processing with UI updates."""
        # start every run with a clean abort flag
        self.processor.clear_abort()
        
        if not uploaded_file:
            return self._no_file_response()
        
        yield self._processing_state()
        
        # Add periodic abort checking during processing
        try:
            # DELETE these 3 lines (they read the stale flag before process_document clears it)
            # if self.processor.is_abort_requested():
            #     yield self._aborted_response()
            #     return

            result = self.processor.process_document(
                uploaded_file,
                page_ranges_str if page_ranges_str and page_ranges_str.strip() else None
            )

            if result.status == "Aborted":
                yield self._aborted_response()
                return

            metrics_html = self._generate_metrics(result)
            analytics_html = self._generate_analytics(result)
            status_html = self._generate_status(result)
            
            # Generate summary
            self.current_document_title = extract_document_title(uploaded_file.name) if uploaded_file else "Document"
            summary_content, summary_success = self.summary_generator.generate_summary(result.content, self.current_document_title)
            self.current_summary = summary_content
            
            # Generate summary statistics
            if summary_success:
                stats = self.summary_generator.get_summary_stats(summary_content, result.content)
                summary_stats_html = f"""
                <div class='status-box status-success'>
                    <h4>📋 Summary Statistics</h4>
                    <p><strong>Summary Length:</strong> {stats['summary_words']} words</p>
                    <p><strong>Compression:</strong> {stats['compression_ratio']}% of original</p>
                    <p><strong>Method:</strong> {"AI-Powered" if stats['ai_powered'] else "Keyword-Based"}</p>
                    <p><strong>Focus:</strong> Benefits & Eligibility</p>
                </div>
                """
            else:
                summary_stats_html = "<div class='status-box status-error'>❌ Summary generation failed</div>"
            
            # Parse evaluation report for side-by-side display
            evaluation_content = result.evaluation_report if hasattr(result, 'evaluation_report') and result.evaluation_report else "*No evaluation report available*"
            self.current_evaluation = evaluation_content  # Store for download
            
            # Parse evaluation report into components
            comparison_summary_html, openai_content, anthropic_content, evaluation_stats_html = self._parse_evaluation_for_comparison(evaluation_content)
            
            # Capture debug data from processing logs
            raw_ocr_data = self._extract_raw_ocr_from_logs()
            
            yield (
                result.content,                 # Markdown
                summary_content,                # Summary Markdown  
                summary_stats_html,             # Summary Stats HTML
                comparison_summary_html,        # Evaluation Comparison Summary
                openai_content,                 # OpenAI Evaluation Markdown
                anthropic_content,              # Anthropic Evaluation Markdown
                evaluation_stats_html,          # Evaluation Stats HTML
                status_html,                    # Status HTML
                metrics_html,                   # Metrics HTML
                result.output_file,             # File
                analytics_html,                 # Analytics HTML
                gr.update(visible=True, interactive=True),        # Clear visible
                gr.update(visible=False),       # Abort hidden
                gr.update(visible=False),       # Processing animation hidden
                raw_ocr_data                    # Raw Vision OCR Output
            )
            
        except Exception as e:
            yield self._error_response(str(e))
    
    def _no_file_response(self):
        """Response when no file is uploaded."""
        return (
            "*Please upload a PDF file to begin processing.*",                 # Markdown
            "*Benefits and eligibility summary will appear here after processing...*",  # Summary
            "<div class='status-box'>Summary statistics will appear here...</div>",      # Summary Stats
            "<div class='status-box'>Upload a document to see evaluation comparison...</div>", # Evaluation Comparison Summary
            "*OpenAI evaluation results will appear here...*",                          # OpenAI Evaluation
            "*Anthropic evaluation results will appear here...*",                       # Anthropic Evaluation
            "<div class='status-box'>Evaluation statistics will appear here...</div>",  # Evaluation Stats
            "<div class='status-box status-error'>❌ No file uploaded</div>",  # Status HTML
            "<div class='status-box'>No metrics available</div>",              # Metrics HTML
            gr.update(value=None),                                             # File
            "<div class='status-box status-error'>Please upload a PDF file</div>",  # Analytics HTML
            gr.update(visible=False),                                          # Clear
            gr.update(visible=False),                                          # Abort
            gr.update(visible=False),                                          # Processing animation hidden
            "Raw OCR output will appear here after processing..."             # Raw OCR Output
        )
    
    def _processing_state(self):
        """Response during processing."""
        return (
            "*🚀 Processing started...*",                                      # Markdown
            "*🔄 Generating summary...*",                                      # Summary
            "<div class='status-box status-processing'>⏳ Processing summary...</div>",    # Summary Stats
            "<div class='status-box status-processing'>⏳ Running dual evaluation...</div>", # Evaluation Comparison Summary
            "*🔄 OpenAI evaluation in progress...*",                          # OpenAI Evaluation
            "*🔄 Anthropic evaluation in progress...*",                       # Anthropic Evaluation
            "<div class='status-box status-processing'>⏳ Processing evaluation...</div>",  # Evaluation Stats
            "<div class='status-box status-processing'>⏳ Processing document...</div>",  # Status HTML
            "<div class='status-box status-processing'>⏳ Processing in progress...</div>",  # Metrics HTML
            gr.update(value=None),                                             # File
            "<div class='status-box status-processing'>Processing in progress...</div>",   # Analytics HTML
            gr.update(visible=True, interactive=False),                                           # Clear visible
            gr.update(visible=True),                                           # Abort visible
            gr.update(value=self._load_animation_html(), visible=True),  # Processing animation visible with random message
            "🔄 Processing..."                                                # Raw OCR Output
        )
    
    def _error_response(self, error_msg):
        """Response for processing errors."""
        return (
            f"*❌ Processing Error: {error_msg}*",                              # Markdown
            "*❌ Summary generation failed due to processing error.*",          # Summary
            "<div class='status-box status-error'>❌ Summary unavailable</div>", # Summary Stats
            "<div class='status-box status-error'>❌ Evaluation comparison failed</div>", # Evaluation Comparison Summary
            "*❌ OpenAI evaluation failed due to processing error.*",           # OpenAI Evaluation
            "*❌ Anthropic evaluation failed due to processing error.*",        # Anthropic Evaluation
            "<div class='status-box status-error'>❌ Evaluation unavailable</div>", # Evaluation Stats
            f"<div class='status-box status-error'>❌ Error: {error_msg}</div>", # Status HTML
            "<div class='status-box status-error'>❌ Processing failed</div>",   # Metrics HTML
            gr.update(value=None),                                              # File
            f"<div class='status-box status-error'>Error: {error_msg}</div>",   # Analytics HTML
            gr.update(visible=True, interactive=True),                                            # Clear visible
            gr.update(visible=False),                                            # Abort visible
            gr.update(visible=False),                                            # Processing animation hidden
            f"❌ Processing failed: {error_msg}"                              # Raw OCR Output
        )
    
    def _aborted_response(self):
        """Response when processing is aborted."""
        return (
            "**⚠️ Processing was aborted by user.**",                           # Markdown
            "*⚠️ Summary generation was aborted.*",                             # Summary
            "<div class='status-box status-error'>⚠️ Summary aborted</div>",    # Summary Stats
            "<div class='status-box status-error'>⚠️ Evaluation aborted</div>", # Evaluation Comparison Summary
            "*⚠️ OpenAI evaluation was aborted.*",                              # OpenAI Evaluation
            "*⚠️ Anthropic evaluation was aborted.*",                           # Anthropic Evaluation
            "<div class='status-box status-error'>⚠️ Evaluation aborted</div>", # Evaluation Stats
            "<div class='status-box status-error'>⚠️ Processing aborted by user</div>", # Status HTML
            "<div class='status-box'>Processing was aborted</div>",             # Metrics HTML
            gr.update(value=None),                                              # File
            "<div class='status-box status-error'>Processing was aborted by user</div>", # Analytics HTML
            gr.update(visible=True, interactive=True),                                            # Clear visible
            gr.update(visible=False),                                           # Abort hidden
            gr.update(visible=False),                                           # Processing animation hidden
            "⚠️ Processing was aborted by user"                                # Raw OCR Output
        )
    
    def _generate_metrics(self, result):
        """Generate metrics HTML."""
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{result.processing_time:.1f}s</div>
                <div class="metric-label">Total Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.vision_calls_used}</div>
                <div class="metric-label">Vision Calls</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{"✓" if result.success else "✗"}</div>
                <div class="metric-label">Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(result.content.split()) if result.content else 0}</div>
                <div class="metric-label">Words</div>
            </div>
        </div>
        """
    
    def _generate_analytics(self, result):
        """Generate detailed analytics HTML."""
        vision_efficiency = f"{(result.vision_calls_used / max(result.pages_processed, 1)):.1f}" if result.pages_processed > 0 else "0"
        
        return f"""
        <div class="status-box {'status-success' if result.success else 'status-error'}">
            <h4>📊 Processing Analytics</h4>
            <p><strong>Pages:</strong> {result.pages_processed}</p>
            <p><strong>Vision calls:</strong> {result.vision_calls_used} ({vision_efficiency} per page)</p>
            <p><strong>Words extracted:</strong> {len(result.content.split()) if result.content else 0}</p>
            <p><strong>Status:</strong> {"Success" if result.success else "Failed"}</p>
        </div>
        """
    
    def _generate_status(self, result):
        """Generate status HTML."""
        if result.success:
            return "<div class='status-box status-success'>✅ Processing completed successfully!</div>"
        else:
            return f"<div class='status-box status-error'>❌ Processing failed: {result.status}</div>"
    
    def clear_all(self):
        """Clear all interface elements."""
        self.processor.clear_abort()
        self.processor.clear_logs()
        # Clear debug data from OCR engine if available
        if hasattr(self.processor, 'ocr_engine') and self.processor.ocr_engine:
            self.processor.ocr_engine.clear_debug_data()
        self.current_summary = ""
        self.current_document_title = ""
        self.current_evaluation = ""
        return (
            "*Processed document content will appear here after processing...*", # Markdown
            "*Benefits and eligibility summary will appear here after processing...*",  # Summary
            "<div class='status-box'>Summary statistics will appear here...</div>",      # Summary Stats
            "<div class='status-box'>Evaluation comparison will appear here after processing...</div>", # Evaluation Comparison Summary
            gr.update(value="*OpenAI evaluation results will appear here...*"),         # OpenAI Evaluation
            gr.update(value="*Anthropic evaluation results will appear here...*"),      # Anthropic Evaluation
            "<div class='status-box'>Evaluation metrics will appear here...</div>",     # Evaluation Stats
            "<div class='status-box'>⏳ Ready to process document...</div>",     # Status HTML
            "<div class='status-box'>Metrics will appear during processing...</div>",  # Metrics HTML
            gr.update(value=None),                                               # File output cleared
            "<div class='status-box'>Analytics will appear after processing...</div>", # Analytics HTML
            gr.update(visible=False, interactive=True),                                            # Clear hidden
            gr.update(visible=False),                                             # Abort hidden
            gr.update(value=""),                                                # Page ranges cleared
            gr.update(value=None),                                               # PDF cleared
            gr.update(visible=False),                                            # Processing animation hidden
            "Raw OCR output will appear here after processing..."              # Raw OCR Output cleared
        )
    
    def abort_processing(self):
        """Abort processing."""
        self.processor.abort_processing()
        return (
            gr.update(),  # content: keep current
            gr.update(),  # summary: keep current
            gr.update(),  # summary stats: keep current
            gr.update(),  # evaluation comparison summary: keep current
            gr.update(),  # openai evaluation: keep current
            gr.update(),  # anthropic evaluation: keep current
            gr.update(),  # evaluation stats: keep current
            "<div class='status-box status-error'>🛑 Abort requested…</div>",       # status
            "<div class='status-box'>Waiting for current step to stop…</div>",      # metrics
            gr.update(),  # file unchanged
            "<div class='status-box status-error'>Aborting current run…</div>",     # analytics
            gr.update(visible=True, interactive=False),   # Clear visible but disabled until abort confirmed
            gr.update(visible=True, interactive=False),   # Abort stays visible but disabled (pressed look)
            gr.update(visible=False)                      # Processing animation hidden
        )
    
    def download_summary_md(self):
        """Download summary as Markdown file."""
        if not self.current_summary:
            return gr.update(value=None, visible=False)
        
        try:
            md_path = self.summary_generator.save_summary_markdown(
                self.current_summary, 
                self.current_document_title or "document"
            )
            
            if md_path:
                return gr.update(value=md_path, visible=True)
            else:
                return gr.update(value=None, visible=False)
                
        except Exception as e:
            print(f"Error downloading MD summary: {e}")
            return gr.update(value=None, visible=False)
    
    def download_summary_pdf(self):
        """Download summary as PDF file."""
        if not self.current_summary:
            return gr.update(value=None, visible=False)
        
        try:
            pdf_path = self.summary_generator.save_summary_pdf(
                self.current_summary,
                self.current_document_title or "document"
            )
            
            if pdf_path:
                return gr.update(value=pdf_path, visible=True)
            else:
                return gr.update(value=None, visible=False)
                
        except Exception as e:
            print(f"Error downloading PDF summary: {e}")
            return gr.update(value=None, visible=False)
    
    def download_evaluation_report(self):
        """Download evaluation report as Markdown file."""
        if not hasattr(self, 'current_evaluation') or not self.current_evaluation:
            return gr.update(value=None, visible=False)
        
        try:
            # Save evaluation report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            eval_filename = f"{self.current_document_title or 'document'}_evaluation_{timestamp}.md"
            eval_path = Path(tempfile.gettempdir()) / eval_filename
            
            with open(eval_path, 'w', encoding='utf-8') as f:
                f.write(self.current_evaluation)
            
            return gr.update(value=str(eval_path), visible=True)
            
        except Exception as e:
            print(f"Error downloading evaluation report: {e}")
            return gr.update(value=None, visible=False)

    def create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Document Ingestion - Agent Edition", css=self.get_css()) as demo:
            
            # Header
            gr.HTML("""
                <div class="main-header">
                    <h1>Document Ingestion</h1>
                    <p style="font-size: 1.2em; color: #34d399;">Agent-powered OCR with intelligent formatting</p>
                    <div style="margin-top: 0.5rem; font-size: 0.9em; opacity: 0.8;">
                        <span style="color: #60a5fa;">OpenAI Vision</span> • 
                        <span style="color: #c084fc;">Anthropic Claude</span> • 
                        <span style="color: #fbbf24;">Multi-Agent Pipeline</span>
                    </div>
                </div>
            """)
            
            with gr.Row():
                # Left Panel - Controls
                with gr.Column(scale=1, elem_classes="left-panel"):
                    
                    gr.HTML('<div class="section-header">📁 Upload Document</div>')
                    pdf_input = gr.File(label="File type: PDF, MD, or TXT", file_types=[".pdf", ".md", ".markdown",".txt"])
                    
                    # Page ranges input
                    page_ranges_input = gr.Textbox(
                        label="Page Ranges (Optional)",
                        placeholder="e.g., 1-5, 10, 15-20 (leave blank for all pages)",
                        info="Specify pages to process. Examples: '1-5' for pages 1-5, '1,3,5' for specific pages, '1-3,10-15' for multiple ranges"
                    )
                    
                    with gr.Row():
                        process_btn = gr.Button("🚀 Process", variant="primary", elem_classes="primary-btn")
                        clear_btn = gr.Button("🗑️ Clear", variant="secondary", visible=False, elem_classes="secondary-btn")
                        abort_btn = gr.Button("🚫 Abort", variant="secondary", visible=False, elem_classes="secondary-btn")
                    
                    gr.HTML('<div class="section-header">📊 Status</div>')
                    status_output = gr.HTML(value="<div class='status-box'>⏳ Ready to process document...</div>")
                    
                    gr.HTML('<div class="section-header">📈 Metrics</div>')
                    metrics_output = gr.HTML(value="<div class='status-box'>Metrics will appear during processing...</div>")
                    
                    gr.HTML('<div class="section-header">⚙️ Configuration</div>')
                    gr.HTML(f"""
                        <div class="status-box">
                            <p><strong>DPI:</strong> {config.dpi}</p>
                            <p><strong>Model Used:</strong> {config.openai_model}</p>
                        </div>
                    """)
                
                # Right Panel - Results
                with gr.Column(scale=2):
                    
                    with gr.Tabs():
                        with gr.Tab("📄 Document"):
                            # Processing animation with your blue robot orb video
                            processing_animation = gr.HTML(
                                value="",
                                visible=False
                            )
                            content_output = gr.Markdown(
                                value="*Processed document content will appear here...*", 
                                show_copy_button=True
                            )
                        
                        with gr.Tab("📋 Summary"):
                            with gr.Row():
                                with gr.Column(scale=2):
                                    summary_output = gr.Markdown(
                                        value="*Benefits and eligibility summary will appear here after processing...*",
                                        show_copy_button=True
                                    )
                                with gr.Column(scale=1):
                                    gr.HTML("<h4>📊 Summary Options</h4>")
                                    summary_stats_output = gr.HTML(
                                        value="<div class='status-box'>Summary statistics will appear here...</div>"
                                    )
                                    with gr.Row():
                                        download_md_btn = gr.Button("📝 Download MD", variant="secondary", size="sm")
                                        download_pdf_btn = gr.Button("📄 Download PDF", variant="secondary", size="sm")
                                    summary_download_output = gr.File(label="Summary Downloads", interactive=False, visible=False)
                        
                        with gr.Tab("🔍 Quality Report"):
                            # Comparison summary at top
                            with gr.Row():
                                evaluation_comparison_summary = gr.HTML(
                                    value="<div class='status-box'>Evaluation comparison will appear here after processing...</div>"
                                )
                            
                            # Side-by-side comparison
                            with gr.Row():
                                with gr.Column(scale=1):
                                    gr.HTML("<h4 style='text-align: center; color: #2563eb;'>🤖 OpenAI GPT-4V Results</h4>")
                                    openai_evaluation = gr.Markdown(
                                        value="*OpenAI evaluation results will appear here...*",
                                        show_copy_button=True
                                    )
                                
                                with gr.Column(scale=1):
                                    gr.HTML("<h4 style='text-align: center; color: #7c3aed;'>🧠 Anthropic Claude Results</h4>")
                                    anthropic_evaluation = gr.Markdown(
                                        value="*Anthropic evaluation results will appear here...*",
                                        show_copy_button=True
                                    )
                            
                            # Download options at bottom
                            with gr.Row():
                                with gr.Column(scale=2):
                                    evaluation_stats_output = gr.HTML(
                                        value="<div class='status-box'>Evaluation metrics will appear here...</div>"
                                    )
                                with gr.Column(scale=1):
                                    download_eval_btn = gr.Button("📥 Download Full Report", variant="secondary", size="sm")
                                    evaluation_download_output = gr.File(label="Evaluation Report", interactive=False, visible=False)
                        
                        with gr.Tab("🔬 Raw Vision OCR"):
                            raw_ocr_output = gr.Textbox(
                                label="Raw Vision OCR Output", 
                                lines=30,
                                max_lines=None,  # Remove max_lines limit to show full content
                                value="Raw OCR output will appear here after processing...",
                                interactive=False,
                                show_copy_button=True,
                                autoscroll=True  # Auto-scroll to show more content
                            )
                        
                        with gr.Tab("💾 Download"):
                            file_output = gr.File(label="Processed File", interactive=False)
                            analytics_output = gr.HTML(value="<div class='status-box'>Analytics will appear after processing...</div>")
            
            # Hidden component for web event communication
            web_event_bridge = gr.Textbox(visible=False, elem_id="web-event-bridge")
            
            process_click = process_btn.click(
                fn=self.process_wrapper,            # generator
                inputs=[pdf_input, page_ranges_input],
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, processing_animation, raw_ocr_output],
                show_api=False,
                show_progress="full"
            )
            
            clear_btn.click(
                fn=self.clear_all,
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, page_ranges_input, pdf_input, processing_animation, raw_ocr_output],
                show_api=False
            )

            abort_btn.click(
                fn=self.abort_processing,
                inputs=None,
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, processing_animation],
                show_api=False
            )
            
            # Add download button handlers
            download_md_btn.click(
                fn=self.download_summary_md,
                outputs=[summary_download_output],
                show_api=False
            )
            
            download_pdf_btn.click(
                fn=self.download_summary_pdf,
                outputs=[summary_download_output],
                show_api=False
            )
            
            # Add evaluation download button handler
            download_eval_btn.click(
                fn=self.download_evaluation_report,
                outputs=[evaluation_download_output],
                show_api=False
            )
            
            # Handle web events from frontend
            web_event_bridge.change(
                fn=self.handle_web_event,
                inputs=[web_event_bridge],
                outputs=[web_event_bridge],
                show_api=False
            )
        
        return demo
    
    def _extract_raw_ocr_from_logs(self):
        """Get raw OCR content from OCR engine."""
        if hasattr(self.processor, 'ocr_engine') and self.processor.ocr_engine:
            return self.processor.ocr_engine.get_debug_raw_ocr_content()
        else:
            return "No raw OCR content available yet. Process a document to see the raw vision OCR extraction results."

def create_ui():
    """Factory function to create the UI."""
    interface = OCRInterface()
    return interface.create_interface()