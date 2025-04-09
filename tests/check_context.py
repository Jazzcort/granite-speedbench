from transformers import AutoTokenizer
def main():
    tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-3.2-8b-instruct")
    
    context_length = ["1000", "2000", "3000", "4000"]
    for l in context_length:
        text_file_name = f"{l}_text.txt"
        code_file_name = f"{l}_code.txt"
        with open(text_file_name, "r") as file:
            content = file.read()
            tokens = tokenizer.encode(content)
            print(f"{text_file_name}: {len(tokens)} tokens")

        with open(code_file_name, "r") as file:
            content = file.read()
            tokens = tokenizer.encode(content)
            print(f"{code_file_name}: {len(tokens)} tokens")

if __name__ == "__main__":
    main()


