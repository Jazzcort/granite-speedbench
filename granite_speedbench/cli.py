import json
import time
import requests
import argparse
from typing import List
import os
import uuid
import datetime
import csv
from dotenv import load_dotenv
from requests.exceptions import Timeout

base_url = "https://granite-3-1-8b-instruct-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com"
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
    subparsers = parser.add_subparsers(dest="backend", help="Please select eith ollama or openai")
    ollama_parser = subparsers.add_parser("ollama", help="Run benchmark against ollama")
    ollama_parser.add_argument("model", nargs="+")
    ollama_parser.add_argument("-f", "--file", nargs="?", type=str , help="Manually provide test files directory")
    ollama_parser.add_argument("-o", "--output", nargs="?", type=str , help="Manually provide output directory")
    ollama_parser.add_argument("-t", "--text", action='store_true', help="Include test cases with pure text")
    ollama_parser.add_argument("-i", "--infinite", action='store_true', help="Run test cases without time limit")

    openai_parser = subparsers.add_parser("openai", help="Run benchmark against openai")
    openai_parser.add_argument("-k", "--key", nargs="?", help="Manually provide api key")
    openai_parser.add_argument("-f", "--file", nargs="?", type=str , help="Manually provide test files directory")
    openai_parser.add_argument("-o", "--output", nargs="?", type=str , help="Manually provide output directory")
    openai_parser.add_argument("-t", "--text", action='store_true', help="Include test cases with pure text")
    openai_parser.add_argument("-i", "--infinite", action='store_true', help="Run test cases without time limit")

    args = parser.parse_args()

    if args.file and (type(args.file) == str) and os.path.isdir(args.file):
        test_dir = args.file

    if args.output and (type(args.output) == str) and os.path.isdir(args.output):
        out_dir = args.output

    if args.backend == "ollama":
        # Check if Ollama is up and running
        try:
            _ = requests.get(url="http://localhost:11434/api/version")
        except requests.exceptions.ConnectionError:
            print("Please start Ollama with 'ollama serve' in order to run the benchmark")
            return 

        for model in args.model:  
            run_ollama_tests(model, test_dir, out_dir, not args.text, args.infinite)
    elif args.backend == "openai":
        # Load api key from .env file
        load_dotenv(dotenv_path=f"{home_dir}/.granite-speedbench/.env")
        # Set api key with manually provided value, if not provided, set it to the value in the .env file.
        api_key = args.key if args.key else os.environ.get("API_KEY")

        # If api key is not provided, terminate the benchmark
        if not api_key:
            print("Provide API key is mandatory for cloud inference.\nYou can either manually provide it with -k flag or store it as API_KEY=<YOUR_API_KEY> in a .env file at <HOME_DIR>/.granite-speedbench")
            return
        
        run_openai_tests(api_key, test_dir, out_dir, not args.text, args.infinite)

def run_single_test_ollama(file, file_path, model, counts, infinite_mode):
    record = TestRecord(file, model, counts)
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
                record.run_failed()
                print(f"Request failed!")

            print("*************************************************************************")

    return record if not should_abandon_record else None

def sort_test_files_with_file_size(test_dir, code_only):
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
    return [ filename for _, filename in sorted(zip(file_size_lst, test_files), key=lambda pair: pair[0]) ]

def print_and_export_benchmark_result(out_dir, model, backend, records):
    if not records:
        return 

    # Clean files
    with open(f"{out_dir}/{backend}-{model}.txt", "w") as f:
        now = datetime.datetime.now()
        f.write(f"This summary is created on {now.strftime('%Y-%m-%d')} at {now.strftime('%H:%M:%S')}\n\n" + "*************************************************************************\n")
    with open(f"{out_dir}/{backend}-{model}.csv", "w") as f:
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
        output = record.summarize() + "*************************************************************************" 
        print(output)
        with open(f"{out_dir}/{backend}-{model}.txt", "a") as file:
            file.write(output + "\n")

        with open(f"{out_dir}/{backend}-{model}.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerows(record.generate_csv())

    print(f"Output directory: {out_dir}")


def run_ollama_tests(model: str, test_dir: str, out_dir: str, code_only: bool, infinite_mode: bool):
    # Restart model
    refresh_model_instance(model)
    counts = 3
    records: List[TestRecord] = []

    sorted_test_files = sort_test_files_with_file_size(test_dir, code_only)

    for test_file in sorted_test_files:
        file_path = os.path.join(test_dir, test_file)
        record = run_single_test_ollama(test_file, file_path, model, counts, infinite_mode)
        if record:
            records.append(record)
        else:
            break

    print_and_export_benchmark_result(out_dir, model, "ollama", records)

def run_openai_tests(key: str, test_dir: str, out_dir: str, code_only: bool, infinite_mode: bool):
    counts = 3
    records: List[TestRecord] = []
    model = "granite-3-1-8b-instruct-w4a16"

    sorted_test_files = sort_test_files_with_file_size(test_dir, code_only)

    for test_file in sorted_test_files:
        file_path = os.path.join(test_dir, test_file)
        record = run_single_test_openai(test_file, file_path, model, counts, infinite_mode, key)
        if record:
            records.append(record)
        else:
            break

    print_and_export_benchmark_result(out_dir, model, "openai", records)

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

def run_single_test_openai(file, file_path, model, counts, infinite_mode, key):
    record = TestRecord(file, model, counts)
    timeout = 120 if not infinite_mode else None
    with open(file_path) as f:
        content = f.read()
        data = {
            "model": model,
            "max_tokens": 200,
            "prompt": content,
            "temperature": 0,
            "stream": True,
            "stream_options": {
                "include_usage": True,
                "continuous_usage_stats": True
            }
        }

        should_abandon_record = False

        for i in range(counts):

            print(f"---- Running test - {file} -------- {i + 1}/{counts}")
            
            start_time = time.perf_counter()
            try:
                response = requests.post(
                    url=base_url + "/v1/completions", 
                    json=data, 
                    headers={"Authorization": f"Bearer {key}"},
                    stream=True,
                    timeout=timeout
                )

                if response.status_code == 200:
                    tps_start_time = None
                    first_token = True
                    token_counts = 0
                    prompt_tokens = -1

                    for chunk in response.iter_lines():
                        # Raise timeout when stream time is more than 2 minutes
                        if timeout and time.perf_counter() - start_time > timeout:
                            raise Timeout

                        if first_token:
                            first_token = False
                            time_received_first_token = time.perf_counter()
                            time_to_first_token = time_received_first_token - start_time
                            record.add_elapsed_times(time_to_first_token)
                            print(f"---- Elapsed time: {time_to_first_token:.3f} seconds")
                        if token_counts == 10:
                            tps_start_time = time.perf_counter()

                        str_chunk = chunk.decode("utf-8")

                        # Valid stream reply always start with "data:"
                        # Here we bypass the empty reply (str_chunk can be "" sometimes)
                        if str_chunk.startswith("data:") and len(str_chunk) > 5:
                            # Here we want to bypass the last reply which is "data:[DONE]"
                            if str_chunk[6] == "{":

                                # Set prompt_tokens if it hasn't been set yet
                                if prompt_tokens < 0:
                                    try:
                                        json_chunk = json.loads(str_chunk[6:])
                                        prompt_tokens = int(json_chunk["usage"]["prompt_tokens"])

                                    except ValueError:
                                        pass
                                    except KeyError:
                                        pass

                                # Count completion tokens
                                token_counts += 1

                    tps_end_time = time.perf_counter()

                    # Only calculate tps if we receive more than 10 tokens
                    if tps_start_time != None:
                        # The cloud inference always sends an empty response before the last response
                        # Therefore, we minus 11 (10 for threshold + 1 for empty response)
                        tps = ( token_counts - 11 ) / (tps_end_time - tps_start_time)
                        record.add_token_rate(tps)
                        print(f"---- Token rate: {tps:.3f} tokens/s")
                    else:
                        record.add_token_rate(-1)

                    record.add_prompt_token(prompt_tokens)

                elif response.status_code == 403:
                    should_abandon_record = True
                    print("Unauthorized requests --- Ababdon this benchmark")
                    break

                else:
                    record.run_failed()
                    print(f"Request failed!")

            except requests.exceptions.Timeout:
                should_abandon_record = True
                print("Single run exceeds 2 minutes ---- Ababdon this test")
                break

            print("*************************************************************************")

    return record if not should_abandon_record else None

class TestRecord:
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

    def summarize(self) -> str:
        summary = f"---- Summary - {self.name} - {self.model} ----\n"

        prompt_tokens = max(self.prompt_tokens)
        if prompt_tokens > 0:
            summary += f"-- Prompt tokens: {prompt_tokens}\n"
        else:
            summary += f"-- Prompt tokens: --\n"

        success_counts = 0
        total_time = 0
        total_token_rate = 0
        for ind in range(self.total_count):
            time_to_first_token = self.elapsed_times[ind]
            token_rate = self.token_rates[ind]
            # Use token_rate as a fact to decide whether the run is successful or not
            if token_rate > 0:
                total_time += time_to_first_token
                total_token_rate += token_rate
                success_counts += 1
                summary += f"------ Run - {ind + 1} -> time to first token: {time_to_first_token:.3f} seconds, token rate: {token_rate:.3f} tokens/s\n"
            else:
                summary += f"------ Run - {ind + 1} -> failed\n"
        if success_counts > 0:
            summary += f"Average time to first token: {(total_time / success_counts):.3f} seconds\n"
            summary += f"Average token rate: {(total_token_rate / success_counts):.3f} tokens/s\n"
        else:
            summary += f"Average elapsed time: --\n"
            summary += f"Average token rate: --\n"
        summary += f"Successful run / Total run: {success_counts}/{self.total_count}\n"
        return summary
    
    def generate_csv(self):
        res = []

        for ind, tokens_count in enumerate(self.prompt_tokens):
            res.append([self.name, tokens_count, self.elapsed_times[ind], self.token_rates[ind]])

        return res
    
    def run_failed(self):
        self.add_elapsed_times(-1)
        self.add_token_rate(-1)
        self.add_prompt_token(-1)


def main():
    os.makedirs(f"{home_dir}/.granite-speedbench/output", exist_ok=True)
    try:
        speed_bench()
    except KeyboardInterrupt:
        print("\n**********Benchmark terminated**********")

if __name__ == "__main__":
    main()
