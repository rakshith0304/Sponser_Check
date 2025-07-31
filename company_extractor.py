import re
import urllib.parse
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class CompanyExtractionResult:
    company_name: Optional[str]
    confidence: float
    extraction_method: str
    reasoning: str
    candidates: List[str]

class CompanyNameExtractor:
    def __init__(self):
        # Common company suffixes to help identify company names
        self.company_suffixes = [
            r'\b(inc|llc|corp|corporation|ltd|limited|co|company|enterprises|group|holdings|technologies|tech|systems|solutions|services|consulting|partners|associates)\b'
        ]
        
        # Words to exclude from company names (common job posting words)
        self.exclude_words = {
            'job', 'position', 'role', 'career', 'opportunity', 'opening', 'posting',
            'description', 'requirements', 'qualifications', 'responsibilities',
            'benefits', 'salary', 'compensation', 'location', 'remote', 'hybrid',
            'full', 'time', 'part', 'contract', 'permanent', 'temporary',
            'senior', 'junior', 'lead', 'principal', 'manager', 'director',
            'engineer', 'developer', 'analyst', 'specialist', 'coordinator',
            'workday', 'application', 'apply', 'now', 'today', 'join', 'team'
        }
        
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
            'dell.com': 'Dell'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_from_url(self, url: str) -> Optional[str]:
        """Extract company name from URL"""
        if not url:
            return None
        
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check known domains first
            for known_domain, company_name in self.known_domains.items():
                if known_domain in domain:
                    return company_name
            
            # Look for Workday subdomain pattern (company.myworkdayjobs.com)
            workday_match = re.match(r'^([^.]+)\.myworkdayjobs\.com', domain)
            if workday_match:
                company_subdomain = workday_match.group(1)
                # Clean up the subdomain to make it more readable
                company_name = company_subdomain.replace('-', ' ').replace('_', ' ')
                company_name = ' '.join(word.capitalize() for word in company_name.split())
                return company_name
            
            # Generic domain extraction (remove .com, .org, etc.)
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                main_domain = domain_parts[0]
                return main_domain.capitalize()
                
        except Exception as e:
            print(f"Error parsing URL: {e}")
        
        return None
    
    def extract_from_header(self, header_text: str) -> List[str]:
        """Extract company name candidates from header section"""
        candidates = []
        
        if not header_text or header_text == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(header_text)
        
        # Header often contains company name in various formats
        # Look for patterns that indicate company names in headers
        header_patterns = [
            # Company name followed by "- Jobs" or "Careers"
            r'^([A-Z][A-Za-z\s&]+?)\s*[-–—]\s*(?:jobs|careers|hiring|employment)',
            # Company name at the beginning of header
            r'^([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,)',
            # "Jobs at [Company]" pattern
            r'jobs\s+at\s+([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,|$)',
            # "Careers at [Company]" pattern
            r'careers\s+at\s+([A-Z][A-Za-z\s&]+?)(?:\s*[-–—]|\s*\||\s*•|\s*,|$)',
            # Company name followed by common header separators
            r'([A-Z][A-Za-z\s&]+?)\s*(?:\s*[-–—]\s*workday|\s*[-–—]\s*job\s*portal|\s*[-–—]\s*employment)',
            # Standalone company name (if header is short and clean)
            r'^([A-Z][A-Za-z\s&]{2,30})$'
        ]
        
        for pattern in header_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                if len(candidate) > 1 and len(candidate) < 50:  # Reasonable length
                    candidates.append(candidate)
        
        return candidates
    
    def extract_from_about_company(self, about_text: str) -> List[str]:
        """Extract company name candidates from about company section"""
        candidates = []
        
        if not about_text or about_text == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(about_text)
        
        # Look for patterns like "About [Company Name]" or "[Company Name] is"
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
                if len(candidate) > 1 and len(candidate) < 50:  # Reasonable length
                    candidates.append(candidate)
        
        return candidates
    
    def extract_from_description(self, description: str) -> List[str]:
        """Extract company name candidates from full job description"""
        candidates = []
        
        if not description or description == "Not found":
            return candidates
        
        cleaned_text = self.clean_text(description)
        
        # Look for company names in common patterns
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
    
    def score_candidate(self, candidate: str) -> float:
        """Score a company name candidate based on various factors"""
        if not candidate:
            return 0.0
        
        score = 0.5  # Base score
        candidate_lower = candidate.lower()
        
        # Bonus for having company suffixes
        suffix_pattern = '|'.join(self.company_suffixes)
        if re.search(suffix_pattern, candidate_lower):
            score += 0.3
        
        # Penalty for common exclude words
        exclude_count = sum(1 for word in self.exclude_words if word in candidate_lower)
        score -= exclude_count * 0.2
        
        # Bonus for proper capitalization
        if candidate[0].isupper():
            score += 0.1
        
        # Penalty for too long names (likely not company names)
        if len(candidate) > 30:
            score -= 0.2
        
        # Bonus for reasonable length
        if 3 <= len(candidate) <= 25:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def extract_company_name(self, url: str, full_description: str, about_company: str, header: str = None) -> CompanyExtractionResult:
        """Main method to extract company name from all available sources"""
        
        all_candidates = []
        extraction_methods = []
        
        # Method 1: Extract from URL
        url_candidate = self.extract_from_url(url)
        if url_candidate:
            all_candidates.append(url_candidate)
            extraction_methods.append("URL")
        
        # Method 2: Extract from header section (NEW)
        if header:
            header_candidates = self.extract_from_header(header)
            all_candidates.extend(header_candidates)
            if header_candidates:
                extraction_methods.append("Header")
        
        # Method 3: Extract from about company section
        about_candidates = self.extract_from_about_company(about_company)
        all_candidates.extend(about_candidates)
        if about_candidates:
            extraction_methods.append("About Company")
        
        # Method 4: Extract from job description
        desc_candidates = self.extract_from_description(full_description)
        all_candidates.extend(desc_candidates)
        if desc_candidates:
            extraction_methods.append("Job Description")
        
        if not all_candidates:
            return CompanyExtractionResult(
                company_name=None,
                confidence=0.0,
                extraction_method="None",
                reasoning="No company name candidates found in any source",
                candidates=[]
            )
        
        # Score all candidates and find the best one
        candidate_scores = {}
        for candidate in all_candidates:
            score = self.score_candidate(candidate)
            candidate_scores[candidate] = score
        
        # Get the best candidate
        best_candidate = max(candidate_scores.keys(), key=lambda x: candidate_scores[x])
        best_score = candidate_scores[best_candidate]
        
        # Determine extraction method used for best candidate
        used_method = "Multiple Sources"
        if url_candidate and best_candidate == url_candidate:
            used_method = "URL"
        elif header and best_candidate in self.extract_from_header(header):
            used_method = "Header"
        elif best_candidate in about_candidates:
            used_method = "About Company"
        elif best_candidate in desc_candidates:
            used_method = "Job Description"
        
        # Generate reasoning
        reasoning = f"Found {len(all_candidates)} candidates from {', '.join(extraction_methods)}. Selected '{best_candidate}' with score {best_score:.2f}"
        
        return CompanyExtractionResult(
            company_name=best_candidate,
            confidence=best_score,
            extraction_method=used_method,
            reasoning=reasoning,
            candidates=list(set(all_candidates))  # Remove duplicates
        )