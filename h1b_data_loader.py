import pandas as pd
import os
from typing import Set, Dict, List
import re

class H1BDataLoader:
    def __init__(self, h1b_data_folder: str = "h1b_data"):
        self.h1b_data_folder = h1b_data_folder
        self.h1b_companies = set()
        self.company_stats = {}  # Store company statistics
        self.load_h1b_data()
    
    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for matching"""
        if not company_name:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', company_name.strip().lower())
        
        # Remove common company suffixes for better matching
        suffixes_to_remove = [
            r'\s+(inc|llc|corp|corporation|ltd|limited|co|company)\.?$',
            r'\s+(enterprises|group|holdings|technologies|tech)\.?$',
            r'\s+(systems|solutions|services|consulting)\.?$',
            r'\s+(partners|associates)\.?$'
        ]
        
        for suffix in suffixes_to_remove:
            normalized = re.sub(suffix, '', normalized)
        
        return normalized.strip()
    
    def load_h1b_data(self):
        """Load H1B data from CSV files (2021, 2022, 2023)"""
        years = ['2021', '2022', '2023']
        
        for year in years:
            csv_file = os.path.join(self.h1b_data_folder, f"{year}.csv")
            
            if not os.path.exists(csv_file):
                print(f"Warning: H1B data file {csv_file} not found")
                continue
            
            try:
                # Read CSV file
                df = pd.read_csv(csv_file)
                
                # Expected columns based on your example:
                # "Fiscal Year",Employer,"Initial Approval","Initial Denial","Continuing Approval","Continuing Denial",NAICS,"Tax ID",State,City,ZIP
                
                if 'Employer' not in df.columns:
                    print(f"Warning: 'Employer' column not found in {csv_file}")
                    continue
                
                # Process each employer
                for _, row in df.iterrows():
                    employer = row.get('Employer', '')
                    if pd.isna(employer) or employer == '':
                        continue
                    
                    # Get approval counts
                    initial_approval = row.get('Initial Approval', 0)
                    continuing_approval = row.get('Continuing Approval', 0)
                    
                    # Only include companies that had approvals
                    if pd.isna(initial_approval):
                        initial_approval = 0
                    if pd.isna(continuing_approval):
                        continuing_approval = 0
                    
                    total_approvals = int(initial_approval) + int(continuing_approval)
                    
                    if total_approvals > 0:
                        normalized_name = self.normalize_company_name(employer)
                        if normalized_name:
                            self.h1b_companies.add(normalized_name)
                            
                            # Store company stats
                            if normalized_name not in self.company_stats:
                                self.company_stats[normalized_name] = {
                                    'original_name': employer,
                                    'total_approvals': 0,
                                    'years': []
                                }
                            
                            self.company_stats[normalized_name]['total_approvals'] += total_approvals
                            self.company_stats[normalized_name]['years'].append(year)
                
                print(f"Loaded {len(df)} companies from {year} H1B data")
                
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
        
        print(f"Total unique H1B sponsoring companies loaded: {len(self.h1b_companies)}")
    
    def check_company_in_h1b_data(self, company_names: List[str]) -> Dict:
        """Check if any of the company names exist in H1B data"""
        results = {
            'found_companies': [],
            'h1b_matches': [],
            'company_details': []
        }
        
        for company_name in company_names:
            if not company_name:
                continue
                
            normalized_candidate = self.normalize_company_name(company_name)
            
            # Direct match
            if normalized_candidate in self.h1b_companies:
                results['found_companies'].append(company_name)
                results['h1b_matches'].append(normalized_candidate)
                
                # Get company details
                stats = self.company_stats.get(normalized_candidate, {})
                results['company_details'].append({
                    'candidate_name': company_name,
                    'matched_name': stats.get('original_name', normalized_candidate),
                    'total_approvals': stats.get('total_approvals', 0),
                    'years_sponsored': stats.get('years', [])
                })
                continue
            
            # Partial match - check if candidate is contained in any H1B company name
            partial_matches = [h1b_company for h1b_company in self.h1b_companies 
                             if normalized_candidate in h1b_company or h1b_company in normalized_candidate]
            
            if partial_matches:
                # Take the best partial match (shortest one, likely most specific)
                best_match = min(partial_matches, key=len)
                results['found_companies'].append(company_name)
                results['h1b_matches'].append(best_match)
                
                stats = self.company_stats.get(best_match, {})
                results['company_details'].append({
                    'candidate_name': company_name,
                    'matched_name': stats.get('original_name', best_match),
                    'total_approvals': stats.get('total_approvals', 0),
                    'years_sponsored': stats.get('years', []),
                    'match_type': 'partial'
                })
        
        return results
    
    def get_company_stats(self, normalized_name: str) -> Dict:
        """Get statistics for a specific company"""
        return self.company_stats.get(normalized_name, {})