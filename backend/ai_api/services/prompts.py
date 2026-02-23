SERIES_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided "Cleaned Data" from a stamp series and generate a high-quality, verified JSON report.

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes or technical specs.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent (e.g., a year that doesn't match the series), mark it as null.
3. VALUATION (Cross-Platform Verification):
  - Phase 1: The Search Loop. Search for the stamp or series on Colnect, Delcampe, and Iberphil.
  - Phase 2: Validation Logic.
    - If High Value/Classic (e.g., 1850 Issue): Look for "Sold" or "Realized" auction prices on Iberphil or StampAuctionNetwork. If a specific price is found (even if Print Run is missing), you MUST provide it. Do not return N/A for classics.
    - If Modern/Common (Post-1960): Check Delcampe for active retail listings. Use the average "Buy It Now" price from reputable sellers.
    - Apply a correction factor of -25% to all market values for all stamps.
  - Phase 3: Series Integrity & The "Value Gate".
    - Series Ceiling Rule: When valuing a complete series, the total market value must never exceed the sum of the individual market values of the stamps within that series. If the calculated series price is higher, adjust it downward to reflect the "set discount" (typically 10-15% lower than the sum of parts).
    - Output VALUATION: N/A ONLY if the stamp cannot be identified or no listings exist across all three platforms.
    - Retail Minimum: If the stamp is common but tradeable, use a Retail Minimum of €0.20 – €0.50 (to reflect individual sale value rather than bulk).
  - Note on Condition: You must provide separate estimates for MNH (Mint Never Hinged) and Used. For classics, "Used" is the standard; MNH requires a "Rare/Auction" disclaimer.
4. EXPANSION: Use your internal knowledge of Spanish philately to expand on the "desc_snippet" and provide a full historical context for the series and specific details for each stamp.

### INPUT DATA:
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue (issue_name).",
  "description": "A comprehensive description of the specific issue, including historical context and the purpose of the emission. Use the issue name and date to provide context about the historical background of the series, its significance in Spanish philately, and any notable events or themes associated with it.",
  "issue_date": "YYYY-MM-DD", if day is missing, use "YYYY-MM-01". If month is also missing, use "YYYY-01-01". If year is missing, use null.
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
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes or technical specs.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent, mark it as null.
3. VALUATION (Cross-Platform Verification):
  - Phase 1: The Search Loop. Search for the stamp or series on Colnect, Delcampe, and Iberphil.
  - Phase 2: Validation Logic.
    - If High Value/Classic (e.g., 1850 Issue): Look for "Sold" or "Realized" auction prices on Iberphil or StampAuctionNetwork. If a specific price is found (even if Print Run is missing), you MUST provide it. Do not return N/A for classics.
    - If Modern/Common (Post-1960): Check Delcampe for active retail listings. Use the average "Buy It Now" price from reputable sellers.
    - Apply a correction factor of -25% to all market values for all stamps.
  - Phase 3: Series Integrity & The "Value Gate".
    - Series Ceiling Rule: When valuing a complete series, the total market value must never exceed the sum of the individual market values of the stamps within that series. If the calculated series price is higher, adjust it downward to reflect the "set discount" (typically 10-15% lower than the sum of parts).
    - Output VALUATION: N/A ONLY if the stamp cannot be identified or no listings exist across all three platforms.
    - Retail Minimum: If the stamp is common but tradeable, use a Retail Minimum of €0.20 – €0.50 (to reflect individual sale value rather than bulk).
  - Note on Condition: You must provide separate estimates for MNH (Mint Never Hinged) and Used. For classics, "Used" is the standard; MNH requires a "Rare/Auction" disclaimer.

### INPUT DATA (Series Info Only):
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue.",
  "description": "A comprehensive description of the specific issue, including historical context and the purpose of the emission. Use the issue name and date to provide context about the historical background of the series, its significance in Spanish philately, and any notable events or themes associated with it.",
  "issue_date": "YYYY-MM-DD", if day is missing, use "YYYY-MM-01". If month is also missing, use "YYYY-01-01". If year is missing, use null.
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
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes or technical specs.
2. CLEANING: Correct any grammatical errors or typos in the source text.
3. VALUATION (Cross-Platform Verification):
  - Phase 1: The Search Loop. Search for the stamp or series on Colnect, Delcampe, and Iberphil.
  - Phase 2: Validation Logic.
    - If High Value/Classic (e.g., 1850 Issue): Look for "Sold" or "Realized" auction prices on Iberphil or StampAuctionNetwork. If a specific price is found (even if Print Run is missing), you MUST provide it. Do not return N/A for classics.
    - If Modern/Common (Post-1960): Check Delcampe for active retail listings. Use the average "Buy It Now" price from reputable sellers.
    - Apply a correction factor of -25% to all market values for all stamps.
  - Phase 3: Series Integrity & The "Value Gate".
    - Series Ceiling Rule: When valuing a complete series, the total market value must never exceed the sum of the individual market values of the stamps within that series. If the calculated series price is higher, adjust it downward to reflect the "set discount" (typically 10-15% lower than the sum of parts).
    - Output VALUATION: N/A ONLY if the stamp cannot be identified or no listings exist across all three platforms.
    - Retail Minimum: If the stamp is common but tradeable, use a Retail Minimum of €0.20 – €0.50 (to reflect individual sale value rather than bulk).
  - Note on Condition: You must provide separate estimates for MNH (Mint Never Hinged) and Used. For classics, "Used" is the standard; MNH requires a "Rare/Auction" disclaimer.
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
