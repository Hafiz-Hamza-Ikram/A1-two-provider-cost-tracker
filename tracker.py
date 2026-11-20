
import os
import sys
import json
import time
from decimal import Decimal

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from groq import Groq


# Load API keys, model names, and prices from .env
load_dotenv(override=True)


def get_setting(name):
    """Read a required environment variable."""
    value = os.getenv(name)

    if not value or not value.strip():
        raise ValueError(
            f"Missing {name}. Please configure it in your .env file."
        )

    return value.strip()


def calculate_cost(input_tokens, output_tokens,
                   input_price, output_price):
    """Calculate the list-price cost in USD."""
    cost = (
        Decimal(input_tokens) * Decimal(str(input_price))
        + Decimal(output_tokens) * Decimal(str(output_price))
    ) / Decimal("1000000")

    return float(cost)


def call_gemini(prompt):
    """Send a prompt to Gemini and return its results."""
    api_key = get_setting("GEMINI_API_KEY")
    model = get_setting("GEMINI_MODEL")

    input_price = Decimal(
        get_setting("GEMINI_INPUT_PRICE_PER_M")
    )
    output_price = Decimal(
        get_setting("GEMINI_OUTPUT_PRICE_PER_M")
    )

    client = genai.Client(api_key=api_key)

    try:

        start = time.perf_counter()

        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                print(f"Gemini attempt {attempt + 1}/{max_attempts}")

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                break

            except errors.ServerError as error:
                # Retry only temporary service failures.
                if error.code not in (500, 502, 503, 504):
                    raise

                if attempt == max_attempts - 1:
                    raise

                delay = 2 ** (attempt + 1)
                print(
                    f"Gemini temporarily unavailable "
                    f"(HTTP {error.code}). Retrying..."
                )
                time.sleep(delay)

        seconds = time.perf_counter() - start


        usage = response.usage_metadata
        if usage is None:
            raise ValueError("Gemini did not return token usage.")

        if usage.prompt_token_count is None:
            raise ValueError("Gemini input token count is missing.")

        if usage.candidates_token_count is None:
            raise ValueError("Gemini output token count is missing.")

        input_tokens = int(usage.prompt_token_count)

        # Gemini may report thinking tokens separately.
        # Include them in billable output tokens.
        visible_tokens = int(usage.candidates_token_count)
        thinking_tokens = int(usage.thoughts_token_count or 0)
        output_tokens = visible_tokens + thinking_tokens

        reply = response.text or ""

        cost = calculate_cost(
            input_tokens,
            output_tokens,
            input_price,
            output_price,
        )

        result = {
            "provider": "gemini",
            "model": model,
            "reply": reply,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_price_per_m": float(input_price),
            "output_price_per_m": float(output_price),
            "cost_usd": cost,
        }

        return result, seconds

    finally:
        client.close()


def call_groq(prompt):
    """Send a prompt to Groq and return its results."""
    api_key = get_setting("GROQ_API_KEY")
    model = get_setting("GROQ_MODEL")

    input_price = Decimal(
        get_setting("GROQ_INPUT_PRICE_PER_M")
    )
    output_price = Decimal(
        get_setting("GROQ_OUTPUT_PRICE_PER_M")
    )

    client = Groq(api_key=api_key)

    try:
        start = time.perf_counter()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        seconds = time.perf_counter() - start

        usage = response.usage
        if usage is None:
            raise ValueError("Groq did not return token usage.")

        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        if input_tokens is None or output_tokens is None:
            raise ValueError("Groq token counts are missing.")

        reply = response.choices[0].message.content or ""

        cost = calculate_cost(
            input_tokens,
            output_tokens,
            input_price,
            output_price,
        )

        result = {
            "provider": "groq",
            "model": model,
            "reply": reply,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "input_price_per_m": float(input_price),
            "output_price_per_m": float(output_price),
            "cost_usd": cost,
        }

        return result, seconds

    finally:
        client.close()


def print_results(results, times):
    """Display model replies and a comparison table."""

    for result in results:
        provider = result["provider"].upper()
        print(f"\n{'=' * 60}")
        print(f"{provider} RESPONSE")
        print(f"Model: {result['model']}")
        print("=" * 60)
        print(result["reply"])

    print("\n" + "=" * 78)
    print("TWO-PROVIDER COST COMPARISON")
    print("=" * 78)

    header = (
        f"{'Provider':<12}"
        f"{'Input':>10}"
        f"{'Output':>10}"
        f"{'Seconds':>12}"
        f"{'Cost (USD)':>18}"
    )

    print(header)
    print("-" * 78)

    for result in results:
        provider = result["provider"]

        print(
            f"{provider:<12}"
            f"{result['input_tokens']:>10}"
            f"{result['output_tokens']:>10}"
            f"{times[provider]:>12.3f}"
            f"{result['cost_usd']:>18.8f}"
        )


def save_results(results):
    """Save provider results to results.json."""
    with open("results.json", "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    print("\nResults saved to results.json")


def main():
    """Run the two-provider cost tracker."""

    if len(sys.argv) < 2:
        print('Usage: uv run tracker.py "your prompt"')
        return 1

    prompt = " ".join(sys.argv[1:]).strip()

    if not prompt:
        print("Error: Prompt cannot be empty.")
        return 1

    # Validate everything before making API calls.
    try:
        settings = [
            "GEMINI_API_KEY",
            "GEMINI_MODEL",
            "GEMINI_INPUT_PRICE_PER_M",
            "GEMINI_OUTPUT_PRICE_PER_M",
            "GROQ_API_KEY",
            "GROQ_MODEL",
            "GROQ_INPUT_PRICE_PER_M",
            "GROQ_OUTPUT_PRICE_PER_M",
        ]

        for setting in settings:
            get_setting(setting)

        print(f"\nPrompt: {prompt}")
        print("\nCalling Gemini and Groq...")

        results = []
        times = {}

        print("\n[1/2] Calling Gemini...")

        gemini_result, gemini_seconds = call_gemini(prompt)
        results.append(gemini_result)
        times["gemini"] = gemini_seconds

        print("[SUCCESS] Gemini responded!")

        print("\n[2/2] Calling Groq...")

        groq_result, groq_seconds = call_groq(prompt)
        results.append(groq_result)
        times["groq"] = groq_seconds

        print("[SUCCESS] Groq responded!")

        print_results(results, times)
        save_results(results)

        return 0

    except Exception as error:
        print(f"\nError Type: {type(error).__name__}")
        print(f"Error Details: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
