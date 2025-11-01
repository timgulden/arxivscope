/**
 * Metadata Sidebar Component for DocScope React Frontend
 * 
 * Displays paper details when a paper is clicked on the canvas.
 * Following Dash paper_metadata_service.py pattern.
 */

import { useEffect } from 'react';
import axios from 'axios';
import type { ApplicationState, StateAction } from '../logic/core/types';

interface MetadataSidebarProps {
  state: ApplicationState;
  dispatch: (action: StateAction) => void;
}

// TODO: Add PaperDetail interface when needed for API response type

const API_BASE_URL = 'http://localhost:5001/api';

/**
 * Metadata Sidebar Component
 * Displays paper details when selectedPaperId is set in state
 */
export function MetadataSidebar({ state, dispatch }: MetadataSidebarProps) {
  const selectedPaperId = state.ui.selectedPaperId;

  // Fetch paper details when a paper is selected
  useEffect(() => {
    if (!selectedPaperId) return;

    const fetchPaperDetails = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/papers/${selectedPaperId}`);
        const paperData = response.data;
        
        // TODO: Store full paper details in state for display
        console.log('Fetched paper details:', paperData);
      } catch (error) {
        console.error('Error fetching paper details:', error);
      }
    };

    fetchPaperDetails();
  }, [selectedPaperId]);

  // If no paper selected, show default message
  if (!selectedPaperId) {
    return (
      <div style={{
        width: '380px',
        backgroundColor: '#ffffff',
        color: '#000000',
        height: '100%',
        overflowY: 'auto',
        padding: 0,
        fontSize: '14px',
        position: 'relative',
      }}>
        <div style={{ padding: '20px' }}>
          <p>Click on a paper to view details</p>
        </div>
      </div>
    );
  }

  // Find the selected paper in the current data
  const selectedPaper = state.data.papers.find(p => p.doctrove_paper_id === selectedPaperId);

  if (!selectedPaper) {
    return (
      <div style={{
        width: '380px',
        backgroundColor: '#ffffff',
        color: '#000000',
        height: '100%',
        overflowY: 'auto',
        padding: 0,
        fontSize: '14px',
        position: 'relative',
      }}>
        <div style={{ padding: '20px' }}>
          <p>Loading paper details...</p>
        </div>
      </div>
    );
  }

  // Format authors (handle array or string)
  const formatAuthors = (authors: string | string[] | undefined): string => {
    if (!authors) return 'Unknown';
    if (Array.isArray(authors)) {
      return authors.join(', ');
    }
    return authors;
  };

  // Format date
  const formatDate = (dateStr: string): string => {
    if (!dateStr) return 'Unknown';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  // Parse and format links
  const formatLinks = (linksData: any): any[] => {
    if (!linksData) return [];
    
    try {
      const parsed = typeof linksData === 'string' ? JSON.parse(linksData) : linksData;
      const links: any[] = [];
      
      if (Array.isArray(parsed)) {
        parsed.forEach(link => {
          if (link.href && link.href.startsWith('http')) {
            links.push({
              text: link.title || link.rel || getLinkText(link.href),
              href: link.href,
            });
          }
        });
      }
      
      return links;
    } catch {
      return [];
    }
  };

  // Determine link text from URL
  const getLinkText = (url: string): string => {
    if (url.includes('arxiv.org')) return 'arXiv';
    if (url.includes('doi.org') || url.includes('dx.doi.org')) return 'DOI';
    if (url.includes('.pdf')) return 'PDF';
    if (url.includes('rand.org')) return 'RAND';
    return 'Link';
  };

  const links = formatLinks(selectedPaper.doctrove_links);

  return (
      <div style={{
        width: '380px',
      backgroundColor: '#ffffff',
      color: '#000000',
      height: '100%',
      overflowY: 'auto',
      padding: 0,
      fontSize: '14px',
      position: 'relative',
    }}>
      <button 
        onClick={() => dispatch({ type: 'UI_SELECT_PAPER', payload: null })}
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          background: 'none',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          color: '#666',
          zIndex: 10,
          width: '30px',
          height: '30px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        ×
      </button>

      {/* Content wrapper with padding */}
      <div style={{ padding: '20px' }}>
        <h3 style={{
          fontWeight: 'bold',
          fontSize: '18px',
          marginBottom: '20px',
          paddingRight: '30px',
        }}>
          {selectedPaper.doctrove_title}
        </h3>

        <div style={{ marginBottom: '5px' }}>
          <strong>Authors:</strong> {formatAuthors(selectedPaper.doctrove_authors)}
        </div>

        <div style={{ marginBottom: '5px' }}>
          <strong>Date:</strong> {formatDate(selectedPaper.doctrove_primary_date)}
        </div>

        <div style={{ marginBottom: '5px' }}>
          <strong>Source:</strong> {selectedPaper.doctrove_source}
        </div>

        {/* Abstract - no label */}
        {selectedPaper.doctrove_abstract && (
          <div style={{ marginTop: '10px', marginBottom: '10px' }}>
            <p style={{ marginTop: 0, lineHeight: '1.6' }}>
              {selectedPaper.doctrove_abstract}
            </p>
          </div>
        )}

        {/* Links as buttons */}
        {links.length > 0 && (
          <div style={{ marginTop: '10px' }}>
            <strong>Links:</strong>
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '8px', 
              marginTop: '10px' 
            }}>
              {links.map((link, idx) => (
                <a
                  key={idx}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#87CEEB',
                    textDecoration: 'none',
                    backgroundColor: 'rgba(135, 206, 235, 0.1)',
                    padding: '6px 12px',
                    borderRadius: '4px',
                    border: '1px solid rgba(135, 206, 235, 0.3)',
                    fontSize: '12px',
                    fontWeight: '500',
                  }}
                >
                  {link.text}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>{/* Close content wrapper */}
    </div>
  );
}

