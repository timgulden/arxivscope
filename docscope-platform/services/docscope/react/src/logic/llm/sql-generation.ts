/**
 * LLM SQL Generation Pure Functions for DocScope React Frontend
 * 
 * Implements LLM SQL generation using pure functions with injected API provider.
 * Following functional programming principles: NO SIDE EFFECTS.
 * 
 * Replicates the exact prompt from the Dash version.
 */

/**
 * Interface for LLM API response
 */
export interface LlmResponse {
  success: boolean;
  sql?: string;
  error?: string;
}

/**
 * Interface for LLM API provider
 */
export interface LlmApiProvider {
  generateSql(naturalLanguage: string): Promise<LlmResponse>;
}

/**
 * Clean up LLM response - remove markdown code blocks, quotes, and extra text
 * This replicates the exact cleaning logic from the Dash version
 */
export function cleanGeneratedSql(generatedSql: string): string {
  if (!generatedSql) {
    return '';
  }

  let cleaned = generatedSql.trim();

  // Remove markdown code blocks
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.substring(3);
  }
  if (cleaned.endsWith('```')) {
    cleaned = cleaned.substring(0, cleaned.length - 3);
  }

  // Remove SQL language specifiers
  if (cleaned.startsWith('sql')) {
    cleaned = cleaned.substring(3);
  }

  // Remove quotes if present
  if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
    cleaned = cleaned.substring(1, cleaned.length - 1);
  }
  if (cleaned.startsWith("'") && cleaned.endsWith("'")) {
    cleaned = cleaned.substring(1, cleaned.length - 1);
  }

  // Clean up any remaining whitespace and newlines
  cleaned = cleaned.trim();

  // Remove any remaining markdown artifacts
  cleaned = cleaned.replace(/`/g, ''); // Remove any remaining backticks

  // CRITICAL: Remove "WHERE" keyword if present at the beginning (case-insensitive)
  // The API expects only the WHERE clause conditions, not the keyword itself
  const whereRegex = /^\s*WHERE\s+/i;
  if (whereRegex.test(cleaned)) {
    cleaned = cleaned.replace(whereRegex, '').trim();
  }

  return cleaned;
}

/**
 * Validate generated SQL - replicates Dash validation logic
 */
export function validateGeneratedSql(sql: string): { valid: boolean; error?: string } {
  if (!sql || sql.trim().length < 10) {
    return { valid: false, error: 'Generated SQL is too short or empty. Please try again.' };
  }

  const sqlUpper = sql.toUpperCase();

  // Check for common invalid patterns (from Dash)
  if (sqlUpper.includes('SELECT') || sqlUpper.includes('FROM') || sqlUpper.includes('JOIN')) {
    return {
      valid: false,
      error: 'Generated SQL contains invalid clauses (SELECT, FROM, JOIN). Only WHERE clause allowed.',
    };
  }

  // Check for invalid fields (from Dash)
  if (sqlUpper.includes('TOPIC')) {
    return { valid: false, error: "Generated SQL contains invalid field 'topic'. Please try a different request." };
  }

  if (sql.includes("doctrove_source = 'doctrove'")) {
    return {
      valid: false,
      error: "Generated SQL has invalid source 'doctrove'. Valid sources are: arxiv, randpub, extpub, aipickle",
    };
  }

  // Check for balanced parentheses (from Dash)
  const openParens = (sql.match(/\(/g) || []).length;
  const closeParens = (sql.match(/\)/g) || []).length;
  if (openParens !== closeParens) {
    return { valid: false, error: 'Generated SQL has unbalanced parentheses. Please try again.' };
  }

  // Check for basic SQL syntax (from Dash)
  const hasOperator = /(=|LIKE|IN|>|<|>=|<=)/i.test(sql);
  if (!hasOperator) {
    return {
      valid: false,
      error: 'Generated SQL appears to be invalid. Please try a different request.',
    };
  }

  return { valid: true };
}

/**
 * Generate SQL from natural language using LLM - PURE function with injected API provider
 * This replicates the exact prompt from the Dash version
 */
export async function generateSqlFromNaturalLanguage(
  naturalLanguage: string,
  guideContent: string,
  schemaContent: string,
  apiProvider: LlmApiProvider
): Promise<{ sql: string; status: string }> {
  if (!naturalLanguage || !naturalLanguage.trim()) {
    throw new Error('Natural language input is required');
  }

  if (!guideContent) {
    throw new Error('Query construction guide is required');
  }

  if (!schemaContent) {
    throw new Error('Database schema is required');
  }

  // Replicate EXACT prompt from Dash version (lines 766-800 in app.py)
  const prompt = `You are a SQL expert. Generate ONLY a SQL WHERE clause for this request: "${naturalLanguage}"

## 💡 HELPFUL GUIDELINES - AUTHOR SEARCHES:

**For searching authors, consider using:**
- Field: \`doctrove_authors\` (works for all sources)
- Syntax: \`array_to_string(doctrove_authors, '|') LIKE '%AuthorName%'\`
- Example: \`doctrove_source = 'randpub' AND array_to_string(doctrove_authors, '|') LIKE '%Gulden%'\`

**Alternative approaches that also work:**
- \`randpub_authors LIKE '%AuthorName%'\` (RAND-specific)
- \`openalex_authors LIKE '%AuthorName%'\` (OpenAlex-specific)

**Note:** \`doctrove_authors\` is preferred because it works universally across all sources.

## INSTRUCTIONS:
Please read and follow the query construction guide and database schema provided below.

## QUERY CONSTRUCTION GUIDE:
${guideContent}

## DATABASE SCHEMA:
${schemaContent}

## TASK:
Based on the guide and schema above, generate a SQL WHERE clause that:
1. Uses ONLY the fields documented in the schema
2. Follows the naming conventions and relationships described
3. Applies the appropriate source constraints
4. Returns ONLY the WHERE clause (no SELECT, FROM, JOIN)

## OUTPUT:
Return ONLY the SQL WHERE clause. Nothing else.

**Note**: After generating SQL, use the "Test Query" button to verify it works before applying.`;

  // Call API provider
  const response = await apiProvider.generateSql(naturalLanguage);

  if (!response.success) {
    throw new Error(response.error || 'Failed to generate SQL');
  }

  if (!response.sql) {
    throw new Error('No SQL generated from API');
  }

  // Clean up the response (replicates Dash cleaning logic)
  // This also strips WHERE keyword if present (more reliable than relying on LLM)
  let generatedSql = cleanGeneratedSql(response.sql);

  // Validate the generated SQL (replicates Dash validation)
  const validation = validateGeneratedSql(generatedSql);
  if (!validation.valid) {
    throw new Error(validation.error || 'Generated SQL validation failed');
  }

  return {
    sql: generatedSql,
    status: '✅ Please check the automatically generated SQL query below',
  };
}

/**
 * Create a default API provider that calls the backend /api/generate-sql endpoint
 */
export function createDefaultLlmApiProvider(apiBaseUrl: string = 'http://localhost:5001'): LlmApiProvider {
  return {
    async generateSql(naturalLanguage: string): Promise<LlmResponse> {
      try {
        const response = await fetch(`${apiBaseUrl}/api/generate-sql`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            natural_language: naturalLanguage,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          return {
            success: false,
            error: errorData.error || `HTTP ${response.status}: ${response.statusText}`,
          };
        }

        const data = await response.json();

        if (!data.success) {
          return {
            success: false,
            error: data.error || 'Failed to generate SQL',
          };
        }

        return {
          success: true,
          sql: data.sql,
        };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Network error occurred',
        };
      }
    },
  };
}

