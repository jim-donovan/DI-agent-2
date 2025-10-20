"""
Text Corruption Detection
Aggressive detection of OCR corruption patterns
"""

import re
from typing import Tuple, List
from config import config

class CorruptionDetector:
    """Aggressive corruption detection for OCR text."""
    
    @classmethod
    def calculate_corruption_score(cls, text: str) -> float:
        """
        Calculate corruption score for text without vision limits check.
        
        Args:
            text: Text to analyze
            
        Returns:
            Corruption score (0.0 = clean, higher = more corrupted)
        """
        total_score, _ = cls.calculate_corruption_score_detailed(text)
        return total_score
    
    @classmethod
    def calculate_corruption_score_detailed(cls, text: str) -> Tuple[float, dict]:
        """
        Calculate corruption score with detailed breakdown.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (total_score, detailed_scores_dict)
        """
        issues = []
        detailed_scores = {}
        
        # Run all corruption checks and track individual scores
        detailed_scores['table_patterns'] = cls._check_table_patterns(text, issues)
        detailed_scores['character_spacing'] = cls._check_character_spacing(text, issues)
        detailed_scores['reversed_words'] = cls._check_reversed_words(text, issues)
        detailed_scores['single_chars'] = cls._check_single_chars(text, issues)
        detailed_scores['encoding_issues'] = cls._check_encoding_issues(text, issues)
        detailed_scores['financial_corruption'] = cls._check_financial_corruption(text, issues)
        detailed_scores['symbols'] = cls._check_symbols(text, issues)
        detailed_scores['content_sparsity'] = cls._check_content_sparsity(text, issues)
        
        total_score = sum(detailed_scores.values())
        return total_score, detailed_scores
    
    @classmethod
    def should_use_vision(cls, text: str, vision_calls_used: int) -> Tuple[bool, str]:
        """
        Determine if vision OCR should be used based on corruption analysis.
        
        Args:
            text: Text to analyze
            vision_calls_used: Number of vision calls already made
            
        Returns:
            Tuple of (should_use_vision, reason)
        """
        
        # Check limits first
        if vision_calls_used >= config.max_vision_calls_per_doc:
            return False, f"Vision limit reached ({config.max_vision_calls_per_doc})"
        
        #if len(text.strip()) < config.min_text_length:
        #    return False, f"Text too short ({len(text.strip())})"
        
        corruption_score = 0.0
        issues = []
        
        # Run all corruption checks
        corruption_score += cls._check_table_patterns(text, issues)
        corruption_score += cls._check_character_spacing(text, issues)
        corruption_score += cls._check_reversed_words(text, issues)
        corruption_score += cls._check_single_chars(text, issues)
        corruption_score += cls._check_encoding_issues(text, issues)
        corruption_score += cls._check_financial_corruption(text, issues)
        corruption_score += cls._check_symbols(text, issues)
        corruption_score += cls._check_content_sparsity(text, issues)
        
        should_use = corruption_score >= config.vision_corruption_threshold
        
        reason = "; ".join(issues) if should_use else f"clean_text(score:{corruption_score:.2f})"
        
        return should_use, reason
    
    @classmethod
    def _check_table_patterns(cls, text: str, issues: List[str]) -> float:
        """Check for table-like patterns including nested/complex tables."""
        lines = text.split('\n')
        separator_lines = 0
        separator_types = []
        table_indicators = 0
        financial_table_indicators = 0
        nested_header_indicators = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
                
            # Calculate the ratio of table separator characters to total characters
            separator_chars = sum(1 for c in stripped if c in '|-_=+')
            total_chars = len(stripped)
            
            # Detect nested table headers (multiple column groups)
            # Pattern: Multiple capitalized phrases separated by spaces/tabs
            if i < len(lines) - 1:
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                if re.findall(r'[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+', stripped) and len(stripped.split()) >= 2:
                    # Check if next line has sub-headers or values
                    if next_line and ('$' in next_line or '%' in next_line or re.search(r'\d', next_line)):
                        nested_header_indicators += 1
                        
            # Detect different types of separator patterns:
            
            # Type 1: Pure separator lines (60%+ separator characters, lowered threshold)
            # Examples: "-------", "======", "_____", "|---|---|", "--------    --------"
            if total_chars > 2 and separator_chars / total_chars >= 0.6:
                separator_lines += 1
                separator_types.append('pure')
                continue
            
            # Type 2: Table borders with pipes and dashes
            # Examples: "|----+----|", "+----+----+", "| -- | -- |"
            if re.match(r'^[\|\+]?[\s\-_=]+[\|\+]?.*[\|\+]?$', stripped) and separator_chars >= 3:
                separator_lines += 1
                separator_types.append('border')
                continue
                
            # Type 3: Mixed separator patterns with spacing
            # Examples: "= = = = =", "- - - - -", "___ ___ ___"
            if re.match(r'^[\s\-_=\|]+$', stripped) and separator_chars >= 3 and total_chars >= 5:
                separator_lines += 1
                separator_types.append('spaced')
                continue
                
            # Type 4: ASCII table junctions
            # Examples: "+===+===+", "├───┼───┤", but fallback to ASCII
            if re.match(r'^[\+\|\-_=\s]+$', stripped) and '+' in stripped and separator_chars >= 3:
                separator_lines += 1
                separator_types.append('junction')
                continue
            
            # Type 5: Simple dash/underscore patterns (new)
            # Examples: "--------    --------    --------"
            if re.match(r'^[\-_]{2,}(\s+[\-_]{2,})+$', stripped):
                separator_lines += 1
                separator_types.append('simple_dash')
                continue
                
            # Type 6: Pipe-separated content (table data indicator)
            # Examples: "| Column 1 | Column 2 | Column 3 |"
            pipe_count = stripped.count('|')
            if pipe_count >= 2:
                table_indicators += 1
                if pipe_count >= 3:  # Strong table indicator
                    separator_types.append('pipe_data')
            
            # Type 7: OCR Table Pattern Detection (based on visual layout corruption)
            # These patterns indicate text that was likely tabular but got mangled by OCR
            
            # Pattern 1: Multiple consecutive spaces (table column separation)
            if re.search(r'\w\s{3,}\w', stripped):  # 3+ spaces between words
                table_indicators += 1
                separator_types.append('space_columns')
            
            # Pattern 2: Short lines with financial/numeric data (table cells)
            if len(stripped.split()) <= 4 and re.search(r'[\$\d%]', stripped):
                financial_table_indicators += 1
            
            # Pattern 3: Lines with mixed text and numbers (typical table row pattern)
            words = stripped.split()
            if len(words) >= 2:
                has_text = any(word.isalpha() and len(word) > 2 for word in words)
                has_numbers = any(re.search(r'[\$\d%]', word) for word in words)
                if has_text and has_numbers:
                    financial_table_indicators += 1
            
            # Pattern 4: Repeated similar line patterns (table rows)
            # This would need context from previous lines - simplified version
            if re.match(r'^[A-Z][a-z\s]+[\$\d%]', stripped):  # "Text description $amount" pattern
                financial_table_indicators += 1
        
        # Calculate table score based on multiple factors
        score = 0.0
        total_lines = len([line for line in lines if line.strip()])
        
        # Very strong indicator: Nested table headers detected
        if nested_header_indicators >= 1:
            issues.append(f"nested_table_headers_detected({nested_header_indicators} instances)")
            score = 1.0  # Always use vision for nested tables
        
        # Strong indicators: Multiple separator lines
        elif separator_lines >= 2:
            type_summary = ', '.join(f"{t}:{separator_types.count(t)}" for t in set(separator_types))
            issues.append(f"table_patterns_detected({separator_lines} separators: {type_summary})")
            score = 0.8
        
        # Moderate indicators: Single separator + pipe data
        elif separator_lines >= 1 and table_indicators >= 1:
            issues.append(f"table_structure_detected({separator_lines} separators, {table_indicators} pipe lines)")
            score = 0.6
            
        # Single separator line with multiple content lines (common table pattern)
        elif separator_lines >= 1 and total_lines >= 3:
            type_summary = ', '.join(f"{t}:{separator_types.count(t)}" for t in set(separator_types))
            issues.append(f"single_separator_table({separator_lines} separator, {total_lines} total lines: {type_summary})")
            score = 0.5
            
        # OCR table corruption patterns (visual layout issues)
        elif financial_table_indicators >= 5:
            issues.append(f"ocr_table_patterns({financial_table_indicators} structured data lines)")
            score = 0.5
        
        # Multiple pipe-separated lines only
        elif table_indicators >= 3:
            issues.append(f"pipe_table_detected({table_indicators} pipe-separated lines)")
            score = 0.4
        
        # Moderate structured data (potential table remnants)
        elif financial_table_indicators >= 3:
            issues.append(f"structured_data_detected({financial_table_indicators} data patterns)")
            score = 0.3
        
        return score

    @classmethod
    def _check_character_spacing(cls, text: str, issues: List[str]) -> float:
        """Check for character spacing corruption."""
        space_count = text.count(' ')
        char_count = len(text.replace(' ', '').replace('\n', ''))
        
        if char_count > 0:
            space_ratio = space_count / char_count
            if space_ratio > 0.5:
                issues.append(f"character_spacing_corruption(ratio:{space_ratio:.2f})")
                return 0.2
        return 0.0
    
    @classmethod
    def _check_reversed_words(cls, text: str, issues: List[str]) -> float:
        """Check for reversed word patterns."""
        words = text.split()
        reversed_count = 0
        
        reversed_patterns = {
            'prefixes': ['gni', 'noi', 'eci', 'de'],
            'suffixes': ['erp', 'bus', 'noc', 'noit'],
            'known_reversed': ['ynapmoc', 'ecnarusni', 'dradnats']
        }
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if len(clean_word) >= 3:
                if (any(clean_word.startswith(p) for p in reversed_patterns['prefixes']) or
                    any(clean_word.endswith(s) for s in reversed_patterns['suffixes']) or
                    clean_word in reversed_patterns['known_reversed']):
                    reversed_count += 1
        
        if len(words) > 0 and reversed_count / len(words) > 0.05:
            issues.append(f"reversed_words({reversed_count}/{len(words)})")
            return 0.6
        return 0.0
    
    @classmethod
    def _check_single_chars(cls, text: str, issues: List[str]) -> float:
        """Check for excessive single character words."""
        words = text.split()
        single_chars = len([w for w in words if len(w) == 1 and w.isalpha()])
        
        if len(words) > 0 and single_chars / len(words) > 0.1:
            issues.append(f"single_char_words({single_chars})")
            return 0.2
        return 0.0
    
    @classmethod
    def _check_encoding_issues(cls, text: str, issues: List[str]) -> float:
        """Check for encoding corruption."""
        weird_chars = len(re.findall(r'[^\w\s.,!?;:()\-$%/€£¥\'"&@#*]', text))
        
        if weird_chars > len(text) * 0.01:
            issues.append(f"encoding_issues({weird_chars})")
            return 0.4
        return 0.0
    
    @classmethod
    def _check_financial_corruption(cls, text: str, issues: List[str]) -> float:
        """Check for financial pattern corruption."""
        suspicious_money = len(re.findall(r'\$\d*0{2,},\d{1,2}', text))
        
        if suspicious_money > 0:
            issues.append(f"financial_corruption({suspicious_money})")
            return 0.2
        return 0.0
      
    
    @classmethod
    def _check_symbols(cls, text: str, issues: List[str]) -> float:
        """Check for symbols that need conversion."""
        checkmark_indicators = text.count('✓') + text.count('✔') + text.count('√')
        
        if checkmark_indicators > 0:
            issues.append(f"checkmark_symbols({checkmark_indicators})")
            return 0.5        
        return 0.0
    
    @classmethod
    def _check_content_sparsity(cls, text: str, issues: List[str]) -> float:
        """Check for sparse content."""
        lines = text.split('\n')
        substantial_lines = [line for line in lines if len(line.strip()) > 20]
        
        if len(substantial_lines) < 2:  # Default threshold
            issues.append(f"sparse_content(substantial_lines:{len(substantial_lines)})")
            return 0.4
        return 0.0