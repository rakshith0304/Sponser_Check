import re
import urllib.parse
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class CompanyExtractionResult:
    company_candidates: List[str]  # Changed to return list instead of single name
    extraction_methods: List[str]
    reasoning: str

class CompanyNameExtractor:
    def __init__(self):
        # Known company domains and their proper names
        self.known_domains = {
            'google.com': 'Google',
            'microsoft.com': 'Microsoft',
            'amazon.com': 'Amazon',
            'apple.com': 'Apple',
            'meta.com': 'Meta',
            'facebook.com': 'Meta',
            'netflix.com': 'Netflix',
            'tesla.com': 'Tesla',
            'uber.com': 'Uber',
            'airbnb.com': 'Airbnb',
            'spotify.com': 'Spotify',
            'salesforce.com': 'Salesforce',
            'oracle.com': 'Oracle',
            'ibm.com': 'IBM',
            'intel.com': 'Intel',
            'nvidia.com': 'NVIDIA',
            'adobe.com': 'Adobe',
            'vmware.com': 'VMware',
            'cisco.com': 'Cisco',
            'dell.com': 'Dell',
            'accenture.com': 'Accenture',
            'deloitte.com': 'Deloitte',
            'pwc.com': 'PwC',
            'ey.com': 'Ernst & Young',
            'kpmg.com': 'KPMG',
            'jpmorgan.com': 'JPMorgan Chase',
            'goldmansachs.com': 'Goldman Sachs',
            'morganstanley.com': 'Morgan Stanley',
            'bankofamerica.com': 'Bank of America'
        }
        
        # Words to exclude from company names
        self.exclude_words = {
            'job', 'position', 'role', 'career', 'opportunity', 'opening', 'posting',
            'description', 'requirements', 'qualifications', 'responsibilities',
            'benefits', 'salary', 'compensation', 'location', 'remote', 'hybrid',
            'full', 'time', 'part', 'contract', 'permanent', 'temporary',
            'senior', 'junior', 'lead', 'principal', 'manager', 'director',
            'engineer', 'developer', 'analyst', 'specialist', 'coordinator',
            'workday', 'application', 'apply', 'now', 'today', 'join', 'team'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_from_url(self, url: str) -> List[str]:
        """Extract company name candidates from URL"""
        candidates = []
        
        if not url:
            return candidates
        
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check known domains first
            for known_domain, company_name in self.known_domains.items():
                if known_domain in domain:
                    candidates.append(company_name)
                    break
            
            # Look for Workday subdomain pattern (company.myworkdayjobs.com)
            workday_match = re.match(r'^([^.]+)\.myworkdayjobs\.com', domain)
            if workday_match:
                company_subdomain = workday_match.group(1)
                # Clean up the subdomain to make it more readable
                company_name = company_subdomain.replace('-', ' ').replace('_', ' ')
                company_name = ' '.join(word.capitalize() for word in company_name.split())
                candidates.append(company_name)
            
            # Generic domain extraction (remove .com, .org, etc.)
            if not candidates:  # Only if no specific match found
                domain_parts = domain.split('.')
                if len(domain_parts) >= 2:
                    main_domain = domain_parts[0]
                    candidates.append(main_domain.capitalize())
                
        except Exception as e:
            print(f"Error parsing URL: {e}")
        
        return candidates
    
    def extract_from_header(self, header_text: str) -> List[str]:
        """Extract company name candidates from header section"""
        candidates = []
        
        if not header_text or header_text == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(header_text)
        
        # Header patterns for company name extraction
        header_patterns = [
            r'^([A-Z][A-Za-z\s&]+?)\s*[-–—]\s*(?:jobs|careers|hiring|employment)',
            r'^([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,)',
            r'jobs\s+at\s+([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,|$)',
            r'careers\s+at\s+([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,|$)',
            r'([A-Z][A-Za-z\s&]+?)\s*(?:\s*[-–—]\s*workday|\s*[-–—]\s*job\s*portal|\s*[-–—]\s*employment)',
            r'^([A-Z][A-Za-z\s&]{2,30})$'
        ]
        
        for pattern in header_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                if len(candidate) > 1 and len(candidate) < 50:
                    candidates.append(candidate)
        
        return candidates
    
    def extract_from_about_company(self, about_text: str) -> List[str]:
        """Extract company name candidates from about company section"""
        candidates = []
        
        if not about_text or about_text == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(about_text)
        
        # About company patterns
        about_patterns = [
            r'about\s+([A-Z][A-Za-z\s&]+?)(?:\s+is|\s+was|\s+-|\s+,|\s+\.|$)',
            r'^([A-Z][A-Za-z\s&]+?)\s+is\s+',
            r'^([A-Z][A-Za-z\s&]+?)\s+was\s+',
            r'welcome\s+to\s+([A-Z][A-Za-z\s&]+?)(?:\s+where|\s+-|\s+,|\s+\.|$)',
            r'join\s+([A-Z][A-Za-z\s&]+?)(?:\s+where|\s+and|\s+-|\s+,|\s+\.|$)'
        ]
        
        for pattern in about_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                if len(candidate) > 1 and len(candidate) < 50:
                    candidates.append(candidate)
        
        return candidates
    
    def extract_from_description(self, description: str) -> List[str]:
        """Extract company name candidates from full job description"""
        candidates = []
        
        if not description or description == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(description)
        
        # Job description patterns
        description_patterns = [
            r'at\s+([A-Z][A-Za-z\s&]+?)(?:\s+we|\s+,|\s+you|\s+our|\s+the|\s+\.|$)',
            r'join\s+([A-Z][A-Za-z\s&]+?)(?:\s+as|\s+and|\s+where|\s+,|\s+\.|$)',
            r'([A-Z][A-Za-z\s&]+?)\s+is\s+(?:a\s+)?(?:leading|global|Fortune|top)',
            r'work\s+(?:at|for)\s+([A-Z][A-Za-z\s&]+?)(?:\s+and|\s+,|\s+\.|$)',
            r'opportunity\s+(?:at|with)\s+([A-Z][A-Za-z\s&]+?)(?:\s+to|\s+,|\s+\.|$)'
        ]
        
        for pattern in description_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                if len(candidate) > 1 and len(candidate) < 50:
                    candidates.append(candidate)
        
        return candidates
    
    def filter_candidates(self, candidates: List[str]) -> List[str]:
        """Filter and clean company name candidates"""
        filtered = []
        
        for candidate in candidates:
            if not candidate:
                continue
                
            candidate_lower = candidate.lower()
            
            # Skip if contains too many exclude words
            exclude_count = sum(1 for word in self.exclude_words if word in candidate_lower)
            if exclude_count > 1:  # Allow one exclude word but not more
                continue
            
            # Skip if too short or too long
            if len(candidate) < 2 or len(candidate) > 50:
                continue
            
            # Add to filtered list if not already present (case-insensitive)
            if not any(existing.lower() == candidate_lower for existing in filtered):
                filtered.append(candidate)
        
        return filtered
    
    def extract_company_candidates(self, url: str, full_description: str, about_company: str, header: str = None) -> CompanyExtractionResult:
        """Main method to extract all company name candidates from available sources"""
        
        all_candidates = []
        extraction_methods = []
        
        # Method 1: Extract from URL
        url_candidates = self.extract_from_url(url)
        if url_candidates:
            all_candidates.extend(url_candidates)
            extraction_methods.append("URL")
        
        # Method 2: Extract from header section
        if header and header != "Not found":
            header_candidates = self.extract_from_header(header)
            if header_candidates:
                all_candidates.extend(header_candidates)
                extraction_methods.append("Header")
        
        # Method 3: Extract from about company section
        about_candidates = self.extract_from_about_company(about_company)
        if about_candidates:
            all_candidates.extend(about_candidates)
            extraction_methods.append("About Company")
        
        # Method 4: Extract from job description
        desc_candidates = self.extract_from_description(full_description)
        if desc_candidates:
            all_candidates.extend(desc_candidates)
            extraction_methods.append("Job Description")
        
        # Filter and clean candidates
        filtered_candidates = self.filter_candidates(all_candidates)
        
        # Generate reasoning
        if filtered_candidates:
            reasoning = f"Found {len(filtered_candidates)} company candidates from {', '.join(extraction_methods)}: {', '.join(filtered_candidates[:3])}"
            if len(filtered_candidates) > 3:
                reasoning += f" and {len(filtered_candidates) - 3} more"
        else:
            reasoning = "No valid company name candidates found in any source"
        
        return CompanyExtractionResult(
            company_candidates=filtered_candidates,
            extraction_methods=extraction_methods,
            reasoning=reasoning
        )