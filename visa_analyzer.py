import re
from typing import List
from dataclasses import dataclass

@dataclass
class SponsorshipAnalysis:
    likely_sponsors: bool
    confidence: float
    reasoning: str
    positive_indicators: List[str]
    negative_indicators: List[str]

class VisaSponsorshipAnalyzer:
    def __init__(self):
        # EXPLICIT NO SPONSORSHIP patterns (90% confidence NO)
        self.no_sponsorship_patterns = [
            # Direct visa restrictions
            r"no visa sponsorship",
            r"sponsorship not available",
            r"we do not sponsor",
            r"will not sponsor",
            r"cannot sponsor",
            r"no h1b sponsorship",
            r"no immigration sponsorship",
            r"visa sponsorship is not provided",
            r"we are unable to sponsor",
            r"not able to sponsor",
            r"does not sponsor",
            r"unable to provide sponsorship",
            r"not eligible for visa sponsorship",
            
            # Work authorization requirements
            r"must be authorized to work",
            r"authorized to work in",
            r"eligible to work in",
            r"must have authorization to work",
            r"must be legally authorized",
            r"legal authorization to work",
            r"work authorization required",
            r"employment authorization required",
            r"require work authorization",
            r"current work authorization",
            
            # Citizenship/permanent residency requirements
            r"citizens only",
            r"citizenship required",
            r"must be a citizen",
            r"citizen or permanent resident",
            r"us citizens and permanent residents",
            r"green card holders only",
            r"permanent resident status required",
            r"must be a us citizen",
            r"only us citizens",
            r"us citizen or permanent resident",
            
            # Security clearance (typically requires citizenship)
            r"security clearance required",
            r"clearance required",
            r"must possess.*clearance",
            r"active security clearance",
            r"secret clearance",
            r"top secret clearance",
            r"confidential clearance",
            r"only u\.s\. citizens are eligible",
            r"must be eligible for.*clearance",
            r"due to.*government contract requirements",
        ]
        
        # EXPLICIT YES SPONSORSHIP patterns (90% confidence YES)
        self.yes_sponsorship_patterns = [
            r"visa sponsorship available",
            r"h1b friendly",
            r"will sponsor qualified candidates",
            r"sponsorship provided",
            r"immigration support",
            r"visa support available",
            r"we sponsor visas",
            r"h1b sponsorship available",
            r"visa assistance provided",
            r"immigration assistance",
            r"work visa support",
            r"h1b transfers welcome",
            r"will provide sponsorship",
            r"sponsor h1b",
            r"sponsor work visa",
            r"provides visa sponsorship",
            r"offers visa sponsorship",
            r"sponsorship is available",
            r"we will sponsor",
            r"able to sponsor",
            r"can sponsor",
        ]

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        text = re.sub(r'\s+', ' ', text.lower().strip())
        return text

    def find_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Find all matching patterns in text"""
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.extend(found)
        return matches

    def analyze_sponsorship(self, text: str) -> SponsorshipAnalysis:
        """Analyze text for visa sponsorship indicators"""
        
        if not text or len(text.strip()) < 50:
            return SponsorshipAnalysis(
                likely_sponsors=False,
                confidence=0.0,
                reasoning="Text too short for analysis",
                positive_indicators=[],
                negative_indicators=["Insufficient text"]
            )
        
        cleaned_text = self.clean_text(text)
        
        # Step 1: Check for explicit NO sponsorship patterns (highest priority)
        no_sponsorship_matches = self.find_patterns(cleaned_text, self.no_sponsorship_patterns)
        if no_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=False,
                confidence=0.90,
                reasoning="Explicit restrictions against visa sponsorship found",
                positive_indicators=[],
                negative_indicators=no_sponsorship_matches[:3]
            )
        
        # Step 2: Check for explicit YES sponsorship patterns
        yes_sponsorship_matches = self.find_patterns(cleaned_text, self.yes_sponsorship_patterns)
        if yes_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=True,
                confidence=0.90,
                reasoning="Explicit visa sponsorship support mentioned",
                positive_indicators=yes_sponsorship_matches[:3],
                negative_indicators=[]
            )
        
        # Step 3: No explicit indicators found - default to NO
        return SponsorshipAnalysis(
            likely_sponsors=False,
            confidence=0.60,
            reasoning="No explicit sponsorship indicators found - most companies that sponsor mention it explicitly",
            positive_indicators=[],
            negative_indicators=["No sponsorship mentioned"]
        )