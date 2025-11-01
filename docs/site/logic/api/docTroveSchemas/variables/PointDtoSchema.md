[**@docscope/logic**](../../../README.md)

***

[@docscope/logic](../../../README.md) / [api/docTroveSchemas](../README.md) / PointDtoSchema

# Variable: PointDtoSchema

> `const` **PointDtoSchema**: `ZodObject`\<\{ `doctrove_embedding_2d`: `ZodOptional`\<`ZodNullable`\<`ZodUnion`\<\[`ZodString`, `ZodTuple`\<\[`ZodNumber`, `ZodNumber`\], `null`\>\]\>\>\>; `doctrove_paper_id`: `ZodString`; `doctrove_primary_date`: `ZodOptional`\<`ZodString`\>; `doctrove_source`: `ZodOptional`\<`ZodString`\>; `doctrove_title`: `ZodOptional`\<`ZodString`\>; \}, `"strip"`, `ZodTypeAny`, \{ `doctrove_embedding_2d?`: `null` \| `string` \| \[`number`, `number`\]; `doctrove_paper_id`: `string`; `doctrove_primary_date?`: `string`; `doctrove_source?`: `string`; `doctrove_title?`: `string`; \}, \{ `doctrove_embedding_2d?`: `null` \| `string` \| \[`number`, `number`\]; `doctrove_paper_id`: `string`; `doctrove_primary_date?`: `string`; `doctrove_source?`: `string`; `doctrove_title?`: `string`; \}\>

Defined in: src/api/docTroveSchemas.ts:8

DTO schema for a paper point as returned by DocTrove API.
Accepts either Postgres point string "(x,y)" or tuple [x,y].
