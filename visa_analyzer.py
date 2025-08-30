import re
from typing import List, Dict
from dataclasses import dataclass
from h1b_data_loader import H1BDataLoader

@dataclass
class SponsorshipAnalysis:
    likely_sponsors: bool
    confidence: float
    reasoning: str
    positive_indicators: List[str]
    negative_indicators: List[str]
    h1b_company_matches: List[str]  # New: H1B historical matches
    company_analysis: List[str]     # New: Company-specific analysis

class VisaSponsorshipAnalyzer:
    def __init__(self):
        # Initialize H1B data loader
        self.h1b_loader = H1BDataLoader()
        
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
            r"Applicants are required to be eligible to lawfully work in the U\.S\. immediately",
            r"employer will not sponsor applicants for U\.S\. work authorization (e\.g\., H-1B visa) for this opportunity"
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

    def analyze_sponsorship_with_companies(self, text: str, company_candidates: List[str]) -> SponsorshipAnalysis:
        """Analyze text for visa sponsorship with company candidate checking"""
        
        if not text or len(text.strip()) < 50:
            return SponsorshipAnalysis(
                likely_sponsors=False,
                confidence=0.0,
                reasoning="Text too short for analysis",
                positive_indicators=[],
                negative_indicators=["Insufficient text"],
                h1b_company_matches=[],
                company_analysis=[]
            )
        
        cleaned_text = self.clean_text(text)
        
        # Step 1: Check for explicit NO sponsorship patterns (highest priority)
        no_sponsorship_matches = self.find_patterns(cleaned_text, self.no_sponsorship_patterns)
        if no_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=False,
                confidence=0.95,
                reasoning="Explicit restrictions against visa sponsorship found",
                positive_indicators=[],
                negative_indicators=no_sponsorship_matches[:3],
                h1b_company_matches=[],
                company_analysis=["Company explicitly states no sponsorship"]
            )
        
        # Step 2: Check for explicit YES sponsorship patterns
        yes_sponsorship_matches = self.find_patterns(cleaned_text, self.yes_sponsorship_patterns)
        if yes_sponsorship_matches:
            return SponsorshipAnalysis(
                likely_sponsors=True,
                confidence=0.95,
                reasoning="Explicit visa sponsorship support mentioned",
                positive_indicators=yes_sponsorship_matches[:3],
                negative_indicators=[],
                h1b_company_matches=[],
                company_analysis=["Company explicitly offers sponsorship"]
            )
        
        # Step 3: Check H1B historical data for company candidates
        h1b_results = self.h1b_loader.check_company_in_h1b_data(company_candidates)
        
        if h1b_results['found_companies']:
            # Company found in H1B data - strong positive indicator
            company_analysis = []
            h1b_matches = []
            
            for detail in h1b_results['company_details']:
                company_name = detail['candidate_name']
                matched_name = detail['matched_name']
                total_approvals = detail['total_approvals']
                years = detail['years_sponsored']
                match_type = detail.get('match_type', 'exact')
                
                if match_type == 'partial':
                    analysis_text = f"{company_name} (matched as {matched_name}) sponsored {total_approvals} H1B visas in {', '.join(years)}"
                else:
                    analysis_text = f"{company_name} sponsored {total_approvals} H1B visas in {', '.join(years)}"
                
                company_analysis.append(analysis_text)
                h1b_matches.append(matched_name)
            
            return SponsorshipAnalysis(
                likely_sponsors=True,
                confidence=0.85,
                reasoning=f"Company has sponsored H1B visas in the past ({', '.join(h1b_results['found_companies'])})",
                positive_indicators=[f"Historical H1B sponsor: {', '.join(h1b_results['found_companies'])}"],
                negative_indicators=[],
                h1b_company_matches=h1b_matches,
                company_analysis=company_analysis
            )
        
        # Step 4: No explicit indicators found and no H1B history - default to NO
        company_analysis = []
        if company_candidates:
            checked_companies = [name for name in company_candidates if name and name != "Not found"]
            if checked_companies:
                company_analysis.append(f"Checked companies: {', '.join(checked_companies[:3])} - no H1B sponsorship history found")
        
        return SponsorshipAnalysis(
            likely_sponsors=False,
            confidence=0.70,
            reasoning="No explicit sponsorship indicators found and no H1B sponsorship history",
            positive_indicators=[],
            negative_indicators=["No sponsorship mentioned", "No H1B history found"],
            h1b_company_matches=[],
            company_analysis=company_analysis
        )

    # Keep the old method for backward compatibility
    def analyze_sponsorship(self, text: str) -> SponsorshipAnalysis:
        """Legacy method - analyze text without company candidates"""
        return self.analyze_sponsorship_with_companies(text, [])