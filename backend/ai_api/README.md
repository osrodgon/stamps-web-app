# AI API Documentation

Welcome to the API documentation for the AI Services resource. This document provides detailed information about the RESTful endpoints for AI-powered stamp series extraction.

The AI API provides intelligent extraction of stamp series information using Large Language Models (LLM) and web scraping technologies. It automates the research process by searching philatelic catalogs, scraping relevant data, and extracting structured information using AI.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/issues/extraction`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Services Overview

The AI API integrates multiple services to provide intelligent stamp series extraction:

| Service | Description |
| :--- | :--- |
| **SearchService** | Searches for stamp series URLs using the Serper API (Google Search) to find relevant philatelic catalog pages. |
| **ScrapingService** | Scrapes and cleans content from philatelic catalog pages (primarily catalogodesellos.fesofi.es). |
| **LLMService** | Processes extracted data using configurable LLM providers (Google Gemini, Groq) to extract structured stamp information. |

---

## Supported LLM Providers

The AI API supports multiple LLM providers through a factory pattern:

| Provider | Description | Configuration |
| :--- | :--- | :--- |
| **Google Gemini** | Google's generative AI model | Set `LLM_PROVIDER=gemini` |
| **Groq** | Fast inference API for LLMs | Set `LLM_PROVIDER=groq` |

---

## API Endpoints

### `POST /issues/extraction/`

Performs AI-powered extraction of stamp series information. This endpoint accepts a series name and date, searches for relevant philatelic catalog pages, scrapes the content, and uses AI to extract structured data.

*   **Summary:** Extract Stamp Series Information using AI
*   **Description:** Performs AI-powered extraction of series information using configurable LLM providers. Requires a name (either series name or the motive of one of the stamps in the series) and publication date.
*   **Request Body:**
    A JSON object containing the extraction parameters.
    ```json
    {
      "name": "Olimpiadas",
      "date": "1992"
    }
    ```
    
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `name` | String | Name of the stamp series to research or the motive of one of the stamps in the series. Max length: 200 characters. |
    | `date` | String | Publication date of the stamp series. Any date format is accepted. |

*   **Alternative Usage - Direct URL:**
    If you already have a URL from the philatelic catalog, you can pass it directly with a zero date:
    ```json
    {
      "name": "https://catalogo.sellos.es/producto/olimpiadas-1992/",
      "date": "0"
    }
    ```

*   **Success Response (200 OK):**
    A JSON object containing the extracted stamp series information.
    ```json
    {
      "issue_name": "Olimpiadas Barcelona 1992",
      "description": "Series commemorating the Barcelona 1992 Olympic Games",
      "issue_date": "1992-07-25",
      "artist": "José María Cruz Novillo",
      "printer": "Fábrica Nacional de Moneda y Timbre",
      "print_type": "Offset",
      "perforation": "13 x 13",
      "paper_type": "Estucado",
      "stamp_type": "Sello",
      "notes": "Commemorative series for Barcelona Olympics",
      "total_printed": 5000000,
      "market_value_mnh": 25.50,
      "market_value_used": 8.00,
      "stamps": [
        {
          "edifil_code": "2461",
          "fesofi_code": "2461",
          "face_value": "5 PTA",
          "description": "Olympic rings and logo",
          "amount_printed": 1000000,
          "color": "Multicolor",
          "market_value_mnh": 3.50,
          "market_value_used": 1.00
        }
      ]
    }
    ```

*   **Response Fields:**
    
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `issue_name` | String | Name of the stamp issue |
    | `description` | String | Historical description or "n/a" |
    | `issue_date` | Date | Issue date in YYYY-MM-DD format or null |
    | `artist` | String | Artist/engraver name or "n/a" |
    | `printer` | String | Printer name or "n/a" |
    | `print_type` | String | Printing technique or "n/a" |
    | `perforation` | String | Perforation measurement or "n/a" |
    | `paper_type` | String | Paper type or "n/a" |
    | `stamp_type` | String | Format (Sello, Hoja Bloque, Carné...) or "n/a" |
    | `notes` | String | Relevant notes or "n/a" |
    | `total_printed` | Integer | Total printed quantity or null |
    | `market_value_mnh` | Float | Market value in mint condition or null |
    | `market_value_used` | Float | Market value in used condition or null |
    | `stamps` | Array | List of individual stamp details |
    
    **Stamp Details Fields:**
    
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `edifil_code` | String | Edifil catalog code or "n/a" |
    | `fesofi_code` | String | Fesofi catalog code or "n/a" |
    | `face_value` | String | Exact face value (e.g., "5 PTA") |
    | `description` | String | Design/motive description or "n/a" |
    | `amount_printed` | Integer | Individual stamp print run or null |
    | `color` | String | Color or "n/a" |
    | `market_value_mnh` | Float | Market value mint condition or null |
    | `market_value_used` | Float | Market value used condition or null |

*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields).
        ```json
        {
          "error": {"name": ["This field is required."]},
          "message": null
        }
        ```
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no information could be found for the provided name and date.
        ```json
        {
          "error": null,
          "message": "Could not find anything for name: Olimpiadas and date: 1992"
        }
        ```
    *   **422 Unprocessable Entity:** If the AI returned invalid or unparseable data.
        ```json
        {
          "error": "Validation error details",
          "message": "AI response format error"
        }
        ```
    *   **500 Internal Server Error:** If the AI service is unavailable or an internal error occurred.
        ```json
        {
          "error": "AI error",
          "message": "AI service unavailable"
        }
        ```

---

## Environment Configuration

The AI API requires the following environment variables:

| Variable | Description | Required |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | The LLM provider to use (`gemini` or `groq`) | Yes |
| `GEMINI_API_KEY` | API key for Google Gemini (if using Gemini) | Conditional |
| `GROQ_API_KEY` | API key for Groq (if using Groq) | Conditional |
| `SERPER_API_KEY` | API key for Serper (Google Search API) | Yes |
| `SERPER_URL` | Serper API endpoint URL | Yes |

---

## Testing

The AI API includes comprehensive tests covering:

- LLM service functionality
- Provider factory pattern
- Series extraction API endpoints
- Batch processing capabilities

Tests are located in the `ai_api/test/` directory and can be run using pytest:

```bash
pytest backend/ai_api/test/