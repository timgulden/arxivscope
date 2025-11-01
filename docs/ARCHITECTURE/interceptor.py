"""
the interceptor library
"""

import logging
import traceback
from functools import reduce
from collections import deque, namedtuple

Interceptor = namedtuple('Interceptor', ['enter', 'leave', 'error'],
                         defaults=(None, None, None))

logger = logging.getLogger(__name__)


def caged(func, ctx):
    """
    call f, adding any exceptions to the context
    """
    try:
        if func:
            logger.debug('calling caged function')
            newctx = func(ctx)
        else:
            logger.debug('no function found, context unchanged')
            newctx = ctx
    except Exception as exc:
        logger.debug('caged exception caught and added')
        logger.debug(traceback.format_exc())
        ctx['error'] = exc
    else:
        ctx = newctx
    return ctx


def leave(ctx):
    """
    execute previous 'leave' in queue
    """
    stack = ctx.get('stack', [])
    if len(stack) > 0:
        logger.debug('popping stack')
        newctx = ctx
        newctx['stack'] = stack
        if 'error' in ctx:
            logger.debug('error found in context')
            handler = stack[-1].error
        else:
            logger.debug('caging leave handler')
            handler = stack[-1].leave
        logger.debug('popping stack and recursing')
        stack.pop()
        return leave(caged(handler, newctx))
    logger.debug('empty stack')
    return ctx


def enter(ctx):
    """
    execute next 'enter' member in queue
    """
    queue = ctx['queue']
    stack = ctx['stack']
    if len(queue) == 0:
        logger.debug('found empty queue')
        interceptor = None
    else:
        logger.debug('peeking at queue')
        interceptor = queue[0]

    if (not interceptor) or ctx.get('error'):
        logger.debug('leaving enter due to empty queue or error')

        # ctx ['stack'].pop ()
        return ctx
    logger.debug('pushing to stack and recursing')

    newctx = ctx
    queue.popleft()
    newctx['queue'] = queue
    stack.append(interceptor)
    newctx['stack'] = stack
    ctx = newctx
    return enter(caged(interceptor.enter, ctx))


def result(ctx):
    """
    raise error or return response
    """
    logger.debug('starting result')
    if 'error' in ctx:
        logger.debug('found error, raising')
        raise ctx['error']
    logger.debug('no errors found, returning response')
    return ctx['response']


def execute(interceptors, *args, **kwargs):
    """
    execute a list of interceptors with an initial context
    """
    message = f'start interceptor execution {str(interceptors)}'
    logger.debug(message)
    request = kwargs.get('request', None)
    queue = deque(interceptors)
    stack = []
    ctx = {'request': request,
           'queue': queue,
           'stack': stack,
           'response': {}}

    logger.debug('start reduction')
    return (reduce(lambda x, f: f(x), [ctx,
                                  enter,
                                  leave,
                                  result]))
