/**
 * Date Slider Component for DocScope React Frontend
 * 
 * Displays date range slider at the bottom of the screen.
 * For arXiv papers with full daily precision.
 * Custom dual-handle range slider implementation.
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import type { ApplicationState, StateAction } from '../logic/core/types';

interface DateSliderProps {
  state: ApplicationState;
  dispatch: (action: StateAction) => void;
  onDateChange?: (yearRange: [number, number]) => void;
}

/**
 * Date Slider Component
 * Bottom bar with dual-handle date range slider
 */
export function DateSlider({ state, dispatch, onDateChange }: DateSliderProps) {
  const yearRange = state.filter.yearRange || [2000, 2025];
  
  const minYear = 1950;
  const maxYear = 2030;
  
  const [isDragging, setIsDragging] = useState<'min' | 'max' | null>(null);
  const sliderRef = useRef<HTMLDivElement>(null);
  
  // Debounce ref for date changes
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Calculate positions as percentages
  const minPercent = ((yearRange[0] - minYear) / (maxYear - minYear)) * 100;
  const maxPercent = ((yearRange[1] - minYear) / (maxYear - minYear)) * 100;

  // Handle mouse events
  const handleMouseDown = (handle: 'min' | 'max') => {
    setIsDragging(handle);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !sliderRef.current) return;

    const rect = sliderRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const newValue = minYear + x * (maxYear - minYear); // Continuous, no rounding

    let newRange: [number, number] = [yearRange[0], yearRange[1]];
    
    if (isDragging === 'min') {
      newRange = [Math.min(newValue, yearRange[1]), yearRange[1]];
    } else {
      newRange = [yearRange[0], Math.max(newValue, yearRange[0])];
    }

    // Update state immediately
    dispatch({ 
      type: 'FILTER_UPDATE', 
      payload: { ...state.filter, yearRange: newRange, lastUpdate: Date.now() }
    });

    // Debounce the fetch
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    debounceTimeoutRef.current = setTimeout(() => {
      if (onDateChange) {
        onDateChange(newRange);
      }
    }, 500);
  }, [isDragging, yearRange, state.filter, dispatch, onDateChange, minYear, maxYear]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Generate marks for every 5 years
  const marks: { year: number; position: number }[] = [];
  for (let year = minYear; year <= maxYear; year += 5) {
    marks.push({
      year,
      position: ((year - minYear) / (maxYear - minYear)) * 100
    });
  }
  
  // Format date for display (mm/dd/yyyy - US format)
  const formatDate = (year: number): string => {
    // Convert fractional year to date
    const fullYear = Math.floor(year);
    const fraction = year - fullYear;
    const daysInYear = isLeapYear(fullYear) ? 366 : 365;
    const dayOfYear = Math.floor(fraction * daysInYear);
    const date = new Date(fullYear, 0, 1);
    date.setDate(date.getDate() + dayOfYear);
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const yearStr = date.getFullYear();
    return `${month}/${day}/${yearStr}`;
  };

  // Helper to check leap year
  const isLeapYear = (year: number): boolean => {
    return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
  };

  return (
    <div style={{
      height: '60px',
      backgroundColor: '#2c3e50',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'flex-start',
      alignItems: 'center',
      padding: '5px 20px 10px 20px',
      borderTop: '2px solid #34495e',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '1200px',
      }}>
        <div style={{
          color: 'white',
          fontSize: '14px',
          fontWeight: 'bold',
          marginBottom: '3px',
          textAlign: 'left',
          userSelect: 'none',
        }}>
          Publication Date Range: {formatDate(yearRange[0])} - {formatDate(yearRange[1])}
        </div>
        
        {/* Custom range slider */}
        <div
          ref={sliderRef}
          style={{
            position: 'relative',
            height: '35px',
            marginTop: 0,
          }}
        >
          {/* Track background */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: 0,
            right: 0,
            height: '4px',
            backgroundColor: '#7f8c8d',
            borderRadius: '2px',
            transform: 'translateY(-50%)',
          }} />
          
          {/* Active range */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: `${minPercent}%`,
            right: `${100 - maxPercent}%`,
            height: '4px',
            backgroundColor: '#4CAF50',
            borderRadius: '2px',
            transform: 'translateY(-50%)',
          }} />
          
          {/* Tick marks and labels */}
          {marks.map(mark => (
            <div
              key={mark.year}
              style={{
                position: 'absolute',
                left: `${mark.position}%`,
                top: '50%',
                transform: 'translate(-50%, -50%)',
              }}
            >
              <div style={{
                width: '2px',
                height: '8px',
                backgroundColor: '#95a5a6',
              }} />
              <div style={{
                position: 'absolute',
                top: '15px',
                left: '50%',
                transform: 'translateX(-50%)',
                color: '#95a5a6',
                fontSize: '10px',
                whiteSpace: 'nowrap',
                userSelect: 'none',
                pointerEvents: 'none',
              }}>
                {mark.year}
              </div>
            </div>
          ))}
          
          {/* Min handle */}
          <div
            onMouseDown={() => handleMouseDown('min')}
            style={{
              position: 'absolute',
              left: `${minPercent}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#4CAF50',
              border: '2px solid white',
              cursor: 'grab',
              boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-25px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#000',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
              userSelect: 'none',
              pointerEvents: 'none',
            }}>
              {formatDate(yearRange[0])}
            </div>
          </div>
          
          {/* Max handle */}
          <div
            onMouseDown={() => handleMouseDown('max')}
            style={{
              position: 'absolute',
              left: `${maxPercent}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#4CAF50',
              border: '2px solid white',
              cursor: 'grab',
              boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-25px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#000',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
              userSelect: 'none',
              pointerEvents: 'none',
            }}>
              {formatDate(yearRange[1])}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
