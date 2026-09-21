# MetroFlow AI

MetroFlow AI is a Streamlit prototype for Delhi Metro route intelligence. It computes metro routes with NetworkX, estimates route-specific crowd conditions for a selected travel time, flags high-risk stations, and generates concise AI-style travel guidance.

## Features

- Source, destination, and travel-time route analysis
- NetworkX shortest-path routing
- Route-specific crowd analysis for stations on the selected journey
- High-risk station detection using predicted crowd scores
- Optional IBM Granite-powered recommendations through watsonx.ai when `WATSONX_APIKEY` and `WATSONX_PROJECT_ID` are set
- Optional OpenAI recommendations remain supported for backward compatibility
- Deterministic recommendation engine when no AI credentials are available
- IBM Bob development workflow and prompts documented in `docs/IBM_BOB_AND_GRANITE.md`
- Interactive PyVis metro network explorer with route highlighting

## Pages

- Home: inputs, journey summary, crowd analysis, high-risk stations, AI recommendations, and route crowd score
- Metro Network Explorer: interactive network visualization, selected route highlighting, and station hover details

## Project Structure

```text
ai_engine/          AI recommendation interface
crowd_engine/       Route-specific crowd prediction and risk scoring
data/               Bundled Delhi Metro station data
pages/              Streamlit pages
route_engine/       NetworkX graph building and route finding
utils/              Data loading, station metadata, styling helpers
visualizations/     PyVis graph and Streamlit display helpers
app.py              Main Streamlit Home page
requirements.txt    Python dependencies
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## IBM Granite Setup (optional)

The app can call IBM Granite through watsonx.ai for the final route recommendation. IBM documents watsonx.ai credentials using an API key, project ID, and service URL. The app reads credentials from environment variables.

```bash
set WATSONX_APIKEY=your_key_here
set WATSONX_PROJECT_ID=your_project_id_here
set WATSONX_URL=https://us-south.ml.cloud.ibm.com
set WATSONX_MODEL_ID=ibm/granite-4-h-small
```

IBM Bob is used as the development partner for this project (planning, implementation, debugging, and testing); it is not claimed as a runtime inference API. See `docs/IBM_BOB_AND_GRANITE.md` for the exact workflow and prompts.

## Optional AI Setup

Set an API key before launching the app to enable optional LLM-generated recommendations:

```bash
set OPENAI_API_KEY=your_key_here
```

Without an API key, the app still generates deterministic route-specific recommendations.

## Supported Data Files

The loader checks for these files under `data/raw/`:

- `stops.txt` or `stops.csv`
- `routes.txt` or `routes.csv`
- `stop_times.txt` or `stop_times.csv`
- `stations.csv`
- `connections.csv`
- `ridership.csv`

If files are absent, the application still runs using its internal Delhi Metro data pipeline.

## Validation

```bash
python -m compileall app.py ai_engine crowd_engine route_engine utils visualizations pages
```


## Crowd-estimation methodology (upgraded)
The crowd engine now uses the supplied `data/line_passenger_demand.csv` dataset. The spreadsheet provides line-level daily passengers, route length, and passengers/km. Passengers/km is normalized across the supplied lines to create a baseline demand score. A transparent time-of-day adjustment is then applied (morning peak, evening peak, shoulder, or off-peak), with small documented station-characteristic adjustments for interchanges and business-area stations.

This is an **estimated crowd level**, not a real-time passenger count. The supplied dataset does not contain station-by-hour passenger counts. Lines without a row in the supplied spreadsheet use the median passengers/km of the supplied lines as a fallback baseline, which is explicitly labelled in the model.


### Network Explorer update
All metro lines remain visible in their assigned line colours. The selected NetworkX route is highlighted in green, with the source in blue and destination in red.
