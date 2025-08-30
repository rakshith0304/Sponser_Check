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
    jsonLdCompanyName: Optional[str] = "Not found"  # New: JSON-LD company name from extension

# Initialize analyzers
analyzer = VisaSponsorshipAnalyzer()
company_extractor = CompanyNameExtractor()

@app.post("/analyze-job")
async def analyze_job_posting(job_data: JobData):
    """Analyze structured job data for visa sponsorship with new pipeline flow"""
    
    print("="*60)
    print("🔍 STARTING JOB ANALYSIS")
    print("="*60)
    
    # Step 1: Get JSON-LD company name from extension
    json_company_name = None
    if job_data.jsonLdCompanyName and job_data.jsonLdCompanyName != "Not found":
        json_company_name = job_data.jsonLdCompanyName
        print(f"📄 JSON-LD Company Name: {json_company_name}")
    else:
        print("📄 No JSON-LD company name found")
    
    # Step 2: Run company name extraction
    print("\n🏢 EXTRACTING COMPANY CANDIDATES...")
    company_result = company_extractor.extract_company_candidates(
        job_data.url, 
        job_data.fullJobDescription, 
        job_data.aboutCompany,
        job_data.header if job_data.header != "Not found" else None
    )
    
    print(f"📊 Extraction Methods: {', '.join(company_result.extraction_methods)}")
    print(f"🎯 Found Candidates: {company_result.company_candidates}")
    
    # Step 3: Combine JSON-LD company name with extracted candidates
    all_company_candidates = []
    
    # Add JSON-LD company name first (highest priority)
    if json_company_name:
        all_company_candidates.append(json_company_name)
    
    # Add extracted candidates
    all_company_candidates.extend(company_result.company_candidates)
    
    # Remove duplicates while preserving order
    unique_candidates = []
    seen = set()
    for candidate in all_company_candidates:
        if candidate and candidate.lower() not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate.lower())
    
    print(f"\n🔗 COMBINED COMPANY CANDIDATES:")
    for i, candidate in enumerate(unique_candidates, 1):
        source = "JSON-LD" if i == 1 and json_company_name else "Extracted"
        print(f"  {i}. {candidate} ({source})")
    
    # Step 4: Determine final company name for display
    final_company_name = unique_candidates[0] if unique_candidates else "Unknown"
    print(f"\n🏆 FINAL COMPANY: {final_company_name}")
    
    # Step 5: Run sponsorship analysis with all company candidates
    print(f"\n💼 ANALYZING SPONSORSHIP...")
    analysis = analyzer.analyze_sponsorship_with_companies(
        job_data.fullJobDescription, 
        unique_candidates
    )
    
    print(f"✅ Analysis Result: {'SPONSORS' if analysis.likely_sponsors else 'NO SPONSORSHIP'}")
    print(f"🎯 Confidence: {analysis.confidence:.2f}")
    print(f"📝 Reasoning: {analysis.reasoning}")
    
    if analysis.h1b_company_matches:
        print(f"📈 H1B Matches: {', '.join(analysis.h1b_company_matches)}")
    
    if analysis.company_analysis:
        print("🔍 Company Analysis:")
        for analysis_item in analysis.company_analysis:
            print(f"  • {analysis_item}")
    
    # Determine result status for UI
    if analysis.likely_sponsors:
        status = "yes"
        color = "green" 
        message = "SPONSORS VISA"
    else:
        status = "no"
        color = "red"
        message = "NO SPONSORSHIP"
    
    print("="*60)
    
    return {
        "status": status,
        "color": color,
        "message": message,
        "confidence": round(analysis.confidence, 2),
        "reasoning": analysis.reasoning,
        "positive_indicators": analysis.positive_indicators,
        "negative_indicators": analysis.negative_indicators,
        "h1b_company_matches": analysis.h1b_company_matches,
        "company_analysis": analysis.company_analysis,
        "job_metadata": {
            "title": job_data.jobTitle,
            "location": job_data.location,
            "employment_type": job_data.employmentType,
            "job_id": job_data.jobId,
            "platform": job_data.platform,
            "final_company_name": final_company_name,
            "json_company_name": json_company_name,
            "extracted_candidates": company_result.company_candidates,
            "all_candidates": unique_candidates
        }
    }

# Keep the old endpoint for backward compatibility
@app.post("/save")
async def analyze_sponsorship_legacy(req: Request):
    """Legacy endpoint for backward compatibility"""
    data = await req.json()
    text = data.get("text", "")
    url = data.get("url", "")
    
    # Perform sponsorship analysis without company candidates
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
    print("🔄 New Pipeline Flow Enabled:")
    print("  1. JSON-LD company extraction from extension")
    print("  2. Company name extraction")
    print("  3. Combine all company candidates") 
    print("  4. H1B historical data checking")
    print("  5. Enhanced sponsorship analysis")
    print("📁 H1B Data: 2021, 2022, 2023 files expected in h1b_data/ folder")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)