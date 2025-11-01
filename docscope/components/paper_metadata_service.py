"""
Pure functional service for paper metadata display.
Handles paper metadata formatting and UI generation using pure functions.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Import Dash html components for link formatting
try:
    from dash import html
except ImportError:
    html = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperMetadata:
    """Immutable paper metadata container."""
    paper_id: str
    title: str
    summary: str
    date: str
    source: str
    authors: List[str]
    doi: str
    similarity_score: Optional[float]
    links: str


def parse_click_data(click_data: Optional[Dict[str, Any]]) -> Optional[PaperMetadata]:
    """
    Parse click data into structured paper metadata.
    
    Args:
        click_data: Raw click data from Plotly scatter plot
        
    Returns:
        Structured PaperMetadata or None if invalid
    """
    if not click_data or not isinstance(click_data, dict):
        return None
    
    points = click_data.get("points", [])
    if not points:
        return None
    
    point = points[0]
    customdata = point.get("customdata")
    if not customdata:
        return None
    
    try:
        # SIMPLE APPROACH: Always fetch individual metadata using paper ID
        # Extract paper ID from click data (first field)
        paper_id = customdata[0] if customdata else None
        print(f"🔍 CLICK DEBUG: Extracted paper ID: {paper_id}")
        
        if not paper_id:
            print(f"🔍 CLICK DEBUG: No paper ID found in click data")
            return None
        
        # Always fetch full metadata for this paper
        print(f"🔍 CLICK DEBUG: Fetching individual metadata for paper {paper_id}")
        try:
            from .data_service import fetch_paper_detail_from_api
            df = fetch_paper_detail_from_api(paper_id)
            print(f"🔍 CLICK DEBUG: Individual fetch returned {len(df)} rows")
            
            if not df.empty:
                row = df.iloc[0]
                title = row.get('Title', '')
                summary = row.get('Summary', '')
                date = row.get('Primary Date', '')
                source = row.get('Source', '')
                authors = row.get('Authors', '')
                doi = row.get('DOI', '')
                links = row.get('Links', '')
                print(f"🔍 CLICK DEBUG: Extracted summary length: {len(summary) if summary else 0}")
            else:
                print(f"🔍 CLICK DEBUG: No data returned from individual fetch")
                return None
        except Exception as e:
            print(f"🔍 CLICK DEBUG: Error fetching full metadata: {e}")
            logger.warning(f"Could not fetch full metadata for paper {paper_id}: {e}")
            return None
        
        # Validate required fields
        if not paper_id or not title:
            return None
        
        return PaperMetadata(
            paper_id=paper_id,
            title=title,
            summary=summary or 'No summary available',
            date=date or 'No date available',
            source=source or 'Unknown source',
            authors=authors if isinstance(authors, list) else [authors] if authors else [],
            doi=doi or '',
            similarity_score=None,  # Not needed for individual paper fetch
            links=links or ''
        )
        
    except (ValueError, TypeError, IndexError) as e:
        logger.error(f"Error parsing click data: {e}")
        return None


def format_authors(authors: List[str]) -> str:
    """Format authors list into display string."""
    if not authors:
        return 'No authors available'
    
    # Clean and format author names
    cleaned_authors = []
    for author in authors:
        if isinstance(author, str) and author.strip():
            cleaned_authors.append(author.strip())
    
    if not cleaned_authors:
        return 'No authors available'
    
    return ', '.join(cleaned_authors)


def format_date(date_str: str) -> str:
    """Format date string for display."""
    if not date_str:
        return 'No date available'
    
    try:
        # Handle various date formats
        if isinstance(date_str, str):
            if 'GMT' in date_str or 'UTC' in date_str:
                # Parse format: "Thu, 10 Jul 2025 00:00:00 GMT"
                from datetime import datetime
                parsed_date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                return f"Year: {parsed_date.year}"
            elif len(date_str) >= 4 and date_str[:4].isdigit():
                # Extract year from string
                return f"Year: {date_str[:4]}"
        
        return str(date_str)
        
    except Exception:
        return str(date_str)


def format_similarity_score(score: Optional[float]) -> str:
    """Format similarity score for display."""
    if score is not None:
        return f"Similarity Score: {score:.3f}"
    return ""


def create_doi_link(doi: str) -> Optional[Any]:
    """Create DOI link if available."""
    if not doi or not isinstance(doi, str):
        return None
    
    try:
        # Import Dash html components
        from dash import html
        
        return html.A(
            f"DOI: {doi}",
            href=f"https://doi.org/{doi}",
            target="_blank",
            style={
                'color': '#87CEEB', 
                'text-decoration': 'none',
                'background-color': 'rgba(135, 206, 235, 0.1)',
                'padding': '6px 12px',
                'border-radius': '4px',
                'border': '1px solid rgba(135, 206, 235, 0.3)',
                'font-size': '12px',
                'font-weight': '500'
            }
        )
    except ImportError:
        # Fallback if Dash html is not available
        logger.warning("Dash html components not available for DOI link")
        return None


def extract_and_format_links(links_data: str, source: str) -> List[Any]:
    """
    Extract and format links from the doctrove_links field.
    
    The links field contains JSON arrays with objects like:
    [{"href": "https://example.com", "rel": "alternate", "type": "text/html"}]
    
    Args:
        links_data: Raw links data from the database (JSON string)
        source: Data source (openalex, aipickle, randpub, extpub)
        
    Returns:
        List of formatted clickable links or empty list if html not available
    """
    if not links_data or not isinstance(links_data, str) or html is None:
        if source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"extpub: No links data available or html not available")
        return []
    
    # Debug logging to see what the actual link data looks like (only if debug enabled)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Processing links for source '{source}': {links_data[:200]}...")
    
    # Special handling for extpub - check if the data might be in a different format
    if source == 'extpub':
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"extpub: Raw links data: '{links_data}'")
            logger.debug(f"extpub: Data type: {type(links_data)}")
            logger.debug(f"extpub: Data length: {len(links_data)}")
            logger.debug(f"extpub: Starts with bracket: {links_data.startswith('[') if links_data else False}")
            logger.debug(f"extpub: Starts with brace: {links_data.startswith('{') if links_data else False}")
        
        # Check if extpub has a different link format
        if links_data.strip() == '' or links_data.strip().lower() in ['null', 'none', 'nan']:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"extpub: Links field is empty or null")
            return []
        
        # Check if extpub has plain text URLs instead of JSON
        if not (links_data.startswith('[') or links_data.startswith('{')):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"extpub: Links data doesn't look like JSON, trying plain text extraction")
            # Try to extract URLs from plain text
            import re
            url_pattern = r'https?://[^\s,;\[\]{}"\']+'
            urls = re.findall(url_pattern, links_data)
            
            if urls:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"extpub: Found {len(urls)} URLs in plain text: {urls}")
                formatted_links = []
                for url in urls:
                    link_text = _get_link_text(url, {}, source)
                    formatted_links.append(
                        html.A(
                            link_text, 
                            href=url, 
                            target="_blank",
                            style={
                                'color': '#87CEEB', 
                                'text-decoration': 'none',
                                'background-color': 'rgba(135, 206, 235, 0.1)',
                                'padding': '6px 12px',
                                'border-radius': '4px',
                                'border': '1px solid rgba(135, 206, 235, 0.3)',
                                'font-size': '12px',
                                'font-weight': '500',
                                'margin-right': '8px'
                            }
                        )
                    )
                return formatted_links
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"extpub: No URLs found in plain text data")
                # Try alternative patterns for extpub
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"extpub: Trying alternative URL patterns...")
                
                # Check for URLs with different separators
                alt_patterns = [
                    r'https?://[^\s,;]+',  # Less restrictive
                    r'https?://[^\s]+',    # Very permissive
                    r'http[^\s]+',         # Catch http without s
                ]
                
                for pattern in alt_patterns:
                    urls = re.findall(pattern, links_data)
                    if urls:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"extpub: Found {len(urls)} URLs with pattern '{pattern}': {urls}")
                        formatted_links = []
                        for url in urls:
                            link_text = _get_link_text(url, {}, source)
                            formatted_links.append(
                                html.A(
                                    link_text, 
                                    href=url, 
                                    target="_blank",
                                    style={
                                        'color': '#87CEEB', 
                                        'text-decoration': 'none',
                                        'background-color': 'rgba(135, 206, 235, 0.1)',
                                        'padding': '6px 12px',
                                        'border-radius': '4px',
                                        'border': '1px solid rgba(135, 206, 235, 0.3)',
                                        'font-size': '12px',
                                        'font-weight': '500',
                                        'margin-right': '8px'
                                    }
                                )
                            )
                        return formatted_links
                
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"extpub: No URLs found with any pattern")
    
    formatted_links = []
    
    try:
        # Try to parse as JSON first (this is the expected format)
        import json
        try:
            parsed = json.loads(links_data)
            
            if isinstance(parsed, list):
                # Handle array of link objects
                for link_obj in parsed:
                    if isinstance(link_obj, dict) and 'href' in link_obj:
                        href = link_obj['href']
                        if href and isinstance(href, str) and href.startswith('http'):
                            # Determine link text based on URL and metadata
                            link_text = _get_link_text(href, link_obj, source)
                            
                            formatted_links.append(
                                html.A(
                                    link_text, 
                                    href=href, 
                                    target="_blank",
                                    style={
                                        'color': '#87CEEB', 
                                        'text-decoration': 'none',
                                        'background-color': 'rgba(135, 206, 235, 0.1)',
                                        'padding': '6px 12px',
                                        'border-radius': '4px',
                                        'border': '1px solid rgba(135, 206, 235, 0.3)',
                                        'font-size': '12px',
                                        'font-weight': '500',
                                        'margin-right': '8px'
                                    }
                                )
                            )
            
            elif isinstance(parsed, dict):
                # Handle single link object or extpub-style object with descriptive keys
                if 'href' in parsed:
                    # Standard link object format
                    href = parsed['href']
                    if href and isinstance(href, str) and href.startswith('http'):
                        link_text = _get_link_text(href, parsed, source)
                        
                        formatted_links.append(
                            html.A(
                                link_text, 
                                href=href, 
                                target="_blank",
                                style={
                                    'color': '#87CEEB', 
                                    'text-decoration': 'none',
                                    'background-color': 'rgba(135, 206, 235, 0.1)',
                                    'padding': '6px 12px',
                                    'border-radius': '4px',
                                    'border': '1px solid rgba(135, 206, 235, 0.3)',
                                    'font-size': '12px',
                                    'font-weight': '500',
                                    'margin-right': '8px'
                                }
                            )
                        )
                else:
                    # extpub-style format: {"RAND Publication": "url", "Publication URL": "url"}
                    for key, value in parsed.items():
                        if isinstance(value, str) and value.startswith('http'):
                            # Use the key as the link text, but clean it up
                            link_text = _clean_extpub_link_text(key, value, source)
                            
                            formatted_links.append(
                                html.A(
                                    link_text, 
                                    href=value, 
                                    target="_blank",
                                    style={
                                        'color': '#87CEEB', 
                                        'text-decoration': 'none',
                                        'background-color': 'rgba(135, 206, 235, 0.1)',
                                        'padding': '6px 12px',
                                        'border-radius': '4px',
                                        'border': '1px solid rgba(135, 206, 235, 0.3)',
                                        'font-size': '12px',
                                        'font-weight': '500',
                                        'margin-right': '8px'
                                    }
                                )
                            )
        
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract URLs as fallback
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"JSON parsing failed for {source}, trying regex fallback")
            import re
            url_pattern = r'https?://[^\s,;\[\]{}"\']+'
            urls = re.findall(url_pattern, links_data)
            
            for url in urls:
                link_text = _get_link_text(url, {}, source)
                formatted_links.append(
                    html.A(
                        link_text, 
                        href=url, 
                        target="_blank",
                        style={
                            'color': '#87CEEB', 
                            'text-decoration': 'none',
                            'background-color': 'rgba(135, 206, 235, 0.1)',
                            'padding': '6px 12px',
                            'border-radius': '4px',
                            'border': '1px solid rgba(135, 206, 235, 0.3)',
                            'font-size': '12px',
                            'font-weight': '500',
                            'margin-right': '8px'
                        }
                    )
                )
    
    except Exception as e:
        logger.error(f"Error formatting links for source '{source}': {e}")
    
    # Log the results (only if debug enabled)
    if logger.isEnabledFor(logging.DEBUG):
        if formatted_links:
            logger.debug(f"Successfully extracted {len(formatted_links)} links for {source}")
        else:
            logger.debug(f"No links extracted for {source} from data: {links_data[:100]}...")
    
    return formatted_links


def _get_link_text(url: str, link_obj: Dict[str, Any], source: str) -> str:
    """
    Determine appropriate text for a link based on URL and metadata.
    
    Args:
        url: The URL
        link_obj: The link object from JSON (may contain 'rel', 'type', etc.)
        source: Data source
        
    Returns:
        Appropriate text for the link
    """
    # Check for specific URL patterns first
    if 'arxiv.org' in url:
        return "ArXiv"
    elif 'doi.org' in url:
        return "DOI"
    elif 'rand.org' in url:
        return "RAND"
    elif 'pdf' in url.lower():
        return "PDF"
    elif 'html' in url.lower():
        return "HTML"
    elif 'researchgate.net' in url:
        return "ResearchGate"
    elif 'academia.edu' in url:
        return "Academia.edu"
    elif 'scholar.google.com' in url:
        return "Google Scholar"
    elif 'semanticscholar.org' in url:
        return "Semantic Scholar"
    elif 'ieee.org' in url:
        return "IEEE"
    elif 'acm.org' in url:
        return "ACM"
    elif 'springer.com' in url:
        return "Springer"
    elif 'sciencedirect.com' in url:
        return "ScienceDirect"
    elif 'wiley.com' in url:
        return "Wiley"
    elif 'tandfonline.com' in url:
        return "Taylor & Francis"
    elif 'sagepub.com' in url:
        return "SAGE"
    elif 'jstor.org' in url:
        return "JSTOR"
    elif 'pubmed.ncbi.nlm.nih.gov' in url:
        return "PubMed"
    elif 'ncbi.nlm.nih.gov' in url:
        return "NCBI"
    
    # Check link object metadata
    rel = link_obj.get('rel', '').lower()
    link_type = link_obj.get('type', '').lower()
    
    if rel == 'alternate':
        if 'pdf' in link_type:
            return "PDF"
        elif 'html' in link_type:
            return "HTML"
        else:
            return "Alternative"
    elif rel == 'canonical':
        return "Canonical"
    elif rel == 'related':
        return "Related"
    
    # Source-specific defaults with more intelligent handling
    if source == 'openalex':
        return "OpenAlex"
    elif source == 'aipickle':
        return "AI Pickle"
    elif source == 'randpub':
        return "RAND"
    elif source == 'extpub':
        # For extpub, try to be more specific based on the URL
        if any(domain in url.lower() for domain in ['researchgate', 'academia', 'scholar', 'semantic']):
            return "Academic"
        elif any(domain in url.lower() for domain in ['ieee', 'acm', 'springer', 'wiley', 'sage', 'jstor']):
            return "Publisher"
        elif any(domain in url.lower() for domain in ['pubmed', 'ncbi', 'nih']):
            return "Medical"
        else:
            return "External"
    
    # Generic fallback
    return "Link"


def _clean_extpub_link_text(key: str, value: str, source: str) -> str:
    """
    Clean up the text for extpub-style links to make it more readable.
    
    Args:
        key: The descriptive key from the JSON (e.g., "RAND Publication", "Publication URL")
        value: The actual URL value
        source: Data source
        
    Returns:
        Cleaned link text
    """
    # Clean up common extpub link text patterns
    key_lower = key.lower()
    
    if "rand" in key_lower:
        return "RAND"
    elif "doi" in key_lower or "publication url" in key_lower:
        return "DOI"
    elif "external" in key_lower:
        return "External"
    elif "research" in key_lower:
        return "Research"
    elif "academic" in key_lower:
        return "Academic"
    elif "pdf" in key_lower:
        return "PDF"
    elif "html" in key_lower:
        return "HTML"
    elif "full text" in key_lower or "fulltext" in key_lower:
        return "Full Text"
    elif "abstract" in key_lower:
        return "Abstract"
    elif "supplement" in key_lower or "supplementary" in key_lower:
        return "Supplement"
    else:
        # For other cases, try to clean up the key text
        # Remove common prefixes and make it more readable
        cleaned = key.replace("_", " ").replace("-", " ")
        # Capitalize first letter of each word
        cleaned = " ".join(word.capitalize() for word in cleaned.split())
        return cleaned


def create_paper_metadata_display(metadata: PaperMetadata) -> Any:
    """Create formatted paper metadata display."""
    try:
        # Import Dash html components
        from dash import html
        
        # Debug logging for extpub papers (only if debug enabled)
        if metadata.source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"extpub paper metadata: title='{metadata.title[:50]}...', links='{metadata.links[:100]}...'")
        
        # Format data for display
        authors_text = format_authors(metadata.authors)
        formatted_date = format_date(metadata.date)
        # similarity_text = format_similarity_score(metadata.similarity_score)  # Removed - not needed
        doi_link = create_doi_link(metadata.doi)
        
        # Build display children
        children = [
            html.H4(
                metadata.title, 
                style={'font-weight': 'bold', 'color': '#ffffff', 'font-size': '20px'}
            ),
            html.P(
                f"Authors: {authors_text}", 
                style={'color': '#ffffff', 'margin-top': '5px'}
            ),
            html.P(
                formatted_date, 
                style={'color': '#ffffff', 'margin-top': '5px'}
            ),
            html.P(
                f"Source: {metadata.source}", 
                style={'color': '#ffffff', 'margin-top': '5px'}
            ),
            html.P(
                metadata.summary, 
                style={'margin-top': '10px', 'color': '#ffffff'}
            )
        ]
        
        # Add links if available
        if metadata.links and metadata.links.strip():
            if metadata.source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"extpub: About to extract links from: '{metadata.links[:100]}...'")
            
            formatted_links = extract_and_format_links(metadata.links, metadata.source)
            
            if metadata.source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"extpub: Link extraction returned {len(formatted_links)} formatted links")
            
            if formatted_links:
                # Enhanced link display with better organization
                children.append(
                    html.Div([
                        html.H6("Links", style={
                            'color': '#ffffff', 
                            'margin-top': '15px', 
                            'margin-bottom': '8px',
                            'font-size': '14px',
                            'font-weight': 'bold',
                            'border-bottom': '1px solid rgba(255, 255, 255, 0.3)',
                            'padding-bottom': '4px'
                        }),
                        html.Div(
                            formatted_links,
                            style={
                                'display': 'flex',
                                'flex-wrap': 'wrap',
                                'gap': '8px',
                                'margin-top': '8px'
                            }
                        )
                    ], style={'margin-top': '10px'})
                )
            else:
                # Fallback: show raw links if formatting failed
                if metadata.source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"extpub: Link formatting failed, showing raw text: '{metadata.links[:100]}...'")
                
                children.append(
                    html.Div([
                        html.H6("Links", style={
                            'color': '#ffffff', 
                            'margin-top': '15px', 
                            'margin-bottom': '8px',
                            'font-size': '14px',
                            'font-weight': 'bold',
                            'border-bottom': '1px solid rgba(255, 255, 255, 0.3)',
                            'padding-bottom': '4px'
                        }),
                        html.P(
                            "Raw link data available", 
                            style={
                                'color': '#cccccc', 
                                'margin-top': '8px',
                                'font-style': 'italic',
                                'font-size': '12px'
                            }
                        )
                    ], style={'margin-top': '10px'})
                )
        else:
            if metadata.source == 'extpub' and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"extpub: No links data available (empty or None)")
        
        # Add similarity score if available - REMOVED (not needed)
        # if similarity_text:
        #     children.append(
        #         html.P(
        #             similarity_text, 
        #             style={'color': '#ffffff', 'margin-top': '5px'}
        #         )
        #     )
        
        # Add DOI link if available
        if doi_link:
            children.append(
                html.Div(
                    doi_link,
                    style={'margin-top': '5px'}
                )
            )
        
        return html.Div(
            style={
                'padding': '10px',
                'background-color': 'rgba(0, 31, 63, 0.85)',
                'color': '#ffffff',
                'border-radius': '5px'
            },
            children=children
        )
        
    except ImportError:
        logger.error("Dash html components not available for metadata display")
        return f"Error: Cannot display metadata - Dash components unavailable"


def create_default_display() -> Any:
    """Create default display when no paper is selected."""
    try:
        from dash import html
        
        return html.Div(
            "Click on a point to see paper details.",
            style={
                'padding': '10px', 
                'background-color': '#e6f3ff', 
                'border': '2px solid blue'
            }
        )
    except ImportError:
        return "Click on a point to see paper details."


def create_error_display(error_message: str) -> Any:
    """Create error display for invalid selections."""
    try:
        from dash import html
        
        return html.Div(
            error_message,
            style={
                'padding': '10px',
                'background-color': '#ffebee',
                'border': '2px solid #f44336',
                'color': '#c62828'
            }
        )
    except ImportError:
        return f"Error: {error_message}"
