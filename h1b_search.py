import pandas as pd
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class H1BCompanyMatch:
    company_name: str
    total_applications: int
    match_confidence: float
    all_matches: List[Dict[str, any]]  # All companies that matched the search

class H1BCompanySearcher:
    def __init__(self, data_folder: str = "h1b_data"):
        self.data_folder = data_folder
        self.companies_df = None
        self.load_h1b_data()
        
    def load_h1b_data(self):
        """Load H1B data from cleaned_h1b.csv"""
        file_path = os.path.join(self.data_folder, "cleaned_h1b.csv")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
            
        try:
            logger.info("Loading H1B data from cleaned_h1b.csv...")
            self.companies_df = pd.read_csv(file_path)
            
            # Ensure we have the expected columns
            if 'Employer' not in self.companies_df.columns or 'H1B_Total' not in self.companies_df.columns:
                logger.error(f"Expected columns 'Employer' and 'H1B_Total' not found. Available columns: {self.companies_df.columns.tolist()}")
                return
            
            # Clean the data
            self.companies_df['Employer'] = self.companies_df['Employer'].astype(str).str.strip()
            self.companies_df['H1B_Total'] = pd.to_numeric(self.companies_df['H1B_Total'], errors='coerce')
            
            # Remove invalid entries
            self.companies_df = self.companies_df[
                (self.companies_df['Employer'] != '') & 
                (self.companies_df['Employer'].notna()) &
                (self.companies_df['H1B_Total'].notna()) &
                (self.companies_df['H1B_Total'] > 0)
            ]
            
            logger.info(f"Loaded {len(self.companies_df)} companies from H1B data")
            
        except Exception as e:
            logger.error(f"Error loading cleaned_h1b.csv: {str(e)}")
    
    def search_company(self, search_term: str) -> Optional[H1BCompanyMatch]:
        """Search for companies containing the search term and return the one with highest H1B count"""
        if not search_term or len(search_term.strip()) < 2:
            return None
        
        if self.companies_df is None or self.companies_df.empty:
            logger.error("No H1B data loaded")
            return None
        
        search_term_clean = search_term.strip().upper()
        
        # Find all companies that contain the search term (case insensitive)
        matches = self.companies_df[
            self.companies_df['Employer'].str.upper().str.contains(search_term_clean, na=False, regex=False)
        ].copy()
        
        if matches.empty:
            return None
        
        # Sort by H1B_Total in descending order to get the highest one first
        matches = matches.sort_values('H1B_Total', ascending=False)
        
        # Get the top match (highest H1B count)
        top_match = matches.iloc[0]
        
        # Prepare all matches for reference
        all_matches = []
        for _, row in matches.head(10).iterrows():  # Limit to top 10 matches
            all_matches.append({
                'company_name': row['Employer'],
                'h1b_count': int(row['H1B_Total'])
            })
        
        # Calculate confidence based on how well the search term matches
        confidence = self.calculate_match_confidence(search_term, top_match['Employer'])
        
        return H1BCompanyMatch(
            company_name=top_match['Employer'],
            total_applications=int(top_match['H1B_Total']),
            match_confidence=confidence,
            all_matches=all_matches
        )
    
    def calculate_match_confidence(self, search_term: str, company_name: str) -> float:
        """Calculate confidence score based on how well the search matches"""
        search_clean = search_term.strip().upper()
        company_clean = company_name.upper()
        
        # Exact match
        if search_clean == company_clean:
            return 1.0
        
        # Search term is the entire company name
        if company_clean == search_clean:
            return 1.0
        
        # Company name starts with search term
        if company_clean.startswith(search_clean):
            return 0.9
        
        # Search term appears at word boundaries
        if re.search(r'\b' + re.escape(search_clean) + r'\b', company_clean):
            return 0.8
        
        # Search term is contained anywhere
        if search_clean in company_clean:
            return 0.7
        
        return 0.5  # Default for any match found by contains()
    
    def get_company_stats(self, company_match: H1BCompanyMatch) -> Dict:
        """Get detailed statistics for a company match"""
        return {
            "company_name": company_match.company_name,
            "total_applications": company_match.total_applications,
            "match_confidence": round(company_match.match_confidence, 2),
            "all_matches": company_match.all_matches,
            "total_matches_found": len(company_match.all_matches)
        }
    
    def get_database_stats(self) -> Dict:
        """Get general database statistics"""
        if self.companies_df is None or self.companies_df.empty:
            return {"total_companies": 0, "status": "not_loaded"}
        
        return {
            "total_companies": len(self.companies_df),
            "total_h1b_applications": int(self.companies_df['H1B_Total'].sum()),
            "status": "ready"
        }

# Example usage and testing
if __name__ == "__main__":
    searcher = H1BCompanySearcher()
    
    # Test searches
    test_companies = ["Wells Fargo", "Google", "Microsoft", "Amazon", "Apple", "Meta"]
    
    for company in test_companies:
        print(f"\n--- Searching for: {company} ---")
        result = searcher.search_company(company)
        if result:
            stats = searcher.get_company_stats(result)
            print(f"Top match: {stats['company_name']}")
            print(f"H1B Applications: {stats['total_applications']}")
            print(f"Match confidence: {stats['match_confidence']}")
            print(f"Total matches found: {stats['total_matches_found']}")
            print("All matches:")
            for match in stats['all_matches'][:5]:  # Show top 5
                print(f"  - {match['company_name']}: {match['h1b_count']} H1B applications")
        else:
            print("No match found")
    
    # Show database stats
    print(f"\n--- Database Stats ---")
    db_stats = searcher.get_database_stats()
    print(f"Total companies: {db_stats.get('total_companies', 0)}")
    print(f"Total H1B applications: {db_stats.get('total_h1b_applications', 0)}")
    print(f"Status: {db_stats.get('status', 'unknown')}")