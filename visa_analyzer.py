import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class SponsorshipAnalysis:
    likely_sponsors: Optional[bool]  # True, False, or None
    confidence: float
    reasoning: str
    positive_indicators: List[str]
    negative_indicators: List[str]
    h1b_company_matches: List[str]
    company_analysis: List[str]

class VisaSponsorshipAnalyzer:
    def __init__(self):
        # Explicit NO sponsorship patterns
        self.no_sponsorship_patterns = [
            r"no visa sponsorship", r"sponsorship not available", r"we do not sponsor",
            r"will not sponsor", r"cannot sponsor", r"no h1b sponsorship",
            r"no immigration sponsorship", r"visa sponsorship is not provided",
            r"we are unable to sponsor", r"not able to sponsor", r"does not sponsor",
            r"unable to provide sponsorship", r"not eligible for visa sponsorship",
            r"must be authorized to work", r"authorized to work in", r"eligible to work in",
            r"must have authorization to work", r"must be legally authorized",
            r"legal authorization to work", r"work authorization required",
            r"employment authorization required", r"require work authorization",
            r"current work authorization", r"citizens only", r"citizenship required",
            r"must be a citizen", r"citizen or permanent resident",
            r"us citizens and permanent residents", r"green card holders only",
            r"permanent resident status required", r"must be a us citizen",
            r"only us citizens", r"us citizen or permanent resident",
            r"security clearance required", r"clearance required",
            r"must possess.*clearance", r"active security clearance",
            r"secret clearance", r"top secret clearance", r"confidential clearance",
            r"only u\.s\. citizens are eligible", r"must be eligible for.*clearance",
            r"due to.*government contract requirements",
            r"applicants are required to be eligible to lawfully work in the u\.s\. immediately",
            r"employer will not sponsor applicants for u\.s\. work authorization",
            r"presently authorized to work for any employer in the united states",
            r"who will not require work visa sponsorship",
            r"now or in the future in order to retain their authorization to work in the united states",
        ]

        # Explicit YES sponsorship patterns
        self.yes_sponsorship_patterns = [
            r"visa sponsorship available", r"h1b friendly", r"will sponsor qualified candidates",
            r"sponsorship provided", r"immigration support", r"visa support available",
            r"we sponsor visas", r"h1b sponsorship available", r"visa assistance provided",
            r"immigration assistance", r"work visa support", r"h1b transfers welcome",
            r"will provide sponsorship", r"sponsor h1b", r"sponsor work visa",
            r"provides visa sponsorship", r"offers visa sponsorship",
            r"sponsorship is available", r"we will sponsor", r"able to sponsor", r"can sponsor",
        ]

        # Positive context indicators
        self.positive_context_patterns = [
            r"international candidates welcome", r"global workforce",
            r"diverse team", r"all qualified candidates", r"equal opportunity employer",
            r"remote work", r"work from anywhere",
        ]

    def clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    def find_patterns(self, text: str, patterns: List[str]) -> List[str]:
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.extend([pattern] * len(found))
        return matches

    def extract_company_indicators(self, text: str) -> List[str]:
        return self.find_patterns(text, self.positive_context_patterns)

    def analyze_sponsorship(self, text: str, company_name: Optional[str] = None) -> SponsorshipAnalysis:
        if not text or len(text.strip()) < 50:
            return SponsorshipAnalysis(
                likely_sponsors=False, confidence=0.0,
                reasoning="Text too short for meaningful analysis",
                positive_indicators=[], negative_indicators=["Insufficient text provided"],
                h1b_company_matches=[], company_analysis=[]
            )

        cleaned = self.clean_text(text)
        no_matches = self.find_patterns(cleaned, self.no_sponsorship_patterns)
        yes_matches = self.find_patterns(cleaned, self.yes_sponsorship_patterns)
        positives = self.extract_company_indicators(cleaned)

        reasoning, likely, conf = "", None, 0.0
        if no_matches:
            likely, conf = False, 0.9 if len(no_matches) > 1 else 0.8
            reasoning = "Explicit restrictions against visa sponsorship found"
        elif yes_matches:
            likely, conf, reasoning = True, 0.9, "Explicit visa sponsorship support mentioned"
        elif positives:
            likely, conf = None, min(0.3 + len(positives) * 0.1, 0.6)
            reasoning = "No explicit sponsorship mention, but positive indicators suggest openness"
        else:
            likely, conf, reasoning = None, 0.1, "No clear sponsorship indicators found"

        company_analysis = [f"Company analysis available for: {company_name}"] if company_name else []

        return SponsorshipAnalysis(
            likely_sponsors=likely, confidence=conf, reasoning=reasoning,
            positive_indicators=(yes_matches + positives)[:5],
            negative_indicators=no_matches[:5],
            h1b_company_matches=[], company_analysis=company_analysis,
        )
