from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional
from pydantic import BaseModel
from visa_analyzer import VisaSponsorshipAnalyzer
from company_extractor import CompanyNameExtractor

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
    header: Optional[str] = "Not found"

# Initialize analyzers
analyzer = VisaSponsorshipAnalyzer()
company_extractor = CompanyNameExtractor()

@app.post("/analyze-job")
async def analyze_job_posting(job_data: JobData):
    """Analyze structured job data for visa sponsorship"""
    
    # Extract company name with header support
    company_result = company_extractor.extract_company_name(
        job_data.url, 
        job_data.fullJobDescription, 
        job_data.aboutCompany,
        job_data.header if job_data.header != "Not found" else None
    )
    
    # Display company name in terminal
    if company_result.company_name:
        print(f"COMPANY: {company_result.company_name}")
        print(f"Method: {company_result.extraction_method} (Confidence: {company_result.confidence:.2f})")
        if len(company_result.candidates) > 1:
            print(f"Other candidates: {', '.join(company_result.candidates[:3])}")
    else:
        print("COMPANY: Unknown (could not extract)")
    
    # Perform sponsorship analysis on full job description
    analysis = analyzer.analyze_sponsorship(job_data.fullJobDescription)
    
    # Determine result status for UI
    if analysis.likely_sponsors:
        status = "yes"
        color = "green" 
        message = "SPONSORS VISA"
    else:
        status = "no"
        color = "red"
        message = "NO SPONSORSHIP"
    
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
            "platform": job_data.platform,
            "company_name": company_result.company_name,
            "company_confidence": round(company_result.confidence, 2)
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
        message = "SPONSORS VISA"
    else:
        status = "no"
        color = "red"
        message = "NO SPONSORSHIP"
    
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
    print("Starting Workday Job Analyzer API...")
    print("Structured data extraction enabled")
    print("Company name extraction enabled (with header support)")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)