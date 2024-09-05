import os
import openai
import json
import sys

def main():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    user_message = sys.argv[1] if len(sys.argv) > 1 else ""
    if not user_message:
        print(json.dumps({"error": "No message provided"}))
        return

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional digital currency trader, and you are good at explaining different pros and cons of digital currencies to others."},
                {"role": "user", "content": user_message}
            ]
        )
        print(json.dumps(completion.choices[0].message))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
