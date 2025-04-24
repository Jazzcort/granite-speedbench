import requests
import argparse
from typing import List
import os
import uuid
import datetime
import csv

home_dir = os.path.expanduser("~")
options = {
    "num_ctx": 32768,
    "num_predict": 10,
    "temperature": 0
}

def speed_bench():
    test_dir: str = os.path.join(os.path.dirname(__file__), "tests")
    out_dir: str = home_dir + "/.granite-speedbench/output"

    parser = argparse.ArgumentParser(prog="granite-speedbench", description="Bench marking granite with Ollama")
    parser.add_argument("model", nargs="+")
    parser.add_argument("-f", "--file", nargs="?", type=str , help="Manually provide test files directory")
    parser.add_argument("-o", "--output", nargs="?", type=str , help="Manually provide output directory")
    parser.add_argument("-t", "--text", action='store_true', help="Include test cases with pure text")
    parser.add_argument("-i", "--infinite", action='store_true', help="Run test cases without time limit")

    args = parser.parse_args()

    if args.file and (type(args.file) == str) and os.path.isdir(args.file):
        test_dir = args.file

    if args.output and (type(args.output) == str) and os.path.isdir(args.output):
        out_dir = args.output

    for model in args.model:
        run_tests(model, test_dir, out_dir, not args.text, args.infinite)

    print(f"Output directory: {out_dir}")

def run_single_test(file, file_path, model, counts, infinite_mode):
    record = TestRecoed(file, model, counts)
    timeout = 120 if not infinite_mode else None
    with open(file_path) as f:
        content = f.read()
        data = {
            "model": model,
            "stream": False,
            "options": options,
            "raw": True
        }

        should_abandon_record = False

        for i in range(counts):
            # Add uuid at the top of the content to dump prefix-cache
            data["prompt"] = f"{uuid.uuid4()}" + "\n" + content

            print(f"---- Running test - {file} -------- {i + 1}/{counts}")
            
            try:
                response = requests.post(url="http://localhost:11434/api/generate", json=data, timeout=timeout)
            except requests.exceptions.Timeout:
                should_abandon_record = True
                print("Single run exceeds 2 minutes ---- Ababdon this test")
                break

            response_json = response.json()

            # Gather time to first token and token rate
            if (response.status_code == 200) and "prompt_eval_duration" in response_json and "eval_count" in response_json and "eval_duration" in response_json and "prompt_eval_count" in response_json and response_json["eval_duration"] > 0:
                time_to_first_token = response_json["prompt_eval_duration"] / 1_000_000_000
                record.add_elapsed_times(time_to_first_token)
                print(f"---- Elapsed time: {time_to_first_token:.3f} seconds")

                tokens = response_json["eval_count"]
                eval_duration = response_json["eval_duration"] / 1_000_000_000
                token_rate = tokens / eval_duration
                record.add_token_rate(token_rate)
                print(f"---- Token rate: {token_rate:.3f} tokens/s")

                record.add_prompt_token(response_json["prompt_eval_count"])
            else:
                record.add_elapsed_times(-1)
                record.add_token_rate(-1)
                record.add_prompt_token(-1)
                print(f"Request failed!")

            print("*************************************************************************")

    return record if not should_abandon_record else None

def run_tests(model: str, test_dir: str, out_dir: str, code_only: bool, infinite_mode: bool):
    # Restart model
    refresh_model_instance(model)
    counts = 3
    records: List[TestRecoed] = []

    test_files = []
    for root, _, files in os.walk(test_dir):
        # Restrict to the current level
        if root != test_dir:
            continue
        for file in files:
            if file.endswith(".txt"):

                if code_only and file.endswith("text.txt"):
                    continue

                test_files.append(file)

    file_size_lst = [ os.path.getsize(os.path.join(test_dir, test_file)) for test_file in test_files ]
    # Sort the test files with their size
    sorted_test_files = [ filename for _, filename in sorted(zip(file_size_lst, test_files), key=lambda pair: pair[0]) ]

    for test_file in sorted_test_files:
        file_path = os.path.join(test_dir, test_file)
        record = run_single_test(test_file, file_path, model, counts, infinite_mode)
        if record:
            records.append(record)
        else:
            break

    # Clean files
    with open(f"{out_dir}/{model}.txt", "w") as f:
        now = datetime.datetime.now()
        f.write(f"This summary is created on {now.strftime('%Y-%m-%d')} at {now.strftime('%H:%M:%S')}\n\n" + "*************************************************************************\n")
    with open(f"{out_dir}/{model}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "num_tokens", "time_to_first_token", "tokens_per_sec"])

    print("\n\
     ____                                             \n\
    / ___| _   _ _ __ ___  _ __ ___   __ _ _ __ _   _ \n\
    \\___ \\| | | | '_ ` _ \\| '_ ` _ \\ / _` | '__| | | |\n\
     ___) | |_| | | | | | | | | | | | (_| | |  | |_| |\n\
    |____/ \\__,_|_| |_| |_|_| |_| |_|\\__,_|_|   \\__, |\n\
                                                |___/ \n")
    print("*************************************************************************")

    # Print and store the summary 
    for record in records:
        output = record.summerize() + "*************************************************************************" 
        print(output)
        with open(f"{out_dir}/{model}.txt", "a") as file:
            file.write(output + "\n")

        with open(f"{out_dir}/{model}.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerows(record.generate_csv())

def refresh_model_instance(model: str):
    data = {
        "model": model,
        "keep_alive": 0
    }
    response = requests.post(url="http://localhost:11434/api/generate", json=data)
    if response.status_code == 200:
        print(f"Successfully shut down {model} model")
    else:
        print(f"Failed to shut down {model} model")

    data = {
        "model": model,
        "prompt": "Dummy",
        "stream": False,
        "options": options,
        "raw": True
    }
    response = requests.post(url="http://localhost:11434/api/generate", json=data)
    if response.status_code == 200:
        print(f"Successfully spawned {model} model")
    else:
        print(f"Failed to spawn {model} model")

class TestRecoed:
    def __init__(self, name: str = "unknown", model: str = "unknown", total_count: int = 0):
        self.name = name
        self.model = model
        self.total_count = total_count
        self.elapsed_times: List[float] = []
        self.token_rates: List[float] = []
        self.prompt_tokens: List[int] = []

    def add_elapsed_times(self, elapsed_time: float):
        self.elapsed_times.append(elapsed_time)

    def add_token_rate(self, token_rate: float):
        self.token_rates.append(token_rate)

    def add_prompt_token(self, prompt_token: int):
        self.prompt_tokens.append(prompt_token)

    def summerize(self) -> str:
        summery = f"---- Summary - {self.name} - {self.model} ----\n"

        prompt_tokens = max(self.prompt_tokens)
        if prompt_tokens > 0:
            summery += f"-- Prompt tokens: {prompt_tokens}\n"
        else:
            summery += f"-- Prompt tokens: --\n"

        success_counts = 0
        total_time = 0
        total_token_rate = 0
        for ind in range(self.total_count):
            time_to_first_token = self.elapsed_times[ind]
            token_rate = self.token_rates[ind]
            if time_to_first_token >= 0:
                total_time += time_to_first_token
                total_token_rate += token_rate
                success_counts += 1
                summery += f"------ Run - {ind + 1} -> time to first token: {time_to_first_token:.3f} seconds, token rate: {token_rate:.3f} tokens/s\n"
            else:
                summery += f"------ Run - {ind + 1} -> failed\n"
        if success_counts > 0:
            summery += f"Average time to first token: {(total_time / success_counts):.3f} seconds\n"
            summery += f"Average token rate: {(total_token_rate / success_counts):.3f} tokens/s\n"
        else:
            summery += f"Average elapsed time: --\n"
            summery += f"Average token rate: --\n"
        summery += f"Successful run / Total run: {success_counts}/{self.total_count}\n"
        return summery
    
    def generate_csv(self):
        res = []

        for ind, tokens_count in enumerate(self.prompt_tokens):
            res.append([self.name, tokens_count, self.elapsed_times[ind], self.token_rates[ind]])

        return res

def main():
    os.makedirs(f"{home_dir}/.granite-speedbench/output", exist_ok=True)
    speed_bench()

if __name__ == "__main__":
    main()
