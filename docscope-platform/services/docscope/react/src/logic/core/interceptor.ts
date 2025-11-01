/**
 * Interceptor Framework for DocScope React Frontend
 * 
 * Following interceptor101.md strictly:
 * - An interceptor is a data structure with 0-3 functions: enter, leave, error
 * - All functions have the same signature: (context) => context
 * - More interceptors are preferred to larger interceptors
 * - No error handling in interceptors (handled by stack executor)
 */

import type { InterceptorContext } from './types';

/**
 * Interceptor data structure following our established pattern.
 * An interceptor has 0-3 functions: enter, leave, error
 * All functions have the same signature: (context) => context
 */
export interface Interceptor {
  enter?: (context: InterceptorContext) => InterceptorContext;
  leave?: (context: InterceptorContext) => InterceptorContext;
  error?: (context: InterceptorContext) => InterceptorContext;
}

/**
 * Execute a stack of interceptors following the established pattern:
 * 1. Call enter functions (left to right)
 * 2. Call leave functions (right to left)
 * 3. On error, call error function of the failing interceptor
 */
export function executeInterceptorStack(
  interceptors: Interceptor[],
  initialContext: InterceptorContext
): InterceptorContext {
  let context = initialContext;
  const executedInterceptors: Interceptor[] = [];

  try {
    // Execute enter functions (left to right)
    for (const interceptor of interceptors) {
      executedInterceptors.push(interceptor);
      if (interceptor.enter) {
        context = interceptor.enter(context);
      }
    }

    // Execute leave functions (right to left)
    for (const interceptor of executedInterceptors.reverse()) {
      if (interceptor.leave) {
        context = interceptor.leave(context);
      }
    }

    return context;
  } catch (error) {
    // Find the interceptor that caused the error
    const errorIndex = executedInterceptors.length - 1;
    const errorInterceptor = executedInterceptors[errorIndex];

    // Add error to context
    context.error = error instanceof Error ? error.message : String(error);

    // Call error function if it exists
    if (errorInterceptor?.error) {
      context = errorInterceptor.error(context);
      // Clear error if handled
      if (context.error) {
        delete context.error;
      }
    }

    // Execute leave functions for interceptors that were entered
    for (let i = errorIndex - 1; i >= 0; i--) {
      const interceptor = executedInterceptors[i];
      if (interceptor.leave) {
        context = interceptor.leave(context);
      }
    }

    return context;
  }
}

