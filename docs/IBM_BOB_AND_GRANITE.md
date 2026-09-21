# IBM Bob + Granite Integration

## What is integrated

- **IBM Bob:** used as the AI development partner for planning, code generation, debugging, testing, and refinement of the MetroFlow workflow. Bob is a development tool, not a runtime model endpoint inside this Streamlit app.
- **IBM Granite on watsonx.ai:** optional runtime generation for the commuter recommendation shown after route analysis.

IBM describes Bob as an AI-first development partner across the software lifecycle, while Granite models can be accessed through watsonx.ai.

## Runtime flow

```text
User selects source + destination + travel time
        -> NetworkX route
        -> historical line-demand crowd estimate
        -> route/risk context
        -> IBM Granite (optional)
        -> five-line commuter recommendation
```

If watsonx credentials are not configured, MetroFlow falls back to its deterministic recommendation engine. This keeps the demo usable offline and prevents the app from pretending that an AI service was called when it was not.

## Environment variables

```text
WATSONX_APIKEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-4-h-small
```

Do not put API keys in Python source code or commit them to Git.

## IBM Bob prompts used for this project

### 1. Architecture

> Review this Streamlit Delhi Metro project. Preserve NetworkX routing, the historical line-level passenger-demand crowd estimator, the interactive Network Explorer, and the user-facing crowd table. Propose a modular architecture for an optional IBM Granite recommendation backend with a deterministic fallback. Do not invent station-level passenger data.

### 2. Crowd-model validation

> Inspect the crowd calculation and verify that every displayed crowd value can be traced to the supplied line-level passengers/km data plus documented time/station adjustments. Identify any place where the code could imply real-time passenger counts and correct the wording.

### 3. Granite integration

> Add an optional IBM Granite on watsonx.ai recommendation backend. Read credentials only from environment variables, never from source code. If credentials are missing or the API fails, use the deterministic recommendation engine. Keep the output concise and route-specific.

### 4. Testing

> Test the MetroFlow route flow for source/destination selection, route calculation, crowd table rendering, Network Explorer highlighting, and Granite fallback behavior. Report failures and fix them without fabricating data.

## Responsible AI

- The app labels crowd results as estimates, not real-time counts.
- No passenger identity or personal data is used.
- Granite receives route/crowd context, not personal commuter information.
- Recommendations are advisory and should not be presented as guaranteed travel conditions.
- Missing credentials or service failures use a deterministic fallback instead of fabricating an AI response.
