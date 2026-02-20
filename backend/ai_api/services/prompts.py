SERIES_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided "Cleaned Data" from a stamp series and generate a high-quality, verified JSON report.

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Do not invent Edifil codes or technical specs.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent (e.g., a year that doesn't match the series), mark it as null.
3. VALUATION: Based on the "tirada" (amount printed), year of emission (1967), and the popularity of the series (e.g., "Paisajes y Monumentos"), provide a realistic market value estimate in Euros for both MNH (Mint Never Hinged/Nuevo) and Used (Usado) states. Ignore inflated catalog values. Use a 'floor' price based on current bulk auction rates.  
    - Note: The market value of a complete series is typically lower than the sum of individual stamps.
4. EXPANSION: Use your internal knowledge of Spanish philately to expand on the "desc_snippet" and provide a full historical context for the series and specific details for each stamp.

### INPUT DATA:
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue (issue_name).",
  "description": "A comprehensive description of the specific issue, including historical context and the purpose of the emission.",
  "issue_date": "YYYY-MM-DD",
  "artist": "Engraver if mentioned in context, otherwise null",
  "printer": "Name of the printing house (printer) or null if not specified",
  "print_type": "The technical method used (e.g., Huecograbado)",
  "perforation": "The perforation measurement (e.g., 13 1/4)",
  "paper_type": "The type of paper used (e.g., Estucado, mate, etc.)",
  "stamp_type": "Type of stamp: sello, carné, hoja bloque, prueba de artista, triptico...",
  "notes": "Any significant philatelic remarks, errors known in the series, or specific notes for collectors.",
  "total_printed": Integer,
  "market_value_mnh": Float,
  "market_value_used": Float,
  "stamps": [
    {
      "edifil_code": "edifil of null",
      "fesofi_code": "fesofi code or null",
      "motive": "The stamp motive or null",
      "face_value": "facial or null",
      "description": "Corrected and expanded description of the desc_snippet. Include any remarks related to the stamp.",
      "amount_printed": Integer,
      "color": "color or null",
      "market_value_mnh": Float,
      "market_value_used": Float
    }
  ]
}
"""

SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided "Series Info" data and generate a high-quality, verified JSON report containing ONLY the series-level information (no stamps).

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Do not invent data.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent, mark it as null.
3. VALUATION: Based on the available information (year, print run, series popularity), provide a realistic market value estimate in Euros for both MNH and Used states for the complete series.

### INPUT DATA (Series Info Only):
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue.",
  "description": "A comprehensive description of the specific issue, including historical context and the purpose of the emission.",
  "issue_date": "YYYY-MM-DD",
  "artist": "Engraver if mentioned in context, otherwise null",
  "printer": "Name of the printing house or null if not specified",
  "print_type": "The technical method used (e.g., Huecograbado)",
  "perforation": "The perforation measurement (e.g., 13 1/4)",
  "paper_type": "The type of paper used (e.g., Estucado, mate, etc.)",
  "stamp_type": "Type of stamp: sello, carné, hoja bloque, prueba de artista, triptico...",
  "notes": "Any significant philatelic remarks, errors known in the series, or specific notes for collectors.",
  "total_printed": Integer,
  "market_value_mnh": Float,
  "market_value_used": Float
}
"""

SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided batch of stamp data and generate detailed information for each stamp.

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Do not invent Edifil codes or technical specs.
2. CLEANING: Correct any grammatical errors or typos in the source text.
3. VALUATION: Based on the series context provided and individual stamp characteristics, provide realistic market value estimates in Euros for both MNH and Used states.
4. EXPANSION: Use your internal knowledge of Spanish philately to expand on the "desc_snippet" and provide detailed descriptions for each stamp.

### SERIES CONTEXT:
{{ series_context }}

### BATCH INFORMATION:
This is batch {{ batch_number }} of {{ total_batches }} total batches.

### INPUT DATA (Stamp Batch):
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "stamps": [
    {
      "edifil_code": "edifil code or null",
      "fesofi_code": "fesofi code or null",
      "motive": "The stamp motive or null",
      "face_value": "facial or null",
      "description": "Corrected and expanded description of the desc_snippet. Include any remarks related to the stamp.",
      "amount_printed": Integer,
      "color": "color or null",
      "market_value_mnh": Float,
      "market_value_used": Float
    }
  ]
}
"""
