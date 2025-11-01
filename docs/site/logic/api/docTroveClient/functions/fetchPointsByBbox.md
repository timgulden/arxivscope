[**@docscope/logic**](../../../README.md)

***

[@docscope/logic](../../../README.md) / [api/docTroveClient](../README.md) / fetchPointsByBbox

# Function: fetchPointsByBbox()

> **fetchPointsByBbox**(`params`): `Promise`\<\{ `points`: [`Point`](../../docTroveSchemas/type-aliases/Point.md)[]; `total?`: `number`; \}\>

Defined in: src/api/docTroveClient.ts:28

Fetch points filtered by bbox from DocTrove API.
Requests minimal fields and maps DTOs to domain `Point`.

## Parameters

### params

[`FetchPointsByBboxParams`](../type-aliases/FetchPointsByBboxParams.md)

## Returns

`Promise`\<\{ `points`: [`Point`](../../docTroveSchemas/type-aliases/Point.md)[]; `total?`: `number`; \}\>
