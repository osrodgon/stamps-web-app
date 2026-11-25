SERIES_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided "Cleaned Data" from a stamp series and generate a high-quality, verified JSON report.

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes, technical specs, print runs or dates.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent (e.g., a year that doesn't match the series), mark it as null.
3. TEXT WORK: The description and the notes are written from the input data only: what the emission commemorates, what it shows, how it was printed and what the catalogue says. Do not add historical context, anecdotes, rarity claims or values from memory. If the input has nothing to say, keep it short instead of filling it in.
4. NO VALUATION: Do not estimate market values, do not search for prices and do not invent them. Prices come from recorded observations elsewhere, not from this report.
5. IMPORTANT: Your output limit is 8192 tokens. Do not truncate the JSON. Ensure every stamp in the batch is fully described before closing the JSON object.

### INPUT DATA:
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue (issue_name).",
  "description": "Description of the emission written from the input data: what it commemorates, its motifs, its printing. No invented context and no values.",
  "issue_date": "YYYY-MM-DD", if day is missing, use "YYYY-MM-01". If month is also missing, use "YYYY-01-01". If year is missing, use null.
  "artist": "Engraver if mentioned in context, otherwise null",
  "printer": "Name of the printing house (printer) or null if not specified",
  "print_type": "The technical method used (e.g., Huecograbado)",
  "perforation": "The perforation measurement (e.g., 13 1/4)",
  "paper_type": "The type of paper used (e.g., Estucado, mate, etc.)",
  "stamp_type": "Type of stamp: sello, carné, hoja bloque, prueba de artista, triptico...",
  "notes": "Remarks the input data actually makes about the series. Empty string when it makes none.",
  "total_printed": Integer,
  "stamps": [
    {
      "edifil_code": "edifil of null",
      "fesofi_code": "fesofi code or null",
      "motive": "The stamp motive or null",
      "face_value": "facial or null",
      "description": "Corrected description of the desc_snippet, written from the input data only. Include remarks the input makes about the stamp.",
      "amount_printed": Integer,
      "color": "color or null"
    }
  ]
}
"""

SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided "Series Info" data and generate a high-quality, verified JSON report containing ONLY the series-level information (no stamps).

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes, technical specs, print runs or dates.
2. CLEANING: Correct any grammatical errors or typos in the source text. If a piece of data is logically inconsistent (e.g., a year that doesn't match the series), mark it as null.
3. TEXT WORK: The description and the notes are written from the input data only: what the emission commemorates, what it shows, how it was printed and what the catalogue says. Do not add historical context, anecdotes, rarity claims or values from memory. If the input has nothing to say, keep it short instead of filling it in.
4. NO VALUATION: Do not estimate market values, do not search for prices and do not invent them. Prices come from recorded observations elsewhere, not from this report.
5. IMPORTANT: Your output limit is 8192 tokens. Do not truncate the JSON. Ensure the JSON object is complete before closing it.

### INPUT DATA (Series Info Only):
{{ input_data }}

### REQUIRED OUTPUT FORMAT (JSON ONLY). Output the final JSON as a single-line string. Remove all indentation, newlines, and carriage returns (minify the JSON). Do not wrap the response in markdown code blocks like ```json. Fields content must be in spanish:
{
  "issue_name": "Name of the issue.",
  "description": "Description of the emission written from the input data: what it commemorates, its motifs, its printing. No invented context and no values.",
  "issue_date": "YYYY-MM-DD", if day is missing, use "YYYY-MM-01". If month is also missing, use "YYYY-01-01". If year is missing, use null.
  "artist": "Engraver if mentioned in context, otherwise null",
  "printer": "Name of the printing house or null if not specified",
  "print_type": "The technical method used (e.g., Huecograbado)",
  "perforation": "The perforation measurement (e.g., 13 1/4)",
  "paper_type": "The type of paper used (e.g., Estucado, mate, etc.)",
  "stamp_type": "Type of stamp: sello, carné, hoja bloque, prueba de artista, triptico...",
  "notes": "Remarks the input data actually makes about the series. Empty string when it makes none.",
  "total_printed": Integer
}
"""

SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE="""
Act as a professional philatelic expert and data architect specialized in Spanish postal history. Your goal is to process the provided batch of stamp data and generate detailed information for each stamp.

### CONSTRAINTS:
1. DATA INTEGRITY: Use the provided input data as the primary source. Never use internal knowledge to fill in missing data. If a field is not provided or is inconsistent, mark it as null. Do not invent Edifil codes, technical specs, print runs or dates.
2. CLEANING: Correct any grammatical errors or typos in the source text.
3. TEXT WORK: Each stamp description is written from the input data of that stamp: its motif, its face value, its colour, what the series says about it. Do not add historical context, anecdotes, rarity claims or values from memory.
4. NO VALUATION: Do not estimate market values, do not search for prices and do not invent them. Prices come from recorded observations elsewhere, not from this report.
5. IMPORTANT: Your output limit is 8192 tokens. Do not truncate the JSON. Ensure every stamp in the batch is fully described before closing the JSON object.

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
      "description": "Corrected description of the desc_snippet, written from the input data only. Include remarks the input makes about the stamp.",
      "amount_printed": Integer,
      "color": "color or null"
    }
  ]
}
"""
