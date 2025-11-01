/**
 * React Hook for Application State Management
 * 
 * Connects UI to the single source of truth in the logic layer.
 * Following STATE_MANAGEMENT_STRATEGY.md patterns.
 */

import { useReducer } from 'react';
import { createInitialState, stateReducer } from '../logic/core/state-store';
import type { ApplicationState } from '../logic/core/types';
import type { StateAction } from '../logic/core/types';

/**
 * Main application state hook
 * Provides state and dispatch function to UI components
 */
export function useAppState(): [ApplicationState, (action: StateAction) => void] {
  const [state, dispatch] = useReducer(stateReducer, createInitialState());

  return [state, dispatch];
}

