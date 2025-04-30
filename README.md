# Granite Speedbench
Granite Speedbench is a simple CLI that runs test cases with different context sizes against Granite models through Ollama.
## Requirement
Python version >= 3.13
## How to use it?
### Clone the repo
```shell
git clone https://github.com/Jazzcort/granite-speedbench.git
cd granite-speedbench
```
### Installation guide
#### Install Granite Speedbench globally
```shell
pip install .
```
If you bump with issue like this when using `pip3`
![Issue picture](https://github.com/Jazzcort/granite-speedbench/blob/main/media/issue.png)

Try adding `--break-system-packages` flag

```shell
pip3 install --break-system-packages .
```
#### Install Granite Speedbench with virtual environment
```shell
python -m venv .venv
. .venv/bin/activate
pip install .
```
### Example
#### ollama
```shell
granite-speedbench ollama granite3.3:8b
```
You can also use your own test files and store the test output to a specific directory.
```shell
granite-speedbench ollama -f path/to/test/file -o path/to/output/file granite3.3:8b
```
You can also test multiple models in one go.
```shell
granite-speedbench ollama granite3.3:2b granite3.3:8b
```
#### openai
If you store your api key in `.env` file.
```shell
granite-speedbench openai
```
You can also provide the api key manually.
```shell
granite-speedbench openai -k <YOUR_API_KEY>
```
You can also use your own test files and store the test output to a specific directory.
```shell
granite-speedbench openai -f path/to/test/file -o path/to/output/file 
```


## Parameters
You can check the usage detail with `-h` flag

### ollama
Benchmark against Ollama.

#### Required
|  Name    | Description |
|----------|----------|
|  model (You can provide multiple models)    | name of the model to be tested  |
#### Optional
| Flag | Name | Description |
|----------|----------|----------|
| -f    | file     | path to the test file directory     |
| -o    | output    | path to the output file directory  |
| -t    | text    | run with pure text test cases |
| -i    | infinite    | run without 2-minute timeout  |

### openai
Benchmark against maas.

#### Required
None, but you need to either provide an api key manually with `-k` flag or create a `.env` file with `API_KEY=<YOUR_API_KEY>` at `<HOME_DIR>/.granite-speedbench`. Otherwise, the benchmark can not be run.

#### Optional
| Flag | Name | Description |
|----------|----------|----------|
| -k    | key     | api key  |
| -f    | file     | path to the test file directory     |
| -o    | output    | path to the output file directory  |
| -t    | text    | run with pure text test cases |
| -i    | infinite    | run without 2-minute timeout  |

## Benchmark
### granite3.3:8b
|                                          | TTFT, 2k |        | TTFT, 20k |        | Tokens/sec (2k)  |        | Tokens/sec (20k)  |        | Overall |
|------------------------------------------|----------|--------|-----------|--------|------------------|--------|-------------------|--------|---------|
|                                          | Time     | Score  | Time      | Score  | Rate             | Score  | Rate              | Score  |         |
|           **Macbook m3 Pro**             | 6.99     | 1.0    | 132.52    | 1.0    | 22.39            | 1.0    | 8.51              | 1.0    | -       |
|           Flash Attention on             | 6.66     | --     | 88.81     | --     | 25.93            | --     | 14.92             | --     | -       |
| Flash Attention on / KV Cache Type q4_0  | 7.18     | --     | 132.53    | --     | 26.41            | --     | 19.88             | --     | -       |

### granite3.3:2b
|                                          | TTFT, 2k |        | TTFT, 20k |        | Tokens/sec (2k)  |        | Tokens/sec (20k)  |        | Overall |
|------------------------------------------|----------|--------|-----------|--------|------------------|--------|-------------------|--------|---------|
|                                          | Time     | Score  | Time      | Score  | Rate             | Score  | Rate              | Score  |         |
|           **Macbook m3 Pro**             | 2.57     | 1.0    | 81.74     | 1.0    | 45.59            | 1.0    | 11.41             | 1.0    | -       |
|           Flash Attention on             | 2.24     | --     | 36.02     | --     | 62.24            | --     | 30.72             | --     | -       |
| Flash Attention on / KV Cache Type q4_0  | 2.28     | --     | 40.12     | --     | 60.41            | --     | 40.12             | --     | -       |

### qwen2.5-coder:7b
|                                          | TTFT, 2k |        | TTFT, 20k |        | Tokens/sec (2k)  |        | Tokens/sec (20k)  |        | Overall |
|------------------------------------------|----------|--------|-----------|--------|------------------|--------|-------------------|--------|---------|
|                                          | Time     | Score  | Time      | Score  | Rate             | Score  | Rate              | Score  |         |
|          **Macbook m3 Pro**              | 5.03     | 1.0    | 84.01     | 1.0    | 27.44            | 1.0    | 12.74             | 1.0    | -       |
|          Flash Attention on              | 4.87     | --     | 61.48     | --     | 30.67            | --     | 23.40             | --     | -       |
| Flash Attention on / KV Cache Type q4_0  | 5.16     | --     | 85.44     | --     | 46.39            | --     | 24.45             | --     | -       |

