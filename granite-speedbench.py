#!/usr/bin/env python3
import requests
import sys
import time
import argparse
from typing import List
import os

home_dir = os.path.expanduser("~")
options = {
    "num_ctx": 8192
}

def speed_bench(is_cli: bool):
    test_dir: str = home_dir + "/.granite-speedbench"
    out_dir: str = home_dir + "/.granite-speedbench/output"
    if not is_cli:
        test_dir = "./tests"
        out_dir = "./output"

    parser = argparse.ArgumentParser(prog="granite-speedbench", description="Bench marking granite with Ollama")
    parser.add_argument("model", nargs="+")
    parser.add_argument("-f", "--file", nargs="?", type=str , help="Manually provide test files directory")
    parser.add_argument("-o", "--output", nargs="?", type=str , help="Manually provide output directory")

    args = parser.parse_args()

    if args.file and (type(args.file) == str) and os.path.isdir(args.file):
        test_dir = args.file

    if args.output and (type(args.output) == str) and os.path.isdir(args.output):
        out_dir = args.output

    for model in args.model:
        run_tests(model, test_dir, out_dir)

    print(f"Output directory: {out_dir}")

def run_tests(model: str, test_dir: str, out_dir: str):
    counts = 3
    records: List[TestRecoed] = []
    for root, dirs, files in os.walk(test_dir):
        # Restruct to the current level
        if root != test_dir:
            continue
        files.sort()
        for file in files:
            if file.endswith(".txt"):
                record = TestRecoed(file, model, counts)
                file_path = os.path.join(root, file)
                with open(file_path) as f:
                    content = f.read()
                    data = {
                        "model": model,
                        "prompt": content,
                        "stream": False,
                        "options": options
                    }
                    for i in range(counts):
                        # Stop the current running model and start fresh
                        refresh_model_instance(model)
                        print(f"---- Running test - {file} -------- {i + 1}/{counts}")

                        start_time = time.perf_counter()
                        response = requests.post(url="http://localhost:11434/api/generate", json=data)
                        end_time = time.perf_counter()
                        if (response.status_code == 200):
                            elapsed_time = end_time - start_time
                            record.add_elapsed_times(elapsed_time)
                            print(f"---- Elapsed time: {elapsed_time} seconds")
                        else:
                            record.add_elapsed_times(-1)
                            print(f"Request failed!")

                        print("----------------------------------------")
                records.append(record)

    # Clean the file
    with open(f"{out_dir}/{model}.txt", "w") as file:
        file.write("")

    for record in records:
        output = record.summerize() + "----------------------------------------" 
        print(output)
        with open(f"{out_dir}/{model}.txt", "a") as file:
            file.write(output + "\n")

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
        "options": options
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
        self.elapsed_times = []

    def add_elapsed_times(self, elapsed_time: float):
        self.elapsed_times.append(elapsed_time)

    def summerize(self) -> str:
        summery = f"---- Summery - {self.name} - {self.model} ----\n"
        success_counts = 0
        total_time = 0
        for ind, t in enumerate(self.elapsed_times):
            if t >= 0:
                total_time += t
                success_counts += 1
                summery += f"------ Run - {ind + 1} -> elapsed time: {t:.3f}\n"
            else:
                summery += f"------ Run - {ind + 1} -> failed\n"
        if success_counts > 0:
            summery += f"Average elapsed time: {(total_time / success_counts):.3f} seconds\n"
        else:
            summery += f"Average elapsed time: --\n"
        summery += f"Successful run / Total run: {success_counts}/{self.total_count}\n"
        return summery

if __name__ == "__main__":
    # Directly use the python file
    if sys.argv[0].endswith(".py"):
        try:
            os.mkdir(f"./output")
        except FileExistsError:
            _ = 1
        finally:
            speed_bench(False)

    # Use as a CLI
    else:
        try:
            os.mkdir(f"{home_dir}/.granite-speedbench/output")
        except FileExistsError:
            _ = 1
        finally:
            speed_bench(True)

