from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
from typing import List
from dataclasses import dataclass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class SponsorshipAnalysis:
    likely_sponsors: bool
    confidence: float
    reasoning: str
    positive_indicators: List[str]
    negative_indicators: List[str]

class VisaSponsorshipAnalyzer:
    def __init__(self):
        # EXPLICIT NO SPONSORSHIP patterns (95% confidence NO)
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
            
            # Security clearance (typically requires citizenship)
            r"security clearance required",
            r"clearance required",
            r"must possess.*clearance",
            r"active security clearance",
            r"secret clearance",
            r"top secret clearance",
            r"confidential clearance",
        ]
        
        # EXPLICIT YES SPONSORSHIP patterns (High confidence YES)
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
            r"international candidates welcome",
            r"will provide sponsorship",
            r"sponsor h1b",
            r"sponsor work visa",
        ]
        
        # Neutral/ambiguous patterns that suggest possible sponsorship
        self.maybe_sponsorship_patterns = [
            r"international candidates",
            r"global talent",
            r"diverse backgrounds",
            r"all qualified applicants",
            r"equal opportunity",
            r"worldwide talent",
            r"relocation assistance",
            r"relocation package",
            r"work from anywhere",
            r"remote candidates",
        ]

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Convert to lowercase and normalize whitespace
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
        
        # Check for explicit NO sponsorship patterns
        no_sponsorship_matches = self.find_patterns(cleaned_text, self.no_sponsorship_patterns)
        if no_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=False,
                confidence=0.95,
                reasoning="Explicit visa sponsorship restrictions found",
                positive_indicators=[],
                negative_indicators=no_sponsorship_matches[:3]  # Show first 3 matches
            )
        
        # Check for explicit YES sponsorship patterns
        yes_sponsorship_matches = self.find_patterns(cleaned_text, self.yes_sponsorship_patterns)
        if yes_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=True,
                confidence=0.90,
                reasoning="Explicit visa sponsorship support mentioned",
                positive_indicators=yes_sponsorship_matches[:3],
                negative_indicators=[]
            )
        
        # Check for neutral/maybe patterns
        maybe_matches = self.find_patterns(cleaned_text, self.maybe_sponsorship_patterns)
        
        if maybe_matches:
            # Some positive signals but not explicit
            confidence = min(0.4 + (len(maybe_matches) * 0.1), 0.7)  # Cap at 0.7
            likely = confidence >= 0.5
            
            return SponsorshipAnalysis(
                likely_sponsors=likely,
                confidence=confidence,
                reasoning=f"Found {len(maybe_matches)} neutral/positive indicator(s) but no explicit sponsorship mention",
                positive_indicators=maybe_matches[:3],
                negative_indicators=[]
            )
        
        # No clear indicators either way
        return SponsorshipAnalysis(
            likely_sponsors=False,
            confidence=0.3,
            reasoning="No clear sponsorship indicators found - likely does not sponsor",
            positive_indicators=[],
            negative_indicators=["No sponsorship indicators"]
        )

# Initialize analyzer
analyzer = VisaSponsorshipAnalyzer()

@app.post("/save")
async def analyze_sponsorship(req: Request):
    data = await req.json()
    text = data.get("text", "")
    
    # Perform sponsorship analysis
    analysis = analyzer.analyze_sponsorship(text)
    
    # Determine result status for UI
    if analysis.confidence >= 0.8 and analysis.likely_sponsors:
        status = "yes"
        color = "green"
        message = "✅ LIKELY SPONSORS"
    elif analysis.likely_sponsors and analysis.confidence >= 0.5:
        status = "yes"
        color = "green"
        message = "✅ PROBABLY SPONSORS"
    elif analysis.confidence >= 0.4:
        status = "unknown"
        color = "yellow"
        message = "⚠️ UNCLEAR"
    else:
        status = "no"
        color = "red"
        message = "❌ LIKELY NO SPONSORSHIP"
    
    return {
        "status": status,
        "color": color,
        "message": message,
        "confidence": round(analysis.confidence, 2),
        "reasoning": analysis.reasoning,
        "positive_indicators": analysis.positive_indicators,
        "negative_indicators": analysis.negative_indicators
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)