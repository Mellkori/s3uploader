# S3 Upload Script

Python script for uploading files to an Amazon S3 bucket. It supports uploading multiple files, specifying an upload directory, and filtering files based on file patterns.
Main focus of this project is for usage in CI/CD pipelines and it is published like PYPI package to https://pypi.org/project/s3uploader-ci-cd/.

## Requirements

- Python 3.9 or higher
- `boto3` package for AWS S3 communication
- `python-dotenv` package for loading environment variables from a .env file

## Installation

Install the required packages using pip:

```powershell
pip install s3uploader-ci-cd
```
# Usage

* Set up your AWS credentials like enviroment variables:
```powershell
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```
Replace your_access_key_id and your_secret_access_key with your actual AWS access key and secret key.

* Run the script with the required command-line arguments:
 ```powershell
python s3upload.py --bucket_name BUCKET_NAME --upload_prefix UPLOAD_PREFIX --source_dir SOURCE_DIR --include INCLUDE_PATTERN
```
Replace BUCKET_NAME with the name of your S3 bucket, region,  UPLOAD_PREFIX with the desired prefix for the uploaded files, SOURCE_DIR with the relative path of the directory containing the files for upload, and INCLUDE_PATTERN with a comma-separated list of file patterns to include in the upload.
 ```powershell
python s3upload.py --bucket_name my-bucket -- region my_region --upload_prefix my-prefix --source_dir my-files --include "*.txt,*.pdf"
```
* This command will upload all .txt and .pdf files from the my-files directory to the my-bucket S3 bucket with the my-prefix prefix.

## Gitlab CI/CD pipeline

* .gitlab-ci.yml

```yaml
publish-to-s3:
  stage: publish
  tags:
    - docker-linux
  image: python:3.11
  before_script:
    # Set the environment variables for AWS credentials
    - export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    - export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    - pip install --upgrade s3uploader
  script:
    - python3 -m s3uploader --bucket_name bucket_name --source_dir src --include file.json --upload_prefix test/my_path
```

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

## Development

Documentation about developement setup for this project [CONTRIBUTING](CONTRIBUTING.md).