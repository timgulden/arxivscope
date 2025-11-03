# Universe Filter Implementation Plan

## Overview

This document breaks down the implementation of the Universe Filter feature in the React frontend, replicating the exact functionality from the Dash prototype.

## Current State

✅ **Completed:**
- Basic `UniverseFilterModal` component (presentational)
- SQL input field
- Test Query button (basic implementation)
- Apply/Cancel buttons

⏳ **Remaining:**
- Natural language input field
- LLM SQL generation (replicate exact Dash prompt)
- View Schema button with DATABASE_SCHEMA.md display
- Enhanced test query with enrichment auto-detection
- LLM API integration with proper error handling
- Documentation updates (UNIVERSE_FILTER_GUIDE.md, DATABASE_SCHEMA.md)

---

## Task Breakdown

### Task 1: Create LLM SQL Generation Pure Function

**Location**: `src/logic/llm/sql-generation.ts`

**Requirements**:
- Replicate EXACT prompt from Dash version (lines 766-800 in `app.py`)
- Load `UNIVERSE_FILTER_GUIDE.md` and `DATABASE_SCHEMA.md` (or pass content as parameter)
- Use same Azure OpenAI API endpoint and authentication
- Clean response exactly as Dash does (remove markdown code blocks, quotes, etc.)
- Pure function with injected API provider

**Prompt Structure** (from Dash):
```typescript
You are a SQL expert. Generate ONLY a SQL WHERE clause for this request: "{natural_language}"

## 💡 HELPFUL GUIDELINES - AUTHOR SEARCHES:
[Author search guidelines]

## INSTRUCTIONS:
Please read and follow the query construction guide and database schema provided below.

## QUERY CONSTRUCTION GUIDE:
{guide_content}

## DATABASE SCHEMA:
{schema_content}

## TASK:
Based on the guide and schema above, generate a SQL WHERE clause that:
1. Uses ONLY the fields documented in the schema
2. Follows the naming conventions and relationships described
3. Applies the appropriate source constraints
4. Returns ONLY the WHERE clause (no SELECT, FROM, JOIN)

## OUTPUT:
Return ONLY the SQL WHERE clause. Nothing else.
```

**API Details** (from Dash):
- URL: `https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4o-2024-11-20-us/chat/completions?api-version=2024-02-01`
- Headers: `Content-Type: application/json`, `Ocp-Apim-Subscription-Key: {api_key}`
- Request: `{"messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.1}`
- Response cleaning: Remove markdown code blocks, SQL language specifiers, quotes, backticks

**Files to Create**:
- `src/logic/llm/sql-generation.ts` - Pure LLM function
- `src/logic/llm/__tests__/sql-generation.test.ts` - Unit tests

---

### Task 2: Add Natural Language Input to UniverseFilterModal

**Location**: `src/components/UniverseFilterModal.tsx`

**Requirements**:
- Add natural language textarea input (above SQL input)
- Add "Generate SQL" button that calls LLM function
- Display generation status/errors
- Follow same layout as Dash version

**UI Elements** (from Dash):
- Natural Language Request label
- Description text: "Describe what papers you want to see in plain English:"
- Textarea with placeholder: `"Show me OpenAlex papers from US and China" or "RAND documents with type = RR"`
- Generate SQL button (blue #007bff)
- Generation status display area

**Files to Modify**:
- `src/components/UniverseFilterModal.tsx`

---

### Task 3: Add View Schema Button and Display

**Location**: `src/components/UniverseFilterModal.tsx`

**Requirements**:
- Add "📋 View Schema" button next to Generate SQL
- Load and display `DATABASE_SCHEMA.md` formatted (markdown → React)
- Toggle display (show/hide schema)
- Use react-markdown or similar for rendering

**UI Elements** (from Dash):
- View Schema button (purple #6f42c1)
- Schema display area (scrollable, max-height 400px)
- Close Schema button

**Files to Modify**:
- `src/components/UniverseFilterModal.tsx`
- May need to install `react-markdown` if not already installed

---

### Task 4: Enhance Test Query Function

**Location**: `src/logic/data/data-fetching.ts` (update existing `testQuery`)

**Requirements**:
- Replicate Dash auto-detection logic (lines 1023-1096)
- Auto-detect enrichment fields from SQL:
  - Three-part patterns: `{source}_{table}_{field}`
  - Two-part patterns: `{source}_{field}`
  - Handle special cases (randpub → randpub_metadata)
- Pass enrichment params to API
- Match Dash error handling and messages

**Auto-Detection Logic** (from Dash):
1. Find three-part patterns: `re.findall(r"(\w+)_(\w+)_(\w+)", sql_query)`
2. Find two-part patterns: `re.findall(r"(\w+)_(\w+)", sql_query)`
3. Filter out main table fields
4. Map to enrichment table names (special case for randpub)

**Files to Modify**:
- `src/logic/data/data-fetching.ts` - Enhance `testQuery` function

---

### Task 5: Create/Update UNIVERSE_FILTER_GUIDE.md

**Location**: `docscope/docs/UNIVERSE_FILTER_GUIDE.md` (create if missing)

**Requirements**:
- Replicate or update guide to reflect React/API protocol
- Document field naming conventions
- Document enrichment table relationships
- Include examples

**Note**: This file is referenced in Dash code but may not exist. Check if it exists first.

**Files to Create/Modify**:
- `docscope/docs/UNIVERSE_FILTER_GUIDE.md`

---

### Task 6: Update DATABASE_SCHEMA.md for API Protocol

**Location**: `docscope/docs/DATABASE_SCHEMA.md`

**Requirements**:
- Verify schema matches current database structure
- Ensure API protocol (field access patterns) is documented
- Update if needed to reflect current backend behavior

**Files to Modify**:
- `docscope/docs/DATABASE_SCHEMA.md`

---

### Task 7: Integrate LLM API in App.tsx

**Location**: `src/App.tsx`

**Requirements**:
- Add handler for Generate SQL button
- Call pure LLM function from logic layer
- Handle API errors gracefully
- Update UniverseFilterModal with generated SQL
- Follow design principles: business logic in logic layer, UI in components

**Files to Modify**:
- `src/App.tsx` - Add LLM handler

---

### Task 8: Update UniverseFilterModal Props and State

**Location**: `src/components/UniverseFilterModal.tsx`

**Requirements**:
- Add natural language input state (transient UI state)
- Add generation status state
- Add schema display state
- Add callbacks: `onGenerateSQL`, `onViewSchema`
- Maintain purely presentational component pattern

**Files to Modify**:
- `src/components/UniverseFilterModal.tsx`

---

## Implementation Order

1. **Task 5 & 6**: Create/verify documentation files first (needed by LLM function)
2. **Task 1**: Create LLM pure function (can be tested independently)
3. **Task 4**: Enhance test query function (needed for Task 3)
4. **Task 2**: Add natural language input to modal
5. **Task 3**: Add view schema button
6. **Task 7**: Integrate LLM in App.tsx
7. **Task 8**: Update modal props (can be done in parallel with 2-7)

---

## Key Requirements

### Design Principles
- ✅ **Pure Functions**: All LLM and test logic in logic layer
- ✅ **UI/Logic Separation**: Modal is presentational, handlers in App.tsx
- ✅ **Dependency Injection**: API calls injected into pure functions
- ✅ **Testable**: All logic functions can be unit tested

### API Details (from Dash)
- **Endpoint**: Azure OpenAI API via RAND gateway
- **Deployment**: `gpt-4o-2024-11-20-us`
- **API Version**: `2024-02-01`
- **Authentication**: `Ocp-Apim-Subscription-Key` header
- **Parameters**: `max_tokens: 2000`, `temperature: 0.1`

### Response Cleaning (from Dash)
1. Remove markdown code blocks (``` at start/end)
2. Remove SQL language specifiers (`sql`)
3. Remove quotes (`"` or `'` if wrapping entire response)
4. Remove backticks
5. Trim whitespace

### Validation (from Dash)
- Check for SELECT, FROM, JOIN (invalid)
- Check for balanced parentheses
- Check for basic SQL operators (=, LIKE, IN, >, <, >=, <=)
- Check for invalid fields (topic, doctrove_source = 'doctrove')

---

## Files Reference

**Dash Implementation:**
- `docscope/app.py` lines 726-899 (LLM generation)
- `docscope/app.py` lines 901-998 (View Schema)
- `docscope/app.py` lines 1000-1161 (Test Query)
- `docscope/app.py` lines 539-711 (Modal UI)

**React Files to Create/Modify:**
- `src/logic/llm/sql-generation.ts` (NEW)
- `src/logic/llm/__tests__/sql-generation.test.ts` (NEW)
- `src/components/UniverseFilterModal.tsx` (MODIFY)
- `src/App.tsx` (MODIFY)
- `src/logic/data/data-fetching.ts` (MODIFY)
- `docscope/docs/UNIVERSE_FILTER_GUIDE.md` (CREATE/MODIFY)
- `docscope/docs/DATABASE_SCHEMA.md` (MODIFY if needed)

---

## Next Steps

1. Check if `UNIVERSE_FILTER_GUIDE.md` exists
2. Review `DATABASE_SCHEMA.md` for accuracy
3. Start with Task 1 (LLM pure function) - can be developed and tested independently
4. Then proceed with UI tasks (Tasks 2, 3, 8)
5. Finally integrate everything (Task 7)

---

*Plan created: [Date]*
*Status: Ready for implementation*

