import requests
import os

options = {
    "num_ctx": 32768,
    "num_predict": 10,
    "temperature": 0
}
def main():

    for root, dirs, files in os.walk("."):
        if root != ".":
            continue
        files.sort()
        for file in files:
            if file.endswith(".txt"):
                with open(file) as f:
                    content = f.read()
                    data = {
                        "model": "granite3.2:8b",
                        "prompt": content,
                        "stream": False,
                        "options": options,
                        "raw": True
                    }
                    response = requests.post(url="http://localhost:11434/api/generate", json=data)
                    json_obj = response.json()
                    if response.status_code == 200 and "prompt_eval_count" in json_obj:
                        print(f"{file}: {json_obj["prompt_eval_count"]} tokens")

if __name__ == "__main__":
    main()


