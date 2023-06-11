# Development

## Requirements

- Python 3.9 or higher
- `boto3` package for AWS S3 communication
- `python-dotenv` package for loading environment variables from a .env file

### Visual studio solution

- This project is completely created in Visual studio 2022. To make modifications please use s3uploader.sln.
- https://learn.microsoft.com/en-gb/visualstudio/python/debugging-python-in-visual-studio?view=vs-2022

* When you set environment variables in PowerShell, they are only available for the current session and will not be visible in Visual Studio.
* To make these environment variables available in Visual Studio, you can create a .env file and configure Visual Studio to load environment variables from this file.

1. Create a .env file in your project's root directory.
2. Add the environment variables to the .env file:
```powershell
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```
3. Install the python-dotenv package
```python
import os
from dotenv import load_dotenv
load_dotenv()

ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
```
4. Configure Visual Studio to load the environment variables from the .env file:
```
PYTHONWARNINGS=default;PYTHONPATH=.;PYTHONUNBUFFERED=1;PYTHONDONTWRITEBYTECODE=1;PYTHONIOENCODING=UTF-8;AWS_ACCESS_KEY_ID=${env:AWS_ACCESS_KEY_ID};AWS_SECRET_ACCESS_KEY=${env:AWS_SECRET_ACCESS_KEY}
```
This configuration tells Visual Studio to use the environment variables defined in your .env file.
Now, when you run your Python script in Visual Studio, it should be able to access the environment variables you defined in the .env file.

### Command-line Arguments

- `--bucket_name`: The name of the S3 bucket
- `--region`: Region (default: 'eu-west-1')
- `--upload_prefix`: The S3 object key prefix for the uploaded files
- `--upload_prefix_config_file`: The path to the output_path config file containing the upload prefix (default: 'output_path.txt')
- `--source_dir`: The relative path of the directory containing the files for upload (default: 'dist/')
- `--include`: A comma-separated string of file patterns to include in the upload (default: '*')
- `--exclude`: A comma-separated string of file patterns to exclude in the upload (default: '')

### Functions

The script includes the following functions:

- `comma_separated_string(string: str)`: Converts a comma-separated string into a list of strings.
- `parse_args(sys_args)`: Parses command-line arguments for the script.
- `upload_file(bucket_name: str, file_path: str, key: str)`: Uploads a file to an AWS S3 bucket using the regular upload method.
- `get_files_to_upload(source_path: pathlib.Path, include_pattern: list[str])`: Retrieves a list of files in the source directory that match the include patterns.
- `upload_files_to_s3(bucket_name: str, files: list[pathlib.Path], upload_prefix: str, source_path: pathlib.Path)`: Uploads each file in the given list to an AWS S3 bucket.
- `construct_source_path_for_upload(source_dir: str)`: Constructs the absolute path for the source directory of files to be uploaded.
- `construct_upload_prefix(upload_prefix: str, output_path_config: pathlib.Path)`: Constructs the final upload prefix for the files in the AWS S3 bucket.
- `main(bucket_name: str, upload_prefix: str, upload_prefix_config_file: str, source_dir: str, include_pattern: str)`: Main function that uploads files to an AWS S3 bucket.

## Unit Tests

Run the unit tests by executing the following command in the project root directory:
```python
python -m unittest discover
```
To run a specific test module or test case, use the following command:
```python
python -m unittest <test_module>.<test_case>
```
To run the unit tests and generate a coverage report, use the following command:
```powershell
coverage run -m unittest discover -s test
coverage html
```

### How to build and publish this package

```powershell
python -m pip install --upgrade pip
pip install poetry
poetry build
pip install --upgrade twine
twine upload dist/*
```