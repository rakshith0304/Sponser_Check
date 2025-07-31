from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for structured data
class JobData(BaseModel):
    jobTitle: str
    location: str
    employmentType: str
    jobId: str
    aboutCompany: str
    fullJobDescription: str
    url: str
    scrapedAt: str
    platform: str

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

def save_job_data(job_data: JobData, analysis: SponsorshipAnalysis):
    """Save job data and analysis results to a file (for future database integration)"""
    try:
        # Create a record with all information
        record = {
            "job_info": job_data.dict(),
            "analysis": {
                "likely_sponsors": analysis.likely_sponsors,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "positive_indicators": analysis.positive_indicators,
                "negative_indicators": analysis.negative_indicators
            },
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Save to JSON file (can be replaced with database later)
        filename = f"job_analyses.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        print(f"✅ Saved job analysis: {job_data.jobTitle} - {job_data.jobId}")
        
    except Exception as e:
        print(f"❌ Error saving job data: {e}")

# Initialize analyzer
analyzer = VisaSponsorshipAnalyzer()

@app.post("/analyze-job")
async def analyze_job_posting(job_data: JobData):
    """Analyze structured job data for visa sponsorship"""
    
    # Perform sponsorship analysis on full job description
    analysis = analyzer.analyze_sponsorship(job_data.fullJobDescription)
    
    # Save the data and analysis results
    save_job_data(job_data, analysis)
    
    # Determine result status for UI
    if analysis.likely_sponsors:
        status = "yes"
        color = "green" 
        message = "✅ SPONSORS VISA"
    else:
        status = "no"
        color = "red"
        message = "❌ NO SPONSORSHIP"
    
    return {
        "status": status,
        "color": color,
        "message": message,
        "confidence": round(analysis.confidence, 2),
        "reasoning": analysis.reasoning,
        "positive_indicators": analysis.positive_indicators,
        "negative_indicators": analysis.negative_indicators,
        "job_metadata": {
            "title": job_data.jobTitle,
            "location": job_data.location,
            "employment_type": job_data.employmentType,
            "job_id": job_data.jobId,
            "platform": job_data.platform
        }
    }

# Keep the old endpoint for backward compatibility
@app.post("/save")
async def analyze_sponsorship_legacy(req: Request):
    """Legacy endpoint for backward compatibility"""
    data = await req.json()
    text = data.get("text", "")
    url = data.get("url", "")
    
    # Perform sponsorship analysis
    analysis = analyzer.analyze_sponsorship(text)
    
    # Determine result status for UI
    if analysis.likely_sponsors:
        status = "yes"
        color = "green" 
        message = "✅ SPONSORS VISA"
    else:
        status = "no"
        color = "red"
        message = "❌ NO SPONSORSHIP"
    
    return {
        "status": status,
        "color": color,
        "message": message,
        "confidence": round(analysis.confidence, 2),
        "reasoning": analysis.reasoning,
        "positive_indicators": analysis.positive_indicators,
        "negative_indicators": analysis.negative_indicators
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Workday Job Analyzer API is running"}

if __name__ == "__main__":
    print("🚀 Starting Workday Job Analyzer API...")
    print("📊 Structured data extraction enabled")
    print("💾 Job data will be saved to job_analyses.jsonl")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)