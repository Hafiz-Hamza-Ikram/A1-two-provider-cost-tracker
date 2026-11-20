# Two-Provider LLM Cost Tracker

A Python command-line application that sends the same prompt to **Google Gemini** and **Groq**, retrieves real API token usage, measures execution time, calculates estimated API costs, and compares the results.

## Features

- Sends the same prompt to two different LLM providers.
- Retrieves actual input and output token counts from API responses.
- Measures API request execution time.
- Calculates estimated costs based on prices per million tokens.
- Displays the responses and a comparison table.
- Saves structured output in `results.json`.
- Loads API keys and model configurations securely from `.env`.
- Handles missing configuration and temporary Gemini server errors.

## Technologies Used

- Python
- uv (Python package manager)
- Google GenAI SDK (`google-genai`)
- Groq Python SDK (`groq`)
- python-dotenv
- Git and GitHub

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Hafiz-Hamza-Ikram/A1-two-provider-cost-tracker.git
cd A1-two-provider-cost-tracker
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`.

```powershell
Copy-Item .env.example .env
```

Update `.env` with your own API credentials:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_INPUT_PRICE_PER_M=0.30
GEMINI_OUTPUT_PRICE_PER_M=2.50

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
GROQ_INPUT_PRICE_PER_M=0.075
GROQ_OUTPUT_PRICE_PER_M=0.30
```

The prices above are the rates configured for this assignment and should be checked against the providers' current pricing documentation before future use.

**Security:** Never commit your `.env` file or share API keys publicly.

## Running the Tracker

Run:

```bash
uv run tracker.py "Explain artificial intelligence in three sentences."
```

Alternatively:

```bash
uv run python tracker.py "Explain artificial intelligence in three sentences."
```

## Cost Calculation

The program calculates estimated cost using:

```text
Cost (USD) =
(Input Tokens × Input Price per 1M) / 1,000,000
+
(Output Tokens × Output Price per 1M) / 1,000,000
```

Token counts come from each provider's API usage data rather than word-count estimations.

## Testing and Sample Results

The application was tested with three different prompts, including an explanation of artificial intelligence and a comparison of supervised and unsupervised machine learning.

### Sample Test

**Prompt:** What is the difference between supervised and unsupervised learning?

| Metric | Google Gemini | Groq |
|---|---:|---:|
| Model | gemini-3.5-flash-lite | openai/gpt-oss-20b |
| Input Tokens | 11 | 83 |
| Output Tokens | 764 | 1,103 |
| Total Tokens | 775 | 1,186 |
| Estimated Cost (USD) | $0.001913300 | $0.000337125 |

Both models successfully generated explanations covering labeled versus unlabeled data, common algorithms, and practical machine-learning examples.

The console also displays the elapsed time for each call. The measured seconds are not included in `results.json` because the assignment specifies eight required fields.

## Output File

After each successful run, the application generates `results.json`.

The JSON file contains a list with one object for each provider, including:

- `provider`
- `model`
- `reply`
- `input_tokens`
- `output_tokens`
- `input_price_per_m`
- `output_price_per_m`
- `cost_usd`

The file is overwritten with the latest results after each successful execution.

## What I Learned

I learned how to integrate multiple LLM providers into a single Python application and retrieve actual token usage directly from API responses. I also learned how differences in tokenization, model output length, and per-million-token pricing influence the estimated cost of AI requests. This assignment helped me understand secure API key management, error handling, and how to compare models using measurable data.

## Security

- API keys are stored in `.env`.
- `.env` is excluded from Git using `.gitignore`.
- `.env.example` provides a safe configuration template.
- No real API credentials are included in the repository.

## References

- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models and Pricing](https://console.groq.com/docs/models)
- [uv Documentation](https://docs.astral.sh/uv/)

---

**Assignment:** Two-Provider Cost Tracker — Assignment 1, Week 1  
**Course:** Agentic AI Developer — IEC
