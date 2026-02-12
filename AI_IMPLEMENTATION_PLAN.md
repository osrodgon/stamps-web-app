# Plan de Implementación: Módulo de IA para Stamps Web App

Este documento detalla la arquitectura, requisitos y pasos necesarios para integrar el sistema de investigación automática de sellos utilizando Google Gemini 1.5 Flash.

## 1. Objetivo
Automatizar la entrada de datos de series filatélicas. El sistema recibirá un nombre y fecha, y devolverá una ficha técnica completa (incluyendo sellos individuales) validada contra el catálogo Edifil, eliminando la necesidad de entrada manual.

## 2. Arquitectura Propuesta
Se implementará una nueva aplicación Django llamada `ai_manager` en el backend. Esta app encapsulará la lógica de IA, separándola de los modelos de datos principales.

### Estructura de Directorios Recomendada
```text
/workspaces/stamps-web-app/
├── backend/
│   ├── ai_manager/                 # [NUEVA APP]
│   │   ├── __init__.py
│   │   ├── apps.py                 # Configuración de la app
│   │   ├── services.py             # Lógica de conexión con Gemini (Core)
│   │   ├── views.py                # Endpoints API (POST /research/)
│   │   └── urls.py                 # Rutas
│   ├── resources/                  # [EXISTENTE]
│   │   ├── series_research_prompt.txt  # Prompt maestro de ingeniería
│   │   └── TESTING_PROMPTS.md          # Guía de pruebas manuales (Playground)
│   └── ...
```

## 3. Requisitos Previos
1.  **Google API Key**:
    - Obtener una clave gratuita en Google AI Studio.
    - Esta clave tiene un límite gratuito de 15 peticiones/minuto (suficiente para este uso).
2.  **Variable de Entorno**:
    - Añadir `GOOGLE_API_KEY` al archivo `.env` del servidor.
3.  **Dependencias Python**:
    - Instalar la librería oficial: `pip install google-generativeai`

## 4. Componentes Clave

### A. El Prompt Maestro (`backend/resources/series_research_prompt.txt`)
Es el componente más crítico. Ha sido diseñado con un **Protocolo de Tolerancia Cero** para evitar alucinaciones.
*   **Entradas**: `{{ issue_name }}`, `{{ issue_date }}`, `{{ edifil_start_number }}`.
*   **Salida**: JSON estricto.
*   **Reglas Clave**:
    - Temperatura 0.0 (Determinista).
    - "Si no lo sabes, devuelve null".
    - Parada de emergencia si cambia el tema de la serie.

### B. Servicio de IA (`backend/ai_manager/services.py`)
Clase `StampResearchService`. Sus responsabilidades son:
1.  Cargar el archivo de texto del prompt.
2.  Inyectar las variables dinámicas.
3.  Llamar a la API de Gemini con la configuración `response_mime_type="application/json"`.
4.  Manejar errores de red o de parseo JSON.

### C. API Endpoint (`backend/ai_manager/views.py`)
Clase `ResearchSeriesView`.
*   **Método**: `POST`
*   **Seguridad**: Requiere autenticación (`IsAuthenticated`).
*   **Payload**:
    ```json
    {
      "issue_name": "Castillos",
      "issue_date": "2007-09-10",
      "edifil_start_number": "4349"
    }
    ```

## 5. Pasos de Implementación (Checklist)

- [ ] **1. Crear la App**: Ejecutar `python manage.py startapp ai_manager` (o crear carpetas manualmente).
- [ ] **2. Instalar Librería**: Añadir `google-generativeai` al `requirements.txt`.
- [ ] **3. Copiar Código**: Implementar `services.py`, `views.py` y `urls.py` con el código generado previamente.
- [ ] **4. Configurar Django**:
    - Añadir `'ai_manager'` a `INSTALLED_APPS` en `settings.py`.
    - Incluir las rutas en `_backend/urls.py`: `path('api/v1/ai/', include('ai_manager.urls'))`.
- [ ] **5. Variables de Entorno**: Configurar `GOOGLE_API_KEY`.

## 6. Estrategia de Pruebas
Si la IA empieza a fallar o a inventar datos, seguir este protocolo:
1.  Abrir `backend/resources/TESTING_PROMPTS.md`.
2.  Copiar el contenido en Google AI Studio.
3.  Ajustar la **Temperature a 0.0**.
4.  Probar con la serie problemática para depurar el prompt sin tocar código.

## 7. Límites y Costes (Gemini 1.5 Flash)
*   **Free Tier**: 1,500 peticiones al día.
*   **Rate Limit**: 15 peticiones por minuto (1 cada 4 segundos).
*   **Acción recomendada**: Si se implementa una carga masiva, añadir un `time.sleep(4)` entre peticiones en el script de carga.

---
*Documento generado para referencia futura.*