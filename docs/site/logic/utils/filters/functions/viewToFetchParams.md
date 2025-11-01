[**@docscope/logic**](../../../README.md)

***

[@docscope/logic](../../../README.md) / [utils/filters](../README.md) / viewToFetchParams

# Function: viewToFetchParams()

> **viewToFetchParams**(`view`, `filters`, `opts?`): `null` \| [`FetchParams`](../type-aliases/FetchParams.md)

Defined in: src/utils/filters.ts:38

Compose API params from view + filters without caching.

## Parameters

### view

#### bbox

`null` \| `string`

### filters

`undefined` | `null` | [`Filters`](../type-aliases/Filters.md)

### opts?

#### defaultSort?

`string`

#### fields?

`string`

#### limit?

`number`

## Returns

`null` \| [`FetchParams`](../type-aliases/FetchParams.md)
