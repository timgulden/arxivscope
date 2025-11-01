"""
OpenAlex Country Enrichment Service
Enriches OpenAlex papers with country information for first author institutions.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
import sys

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from enrichment_framework import BaseEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

class OpenAlexCountryEnrichment(BaseEnrichment):
    """
    Enrichment service for determining countries of first author institutions in OpenAlex papers.
    
    Creates an enrichment table with:
    - country: Full country name
    - uschina: Coded as "United States", "China", or "Rest of the World"
    """
    
    def __init__(self):
        super().__init__("openalex_country", "derived")
        # Use RAND's Azure OpenAI service configuration
        self.azure_openai_key = "a349cd5ebfcb45f59b2004e6e8b7d700"
        self.azure_openai_endpoint = "https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4o-2024-11-20-us/chat/completions?api-version=2024-02-01"
        
    def get_required_fields(self) -> List[str]:
        """Get fields required from doctrove_papers table."""
        return ['doctrove_paper_id', 'doctrove_source']
    
    def get_source_metadata(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get OpenAlex metadata for a paper.
        
        Args:
            paper: Paper dictionary with doctrove_paper_id
            
        Returns:
            OpenAlex metadata dictionary
        """
        if paper.get('doctrove_source') != 'openalex':
            return {}
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        SELECT * FROM openalex_metadata 
                        WHERE doctrove_paper_id = %s
                    """, (paper['doctrove_paper_id'],))
                    
                    row = cur.fetchone()
                    if row:
                        # Convert row to dict using column names
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, row))
                except Exception as e:
                    logger.warning(f"Could not get OpenAlex metadata: {e}")
        
        return {}
    
    def get_field_definitions(self) -> Dict[str, str]:
        """Get field definitions for the enrichment table."""
        return {
            'country': 'TEXT',
            'uschina': 'TEXT',
            'institution_name': 'TEXT',
            'confidence': 'FLOAT',
            'llm_response': 'TEXT'
        }
    
    def extract_first_author_country_info(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract country information for the first author from OpenAlex metadata.
        
        Args:
            paper: Paper dictionary with doctrove_paper_id
            
        Returns:
            Dictionary with country info or None if not found
        """
        try:
            # Get OpenAlex metadata for this paper
            source_metadata = self.get_source_metadata(paper)
            if not source_metadata:
                logger.debug(f"No source metadata found for paper {paper.get('doctrove_paper_id')}")
                return None
            
            # Parse the raw data JSON
            raw_data = source_metadata.get('openalex_raw_data')
            if not raw_data:
                logger.debug(f"No raw data found for paper {paper.get('doctrove_paper_id')}")
                return None
                
            if isinstance(raw_data, str):
                raw_data = json.loads(raw_data)
            
            # Get authorships from the raw data
            authorships = raw_data.get('authorships', [])
            if not authorships or len(authorships) == 0:
                return None
            
            # Get first author's information
            first_author = authorships[0]
            
            # Check if we have country information directly
            countries = first_author.get('countries', [])
            if countries and len(countries) > 0:
                # Use the first country
                country_code = countries[0]
                return {
                    'country_code': country_code,
                    'source': 'direct_country'
                }
            
            # Check if we have institutions with country information
            institutions = first_author.get('institutions', [])
            if institutions and len(institutions) > 0:
                # Get the first institution's country
                first_institution = institutions[0]
                country_code = first_institution.get('country_code')
                if country_code:
                    return {
                        'country_code': country_code,
                        'institution_name': first_institution.get('display_name'),
                        'source': 'institution_country'
                    }
            
            # Fallback to raw affiliation strings for LLM processing
            raw_affiliations = first_author.get('raw_affiliation_strings', [])
            if raw_affiliations and len(raw_affiliations) > 0:
                return {
                    'institution_name': raw_affiliations[0],
                    'source': 'raw_affiliation'
                }
            
            return None
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Error extracting country info from paper {paper.get('doctrove_paper_id')}: {e}")
            return None
    
    def convert_country_code_to_names(self, country_code: str) -> Tuple[str, str]:
        """
        Convert country code to full country name and uschina code.
        
        Args:
            country_code: Two-letter country code (e.g., 'US', 'CN', 'GH')
            
        Returns:
            Tuple of (country_name, uschina_code)
        """
        # Country code to full name mapping
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
        
        # Determine uschina code
        if country_code == 'US':
            uschina = 'United States'
        elif country_code == 'CN':
            uschina = 'China'
        else:
            uschina = 'Rest of the World'
        
        return country_name, uschina
    
    def determine_country_with_llm(self, institution_name: str) -> Tuple[str, str, float, str]:
        """
        Use Azure OpenAI to determine the country for an institution.
        
        Args:
            institution_name: Name of the institution
            
        Returns:
            Tuple of (country_name, uschina_code, confidence, llm_response)
        """
        if not self.azure_openai_key or not self.azure_openai_endpoint:
            logger.error("Azure OpenAI credentials not configured")
            return "Unknown", "Rest of the World", 0.0, "Azure OpenAI not configured"
        
        try:
            import requests
            import certifi
            
            # Create prompt
            prompt = f"""Determine the country for this academic institution: {institution_name}

Return your response in this exact JSON format:
{{
    "country": "Full country name",
    "uschina": "United States" or "China" or "Rest of the World"
}}

Only return the JSON, no other text."""
            
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
            response.raise_for_status()
            
            response_data = response.json()
            llm_response = response_data["choices"][0]["message"]["content"].strip()
            
            # Parse response
            try:
                result = json.loads(llm_response)
                country = result.get('country', 'Unknown')
                uschina = result.get('uschina', 'Rest of the World')
                confidence = 0.95  # High confidence for structured response
                
                return country, uschina, confidence, llm_response
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response for {institution_name}: {llm_response}")
                return "Unknown", "Rest of the World", 0.5, llm_response
                
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI for {institution_name}: {e}")
            return "Unknown", "Rest of the World", 0.0, f"Error: {str(e)}"
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers and return country enrichment results.
        
        Args:
            papers: List of paper dictionaries with required fields
            
        Returns:
            List of enrichment result dictionaries
        """
        results = []
        
        for paper in papers:
            # Only process OpenAlex papers
            if paper.get('doctrove_source') != 'openalex':
                continue
                
            # Extract first author country information
            country_info = self.extract_first_author_country_info(paper)
            if not country_info:
                logger.debug(f"No country info found for paper {paper.get('doctrove_paper_id')}")
                continue
            
            source = country_info.get('source')
            confidence = 0.95  # High confidence for OpenAlex data
            
            if source == 'direct_country':
                # We have direct country code from OpenAlex
                country_code = country_info['country_code']
                country, uschina = self.convert_country_code_to_names(country_code)
                institution_name = None
                llm_response = f"Direct country code: {country_code}"
                
            elif source == 'institution_country':
                # We have country code from institution
                country_code = country_info['country_code']
                country, uschina = self.convert_country_code_to_names(country_code)
                institution_name = country_info.get('institution_name')
                llm_response = f"Institution country code: {country_code}"
                
            elif source == 'raw_affiliation':
                # Fallback to LLM for raw affiliation strings
                institution_name = country_info['institution_name']
                country, uschina, confidence, llm_response = self.determine_country_with_llm(institution_name)
                
            else:
                logger.warning(f"Unknown source type: {source}")
                continue
            
            # Create enrichment result
            result = {
                'paper_id': paper['doctrove_paper_id'],
                'openalex_country_country': country,
                'openalex_country_uschina': uschina,
                'openalex_country_institution_name': institution_name,
                'openalex_country_confidence': confidence,
                'openalex_country_llm_response': llm_response
            }
            
            results.append(result)
            logger.debug(f"Processed {institution_name or 'Unknown'} -> {country} ({uschina}) via {source}")
        
        return results

def create_openalex_country_enrichment() -> OpenAlexCountryEnrichment:
    """Factory function to create OpenAlex country enrichment service."""
    return OpenAlexCountryEnrichment()

if __name__ == "__main__":
    # Test with a small subset of papers
    logging.basicConfig(level=logging.INFO)
    
    # Get connection factory
    connection_factory = create_connection_factory()
    
    # Get small subset of OpenAlex papers for testing
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_authors, doctrove_source
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                LIMIT 5
            """)
            
            papers = []
            for row in cur.fetchall():
                papers.append({
                    'doctrove_paper_id': row[0],
                    'doctrove_authors': row[1],
                    'doctrove_source': row[2]
                })
    
    # Create and run enrichment
    enrichment = create_openalex_country_enrichment()
    
    # Create table if needed
    enrichment.create_table_if_needed()
    
    # Process papers
    results = enrichment.process_papers(papers)
    
    # Insert results
    if results:
        inserted_count = enrichment.insert_results(results)
        print(f"Successfully processed {len(results)} papers, inserted {inserted_count} records")
    else:
        print("No results to insert")
