[**@docscope/logic**](../../../README.md)

***

[@docscope/logic](../../../README.md) / [logic/viewManagement](../README.md) / extractViewFromRelayoutPure

# Function: extractViewFromRelayoutPure()

> **extractViewFromRelayoutPure**(`relayout`, `currentTime`): `null` \| [`ViewState`](../type-aliases/ViewState.md)

Defined in: src/logic/viewManagement.ts:77

Extract a ViewState from a chart relayout payload (e.g., Plotly).

Supports both separate key form and array form for axis ranges.

## Parameters

### relayout

`Record`\<`string`, `any`\>

### currentTime

`number`

## Returns

`null` \| [`ViewState`](../type-aliases/ViewState.md)
