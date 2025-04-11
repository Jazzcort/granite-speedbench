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
```shell
granite-speedbench granite3.2:8b
```
You can also use your own test files and store the test output to the specific directory
```shell
granite-speedbench -f path/to/test/file -o path/to/output/file granite3.2:8b
```
You can also test multiple models in one go
```shell
granite-speedbench granite3.2:2b granite3.2:8b
```

## Parameters
You can check the usage detail with `-h` flag
### Required
|  Name    | Description |
|----------|----------|
|  model (You can provide multiple models)    | name of the model to be tested  |
### Optional
| Flag | Name | Description |
|----------|----------|----------|
| -f    | file     | path to the test file directory     |
| -o    | output    | path to the output file directory  |

