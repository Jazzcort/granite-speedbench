import requests
import os
import argparse

options = {
    "num_ctx": 32768,
    "num_predict": 10,
    "temperature": 0
}

def count_tokens(model: str):
    for root, _, files in os.walk("."):
        if root != ".":
            continue
        files.sort()
        for file in files:
            if file.endswith(".txt"):
                with open(file) as f:
                    content = f.read()
                    data = {
                        "model": model,
                        "prompt": content,
                        "stream": False,
                        "options": options,
                        "raw": True
                    }
                    response = requests.post(url="http://localhost:11434/api/generate", json=data)
                    json_obj = response.json()
                    if response.status_code == 200 and "prompt_eval_count" in json_obj:
                        print(f"{file}: {json_obj["prompt_eval_count"]} tokens")

def main():
    parser = argparse.ArgumentParser(prog="token-counter", description="count token size for test file")
    parser.add_argument("model", nargs="+")
    args = parser.parse_args()

    for model in args.model:
        count_tokens(model)

if __name__ == "__main__":
    main()


