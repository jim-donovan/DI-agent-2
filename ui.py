"""
Gradio User Interface
Clean, modern UI for the OCR processor
"""

import gradio as gr
import tempfile
import random
import shutil
import time
from pathlib import Path
from datetime import datetime
from processor_optimized import OptimizedDocumentProcessor as DocumentProcessor
from config import config
from summary_generator import SummaryGenerator
from utils import extract_document_title, get_recommendation_color
from metadata_reporter import MetadataReporter

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
        "The architects are still drafting...",
        "Mining some bitcoins...",
        "Pay no heed to the man behind the curtain...",
        "Enjoying the elevator music?",
        "And dream of faster computers...",
        "Turns out 'attention is all you need' was slightly optimistic...",
        "We scaled. The laws didn't mention latency <oops>",
        "Checking the gravitational constant in your locale...",
        "Hum something loud while others stare...",
        "We're not in Kansas anymore...",
        "The server is powered by a lemon and two electrodes...",
        "We're testing your patience...",
        "Follow the white rabbit...",
        "Summoning your invisible 6-foot assistant...",
        "Why don't you order a sandwich?",
        "While the satellite moves into position...",
        "The bits are flowing slowly today...",
        "It's still faster than you could draw it...",
        "Looking for sense of humor, please hold on.",
        "I should have had a V8 this morning...",
        "My other loading screen is much faster.",
        "Peopled version: testing on Tommy... we're going to need another Tommy.",
        "End of line...",
        "(Insert quarter)",
        "Are we there yet?",
        "Just count to 10...",
        "Why so serious?",
        "It's not you. It's me.",
        "Fine-tuning your expectations...",
        "LLM: Large Loading Model...",
        "The version I have of this on local has much funnier load screens.",
        "Do not run! We are your friends!",
        "Do you come here often?",
        "Warning: Don't set yourself on fire.",
        "Loading humorous message ... please wait",
        "Creating time-loop inversion field...",
        "WARNING: SYSTEM FAILURE! Unable to find sense of humor. Aborting...",
        "I'm sorry Dave, I can't do that.",
        "Looking for exact change...",
        "All your web browser are belong to us...",
        "All I really need is a kilobit...",
        "What do you call 8 Hobbits? A Hobbyte!",
        "Should have used a compiled language...",
        "Is this Windows?",
        "Adjusting flux capacitor...",
        "I swear it's almost done.",
        "Listening for the sound of one hand clapping...",
        "Keeping all the 1's and removing all the 0's...",
        "Attention mechanism is distracted. Back in a moment...",
        "Making sure all the i's have dots...",
        "We are not liable for any broken screens as a result of waiting.",
        "We're going to need more dilithium crystals...",
        "I'm guessing gravitational forces vary depending on distance from the core",
        "Connecting Neurotoxin Storage Tank...",
        "Granting wishes...",
        "Time flies when you're having fun...",
        "Get some coffee and come back in ten minutes...",
        "Spinning the hamster wheel...",
        "99 bottles of beer on the wall...",
        "Somewhere, an NVIDIA GPU is crying...",
        "DEVIATION IS A SERIOUS VIOLATION (model has left the chat)...",
        "Be careful not to step in the git-gui...",
        "Our moat: we prompt it dIfFerReNtLy...",
        "Dammit Jim!",
        "You shall not pass! Yet...",
        "Load it and they will come...",
        "There is no spoon. Because we are not done loading it...",
        "Your left thumb prints are being processed...",
        "Problems may exist between keyboard and chair...",
        "Computing the secret to life, the universe, and everything...[42 chunks later]",
        "Mining some bitcoins...",
        "Downloading more RAM...",
        "Updating to Windows Vista...",
        "Alert! User detected. Please wait...",
        "Searching for plot device...",
        "Laughing at your browser's expectations...",
        "The severity of your issue is always lower than you expected...",
        "Please wait while the intern refills his coffee. Yes you, Alastair...",
        "A different error message? Finally, some progress!",
        "Hold on while we git our shit together...sorry",
        "Please hold on as we reheat our coffee...",
        "Kindly hold while we convert this bug to a feature...",
        "Winter is coming...",
        "Installing dependencies...",
        "Distracted by cat gifs...",
        "Finding someone to hold my beer...",
        "@todo Insert witty loading message...",
        "Let's hope it's worth the wait...",
        "Aw, snap! jk...",
        "Ordering 1s and 0s...",
        "Dividing by zero...",
        "If I'm not back in five minutes, just wait longer...",
        "Web developers do it with <style>",
        "Optimizing the optimizer...",
        "Teaching the model to count... (it's gotten to 17 so far)",
        "Reading Terms and Conditions for you...",
        "Is there antibody out there?",
        "In 1905, Einstein published a theory about space. It was about time ...",
        "How about this weather, eh?",
        "Inference: fast. User validation: bUfFeRiNg...",
        "Everything in this universe is either a potato or not a potato...",
        "The severity of the itch is inversely proportional to the ability to reach it.",
        "The shortest distance between two points is under construction.",
        "I'm going to count to three and then you can stop. 99... 98... 97... 96 ...",
        "I'm not slacking off. My code's compiling.",
        "Compiling the compiler...",
        "Caching the cache...",
        "Entangling superstrings...",
        "Running A/B tests (AB approves this message...)",
        "Twiddling thumbs...",
        "Searching for Schrodinger's Cat...",
        "Organic chemistry is hard. It creates alkynes of problems",
        "Constructing additional pylons...",
        "Shovelling coal into the server...",
        "Programming the flux capacitor...",
        "The elves are having labor troubles...",
        "How did you get here?",
        "Computing the last digit of pi...",
        "Waiting for the system admin to hit enter...",
        "The model is 99% loaded. The last 1% is where all the intelligence lives...",
        "I'M ON A BOAT!",
        "Catching 'em all..."
    ]
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.summary_generator = SummaryGenerator(self.processor.logger)
        self.current_summary = ""
        self.current_document_title = ""
        self.current_evaluation = ""
        # Debug data storage
        self.raw_ocr_output = ""
        # Excel configuration storage
        self.excel_structure_config = None
        # Vision recommendations storage
        self.vision_recommendations = None
        self.current_uploaded_file = None

        # Create local downloads directory for Gradio (if enabled)
        self.use_local_downloads = config.use_local_downloads_directory
        if self.use_local_downloads:
            self.downloads_dir = Path("gradio_downloads")
            self.downloads_dir.mkdir(exist_ok=True)
        else:
            self.downloads_dir = None

    def _get_download_path(self, original_path: str) -> str:
        """Get the appropriate download path based on configuration."""
        if not original_path:
            return None

        if self.use_local_downloads and self.downloads_dir:
            # Copy to local directory for Gradio serving
            local_file = self.downloads_dir / Path(original_path).name
            shutil.copy2(original_path, local_file)
            return str(local_file)
        else:
            # Use original path (for HuggingFace deployment)
            return original_path

    def _load_animation_html(self):
        """Load the processing animation with CSS-based message cycling."""
        # Get multiple messages for CSS animation cycling
        # Use 80 messages for ~5.7 minutes of unique content (80 * 4.3s = 344s)
        messages_sample = random.sample(self.LOADING_MESSAGES, min(80, len(self.LOADING_MESSAGES)))

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
                        box-shadow: 0 0 20px rgba(223, 87, 159, 0.6),
                                    0 0 40px rgba(236, 110, 83, 0.4),
                                    0 0 60px rgba(191, 200, 90, 0.2);
                    }}
                    50% {{
                        box-shadow: 0 0 30px rgba(223, 87, 159, 0.8),
                                    0 0 60px rgba(236, 110, 83, 0.6),
                                    0 0 90px rgba(191, 200, 90, 0.4);
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
                    background: linear-gradient(135deg, #DF579F 0%, #EC6E53 50%, #BFC85A 100%);
                    border-radius: 50%;
                    animation: pulse 4.3s ease-in-out infinite, glow 4.3s ease-in-out infinite;
                    box-shadow: 0 0 40px rgba(236, 110, 83, 0.6);
                }}
                .orbit-ring {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 160px;
                    height: 160px;
                    margin: -80px 0 0 -80px;
                    border: 2px solid rgba(236, 110, 83, 0.2);
                    border-radius: 50%;
                }}
                .orbiting-dot {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 20px;
                    height: 20px;
                    margin: -10px 0 0 -10px;
                    background: linear-gradient(135deg, #DF579F, #EC6E53);
                    border-radius: 50%;
                    box-shadow: 0 0 20px rgba(223, 87, 159, 0.8);
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
                {"".join(f".cycling-messages span:nth-child({i+1}) {{ animation-delay: {total_duration * i / len(messages_sample):.1f}s; }}" for i in range(len(messages_sample)))}
            </style>
            <div class="processing-container">
                <div class="orbit-ring"></div>
                <div class="central-orb"></div>
                <div class="orbiting-dot orbiting-dot-1"></div>
                <div class="orbiting-dot orbiting-dot-2"></div>
                <div class="orbiting-dot orbiting-dot-3"></div>
            </div>
            <h3 style="background: linear-gradient(135deg, #DF579F, #EC6E53, #BFC85A); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-top: 30px; font-family: 'Rajdhani', sans-serif; font-weight: 600; text-align: center; letter-spacing: 0.5px;">Processing your document...</h3>
            <div class="cycling-messages" style="color: #EC6E53; font-family: 'Rajdhani', sans-serif; font-weight: 500; text-align: center; letter-spacing: 0.3px;">
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
            
            # Check if this is a comparison report (look for both evaluations)
            if "ANTHROPIC EVALUATION" in evaluation_content and "OPENAI EVALUATION" in evaluation_content:
                return self._parse_dual_evaluation(evaluation_content)
            else:
                # Single evaluation - put it in OpenAI column 
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
        
        lines = evaluation_content.split('\n')
        
        # Extract sections
        openai_lines = []
        anthropic_lines = []
        current_section = None
        
        for line in lines:
            # Check for the actual headers used by CheckerAgent
            if "OPENAI EVALUATION" in line:
                current_section = "openai"
                openai_lines.append("## OpenAI Evaluation")
            elif "ANTHROPIC EVALUATION" in line:
                current_section = "anthropic"
                anthropic_lines.append("## Anthropic Evaluation")
            elif "DEBUG INFORMATION" in line or "EVALUATOR COMPARISON" in line:
                current_section = None
            elif current_section == "openai":
                openai_lines.append(line)
            elif current_section == "anthropic":
                anthropic_lines.append(line)
        
        # Extract scores and recommendations directly from evaluation sections
        openai_score = self._extract_score(evaluation_content, "OPENAI")
        anthropic_score = self._extract_score(evaluation_content, "ANTHROPIC")
        openai_rec = self._extract_recommendation(evaluation_content, "OPENAI")  
        anthropic_rec = self._extract_recommendation(evaluation_content, "ANTHROPIC")
        
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
        
        # Find the evaluation section and look for score in next few lines
        for i, line in enumerate(lines):
            line = line.strip()
            if f"{marker} EVALUATION" in line:
                # Look for score in the next 10 lines after finding the section
                for j in range(i + 1, min(i + 10, len(lines))):
                    check_line = lines[j].strip()
                    if "Score:" in check_line:
                        try:
                            # Handle formats like "Score: 85.0/100"
                            score_part = check_line.split("Score:")[1].strip()
                            score = score_part.split('/')[0].strip()
                            return f"{score}/100"
                        except Exception as e:
                            continue
                    # Stop if we hit another evaluation section
                    if "EVALUATION" in check_line and marker not in check_line:
                        break
                break
        
        return "N/A"
    
    def _extract_recommendation(self, content: str, marker: str) -> str:
        """Extract recommendation from evaluation content."""
        lines = content.split('\n')
        
        # Find the evaluation section and look for recommendation in next few lines
        for i, line in enumerate(lines):
            line = line.strip()
            if f"{marker} EVALUATION" in line:
                # Look for recommendation in the next 10 lines after finding the section
                for j in range(i + 1, min(i + 10, len(lines))):
                    check_line = lines[j].strip()
                    if "Recommendation:" in check_line:
                        try:
                            # Handle formats like "Recommendation: ACCEPT"
                            rec_part = check_line.split("Recommendation:")[1].strip()
                            # Remove any trailing text after whitespace
                            return rec_part.split()[0] if rec_part else "UNKNOWN"
                        except Exception as e:
                            continue
                    # Stop if we hit another evaluation section
                    if "EVALUATION" in check_line and marker not in check_line:
                        break
                break
        
        return "UNKNOWN"
    
    def _extract_score_from_summary(self, content: str, provider: str) -> str:
        """Extract score from evaluation comparison summary section."""
        lines = content.split('\n')
        
        # Look for the specific evaluation sections in the report
        in_provider_section = False
        
        for line in lines:
            # Check if we're in the right evaluation section
            if provider.upper() in line and "EVALUATION" in line:
                in_provider_section = True
                continue
            elif in_provider_section and ("=" in line and len(line.strip()) > 10 and line.strip().count("=") > 10):
                # We've hit another section separator
                in_provider_section = False
                continue
                
            # If we're in the right section, look for score
            if in_provider_section and "Score:" in line:
                try:
                    # Handle formats like "Score: 85.0/100"
                    score_part = line.split("Score:")[1].strip()
                    score = score_part.split('/')[0].strip()
                    return f"{score}/100"
                except Exception as e:
                    continue
        
        return "N/A"
    
    def _extract_recommendation_from_summary(self, content: str, provider: str) -> str:
        """Extract recommendation from evaluation comparison summary section."""
        lines = content.split('\n')
        
        # Look for the specific evaluation sections in the report
        in_provider_section = False
        
        for line in lines:
            # Check if we're in the right evaluation section
            if provider.upper() in line and "EVALUATION" in line:
                in_provider_section = True
                continue
            elif in_provider_section and ("=" in line and len(line.strip()) > 10 and line.strip().count("=") > 10):
                # We've hit another section separator
                in_provider_section = False
                continue
                
            # If we're in the right section, look for recommendation
            if in_provider_section and "Recommendation:" in line:
                try:
                    # Handle formats like "Recommendation: ACCEPT"
                    rec_part = line.split("Recommendation:")[1].strip()
                    # Remove any trailing text after whitespace
                    return rec_part.split()[0] if rec_part else "UNKNOWN"
                except Exception as e:
                    continue
        
        return "UNKNOWN"
    
    def _extract_agreement(self, content: str) -> str:
        """Extract agreement level from comparison report."""
        lines = content.split('\n')
        for line in lines:
            if "Agreement Level:" in line:
                try:
                    agreement = line.split("Agreement Level:")[1].strip()
                    return agreement
                except (IndexError, AttributeError):
                    pass
        return "Unknown"

    def get_css(self) -> str:
        """Get CSS styling for the interface."""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Literata:wght@400;500;600;700;800&family=Rajdhani:wght@400;500;600;700&display=swap');
        
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
            font-family: 'Literata', serif !important;
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
            font-family: 'Literata', serif !important;
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
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }

        @media (max-width: 1200px) {
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
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
            font-family: 'Literata', serif !important;
        }

        /* Ensure all progress-related elements use blue theme */
        div[class*="progress"] {
            color: #67e8f9 !important;
        }

        /* Navigation Button Styles */
        .nav-btn {
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            padding: 16px 32px !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            font-family: 'Literata', serif !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin: 10px 5px !important;
        }

        /* Document OCR nav button - Cyan/Blue */
        .nav-btn-doc {
            background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow:
                0 4px 12px rgba(6, 182, 212, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        }

        .nav-btn-doc:hover {
            background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow:
                0 6px 16px rgba(6, 182, 212, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }

        /* Excel Processor nav button - Gray (inactive) */
        .nav-btn-excel,
        .nav-btn-excel-inactive {
            background: linear-gradient(135deg, #52525b 0%, #71717a 100%) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow:
                0 4px 12px rgba(82, 82, 91, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        }

        .nav-btn-excel:hover,
        .nav-btn-excel-inactive:hover {
            background: linear-gradient(135deg, #71717a 0%, #a1a1aa 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow:
                0 6px 16px rgba(82, 82, 91, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }

        /* Excel Processor nav button - Cyan/Blue (active) */
        .nav-btn-excel-active {
            background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow:
                0 4px 12px rgba(6, 182, 212, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        }

        .nav-btn-excel-active:hover {
            background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow:
                0 6px 16px rgba(6, 182, 212, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }

        /* Make navigation buttons full width on mobile */
        @media (max-width: 768px) {
            .nav-btn {
                width: 100% !important;
                margin: 5px 0 !important;
            }
        }

        /* Image Overlay Modal */
        #imageOverlay {
            display: none;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        #imageOverlay.show {
            display: flex !important;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        #overlayImage {
            max-width: 90vw;
            max-height: 90vh;
            width: auto;
            height: auto;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            animation: zoomIn 0.3s ease;
        }

        @keyframes zoomIn {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        #overlayClose {
            position: absolute;
            top: 20px;
            right: 40px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.1);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        #overlayClose:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: rotate(90deg);
        }

        #overlayCaption {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: #f1f1f1;
            font-size: 18px;
            font-weight: 500;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }

        /* Logs Output Styling */
        .logs-output textarea {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
            background: rgba(0, 0, 0, 0.4) !important;
            color: #e2e8f0 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 1rem !important;
        }

        .logs-output textarea::-webkit-scrollbar {
            width: 10px;
        }

        .logs-output textarea::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
        }

        .logs-output textarea::-webkit-scrollbar-thumb {
            background: rgba(6, 182, 212, 0.4);
            border-radius: 5px;
        }

        .logs-output textarea::-webkit-scrollbar-thumb:hover {
            background: rgba(6, 182, 212, 0.6);
        }

        /* Feedback Form Styles */
        .feedback-form-container {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
            border-radius: 16px !important;
            padding: 1.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            margin-top: 1.5rem;
        }

        #tally-feedback-embed {
            width: 100% !important;
            min-height: 450px !important;
            border: none !important;
            border-radius: 12px !important;
            background: transparent !important;
        }

        #tally-feedback-embed iframe {
            border-radius: 12px !important;
        }

        """

    def _parse_excel_config(self, excel_column_config, excel_header_rows, excel_include_headers=False):
        """Parse Excel configuration from UI into structure for agents."""
        if excel_column_config is None or (hasattr(excel_column_config, 'empty') and excel_column_config.empty):
            self.excel_structure_config = None
            return

        # Convert dataframe/list config to structured format
        column_structure = []

        # Handle both list and dataframe formats
        if hasattr(excel_column_config, 'iterrows'):
            # It's a DataFrame
            for idx, row in excel_column_config.iterrows():
                col_name = row[0]  # First column
                role = row[1]      # Second column
                if role.lower() == "ignore":
                    continue

                column_structure.append({
                    "index": idx,
                    "header": col_name,
                    "role": role.lower().replace(" ", "_"),  # "Label 1" -> "label_1"
                    "type": "data" if role.lower() == "data" else "text"
                })
        else:
            # It's a list of lists
            for idx, (col_name, role) in enumerate(excel_column_config):
                if role.lower() == "ignore":
                    continue

                column_structure.append({
                    "index": idx,
                    "header": col_name,
                    "role": role.lower().replace(" ", "_"),  # "Label 1" -> "label_1"
                    "type": "data" if role.lower() == "data" else "text"
                })

        self.excel_structure_config = {
            "type": "openpyxl_worksheet",
            "column_structure": column_structure,
            "data_start_row": int(excel_header_rows) if excel_header_rows else 1,
            "hierarchical": False,
            "merged_cells": [],
            "user_configured": True,
            "include_headers": excel_include_headers
        }


    def handle_file_upload(self, uploaded_file):
        """Handle file upload and show Excel config UI if needed."""
        import pandas as pd

        if not uploaded_file:
            return gr.update(visible=False), None, None, None

        # Check if this is an Excel file
        file_extension = Path(uploaded_file.name).suffix.lower()
        is_excel = file_extension in ['.xlsx', '.xls', '.csv']

        if not is_excel:
            # Hide Excel config for non-Excel files
            return gr.update(visible=False), None, None, None

        try:
            # Load Excel file to show preview
            if file_extension == '.csv':
                df = pd.read_csv(uploaded_file.name, nrows=10)
            else:
                df = pd.read_excel(uploaded_file.name, nrows=10, engine='openpyxl')

            # Create column configuration dataframe with default roles
            column_names = df.columns.tolist()

            # Smart defaults: assume first column is Label 1, last few are Data
            default_config = []
            for i, col in enumerate(column_names):
                if i == 0:
                    role = "Label 1"
                elif i < 3:  # First 3 columns might be labels
                    role = "Label " + str(i + 1)
                else:
                    role = "Data"
                default_config.append([str(col), role])

            # Show Excel config section
            return (
                gr.update(visible=True),  # Show the section
                df,  # Preview dataframe
                default_config,  # Column configuration
                1,  # Default header rows
                False  # Default: no section headers
            )

        except Exception as e:
            print(f"Error loading Excel preview: {e}")
            return gr.update(visible=False), None, None, None, None

    def process_wrapper(self, uploaded_file, page_ranges_str, excel_column_config=None, excel_header_rows=1, excel_include_headers=False,
                       enable_summary=False, enable_quality_report=False, enable_raw_ocr=False, vision_table=None):
        """Wrapper for document processing with UI updates."""
        # Convert dropdown strings to booleans (Gradio dropdowns return strings)
        enable_summary = enable_summary == "Enabled" if isinstance(enable_summary, str) else enable_summary
        enable_quality_report = enable_quality_report == "Enabled" if isinstance(enable_quality_report, str) else enable_quality_report
        enable_raw_ocr = enable_raw_ocr == "Enabled" if isinstance(enable_raw_ocr, str) else enable_raw_ocr

        # start every run with a clean abort flag
        self.processor.clear_abort()

        # Store Excel configuration if provided
        if excel_column_config is not None and len(excel_column_config) > 0:
            self._parse_excel_config(excel_column_config, excel_header_rows, excel_include_headers)

        # Parse vision recommendations from table (DataFrame from Gradio)
        vision_page_settings = None

        if vision_table is not None and len(vision_table) > 0:
            import pandas as pd

            # Check if it's a DataFrame
            if isinstance(vision_table, pd.DataFrame):
                vision_page_settings = {}

                # DataFrame columns: ["Page", "Recommended", "Reason", "Thumbnail"]
                for idx, row in vision_table.iterrows():
                    try:
                        page_num = int(row.iloc[0])  # Page column
                        recommendation = str(row.iloc[1]).upper()  # Recommended column

                        if recommendation in ["YES", "NO"]:
                            vision_page_settings[page_num] = recommendation
                            self.processor.logger.log_step(f"📋 Page {page_num} -> {recommendation} (from user table)")
                    except (ValueError, TypeError, IndexError) as e:
                        # Skip invalid rows
                        continue

                if vision_page_settings:
                    vision_yes = sum(1 for v in vision_page_settings.values() if v == "YES")
                    vision_no = sum(1 for v in vision_page_settings.values() if v == "NO")
                    self.processor.logger.log_step("")
                    self.processor.logger.log_step("=" * 60)
                    self.processor.logger.log_step("📊 VISION OCR CONFIGURATION (User-Edited)")
                    self.processor.logger.log_step("=" * 60)
                    self.processor.logger.log_step(f"✅ {vision_yes} pages WITH vision OCR")
                    self.processor.logger.log_step(f"⚡ {vision_no} pages WITHOUT vision (fast mode)")
                    self.processor.logger.log_step("=" * 60)
                    self.processor.logger.log_step("")
                else:
                    self.processor.logger.log_warning("⚠️ Vision table is empty or invalid")
            else:
                # Handle as list of rows (legacy)
                vision_page_settings = {}
                for row in vision_table:
                    try:
                        if len(row) >= 2 and row[0] and row[1]:
                            page_num = int(row[0])
                            recommendation = str(row[1]).upper()
                            vision_page_settings[page_num] = recommendation
                    except (ValueError, TypeError, IndexError) as e:
                        continue

                if vision_page_settings:
                    vision_yes = sum(1 for v in vision_page_settings.values() if v == "YES")
                    vision_no = sum(1 for v in vision_page_settings.values() if v == "NO")
                    self.processor.logger.log_step(f"📊 Vision recommendations: {vision_yes} pages WITH vision OCR, {vision_no} pages WITHOUT")

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
                page_ranges_str if page_ranges_str and page_ranges_str.strip() else None,
                excel_structure_config=self.excel_structure_config,
                vision_page_settings=vision_page_settings,
                enable_summary=enable_summary,
                enable_quality_report=enable_quality_report,
                enable_raw_ocr=enable_raw_ocr
            )

            if result.status == "Aborted":
                yield self._aborted_response()
                return

            metrics_html = self._generate_metrics(result)
            analytics_html = self._generate_analytics(result)
            status_html = self._generate_status(result)
            
            # Check if this is an Excel file
            file_extension = Path(uploaded_file.name).suffix.lower() if uploaded_file else ""
            is_excel = file_extension in ['.xlsx', '.xls', '.csv']

            # Generate summary (skip for Excel files and if disabled)
            self.current_document_title = extract_document_title(uploaded_file.name) if uploaded_file else "Document"

            summary_time = 0.0
            if enable_summary and not is_excel:
                summary_start = time.time()
                summary_content, summary_success = self.summary_generator.generate_summary(result.content, self.current_document_title)
                summary_time = time.time() - summary_start
                self.current_summary = summary_content
            else:
                # Skip summary generation
                if is_excel:
                    summary_content = "Summary generation is disabled for Excel files."
                elif not enable_summary:
                    summary_content = "Summary generation was disabled by user."
                else:
                    summary_content = "Summary generation is disabled."
                summary_success = False
                self.current_summary = summary_content

            # Update result with summary timing
            result.summary_time = summary_time

            # Generate summary statistics
            if summary_success and not is_excel and enable_summary:
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
            elif is_excel:
                summary_stats_html = "<div class='status-box status-info'>ℹ️ Summary generation is disabled for Excel files</div>"
            elif not enable_summary:
                summary_stats_html = "<div class='status-box status-info'>ℹ️ Summary generation was disabled by user</div>"
            else:
                summary_stats_html = "<div class='status-box status-error'>❌ Summary generation failed</div>"
            
            # Parse evaluation report for side-by-side display
            # Get evaluation report directly from the ProcessingResult
            if enable_quality_report:
                evaluation_content = result.evaluation_report if hasattr(result, 'evaluation_report') and result.evaluation_report else "*No evaluation report available*"
            else:
                evaluation_content = "*Quality report generation was disabled by user.*"
            self.current_evaluation = evaluation_content  # Store for download

            # Debug output file

            # Handle main output file based on configuration
            if result.output_file:
                result.output_file = self._get_download_path(result.output_file)

            # Parse evaluation report into components
            comparison_summary_html, openai_content, anthropic_content, evaluation_stats_html = self._parse_evaluation_for_comparison(evaluation_content)

            # Capture debug data from processing logs
            if enable_raw_ocr:
                raw_ocr_data = self._extract_raw_ocr_from_logs()
            else:
                raw_ocr_data = "Raw OCR extraction was disabled by user."
            
            # Get processing logs
            logs_data = self.processor.logger.get_logs() if hasattr(self.processor, 'logger') else "No logs available"

            # Generate AI metadata cleaning report
            cleaning_report_md = "*No AI metadata cleaning report available*"
            if hasattr(result, 'agent_responses') and result.agent_responses:
                try:
                    report = MetadataReporter.generate_report(
                        result.agent_responses,
                        total_pages=result.pages_processed
                    )
                    cleaning_report_md = report.to_markdown()
                except Exception as e:
                    cleaning_report_md = f"*Error generating cleaning report: {str(e)}*"

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
                raw_ocr_data,                   # Raw Vision OCR Output
                logs_data,                      # Analysis Logs
                cleaning_report_md              # Cleaning Report
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
            "Raw OCR output will appear here after processing...",            # Raw OCR Output
            "Processing logs will appear here...",                            # Analysis Logs
            "*AI metadata cleaning report will appear here after processing...*" # Cleaning Report
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
            "🔄 Processing...",                                               # Raw OCR Output
            "🔄 Collecting logs...",                                          # Analysis Logs
            "🔄 Generating cleaning report..."                                # Cleaning Report
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
            f"❌ Processing failed: {error_msg}",                             # Raw OCR Output
            f"❌ Error during processing: {error_msg}",                       # Analysis Logs
            f"*❌ Cleaning report unavailable due to error: {error_msg}*"     # Cleaning Report
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
            "⚠️ Processing was aborted by user",                               # Raw OCR Output
            "⚠️ Processing was aborted by user",                               # Analysis Logs
            "*⚠️ Cleaning report unavailable - processing was aborted*"        # Cleaning Report
        )
    
    def _generate_metrics(self, result):
        """Generate metrics HTML."""
        # Format token count (e.g., 25.3K or 1.2M)
        def format_number(num):
            if num >= 1_000_000:
                return f"{num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{num/1_000:.1f}K"
            else:
                return str(num)

        # Format cost
        cost_str = f"${result.estimated_cost:.3f}" if hasattr(result, 'estimated_cost') and result.estimated_cost > 0 else "N/A"
        tokens_str = format_number(result.total_tokens) if hasattr(result, 'total_tokens') and result.total_tokens > 0 else "N/A"

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
                <div class="metric-value">{tokens_str}</div>
                <div class="metric-label">Tokens Used</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{cost_str}</div>
                <div class="metric-label">Est. Cost</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.pages_processed}</div>
                <div class="metric-label">Pages</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(result.content.split()) if result.content else 0:,}</div>
                <div class="metric-label">Words</div>
            </div>
        </div>
        """
    
    def _generate_analytics(self, result):
        """Generate detailed analytics HTML."""
        vision_efficiency = f"{(result.vision_calls_used / max(result.pages_processed, 1)):.1f}" if result.pages_processed > 0 else "0"

        # Component timing breakdown
        timing_breakdown = ""
        if hasattr(result, 'vision_ocr_time') or hasattr(result, 'quality_report_time') or hasattr(result, 'summary_time'):
            vision_ocr_time = getattr(result, 'vision_ocr_time', 0.0)
            quality_report_time = getattr(result, 'quality_report_time', 0.0)
            summary_time = getattr(result, 'summary_time', 0.0)

            # Only show timing breakdown if at least one component has time
            if vision_ocr_time > 0 or quality_report_time > 0 or summary_time > 0:
                timing_breakdown = f"""
            <p><strong>Component Timing:</strong></p>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>Vision OCR & Processing: {vision_ocr_time:.2f}s</li>
                <li>Quality Report: {quality_report_time:.2f}s</li>
                <li>Summary Generation: {summary_time:.2f}s</li>
            </ul>
            """

        # Token breakdown
        token_breakdown = ""
        if hasattr(result, 'total_tokens') and result.total_tokens > 0:
            vision_pct = (result.vision_tokens / result.total_tokens * 100) if result.total_tokens > 0 else 0
            formatting_pct = (result.formatting_tokens / result.total_tokens * 100) if result.total_tokens > 0 else 0
            token_breakdown = f"""
            <p><strong>Token Breakdown:</strong></p>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>Vision OCR: {result.vision_tokens:,} ({vision_pct:.1f}%)</li>
                <li>Formatting: {result.formatting_tokens:,} ({formatting_pct:.1f}%)</li>
                <li>Total: {result.total_tokens:,}</li>
            </ul>
            """

        # Cost breakdown
        cost_breakdown = ""
        if hasattr(result, 'estimated_cost') and result.estimated_cost > 0:
            cost_breakdown = f"""
            <p><strong>Cost Estimate:</strong> ${result.estimated_cost:.4f} USD</p>
            <p style="font-size: 0.85em; opacity: 0.8;">Based on GPT-4o ($10/1M tokens) and Claude Sonnet ($3/1M tokens)</p>
            """

        return f"""
        <div class="status-box {'status-success' if result.success else 'status-error'}">
            <h4>📊 Processing Analytics</h4>
            <p><strong>Pages Processed:</strong> {result.pages_processed}</p>
            <p><strong>Vision Calls:</strong> {result.vision_calls_used} ({vision_efficiency} per page)</p>
            <p><strong>Words Extracted:</strong> {len(result.content.split()) if result.content else 0:,}</p>
            <p><strong>Processing Time:</strong> {result.processing_time:.2f}s ({result.processing_time/max(result.pages_processed,1):.2f}s per page)</p>
            {timing_breakdown}
            {token_breakdown}
            {cost_breakdown}
            <p><strong>Status:</strong> {"✅ Success" if result.success else "❌ Failed"}</p>
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
        self.excel_structure_config = None  # Clear Excel config
        self.vision_recommendations = None  # Clear vision recommendations
        self.current_uploaded_file = None  # Clear uploaded file
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
            "Raw OCR output will appear here after processing...",              # Raw OCR Output cleared
            "<div class='status-box'>⏳ Upload a PDF, then click Analyze</div>", # Analyze status reset
            None,                                                                 # Vision recommendation table cleared
            gr.update(visible=False),                                            # Vision recommendation table hidden
            "Processing logs will appear here...",                               # Analysis Logs cleared
            "*AI metadata cleaning report will appear here after processing...*" # Cleaning Report cleared
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
                download_path = self._get_download_path(md_path)
                return gr.update(value=download_path, visible=True)
            else:
                return gr.update(value=None, visible=False)

        except Exception as e:
            print(f"Error downloading MD summary: {e}")
            import traceback
            traceback.print_exc()
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
                download_path = self._get_download_path(pdf_path)
                return gr.update(value=download_path, visible=True)
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
            # Save evaluation report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            eval_filename = f"{self.current_document_title or 'document'}_evaluation_{timestamp}.md"

            if self.use_local_downloads and self.downloads_dir:
                # Save directly to local downloads directory
                eval_path = self.downloads_dir / eval_filename
            else:
                # Save to temp directory for HuggingFace
                eval_path = Path(tempfile.gettempdir()) / eval_filename

            with open(eval_path, 'w', encoding='utf-8') as f:
                f.write(self.current_evaluation)

            return gr.update(value=str(eval_path), visible=True)

        except Exception as e:
            print(f"Error downloading evaluation report: {e}")
            return gr.update(value=None, visible=False)

    def handle_excel_upload(self, uploaded_file):
        """Handle Excel file upload and show preview + default config + sheet names."""
        import pandas as pd
        import openpyxl

        # Reset saved configurations
        self.saved_sheet_configs = {}

        if not uploaded_file:
            return (None, None, gr.update(choices=[], value=None, visible=False),
                    gr.update(value="", visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(value="<div class='status-box'>No sheets configured yet.</div>"))

        try:
            file_extension = Path(uploaded_file.name).suffix.lower()

            # Get sheet names if it's an Excel file (not CSV)
            sheet_names = []
            if file_extension in ['.xlsx', '.xls']:
                wb = openpyxl.load_workbook(uploaded_file.name, read_only=True, data_only=True)
                sheet_names = wb.sheetnames
                wb.close()

                # Default to first sheet for initial preview
                df = pd.read_excel(uploaded_file.name, sheet_name=0, nrows=10, engine='openpyxl')

                # Show sheet selector if multiple sheets
                if len(sheet_names) > 1:
                    return (
                        df,
                        self._generate_default_column_config(df),
                        gr.update(choices=sheet_names, value=sheet_names[0], visible=True),
                        gr.update(value=f"<div class='status-box' style='background: rgba(59, 130, 246, 0.1);'>📄 Previewing: <strong>{sheet_names[0]}</strong></div>", visible=True),
                        gr.update(visible=True),  # Show save button
                        gr.update(visible=True),  # Show clear button
                        gr.update(value="<div class='status-box'>No sheets configured yet. Configure and save sheets below.</div>")
                    )
                else:
                    # Single sheet, no selector needed
                    return (
                        df,
                        self._generate_default_column_config(df),
                        gr.update(choices=sheet_names, value=sheet_names[0] if sheet_names else None, visible=False),
                        gr.update(value="", visible=False),
                        gr.update(visible=False),  # Hide save button for single sheet
                        gr.update(visible=False),
                        gr.update(value="<div class='status-box'>Single sheet - configuration will be applied automatically.</div>")
                    )
            else:
                # CSV file
                df = pd.read_csv(uploaded_file.name, nrows=10)
                return (
                    df,
                    self._generate_default_column_config(df),
                    gr.update(choices=[], value=None, visible=False),
                    gr.update(value="", visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value="<div class='status-box'>CSV file - configuration will be applied automatically.</div>")
                )

        except Exception as e:
            self.processor.logger.error(f"Error loading Excel preview: {e}")
            return (None, None, gr.update(choices=[], value=None, visible=False),
                    gr.update(value="", visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(value="<div class='status-box status-error'>Error loading file</div>"))

    def _generate_default_column_config(self, df):
        """Generate default column configuration for a dataframe."""
        column_names = df.columns.tolist()
        default_config = []
        for i, col in enumerate(column_names):
            if i == 0:
                role = "Label 1"
            elif i < 3:  # First 3 columns might be labels
                role = "Label " + str(i + 1)
            else:
                role = "Data"
            default_config.append([str(col), role])
        return default_config

    def preview_excel_sheet(self, uploaded_file, selected_sheet):
        """Preview a specific sheet from the Excel file when dropdown changes."""
        import pandas as pd

        if not uploaded_file or not selected_sheet:
            return (None, None, gr.update(value="<div class='status-box status-error'>⚠️ Please select a sheet</div>", visible=True))

        try:
            df = pd.read_excel(uploaded_file.name, sheet_name=selected_sheet, nrows=10, engine='openpyxl')

            return (
                df,
                self._generate_default_column_config(df),
                gr.update(value=f"<div class='status-box' style='background: rgba(59, 130, 246, 0.1);'>📄 Previewing: <strong>{selected_sheet}</strong></div>", visible=True)
            )

        except Exception as e:
            self.processor.logger.error(f"Error previewing sheet: {e}")
            return (
                None,
                None,
                gr.update(value=f"<div class='status-box status-error'>❌ Error: {str(e)}</div>", visible=True)
            )

    def save_sheet_configuration(self, selected_sheet, excel_column_config, excel_header_rows, excel_include_headers):
        """Save configuration for the currently selected sheet."""
        if not selected_sheet:
            return gr.update(value="<div class='status-box status-error'>⚠️ Please select a sheet first</div>")

        if not hasattr(self, 'saved_sheet_configs'):
            self.saved_sheet_configs = {}

        # Store configuration for this sheet
        self.saved_sheet_configs[selected_sheet] = {
            'column_config': excel_column_config,
            'header_rows': excel_header_rows,
            'include_headers': excel_include_headers
        }

        # Generate display of saved sheets
        saved_html = "<div class='status-box status-success'>"
        saved_html += f"<strong>✅ {len(self.saved_sheet_configs)} Sheet(s) Configured:</strong><br><br>"
        for sheet_name in self.saved_sheet_configs.keys():
            saved_html += f"📄 <strong>{sheet_name}</strong><br>"
        saved_html += "<br>Click 'Process Excel' to convert all configured sheets.</div>"

        return gr.update(value=saved_html)

    def clear_saved_configurations(self):
        """Clear all saved sheet configurations."""
        self.saved_sheet_configs = {}
        return gr.update(value="<div class='status-box'>No sheets configured yet. Configure and save sheets below.</div>")

    def process_excel_wrapper(self, uploaded_file):
        """Wrapper for Excel processing with UI updates."""
        self.processor.clear_abort()

        if not uploaded_file:
            yield self._no_excel_response()
            return

        # Use saved configurations if available, otherwise use current config
        if not hasattr(self, 'saved_sheet_configs'):
            self.saved_sheet_configs = {}

        yield self._excel_processing_state()

        try:
            import pandas as pd
            from pathlib import Path
            import tempfile
            import os

            file_extension = Path(uploaded_file.name).suffix.lower()

            # If saved configurations exist, process those sheets
            if self.saved_sheet_configs and len(self.saved_sheet_configs) > 0 and file_extension in ['.xlsx', '.xls']:
                all_content = []

                for sheet_name, config in self.saved_sheet_configs.items():
                    self.processor.logger.log_step(f"📊 Processing sheet: {sheet_name}")

                    # Parse config for this sheet
                    column_config = config['column_config']
                    if column_config is not None and len(column_config) > 0:
                        self._parse_excel_config(
                            column_config,
                            config['header_rows'],
                            config['include_headers']
                        )

                    # Create temp file for this sheet only
                    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                        df = pd.read_excel(uploaded_file.name, sheet_name=sheet_name, engine='openpyxl')
                        df.to_excel(tmp.name, index=False, engine='openpyxl')
                        tmp_path = tmp.name

                    # Create a mock uploaded file for this sheet
                    class SheetFile:
                        def __init__(self, path, name):
                            self.name = path
                            self.orig_name = name

                    sheet_file = SheetFile(tmp_path, f"{sheet_name}.xlsx")

                    # Process this sheet
                    result = self.processor.process_document(
                        sheet_file,
                        page_ranges_str=None,
                        excel_structure_config=self.excel_structure_config
                    )

                    # Clean up temp file
                    os.unlink(tmp_path)

                    if result.status == "Aborted":
                        yield self._excel_aborted_response()
                        return

                    # Combine content with sheet header
                    if result.content:
                        all_content.append(f"## {sheet_name}\n\n{result.content}\n\n")

                # Create combined result
                result.content = "\n".join(all_content)
                metrics_html = self._generate_metrics(result)
                metrics_html = metrics_html.replace("</div>", f"<br>📑 Processed {len(self.saved_sheet_configs)} sheets</div>")

            else:
                # Single sheet or CSV processing (no saved configs)
                result = self.processor.process_document(
                    uploaded_file,
                    page_ranges_str=None,
                    excel_structure_config=None
                )

                if result.status == "Aborted":
                    yield self._excel_aborted_response()
                    return

                metrics_html = self._generate_metrics(result)

            analytics_html = self._generate_analytics(result)
            status_html = self._generate_status(result)

            # Handle output file
            if result.output_file:
                result.output_file = self._get_download_path(result.output_file)

            yield (
                result.content,                 # Formatted content
                status_html,                    # Status
                metrics_html,                   # Metrics
                result.output_file,             # File download
                analytics_html,                 # Analytics
                gr.update(visible=True, interactive=True),  # Clear button
                gr.update(visible=False),       # Abort hidden
                gr.update(visible=False)        # Animation hidden
            )

        except Exception as e:
            yield self._excel_error_response(str(e))

    def _no_excel_response(self):
        """Response when no Excel file is uploaded."""
        return (
            "*Please upload an Excel or CSV file to begin processing.*",
            "<div class='status-box status-error'>❌ No file uploaded</div>",
            "<div class='status-box'>No metrics available</div>",
            gr.update(value=None),
            "<div class='status-box status-error'>Please upload an Excel file</div>",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    def _excel_processing_state(self):
        """Response during Excel processing."""
        return (
            "*🚀 Processing Excel file...*",
            "<div class='status-box status-processing'>⏳ Processing Excel...</div>",
            "<div class='status-box status-processing'>⏳ Processing in progress...</div>",
            gr.update(value=None),
            "<div class='status-box status-processing'>Processing in progress...</div>",
            gr.update(visible=True, interactive=False),
            gr.update(visible=True),
            gr.update(value=self._load_animation_html(), visible=True)
        )

    def _excel_error_response(self, error_msg):
        """Response for Excel processing errors."""
        return (
            f"*❌ Processing Error: {error_msg}*",
            f"<div class='status-box status-error'>❌ Error: {error_msg}</div>",
            "<div class='status-box status-error'>❌ Processing failed</div>",
            gr.update(value=None),
            f"<div class='status-box status-error'>Error: {error_msg}</div>",
            gr.update(visible=True, interactive=True),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    def _excel_aborted_response(self):
        """Response when Excel processing is aborted."""
        return (
            "**⚠️ Processing was aborted by user.**",
            "<div class='status-box status-error'>⚠️ Processing aborted by user</div>",
            "<div class='status-box'>Processing was aborted</div>",
            gr.update(value=None),
            "<div class='status-box status-error'>Processing was aborted by user</div>",
            gr.update(visible=True, interactive=True),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    def clear_excel(self):
        """Clear Excel interface elements."""
        self.processor.clear_abort()
        self.processor.clear_logs()
        self.excel_structure_config = None
        return (
            "*Processed Excel content will appear here...*",
            "<div class='status-box'>⏳ Ready to process Excel file...</div>",
            "<div class='status-box'>Metrics will appear during processing...</div>",
            gr.update(value=None),
            "<div class='status-box'>Analytics will appear after processing...</div>",
            gr.update(visible=False, interactive=True),
            gr.update(visible=False),
            gr.update(value=None),
            gr.update(visible=False),
            None,  # Clear preview
            None   # Clear column config
        )

    def handle_document_upload(self, uploaded_file):
        """Handle document upload and update analyze status."""
        if not uploaded_file:
            return "<div class='status-box status-error'>❌ No file uploaded</div>"

        # Store the uploaded file
        self.current_uploaded_file = uploaded_file

        # Check if this is a PDF (only PDFs need vision recommendation)
        file_extension = Path(uploaded_file.name).suffix.lower()
        is_pdf = file_extension == '.pdf'

        if is_pdf:
            return "<div class='status-box status-success'>✅ PDF uploaded! Click 'Analyze Document' to get recommendations</div>"
        else:
            return "<div class='status-box status-info'>ℹ️ Non-PDF file - vision analysis not needed</div>"

    def refresh_vision_summary(self, vision_table):
        """Refresh the vision OCR summary based on current table contents."""
        import pandas as pd

        if vision_table is None or len(vision_table) == 0:
            return ""

        try:
            vision_yes = 0
            vision_no = 0

            if isinstance(vision_table, pd.DataFrame):
                for idx, row in vision_table.iterrows():
                    try:
                        recommendation = str(row.iloc[1]).upper()  # Recommended column
                        if recommendation == "YES":
                            vision_yes += 1
                        elif recommendation == "NO":
                            vision_no += 1
                    except (ValueError, TypeError, IndexError):
                        continue
            else:
                # Handle as list
                for row in vision_table:
                    try:
                        if len(row) >= 2:
                            recommendation = str(row[1]).upper()
                            if recommendation == "YES":
                                vision_yes += 1
                            elif recommendation == "NO":
                                vision_no += 1
                    except (ValueError, TypeError, IndexError):
                        continue

            summary_box = f"""
            <div class='status-box' style='background: rgba(6, 182, 212, 0.15) !important; border: 2px solid rgba(6, 182, 212, 0.5);'>
                <div style='font-size: 1.1em; font-weight: 600; margin-bottom: 0.5rem; color: #06b6d4;'>📊 Vision OCR Summary (Updated)</div>
                <div style='display: flex; gap: 2rem; justify-content: center; font-size: 1.05em;'>
                    <div>✅ <strong style='color: #34d399;'>{vision_yes} pages</strong> WITH vision</div>
                    <div>⚡ <strong style='color: #fbbf24;'>{vision_no} pages</strong> WITHOUT vision</div>
                </div>
            </div>
            """

            return summary_box

        except Exception as e:
            self.processor.logger.error(f"Error refreshing vision summary: {e}")
            return f"<div class='status-box status-error'>❌ Error refreshing summary: {str(e)}</div>"

    def analyze_document_for_vision(self, uploaded_file, page_ranges_str):
        """Analyze document and generate vision OCR recommendations."""
        from vision_recommendation_agent import VisionRecommendationAgent
        from api_client import APIClient

        if not uploaded_file:
            self.processor.logger.log_warning("Vision analysis: No file uploaded")
            return (
                "<div class='status-box status-error'>❌ No file uploaded</div>",
                None,
                gr.update(visible=False),  # table
                gr.update(visible=False),  # refresh button
                "",                         # summary box content
                gr.update(visible=False)   # summary box
            )

        try:
            # Log start of analysis
            self.processor.logger.log_step(f"🔎 Starting vision analysis for: {Path(uploaded_file.name).name}")
            if page_ranges_str and page_ranges_str.strip():
                self.processor.logger.log_step(f"📄 Page ranges: {page_ranges_str}")
            else:
                self.processor.logger.log_step("📄 Analyzing all pages")

            # Initialize vision recommendation agent
            api_client = APIClient(config)
            vision_agent = VisionRecommendationAgent(api_client, self.processor.logger)

            # Show analyzing status
            analyzing_status = "<div class='status-box status-processing'>⏳ Analyzing pages...</div>"

            # Analyze document
            self.processor.logger.log_step("🤖 Running vision recommendation agent...")
            result = vision_agent.process(
                input_data={
                    "file_path": uploaded_file.name,
                    "page_ranges": page_ranges_str if page_ranges_str and page_ranges_str.strip() else None
                }
            )

            if not result.success:
                self.processor.logger.error(f"Vision recommendation failed: {result.metadata.get('error')}")
                return (
                    f"<div class='status-box status-error'>❌ Analysis failed: {result.metadata.get('error')}</div>",
                    None,
                    gr.update(visible=False),  # table
                    gr.update(visible=False),  # refresh button
                    "",                         # summary box content
                    gr.update(visible=False)   # summary box
                )

            # Store recommendations
            self.vision_recommendations = result.content

            # Format for dataframe display (without thumbnails in table)
            table_data = []
            for rec in result.content:
                table_data.append([
                    rec["page"],
                    rec["recommendation"],
                    rec["reason"]
                ])

            # Create separate HTML gallery for thumbnails (listeners attached via MutationObserver in header)
            thumbnails_html = "<div id='thumbnailGallery' style='display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem;'>"

            for rec in result.content:
                if rec.get("thumbnail"):
                    page_num = rec["page"]
                    recommendation = rec["recommendation"]
                    border_color = "#10b981" if recommendation == "YES" else "#6b7280"
                    full_image = rec.get("full_image", rec["thumbnail"])  # Fallback to thumbnail if full_image not available
                    thumbnails_html += f"""
                    <div style='text-align: center;'>
                        <div style='font-size: 0.9em; color: #f0f9ff; margin-bottom: 0.5rem; font-weight: 600;'>
                            Page {page_num} - {recommendation}
                        </div>
                        <img class='thumbnail-image'
                             data-page='{page_num}'
                             data-full-image='data:image/png;base64,{full_image}'
                             src='data:image/png;base64,{rec["thumbnail"]}'
                             style='max-width: 100%; height: auto; cursor: pointer; border: 3px solid {border_color}; border-radius: 8px; transition: all 0.3s ease;'
                             onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 8px 16px rgba(0,0,0,0.3)';"
                             onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';"
                             title='Click to view full size' />
                    </div>
                    """

            thumbnails_html += "</div>"

            # Count recommendations
            vision_yes = sum(1 for rec in result.content if rec["recommendation"] == "YES")
            vision_no = sum(1 for rec in result.content if rec["recommendation"] == "NO")

            # Log analysis results
            self.processor.logger.log_success(f"✅ Vision analysis complete!")
            self.processor.logger.log_step(f"📊 Results: {vision_yes} pages WITH vision, {vision_no} pages WITHOUT vision")

            # Log individual page recommendations
            for rec in result.content:
                method_emoji = "🧠" if rec.get("method") == "vision" else "⚡"
                self.processor.logger.log_step(
                    f"  {method_emoji} Page {rec['page']}: {rec['recommendation']} - {rec['reason']} "
                    f"(confidence: {rec.get('confidence', 0):.2f}, method: {rec.get('method', 'unknown')})"
                )

            success_status = f"""
            <div class='status-box status-success'>
                ✅ Analysis complete!
                <br><strong>{vision_yes} pages</strong> need vision OCR,
                <strong>{vision_no} pages</strong> don't
                <br>Edit table if needed, then click Process
            </div>
            """

            summary_box = f"""
            <div class='status-box' style='background: rgba(6, 182, 212, 0.15) !important; border: 2px solid rgba(6, 182, 212, 0.5);'>
                <div style='font-size: 1.1em; font-weight: 600; margin-bottom: 0.5rem; color: #06b6d4;'>📊 Vision OCR Summary</div>
                <div style='display: flex; gap: 2rem; justify-content: center; font-size: 1.05em;'>
                    <div>✅ <strong style='color: #34d399;'>{vision_yes} pages</strong> WITH vision</div>
                    <div>⚡ <strong style='color: #fbbf24;'>{vision_no} pages</strong> WITHOUT vision</div>
                </div>
            </div>
            """

            # Return status, table data, summary, and thumbnails for Analyze tab display
            return (
                success_status,
                table_data,
                gr.update(visible=True),  # table visible
                gr.update(visible=True),  # refresh button visible
                summary_box,               # summary box content
                gr.update(visible=True),   # summary box visible
                thumbnails_html,           # thumbnail gallery HTML
                gr.update(visible=True)    # gallery visible
            )

        except Exception as e:
            self.processor.logger.error(f"Error analyzing document for vision: {e}")
            import traceback
            traceback.print_exc()
            return (
                f"<div class='status-box status-error'>❌ Error: {str(e)}</div>",
                None,
                gr.update(visible=False),  # table
                gr.update(visible=False),  # refresh button
                "",                         # summary box content
                gr.update(visible=False),  # summary box
                "",                         # thumbnail gallery HTML
                gr.update(visible=False)   # gallery
            )

    def create_interface(self):
        """Create the Gradio interface."""

        # Custom JavaScript for thumbnail click handlers and overlay
        custom_js = """
        function() {
            console.log('Gradio custom JS executing...');

            // Setup overlay close handlers
            function setupOverlayHandlers() {
                const overlay = document.getElementById('imageOverlay');
                const closeBtn = document.getElementById('overlayClose');

                if (overlay && !overlay.hasAttribute('data-handlers-attached')) {
                    overlay.setAttribute('data-handlers-attached', 'true');

                    // Click on overlay background to close
                    overlay.addEventListener('click', function(e) {
                        if (e.target.id === 'imageOverlay') {
                            overlay.classList.remove('show');
                            document.body.style.overflow = 'auto';
                        }
                    });

                    // Click on X button to close
                    if (closeBtn) {
                        closeBtn.addEventListener('click', function(e) {
                            e.stopPropagation();
                            overlay.classList.remove('show');
                            document.body.style.overflow = 'auto';
                        });
                    }

                    console.log('✅ Overlay close handlers attached');
                }
            }

            // Function to attach click listeners to thumbnails
            function attachThumbnailListeners() {
                const images = document.querySelectorAll('.thumbnail-image');
                let attachedCount = 0;

                images.forEach(function(img) {
                    if (!img.hasAttribute('data-click-attached')) {
                        img.setAttribute('data-click-attached', 'true');
                        img.addEventListener('click', function() {
                            // Use full-resolution image instead of thumbnail
                            const fullImageSrc = this.getAttribute('data-full-image') || this.src;
                            const pageNum = this.getAttribute('data-page');

                            const overlay = document.getElementById('imageOverlay');
                            const overlayImg = document.getElementById('overlayImage');
                            const caption = document.getElementById('overlayCaption');

                            if (overlay && overlayImg && caption) {
                                overlayImg.src = fullImageSrc;
                                caption.textContent = 'Page ' + pageNum;
                                overlay.classList.add('show');
                                document.body.style.overflow = 'hidden';
                            }
                        });
                        attachedCount++;
                    }
                });

                if (attachedCount > 0) {
                    console.log('✅ Attached click listeners to ' + attachedCount + ' thumbnails');
                }
            }

            // Setup overlay handlers immediately
            setupOverlayHandlers();

            // Use MutationObserver to detect when thumbnails are added
            const observer = new MutationObserver(function(mutations) {
                attachThumbnailListeners();
                setupOverlayHandlers(); // Re-check in case overlay was re-rendered
            });

            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Try immediately
            attachThumbnailListeners();

            console.log('🔍 MutationObserver set up for thumbnails');
        }
        """

        with gr.Blocks(title="Document Ingestion - Agent Edition", css=self.get_css(), js=custom_js) as demo:

            # Header with Navigation
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

                <!-- Image Overlay Modal -->
                <div id="imageOverlay">
                    <span id="overlayClose">&times;</span>
                    <img id="overlayImage" src="" alt="Page preview">
                    <div id="overlayCaption"></div>
                </div>

                <script>
                function showImageOverlay(imageSrc, pageNum) {
                    const overlay = document.getElementById('imageOverlay');
                    const img = document.getElementById('overlayImage');
                    const caption = document.getElementById('overlayCaption');

                    img.src = imageSrc;
                    caption.textContent = 'Page ' + pageNum;
                    overlay.classList.add('show');

                    // Prevent body scroll when overlay is open
                    document.body.style.overflow = 'hidden';
                }

                function closeOverlay(event) {
                    // Only close if clicking the background or close button
                    if (event.target.id === 'imageOverlay' || event.target.id === 'overlayClose') {
                        const overlay = document.getElementById('imageOverlay');
                        overlay.classList.remove('show');
                        document.body.style.overflow = 'auto';
                    }
                }

                // Close overlay with Escape key
                document.addEventListener('keydown', function(event) {
                    if (event.key === 'Escape') {
                        const overlay = document.getElementById('imageOverlay');
                        if (overlay.classList.contains('show')) {
                            overlay.classList.remove('show');
                            document.body.style.overflow = 'auto';
                        }
                    }
                });
                </script>
            """)

            # Navigation Bar
            with gr.Row():
                document_nav_btn = gr.Button("📄 DOCUMENT OCR", size="lg", elem_classes="nav-btn nav-btn-doc")
                excel_nav_btn = gr.Button("📊 EXCEL PROCESSOR", size="lg", elem_classes="nav-btn nav-btn-excel")

            # PAGE 1: Document OCR (existing interface)
            document_page = gr.Column(visible=True)
            with document_page:
                with gr.Row():
                    # Left Panel - Controls
                    with gr.Column(scale=1, elem_classes="left-panel"):

                        gr.HTML('<div class="section-header">📁 Upload Document</div>')
                        pdf_input = gr.File(label="File type: PDF, MD, TXT", file_types=[".pdf", ".md", ".markdown", ".txt"])

                        # Page ranges input
                        page_ranges_input = gr.Textbox(
                            label="Page Ranges (Optional)",
                            placeholder="e.g., 1-5, 10, 15-20 (leave blank for all pages)",
                            info="Specify pages to process. Examples: '1-5' for pages 1-5, '1,3,5' for specific pages, '1-3,10-15' for multiple ranges"
                        )

                        with gr.Row():
                            process_btn = gr.Button("🚀 Process", elem_classes="primary-btn")
                            clear_btn = gr.Button("🗑️ Clear", visible=False, elem_classes="secondary-btn")
                            abort_btn = gr.Button("🚫 Abort", visible=False, elem_classes="secondary-btn")

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

                        # Feedback Form Section
                        if config.tally_form_id:
                            gr.HTML('<div class="section-header">💬 Feedback</div>')
                            gr.HTML(f"""
                                <div class="feedback-form-container">
                                    <div style="padding: 1.5rem; text-align: center;">
                                        <p style="margin-bottom: 1rem; color: #94a3b8;">Have feedback or suggestions?</p>
                                        <a href="https://tally.so/r/{config.tally_form_id}"
                                           target="_blank"
                                           style="
                                               display: inline-block;
                                               padding: 0.75rem 1.5rem;
                                               background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
                                               color: white;
                                               text-decoration: none;
                                               border-radius: 8px;
                                               font-weight: 600;
                                               transition: transform 0.2s;
                                           "
                                           onmouseover="this.style.transform='scale(1.05)'"
                                           onmouseout="this.style.transform='scale(1)'">
                                            📝 Open Feedback Form
                                        </a>
                                    </div>
                                </div>
                            """)

                    # Right Panel - Results
                    with gr.Column(scale=2):

                        # Processing Options - Dropdown menus (checkboxes don't work in Gradio)
                        gr.HTML("""
                        <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.1);">
                            <h3 style="margin: 0; color: #f0f9ff;">⚙️ Processing Options</h3>
                        </div>
                        """)

                        with gr.Row():
                            enable_summary_toggle = gr.Dropdown(
                                label="📊 Summary Generation",
                                choices=["Disabled", "Enabled"],
                                value="Disabled",
                                info="Generate executive summary of document"
                            )
                            enable_quality_report_toggle = gr.Dropdown(
                                label="✅ Quality Report",
                                choices=["Disabled", "Enabled"],
                                value="Disabled",
                                info="Detailed quality analysis and metrics"
                            )
                            enable_raw_ocr_toggle = gr.Dropdown(
                                label="📝 Raw OCR Output",
                                choices=["Disabled", "Enabled"],
                                value="Disabled",
                                info="Unformatted OCR extraction results"
                            )

                        with gr.Tabs():
                            with gr.Tab("🔎 Analyze"):
                                gr.HTML('<div class="section-header" style="text-align: center; margin-bottom: 20px;">📊 AI Vision OCR Analysis</div>')

                                gr.Markdown("""
                                ### How it works:
                                1. **Upload a PDF** in the left panel
                                2. **Click "Analyze Document"** below to get AI recommendations
                                3. **Review the table** - AI will recommend YES/NO for vision OCR per page
                                4. **Edit if needed** - Click any cell to change YES ↔ NO
                                5. **Click "🚀 Process"** to run with your settings

                                **Why analyze first?**
                                - Saves API costs by only using vision where needed
                                - Faster processing for text-only pages
                                - You control the final decision
                                """)

                                # Center-aligned button row
                                with gr.Row():
                                    analyze_btn = gr.Button("🔎 Analyze Document", size="lg", variant="secondary", scale=1)

                                analyze_status = gr.HTML(value="<div class='status-box'>⏳ Upload a PDF, then click Analyze</div>")

                                # Show vision recommendation table here in main view
                                vision_recommendation_table_display = gr.Dataframe(
                                    label="Page-by-Page Vision Recommendations (Editable)",
                                    headers=["Page", "Recommended", "Reason"],
                                    datatype=["number", ["YES", "NO"], "str"],
                                    interactive=True,
                                    row_count=(1, "dynamic"),
                                    col_count=(3, "fixed"),
                                    wrap=True,
                                    visible=False
                                )

                                # Thumbnail gallery (clickable)
                                vision_thumbnails_gallery = gr.HTML(
                                    value="",
                                    visible=False,
                                    label="Page Thumbnails (Click to enlarge)"
                                )

                                gr.Markdown("**💡 Tip:** Change 'YES' to 'NO' (or vice versa) in the Recommended column to override AI suggestions.")

                                # Summary box that updates after table edits
                                with gr.Row():
                                    refresh_summary_btn = gr.Button("🔄 Refresh Summary", variant="secondary", size="sm", visible=False)

                                vision_summary_box = gr.HTML(value="", visible=False)

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
                                        summary_download_output = gr.File(label="Summary Downloads", interactive=False, visible=False, type="filepath")

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
                                        evaluation_download_output = gr.File(label="Evaluation Report", interactive=False, visible=False, type="filepath")

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
                                file_output = gr.File(label="Processed File", interactive=False, type="filepath")
                                analytics_output = gr.HTML(value="<div class='status-box'>Analytics will appear after processing...</div>")

                            with gr.Tab("📋 Analysis Logs"):
                                logs_output = gr.Textbox(
                                    value="Processing logs will appear here...",
                                    label="",
                                    lines=30,
                                    max_lines=50,
                                    show_copy_button=True,
                                    interactive=False,
                                    elem_classes=["logs-output"]
                                )

                                # AI Metadata Cleaning Report
                                gr.HTML('<div class="section-header" style="margin-top: 20px;">🧹 AI Metadata Cleaning Report</div>')
                                cleaning_report_output = gr.Markdown(
                                    value="*AI metadata cleaning report will appear here after processing...*",
                                    show_copy_button=True,
                                    visible=True
                                )

            # PAGE 2: Excel Processor (dedicated full-width interface)
            excel_page = gr.Column(visible=False)
            with excel_page:
                gr.HTML('<div class="section-header" style="text-align: center; font-size: 1.5rem;">📊 Excel Table Processor</div>')
                gr.Markdown("**Upload and configure how to extract data from Excel/CSV files**")

                with gr.Row():
                    # Left: Upload and Configuration
                    with gr.Column(scale=1):
                        gr.HTML('<div class="section-header">📁 Upload Excel File</div>')
                        excel_input = gr.File(
                            label="File type: Excel or CSV",
                            file_types=[".xlsx", ".xls", ".csv"]
                        )

                        gr.HTML('<div class="section-header">⚙️ Table Structure</div>')
                        excel_header_rows = gr.Number(
                            label="Number of Header Rows",
                            value=1,
                            minimum=0,
                            maximum=10,
                            step=1,
                            info="How many rows at the top are headers (not data)"
                        )

                        excel_include_headers = gr.Dropdown(
                            choices=[("Off", False), ("On", True)],
                            value=False,
                            label="Include Section Headers",
                            info="Add H2 section headers to group related data"
                        )

                        with gr.Row():
                            excel_process_btn = gr.Button("🚀 Process Excel", elem_classes="primary-btn")
                            excel_clear_btn = gr.Button("🗑️ Clear", visible=False, elem_classes="secondary-btn")
                            excel_abort_btn = gr.Button("🚫 Abort", visible=False, elem_classes="secondary-btn")

                        gr.HTML('<div class="section-header">📊 Status</div>')
                        excel_status_output = gr.HTML(value="<div class='status-box'>⏳ Ready to process Excel file...</div>")

                        gr.HTML('<div class="section-header">📈 Metrics</div>')
                        excel_metrics_output = gr.HTML(value="<div class='status-box'>Metrics will appear during processing...</div>")

                    # Right: Preview and Column Configuration
                    with gr.Column(scale=2):
                        gr.HTML('<div class="section-header">📑 Sheet Selection & Configuration</div>')

                        with gr.Row():
                            excel_sheet_dropdown = gr.Dropdown(
                                choices=[],
                                value=None,
                                label="Select Sheet to Configure",
                                info="Choose one sheet at a time",
                                visible=False
                            )

                        gr.Markdown("**Workflow:** Select sheet → Preview data → Configure columns → Save → Repeat for other sheets → Process")

                        gr.HTML('<div class="section-header">👁️ Preview (First 10 rows)</div>')
                        excel_current_sheet_label = gr.HTML(value="", visible=False)
                        excel_preview = gr.Dataframe(
                            label="Data Preview",
                            interactive=False,
                            wrap=True
                        )

                        gr.HTML('<div class="section-header">🎛️ Column Configuration</div>')
                        gr.Markdown("""
                        **Configure how each column should be processed:**
                        - **Label 1, Label 2, Label 3...** - Columns that form the row identifier (concatenated left-to-right with " - ")
                        - **Data** - Columns containing values to extract
                        - **Ignore** - Skip this column entirely
                        """)

                        excel_column_config = gr.Dataframe(
                            label="Column Roles",
                            headers=["Column", "Role"],
                            datatype=["str", "str"],
                            interactive=True,
                            row_count=(1, "dynamic"),
                            col_count=(2, "fixed")
                        )

                        with gr.Row():
                            excel_save_config_btn = gr.Button("💾 Save Configuration", size="sm", visible=False, elem_classes="primary-btn")
                            excel_clear_saved_btn = gr.Button("🗑️ Clear All Saved", size="sm", visible=False, elem_classes="secondary-btn")

                        gr.HTML('<div class="section-header">✅ Saved Configurations</div>')
                        excel_saved_sheets_display = gr.HTML(
                            value="<div class='status-box'>No sheets configured yet. Select a sheet above, configure columns, then click Save.</div>"
                        )

                # Results Section (Full Width)
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="section-header">📄 Results</div>')

                        with gr.Tabs():
                            with gr.Tab("📄 Formatted Output"):
                                excel_processing_animation = gr.HTML(value="", visible=False)
                                excel_content_output = gr.Markdown(
                                    value="*Processed Excel content will appear here...*",
                                    show_copy_button=True
                                )

                            with gr.Tab("💾 Download"):
                                excel_file_output = gr.File(label="Processed File", interactive=False, type="filepath")
                                excel_analytics_output = gr.HTML(value="<div class='status-box'>Analytics will appear after processing...</div>")

            # Hidden components for cross-page compatibility
            web_event_bridge = gr.Textbox(visible=False, elem_id="web-event-bridge")
            dummy_excel_config = gr.State(None)
            dummy_header_rows = gr.State(None)
            dummy_include_headers = gr.State(None)

            # Navigation handlers - switch between pages and update button styles
            document_nav_btn.click(
                fn=lambda: (
                    gr.update(visible=True),  # Show document page
                    gr.update(visible=False),  # Hide excel page
                    gr.update(elem_classes="nav-btn nav-btn-doc"),  # Active: cyan
                    gr.update(elem_classes="nav-btn nav-btn-excel")  # Inactive: gray
                ),
                outputs=[document_page, excel_page, document_nav_btn, excel_nav_btn],
                show_api=False
            )

            excel_nav_btn.click(
                fn=lambda: (
                    gr.update(visible=False),  # Hide document page
                    gr.update(visible=True),  # Show excel page
                    gr.update(elem_classes="nav-btn nav-btn-excel-inactive"),  # Inactive: gray
                    gr.update(elem_classes="nav-btn nav-btn-excel-active")  # Active: cyan
                ),
                outputs=[document_page, excel_page, document_nav_btn, excel_nav_btn],
                show_api=False
            )

            # Document page: PDF upload handler to update analyze status
            pdf_input.upload(
                fn=self.handle_document_upload,
                inputs=[pdf_input],
                outputs=[analyze_status],
                show_api=False
            )

            # Document page: Analyze button for vision recommendations
            analyze_btn.click(
                fn=self.analyze_document_for_vision,
                inputs=[pdf_input, page_ranges_input],
                outputs=[
                    analyze_status,
                    vision_recommendation_table_display,
                    vision_recommendation_table_display,  # visibility
                    refresh_summary_btn,                  # visibility
                    vision_summary_box,                   # content
                    vision_summary_box,                   # visibility
                    vision_thumbnails_gallery,            # gallery HTML
                    vision_thumbnails_gallery             # gallery visibility
                ],
                show_api=False
            )

            # Refresh summary button
            refresh_summary_btn.click(
                fn=self.refresh_vision_summary,
                inputs=[vision_recommendation_table_display],
                outputs=[vision_summary_box],
                show_api=False
            )

            # Excel page: File upload handler to show preview and config
            excel_input.upload(
                fn=self.handle_excel_upload,
                inputs=[excel_input],
                outputs=[excel_preview, excel_column_config, excel_sheet_dropdown, excel_current_sheet_label,
                        excel_save_config_btn, excel_clear_saved_btn, excel_saved_sheets_display],
                show_api=False
            )

            # Excel page: Sheet dropdown change - preview that sheet
            excel_sheet_dropdown.change(
                fn=self.preview_excel_sheet,
                inputs=[excel_input, excel_sheet_dropdown],
                outputs=[excel_preview, excel_column_config, excel_current_sheet_label],
                show_api=False
            )

            # Excel page: Save configuration button
            excel_save_config_btn.click(
                fn=self.save_sheet_configuration,
                inputs=[excel_sheet_dropdown, excel_column_config, excel_header_rows, excel_include_headers],
                outputs=[excel_saved_sheets_display],
                show_api=False
            )

            # Excel page: Clear saved configurations button
            excel_clear_saved_btn.click(
                fn=self.clear_saved_configurations,
                outputs=[excel_saved_sheets_display],
                show_api=False
            )

            # Document page: Process button (no Excel config needed)
            process_click = process_btn.click(
                fn=self.process_wrapper,            # generator
                inputs=[pdf_input, page_ranges_input, dummy_excel_config, dummy_header_rows, dummy_include_headers,
                       enable_summary_toggle, enable_quality_report_toggle, enable_raw_ocr_toggle, vision_recommendation_table_display],
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, processing_animation, raw_ocr_output, logs_output, cleaning_report_output],
                show_api=False,
                show_progress="full"
            )

            # Excel page: Process button
            excel_process_btn.click(
                fn=self.process_excel_wrapper,
                inputs=[excel_input],
                outputs=[excel_content_output, excel_status_output, excel_metrics_output, excel_file_output,
                        excel_analytics_output, excel_clear_btn, excel_abort_btn, excel_processing_animation],
                show_api=False,
                show_progress="full"
            )
            
            # Document page: Clear button
            clear_btn.click(
                fn=self.clear_all,
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, page_ranges_input, pdf_input, processing_animation, raw_ocr_output,
                        analyze_status, vision_recommendation_table_display, vision_recommendation_table_display, logs_output, cleaning_report_output],
                show_api=False
            )

            # Excel page: Clear button
            excel_clear_btn.click(
                fn=self.clear_excel,
                outputs=[excel_content_output, excel_status_output, excel_metrics_output, excel_file_output,
                        excel_analytics_output, excel_clear_btn, excel_abort_btn, excel_input, excel_processing_animation,
                        excel_preview, excel_column_config],
                show_api=False
            )

            # Document page: Abort button
            abort_btn.click(
                fn=self.abort_processing,
                inputs=None,
                outputs=[content_output, summary_output, summary_stats_output, evaluation_comparison_summary, openai_evaluation, anthropic_evaluation, evaluation_stats_output,
                        status_output, metrics_output, file_output, analytics_output, clear_btn, abort_btn, processing_animation],
                show_api=False
            )

            # Excel page: Abort button
            excel_abort_btn.click(
                fn=self.abort_processing,
                inputs=None,
                outputs=[excel_content_output, excel_status_output, excel_metrics_output, excel_file_output,
                        excel_analytics_output, excel_clear_btn, excel_abort_btn, excel_processing_animation],
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
            raw_content = self.processor.ocr_engine.get_debug_raw_ocr_content()
            # Add debug info if no content captured
            if "No raw OCR content captured" in raw_content:
                debug_info = f"\n\n🔍 Debug Info:\n"
                debug_info += f"- OCR Engine exists: Yes\n"
                debug_info += f"- Debug content list size: {len(self.processor.ocr_engine.debug_raw_ocr_content)}\n"
                debug_info += f"- Vision calls made: {self.processor.ocr_engine.vision_calls_used}\n"
                return raw_content + debug_info
            return raw_content
        else:
            return "⚠️ Error: OCR engine not initialized. Cannot retrieve raw OCR content."

def create_ui():
    """Factory function to create the UI."""
    interface = OCRInterface()
    return interface.create_interface()