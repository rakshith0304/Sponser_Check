from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from visa_analyzer import VisaSponsorshipAnalyzer
from h1b_search import H1BCompanySearcher

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobData(BaseModel):
    fullJobDescription: str

class CompanySearchRequest(BaseModel):
    company_name: str

analyzer = VisaSponsorshipAnalyzer()
h1b_searcher = H1BCompanySearcher()

def determine_analysis_status(analysis):
    """Helper function to determine UI status from analysis result"""
    if analysis.likely_sponsors:
        return {
            "status": "yes",
            "color": "#2A9D8F", 
            "message": "SPONSORS VISA"
        }
    elif analysis.likely_sponsors is None:
        return {
            "status": "unknown",
            "color": "#F4A261",
            "message": "SPONSORSHIP UNKNOWN"
        }
    else:
        return {
            "status": "no",
            "color": "#E63946",
            "message": "NO SPONSORSHIP"
        }

def build_base_response(analysis):
    """Helper function to build base response structure"""
    status_info = determine_analysis_status(analysis)
    
    return {
        "status": status_info["status"],
        "color": status_info["color"],
        "message": status_info["message"],
        "reasoning": analysis.reasoning,
        "positive_indicators": analysis.positive_indicators,
        "negative_indicators": analysis.negative_indicators
    }

@app.post("/analyze-job")
async def analyze_job_posting(job_data: JobData):
    """Analyze job description for visa sponsorship"""
    analysis = analyzer.analyze_sponsorship(job_data.fullJobDescription)
    return build_base_response(analysis)

@app.post("/search-h1b-company")
async def search_h1b_company(request: CompanySearchRequest):
    """Search for a company in H1B sponsorship data"""
    try:
        company_name = request.company_name.strip()
        
        if len(company_name) < 2:
            raise HTTPException(status_code=400, detail="Company name must be at least 2 characters long")
        
        # Search for the company
        result = h1b_searcher.search_company(company_name)
        
        if not result:
            return {
                "found": False,
                "message": f"No H1B sponsorship data found for '{company_name}'",
                "company_name": company_name
            }
        
        stats = h1b_searcher.get_company_stats(result)
        
        # Format response message
        message = f"{stats['company_name']} has sponsored {stats['total_applications']} H1B applications"
        
        if stats['total_matches_found'] > 1:
            message += f" (top result from {stats['total_matches_found']} similar companies found)"
        
        return {
            "found": True,
            "message": message,
            "company_name": stats['company_name'],
            "total_applications": stats['total_applications'],
            "match_confidence": stats['match_confidence'],
            "search_term": company_name,
            "total_matches_found": stats['total_matches_found'],
            "all_matches": stats['all_matches'][:5]  # Return top 5 matches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching H1B data: {str(e)}")

@app.post("/save")
async def analyze_sponsorship_legacy(req: Request):
    """Legacy endpoint for backward compatibility"""
    data = await req.json()
    text = data.get("text", "")
    analysis = analyzer.analyze_sponsorship(text)
    return build_base_response(analysis)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Job Analyzer API is running"}

@app.get("/h1b-stats")
async def get_h1b_stats():
    """Get general H1B database statistics"""
    try:
        stats = h1b_searcher.get_database_stats()
        return stats
    except Exception as e:
        return {
            "total_companies": 0,
            "total_h1b_applications": 0,
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    print("Starting Job Analyzer API...")
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)