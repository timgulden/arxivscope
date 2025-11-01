[**@docscope/logic**](../../../README.md)

***

[@docscope/logic](../../../README.md) / [logic/viewManagement](../README.md) / isViewStable

# Function: isViewStable()

> **isViewStable**(`currentView`, `previousView`, `stabilityThreshold`): `boolean`

Defined in: src/logic/viewManagement.ts:154

Determine if two views are effectively the same (debounce jitter).

## Parameters

### currentView

[`ViewState`](../type-aliases/ViewState.md)

### previousView

[`ViewState`](../type-aliases/ViewState.md)

### stabilityThreshold

`number` = `0.001`

## Returns

`boolean`
