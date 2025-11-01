import { describe, it, expect } from 'vitest';
import { executeInterceptorStack, type Interceptor } from '../interceptor';
import type { InterceptorContext } from '../types';

describe('Interceptor Stack Execution', () => {
  describe('executeInterceptorStack', () => {
    it('should execute enter functions left to right', () => {
      const callOrder: string[] = [];
      const interceptors: Interceptor[] = [
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('I1.enter');
            return ctx;
          },
        },
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('I2.enter');
            return ctx;
          },
        },
      ];

      executeInterceptorStack(interceptors, {});

      expect(callOrder).toEqual(['I1.enter', 'I2.enter']);
    });

    it('should execute leave functions right to left', () => {
      const callOrder: string[] = [];
      const interceptors: Interceptor[] = [
        {
          enter: () => ({}),
          leave: (ctx: InterceptorContext) => {
            callOrder.push('I1.leave');
            return ctx;
          },
        },
        {
          enter: () => ({}),
          leave: (ctx: InterceptorContext) => {
            callOrder.push('I2.leave');
            return ctx;
          },
        },
      ];

      executeInterceptorStack(interceptors, {});

      expect(callOrder).toEqual(['I2.leave', 'I1.leave']);
    });

    it('should handle interceptors without leave functions', () => {
      const callOrder: string[] = [];
      const interceptors: Interceptor[] = [
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('I1.enter');
            return ctx;
          },
          // No leave function
        },
        {
          enter: () => ({}),
          leave: (ctx: InterceptorContext) => {
            callOrder.push('I2.leave');
            return ctx;
          },
        },
      ];

      executeInterceptorStack(interceptors, {});

      expect(callOrder).toEqual(['I1.enter', 'I2.leave']);
    });

    it('should transform context through interceptors', () => {
      const interceptors: Interceptor[] = [
        {
          enter: (ctx: InterceptorContext) => {
            ctx.step1 = 'done';
            return ctx;
          },
        },
        {
          enter: (ctx: InterceptorContext) => {
            ctx.step2 = 'done';
            return ctx;
          },
        },
      ];

      const result = executeInterceptorStack(interceptors, { initial: 'value' });

      expect(result.step1).toBe('done');
      expect(result.step2).toBe('done');
      expect(result.initial).toBe('value');
    });

    it('should call error function on exception', () => {
      const errorHandler = (ctx: InterceptorContext) => {
        // Clear error
        if (ctx.error) {
          delete ctx.error;
        }
        return ctx;
      };

      const interceptors: Interceptor[] = [
        {
          enter: () => {
            throw new Error('Test error');
          },
          error: errorHandler,
        },
      ];

      const result = executeInterceptorStack(interceptors, {});

      // Error should be cleared if handler called
      expect(result.error).toBeUndefined();
    });

    it('should execute leave functions for all entered interceptors on error', () => {
      const callOrder: string[] = [];
      const interceptors: Interceptor[] = [
        {
          enter: () => ({}),
          leave: (ctx: InterceptorContext) => {
            callOrder.push('I1.leave');
            return ctx;
          },
        },
        {
          enter: () => {
            throw new Error('Test error');
          },
          error: (ctx: InterceptorContext) => {
            callOrder.push('I2.error');
            if (ctx.error) {
              delete ctx.error;
            }
            return ctx;
          },
        },
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('I3.enter'); // Should not be called
            return ctx;
          },
        },
      ];

      executeInterceptorStack(interceptors, {});

      // I3.enter should not be called (error before it)
      expect(callOrder).toEqual(['I2.error', 'I1.leave']);
    });

    it('should handle empty interceptor array', () => {
      const result = executeInterceptorStack([], { test: 'value' });

      expect(result.test).toBe('value');
    });

    it('should handle interceptors with no functions', () => {
      const interceptors: Interceptor[] = [{}, {}, {}];

      const result = executeInterceptorStack(interceptors, { test: 'value' });

      expect(result.test).toBe('value');
    });

    it('should handle complex interceptor chains', () => {
      const callOrder: string[] = [];
      const interceptors: Interceptor[] = [
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('A.enter');
            ctx.a = 'A';
            return ctx;
          },
          leave: (ctx: InterceptorContext) => {
            callOrder.push('A.leave');
            ctx.a = ctx.a + 'L';
            return ctx;
          },
        },
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('B.enter');
            ctx.b = 'B';
            return ctx;
          },
          leave: (ctx: InterceptorContext) => {
            callOrder.push('B.leave');
            ctx.b = ctx.b + 'L';
            return ctx;
          },
        },
        {
          enter: (ctx: InterceptorContext) => {
            callOrder.push('C.enter');
            ctx.c = 'C';
            return ctx;
          },
          leave: (ctx: InterceptorContext) => {
            callOrder.push('C.leave');
            ctx.c = ctx.c + 'L';
            return ctx;
          },
        },
      ];

      const result = executeInterceptorStack(interceptors, {});

      expect(callOrder).toEqual([
        'A.enter',
        'B.enter',
        'C.enter',
        'C.leave',
        'B.leave',
        'A.leave',
      ]);
      expect(result.a).toBe('AL');
      expect(result.b).toBe('BL');
      expect(result.c).toBe('CL');
    });
  });
});

