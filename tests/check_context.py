from transformers import AutoTokenizer
import os
def main():
    tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-3.2-8b-instruct")
    
    for root, dirs, files in os.walk("."):
        if root != ".":
            continue
        files.sort()
        for file in files:
            if file.endswith(".txt"):
                with open(file) as f:
                    content = f.read()
                    tokens = tokenizer.encode(content)
                    print(f"{file}: {len(tokens)} tokens")

if __name__ == "__main__":
    main()


