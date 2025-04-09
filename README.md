# Granite Speedbench
Granite Speedbench is a simple CLI that runs test cases with different context sizes against Granite models through Ollama.
## How to use it?
Clone the repo
```shell
git clone https://github.com/Jazzcort/granite-speedbench.git
cd granite-speedbench
```

## Use as CLI
### Linux/Mac
Use the installation script provide in this repo.
```shell
sudo ./add_to_cli.sh
```
Run it as a CLI (Please make sure Ollama is running and the tested model is installed)
```shell
granite-speedbench granite3.2:8b
```

## Use as python file
Use it inside the cloned repo
```shell
python3 granite-speedbench.py granite3.2:8b
```

## Parameters
You can check the usage detail with `-h` flag
### Required
|  Name    | Description |
|----------|----------|
|  model    | name of the model to be tested  |
### Optional
| Flag | Name | Description |
|----------|----------|----------|
| -f    | file     | Path to the test file directory     |
| -o    | output    | Path to the output file directory  |

