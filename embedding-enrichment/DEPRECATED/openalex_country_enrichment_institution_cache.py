"""
Institution-Cached OpenAlex Country Enrichment Service
Extracts unique institutions first, then makes minimal LLM calls for maximum efficiency.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple, Set
import sys
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from enrichment_framework import BaseEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

class InstitutionCachedOpenAlexCountryEnrichment(BaseEnrichment):
    """
    Optimized enrichment service that caches institution country lookups.
    
    Key optimizations:
    - Extract all unique institutions first
    - Make LLM calls only for unique institutions
    - Cache results and apply to all papers with same institution
    - Dramatically reduces API calls (90%+ reduction)
    """
    
    def __init__(self):
        super().__init__("openalex_country", "derived")
        # Use RAND's Azure OpenAI service configuration
        self.azure_openai_key = "a349cd5ebfcb45f59b2004e6e8b7d700"
        self.azure_openai_endpoint = "https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4o-2024-11-20-us/chat/completions?api-version=2024-02-01"
        
    def get_required_fields(self) -> List[str]:
        """Get fields required from doctrove_papers table."""
        return ['doctrove_paper_id', 'doctrove_source']
    
    def get_field_definitions(self) -> Dict[str, str]:
        """Get field definitions for the enrichment table."""
        return {
            'country': 'TEXT',
            'uschina': 'TEXT',
            'institution_name': 'TEXT',
            'confidence': 'FLOAT',
            'llm_response': 'TEXT'
        }
    
    def fetch_metadata_batch(self, paper_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch OpenAlex metadata for a batch of papers in one query.
        
        Args:
            paper_ids: List of doctrove_paper_ids
            
        Returns:
            Dictionary mapping paper_id to metadata
        """
        if not paper_ids:
            return {}
        
        # Convert list to tuple for SQL IN clause
        paper_ids_tuple = tuple(paper_ids)
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Use a single query to get all metadata
                cur.execute("""
                    SELECT doctrove_paper_id, openalex_raw_data
                    FROM openalex_metadata 
                    WHERE doctrove_paper_id IN %s
                """, (paper_ids_tuple,))
                
                metadata_dict = {}
                for row in cur.fetchall():
                    paper_id = row[0]
                    raw_data = row[1]
                    
                    if raw_data:
                        try:
                            # Parse JSON once per paper
                            if isinstance(raw_data, str):
                                parsed_data = json.loads(raw_data)
                            else:
                                parsed_data = raw_data
                            
                            metadata_dict[paper_id] = parsed_data
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON for paper {paper_id}")
                            continue
                
                return metadata_dict
    
    def extract_institution_info_from_metadata(self, paper_id: str, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract institution information from pre-parsed metadata.
        
        Args:
            paper_id: Paper ID for logging
            raw_data: Pre-parsed OpenAlex raw data
            
        Returns:
            Dictionary with institution info or None if not found
        """
        try:
            # Get authorships from the raw data
            authorships = raw_data.get('authorships', [])
            if not authorships or len(authorships) == 0:
                return None
            
            # Look through all authorships to find the first one with institution data
            for authorship in authorships:
                # Check if we have country information directly
                countries = authorship.get('countries', [])
                if countries and len(countries) > 0:
                    # Use the first country
                    country_code = countries[0]
                    return {
                        'country_code': country_code,
                        'source': 'direct_country',
                        'institution_name': None
                    }
                
                # Check if we have institutions with country information
                institutions = authorship.get('institutions', [])
                if institutions and len(institutions) > 0:
                    # Get the first institution's country
                    first_institution = institutions[0]
                    country_code = first_institution.get('country_code')
                    institution_name = first_institution.get('display_name')
                    
                    if country_code:
                        return {
                            'country_code': country_code,
                            'institution_name': institution_name,
                            'source': 'institution_country'
                        }
                    elif institution_name:
                        return {
                            'country_code': None,
                            'institution_name': institution_name,
                            'source': 'institution_no_country'
                        }
                
                # Fallback to raw affiliation strings for LLM processing
                raw_affiliations = authorship.get('raw_affiliation_strings', [])
                if raw_affiliations and len(raw_affiliations) > 0:
                    return {
                        'country_code': None,
                        'institution_name': raw_affiliations[0],
                        'source': 'raw_affiliation'
                    }
            
            return None
            
        except (KeyError, IndexError) as e:
            logger.warning(f"Error extracting institution info from paper {paper_id}: {e}")
            return None
    
    def convert_country_code_to_names(self, country_code: str) -> Tuple[str, str]:
        """
        Convert country code to full country name and uschina code.
        
        Args:
            country_code: Two-letter country code (e.g., 'US', 'CN', 'GH')
            
        Returns:
            Tuple of (country_name, uschina_code)
        """
        # Simplified country mapping for performance
        country_mapping = {
            'US': 'United States',
            'CN': 'China',
            'GB': 'United Kingdom',
            'DE': 'Germany',
            'FR': 'France',
            'CA': 'Canada',
            'AU': 'Australia',
            'JP': 'Japan',
            'IN': 'India',
            'BR': 'Brazil',
            'IT': 'Italy',
            'ES': 'Spain',
            'NL': 'Netherlands',
            'SE': 'Sweden',
            'CH': 'Switzerland',
            'KR': 'South Korea',
            'RU': 'Russia',
            'SG': 'Singapore',
            'IL': 'Israel',
            'NO': 'Norway',
            'DK': 'Denmark',
            'FI': 'Finland',
            'BE': 'Belgium',
            'AT': 'Austria',
            'IE': 'Ireland',
            'NZ': 'New Zealand',
            'PL': 'Poland',
            'PT': 'Portugal',
            'GR': 'Greece',
            'CZ': 'Czech Republic',
            'HU': 'Hungary',
            'TR': 'Turkey',
            'MX': 'Mexico',
            'AR': 'Argentina',
            'CL': 'Chile',
            'CO': 'Colombia',
            'PE': 'Peru',
            'VE': 'Venezuela',
            'ZA': 'South Africa',
            'EG': 'Egypt',
            'NG': 'Nigeria',
            'KE': 'Kenya',
            'GH': 'Ghana',
            'ET': 'Ethiopia',
            'UG': 'Uganda',
            'TZ': 'Tanzania',
            'MW': 'Malawi',
            'ZM': 'Zambia',
            'ZW': 'Zimbabwe',
            'BW': 'Botswana',
            'NA': 'Namibia',
            'LS': 'Lesotho',
            'SZ': 'Eswatini',
            'MG': 'Madagascar',
            'MU': 'Mauritius',
            'SC': 'Seychelles',
            'DJ': 'Djibouti',
            'SO': 'Somalia',
            'ER': 'Eritrea',
            'SD': 'Sudan',
            'SS': 'South Sudan',
            'CF': 'Central African Republic',
            'TD': 'Chad',
            'CM': 'Cameroon',
            'GQ': 'Equatorial Guinea',
            'GA': 'Gabon',
            'CG': 'Republic of the Congo',
            'CD': 'Democratic Republic of the Congo',
            'AO': 'Angola',
            'ST': 'São Tomé and Príncipe',
            'GW': 'Guinea-Bissau',
            'GN': 'Guinea',
            'SL': 'Sierra Leone',
            'LR': 'Liberia',
            'CI': 'Ivory Coast',
            'BF': 'Burkina Faso',
            'ML': 'Mali',
            'NE': 'Niger',
            'SN': 'Senegal',
            'GM': 'Gambia',
            'CV': 'Cape Verde',
            'MR': 'Mauritania',
            'MA': 'Morocco',
            'DZ': 'Algeria',
            'TN': 'Tunisia',
            'LY': 'Libya',
            'EH': 'Western Sahara',
            'SA': 'Saudi Arabia',
            'AE': 'United Arab Emirates',
            'QA': 'Qatar',
            'KW': 'Kuwait',
            'BH': 'Bahrain',
            'OM': 'Oman',
            'YE': 'Yemen',
            'JO': 'Jordan',
            'LB': 'Lebanon',
            'SY': 'Syria',
            'IQ': 'Iraq',
            'IR': 'Iran',
            'AF': 'Afghanistan',
            'PK': 'Pakistan',
            'BD': 'Bangladesh',
            'LK': 'Sri Lanka',
            'NP': 'Nepal',
            'BT': 'Bhutan',
            'MV': 'Maldives',
            'MM': 'Myanmar',
            'TH': 'Thailand',
            'LA': 'Laos',
            'KH': 'Cambodia',
            'VN': 'Vietnam',
            'MY': 'Malaysia',
            'ID': 'Indonesia',
            'PH': 'Philippines',
            'TL': 'East Timor',
            'BN': 'Brunei',
            'PG': 'Papua New Guinea',
            'FJ': 'Fiji',
            'NC': 'New Caledonia',
            'VU': 'Vanuatu',
            'SB': 'Solomon Islands',
            'TO': 'Tonga',
            'WS': 'Samoa',
            'KI': 'Kiribati',
            'TV': 'Tuvalu',
            'NR': 'Nauru',
            'PW': 'Palau',
            'MH': 'Marshall Islands',
            'FM': 'Micronesia',
            'CK': 'Cook Islands',
            'NU': 'Niue',
            'TK': 'Tokelau',
            'AS': 'American Samoa',
            'GU': 'Guam',
            'MP': 'Northern Mariana Islands',
            'PR': 'Puerto Rico',
            'VI': 'U.S. Virgin Islands',
            'AI': 'Anguilla',
            'AG': 'Antigua and Barbuda',
            'AW': 'Aruba',
            'BS': 'Bahamas',
            'BB': 'Barbados',
            'BZ': 'Belize',
            'BM': 'Bermuda',
            'VG': 'British Virgin Islands',
            'KY': 'Cayman Islands',
            'CR': 'Costa Rica',
            'CU': 'Cuba',
            'DM': 'Dominica',
            'DO': 'Dominican Republic',
            'SV': 'El Salvador',
            'GD': 'Grenada',
            'GT': 'Guatemala',
            'HT': 'Haiti',
            'HN': 'Honduras',
            'JM': 'Jamaica',
            'NI': 'Nicaragua',
            'PA': 'Panama',
            'KN': 'Saint Kitts and Nevis',
            'LC': 'Saint Lucia',
            'VC': 'Saint Vincent and the Grenadines',
            'TT': 'Trinidad and Tobago',
            'TC': 'Turks and Caicos Islands',
            'UY': 'Uruguay',
            'PY': 'Paraguay',
            'BO': 'Bolivia',
            'EC': 'Ecuador',
            'GY': 'Guyana',
            'SR': 'Suriname',
            'FK': 'Falkland Islands',
            'GF': 'French Guiana',
            'RO': 'Romania',
            'BG': 'Bulgaria',
            'HR': 'Croatia',
            'SI': 'Slovenia',
            'SK': 'Slovakia',
            'EE': 'Estonia',
            'LV': 'Latvia',
            'LT': 'Lithuania',
            'MT': 'Malta',
            'CY': 'Cyprus',
            'LU': 'Luxembourg',
            'IS': 'Iceland',
            'AD': 'Andorra',
            'MC': 'Monaco',
            'LI': 'Liechtenstein',
            'SM': 'San Marino',
            'VA': 'Vatican City',
            'AL': 'Albania',
            'BA': 'Bosnia and Herzegovina',
            'ME': 'Montenegro',
            'MK': 'North Macedonia',
            'RS': 'Serbia',
            'XK': 'Kosovo',
            'AM': 'Armenia',
            'AZ': 'Azerbaijan',
            'BY': 'Belarus',
            'GE': 'Georgia',
            'KZ': 'Kazakhstan',
            'KG': 'Kyrgyzstan',
            'MD': 'Moldova',
            'TJ': 'Tajikistan',
            'TM': 'Turkmenistan',
            'UZ': 'Uzbekistan',
            'MN': 'Mongolia',
            'KP': 'North Korea',
            'TW': 'Taiwan',
            'HK': 'Hong Kong',
            'MO': 'Macau'
        }
        
        # Get full country name
        country_name = country_mapping.get(country_code, f"Unknown ({country_code})")
        
        # Determine uschina code - only assign known countries to specific categories
        if country_code == 'US':
            uschina = 'United States'
        elif country_code == 'CN':
            uschina = 'China'
        elif country_code in country_mapping:
            # Known country that's not US or China
            uschina = 'Rest of the World'
        else:
            # Unknown country code
            uschina = 'Unknown'
        
        return country_name, uschina
    
    def determine_country_with_llm(self, institution_name: str, max_retries: int = 3) -> Tuple[str, str, float, str]:
        """
        Use Azure OpenAI to determine the country for an institution.
        Includes rate limiting and retry logic.
        
        Args:
            institution_name: Name of the institution
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (country_name, uschina_code, confidence, llm_response)
        """
        if not self.azure_openai_key or not self.azure_openai_endpoint:
            logger.error("Azure OpenAI credentials not configured")
            return "Unknown", "Unknown", 0.0, "Azure OpenAI not configured"
        
        for attempt in range(max_retries + 1):
            try:
                import requests
                import certifi
                
                # Create prompt
                prompt = f"""Determine the country for this academic institution: {institution_name}

Return your response in this exact JSON format:
{{
    "country": "Full country name",
    "uschina": "United States" or "China" or "Rest of the World" or "Unknown"
}}

Use "United States" for US institutions, "China" for Chinese institutions, "Rest of the World" for known non-US/China countries, and "Unknown" only if you cannot determine the country.

IMPORTANT: Return ONLY the JSON. Do not include any markdown formatting, code blocks, or additional text."""
                
                # Call Azure OpenAI using RAND's API
                headers = {
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": self.azure_openai_key
                }
                
                data = {
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that determines countries for academic institutions."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1
                }
                
                response = requests.post(
                    self.azure_openai_endpoint, 
                    headers=headers, 
                    json=data, 
                    verify=certifi.where(), 
                    timeout=30
                )
                
                # Handle rate limiting
                if response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited for {institution_name}. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries + 1}")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                response_data = response.json()
                llm_response = response_data["choices"][0]["message"]["content"].strip()
                
                # Parse response - handle markdown formatting
                try:
                    # Strip markdown formatting if present
                    cleaned_response = llm_response.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                    
                    result = json.loads(cleaned_response)
                    country = result.get('country', 'Unknown')
                    uschina = result.get('uschina', 'Unknown')
                    confidence = 0.95  # High confidence for structured response
                    
                    # Validate uschina code - ensure it's one of the four valid categories
                    valid_uschina_codes = ['United States', 'China', 'Rest of the World', 'Unknown']
                    if uschina not in valid_uschina_codes:
                        logger.warning(f"Invalid uschina code '{uschina}' for {institution_name}, defaulting to 'Unknown'")
                        uschina = 'Unknown'
                    
                    # Add rate limiting delay between successful calls
                    time.sleep(0.5)  # 0.5 second delay between individual calls
                    
                    return country, uschina, confidence, llm_response
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse LLM response for {institution_name}: {llm_response}")
                    return "Unknown", "Unknown", 0.5, llm_response
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Request failed for {institution_name} (attempt {attempt + 1}/{max_retries + 1}): {e}. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All retry attempts failed for {institution_name}: {e}")
                    return "Unknown", "Unknown", 0.0, f"Error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error calling Azure OpenAI for {institution_name}: {e}")
                return "Unknown", "Unknown", 0.0, f"Error: {str(e)}"
        
        # If we get here, all retries failed
        logger.error(f"All retry attempts failed for {institution_name}")
        return "Unknown", "Unknown", 0.0, "All retry attempts failed"
    
    def determine_countries_batch_with_llm(self, institution_names: List[str], max_retries: int = 3) -> Dict[str, Tuple[str, str, float, str]]:
        """
        Use Azure OpenAI to determine countries for multiple institutions in a single API call.
        Includes rate limiting and retry logic. Failed institutions are tagged for later processing.
        
        Args:
            institution_names: List of institution names
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary mapping institution_name to (country_name, uschina_code, confidence, llm_response)
        """
        if not self.azure_openai_key or not self.azure_openai_endpoint:
            logger.error("Azure OpenAI credentials not configured")
            return {name: ("Unknown", "Unknown", 0.0, "Azure OpenAI not configured") for name in institution_names}
        
        if not institution_names:
            return {}
        
        for attempt in range(max_retries + 1):
            try:
                import requests
                import certifi
                
                # Create batched prompt
                institutions_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(institution_names)])
                
                prompt = f"""Determine the country for each of these academic institutions:

{institutions_text}

Return your response as a JSON array with one object per institution, in this exact format:
[
    {{
        "institution": "institution name",
        "country": "Full country name",
        "uschina": "United States" or "China" or "Rest of the World" or "Unknown"
    }},
    ...
]

Use "United States" for US institutions, "China" for Chinese institutions, "Rest of the World" for known non-US/China countries, and "Unknown" only if you cannot determine the country.

IMPORTANT: Return ONLY the JSON array. Do not include any markdown formatting, code blocks, or additional text."""
                
                # Call Azure OpenAI using RAND's API
                headers = {
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": self.azure_openai_key
                }
                
                data = {
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that determines countries for academic institutions. Process multiple institutions efficiently."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,  # Increased for batch processing
                    "temperature": 0.1
                }
                
                response = requests.post(
                    self.azure_openai_endpoint, 
                    headers=headers, 
                    json=data, 
                    verify=certifi.where(), 
                    timeout=60  # Increased timeout for batch processing
                )
                
                # Handle rate limiting
                if response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries + 1}")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                response_data = response.json()
                llm_response = response_data["choices"][0]["message"]["content"].strip()
                
                # Parse response - handle markdown formatting
                try:
                    # Strip markdown formatting if present
                    cleaned_response = llm_response.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                    
                    results = json.loads(cleaned_response)
                    if not isinstance(results, list):
                        raise ValueError("Expected JSON array")
                    
                    # Create mapping from institution name to result
                    institution_results = {}
                    for result in results:
                        institution_name = result.get('institution', '').strip()
                        country = result.get('country', 'Unknown')
                        uschina = result.get('uschina', 'Unknown')
                        
                        # Validate uschina code
                        valid_uschina_codes = ['United States', 'China', 'Rest of the World', 'Unknown']
                        if uschina not in valid_uschina_codes:
                            logger.warning(f"Invalid uschina code '{uschina}' for {institution_name}, defaulting to 'Unknown'")
                            uschina = 'Unknown'
                        
                        institution_results[institution_name] = (country, uschina, 0.95, llm_response)
                    
                    # Handle any institutions that weren't in the response - tag them for later processing
                    failed_institutions = []
                    for institution_name in institution_names:
                        if institution_name not in institution_results:
                            failed_institutions.append(institution_name)
                            # Tag as failed for later processing
                            institution_results[institution_name] = ("FAILED_BATCH", "FAILED_BATCH", 0.0, f"Failed to process in batch: {llm_response}")
                    
                    if failed_institutions:
                        logger.warning(f"Failed to process {len(failed_institutions)} institutions in batch - will be processed later")
                    
                    # Add rate limiting delay between successful calls
                    time.sleep(1)  # 1 second delay between calls
                    
                    return institution_results
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse LLM response for batch: {e}")
                    logger.warning(f"Response was: {llm_response}")
                    # Tag all institutions in this batch as failed for later processing
                    failed_results = {}
                    for institution_name in institution_names:
                        failed_results[institution_name] = ("FAILED_BATCH", "FAILED_BATCH", 0.0, f"Batch parsing failed: {str(e)}")
                    logger.warning(f"Tagged {len(institution_names)} institutions for later processing due to parsing failure")
                    return failed_results
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All retry attempts failed for batch: {e}")
                    # Tag all institutions as failed for later processing
                    failed_results = {}
                    for institution_name in institution_names:
                        failed_results[institution_name] = ("FAILED_BATCH", "FAILED_BATCH", 0.0, f"All retry attempts failed: {str(e)}")
                    logger.warning(f"Tagged {len(institution_names)} institutions for later processing due to retry failures")
                    return failed_results
            
            except Exception as e:
                logger.error(f"Unexpected error calling Azure OpenAI for batch: {e}")
                # Tag all institutions as failed for later processing
                failed_results = {}
                for institution_name in institution_names:
                    failed_results[institution_name] = ("FAILED_BATCH", "FAILED_BATCH", 0.0, f"Unexpected error: {str(e)}")
                logger.warning(f"Tagged {len(institution_names)} institutions for later processing due to unexpected error")
                return failed_results
        
        # If we get here, all retries failed
        logger.error(f"All retry attempts failed for batch of {len(institution_names)} institutions")
        failed_results = {}
        for institution_name in institution_names:
            failed_results[institution_name] = ("FAILED_BATCH", "FAILED_BATCH", 0.0, "All retry attempts failed")
        logger.warning(f"Tagged {len(institution_names)} institutions for later processing due to all retry failures")
        return failed_results
    
    def _fallback_individual_processing(self, institution_names: List[str]) -> Dict[str, Tuple[str, str, float, str]]:
        """
        Fallback method to process institutions individually if batch processing fails.
        
        Args:
            institution_names: List of institution names
            
        Returns:
            Dictionary mapping institution_name to (country_name, uschina_code, confidence, llm_response)
        """
        logger.debug(f"Falling back to individual processing for {len(institution_names)} institutions")
        results = {}
        for institution_name in institution_names:
            country, uschina, confidence, llm_response = self.determine_country_with_llm(institution_name)
            results[institution_name] = (country, uschina, confidence, llm_response)
        return results
    
    def process_papers_with_institution_cache(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers using institution caching for maximum efficiency.
        
        Args:
            papers: List of paper dictionaries with required fields
            
        Returns:
            List of enrichment result dictionaries
        """
        if not papers:
            return []
        
        # Extract paper IDs for batch processing
        paper_ids = [paper['doctrove_paper_id'] for paper in papers if paper.get('doctrove_source') == 'openalex']
        
        if not paper_ids:
            return []
        
        logger.debug(f"Processing {len(paper_ids)} OpenAlex papers with institution caching")
        
        # Fetch all metadata in one batch query
        metadata_dict = self.fetch_metadata_batch(paper_ids)
        logger.debug(f"Retrieved metadata for {len(metadata_dict)} papers")
        
        # Phase 1: Extract all institution information
        paper_institution_map = {}  # paper_id -> institution_info
        unique_institutions = set()  # Set of unique institution names
        
        for paper in papers:
            if paper.get('doctrove_source') != 'openalex':
                continue
                
            paper_id = paper['doctrove_paper_id']
            raw_data = metadata_dict.get(paper_id)
            
            if not raw_data:
                continue
            
            # Extract institution information
            institution_info = self.extract_institution_info_from_metadata(paper_id, raw_data)
            if not institution_info:
                continue
            
            paper_institution_map[paper_id] = institution_info
            
            # Add to unique institutions if it needs LLM processing
            if institution_info['source'] in ['institution_no_country', 'raw_affiliation']:
                institution_name = institution_info['institution_name']
                if institution_name:
                    unique_institutions.add(institution_name)
        
        logger.debug(f"Found {len(unique_institutions)} unique institutions needing LLM processing")
        
        # Phase 2: Process unique institutions with batched LLM calls
        institution_cache = {}  # institution_name -> (country, uschina, confidence, llm_response)
        
        if unique_institutions:
            unique_institutions_list = list(unique_institutions)
            batch_size = 50  # Process up to 50 institutions per API call
            
            logger.debug(f"Processing {len(unique_institutions_list)} unique institutions with batched LLM calls (batch size: {batch_size})")
            
            for i in range(0, len(unique_institutions_list), batch_size):
                batch_institutions = unique_institutions_list[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(unique_institutions_list) + batch_size - 1) // batch_size
                
                logger.debug(f"Processing batch {batch_num}/{total_batches}: {len(batch_institutions)} institutions")
                
                # Process batch of institutions
                batch_results = self.determine_countries_batch_with_llm(batch_institutions)
                institution_cache.update(batch_results)
        
        # Phase 3: Generate results using cached data
        results = []
        
        for paper_id, institution_info in paper_institution_map.items():
            source = institution_info.get('source')
            confidence = 0.95  # High confidence for OpenAlex data
            
            if source == 'direct_country':
                # We have direct country code from OpenAlex
                country_code = institution_info['country_code']
                country, uschina = self.convert_country_code_to_names(country_code)
                institution_name = None
                llm_response = f"Direct country code: {country_code}"
                
            elif source == 'institution_country':
                # We have country code from institution
                country_code = institution_info['country_code']
                country, uschina = self.convert_country_code_to_names(country_code)
                institution_name = institution_info.get('institution_name')
                llm_response = f"Institution country code: {country_code}"
                
            elif source in ['institution_no_country', 'raw_affiliation']:
                # Use cached LLM result
                institution_name = institution_info['institution_name']
                if institution_name in institution_cache:
                    country, uschina, confidence, llm_response = institution_cache[institution_name]
                else:
                    logger.warning(f"No cached result for institution: {institution_name}")
                    continue
                
            else:
                logger.warning(f"Unknown source type: {source}")
                continue
            
            # Create enrichment result
            result = {
                'paper_id': paper_id,
                'openalex_country_country': country,
                'openalex_country_uschina': uschina,
                'openalex_country_institution_name': institution_name,
                'openalex_country_confidence': confidence,
                'openalex_country_llm_response': llm_response
            }
            
            results.append(result)
            logger.debug(f"Processed {institution_name or 'Unknown'} -> {country} ({uschina}) via {source}")
        
        return results
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers using the institution caching approach.
        
        Args:
            papers: List of paper dictionaries with required fields
            
        Returns:
            List of enrichment result dictionaries
        """
        return self.process_papers_with_institution_cache(papers)

def create_institution_cached_openalex_country_enrichment() -> InstitutionCachedOpenAlexCountryEnrichment:
    """Factory function to create institution-cached OpenAlex country enrichment service."""
    return InstitutionCachedOpenAlexCountryEnrichment()
