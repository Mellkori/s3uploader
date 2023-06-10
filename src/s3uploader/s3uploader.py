import logging
import sys
import boto3
import argparse
import pathlib
import os
import dotenv
import fnmatch

# Define the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def separate_arguments(string : str) -> list[str] :
    """
    Converts a comma-separated string into a list of strings.

    Args:
        string (str): A comma-separated string.

    Returns:
        list[str]: A list of strings obtained by splitting the input string by commas.
    """
    if ',' in string:
        return [s.strip() for s in string.split(',') if s.strip()]
    else:
        return [string]

def parse_args(sys_args):
    """
    Parses command-line arguments for the script.

    Args:
        sys_args (list[str]): Command-line arguments passed to the script.

    Returns:
        argparse.Namespace: An object containing the parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Upload files to an S3 bucket.')
    parser.add_argument('--bucket_name', required=True, help='the name of the S3 bucket')
    parser.add_argument('--region', default='eu-west-1', help='region')
    parser.add_argument('--upload_prefix', default='', type=str, help='prefix which will be used for uploading to S3 bucket')
    parser.add_argument('--upload_prefix_config_file', default='', type=str, help='prefix will be loaded from config file (default: output_path.txt)')
    parser.add_argument('--source_dir', type=str, default='.', help='the relative path of the directory containing the files for upload (default: dist/)')
    parser.add_argument('--include', default='*', type=separate_arguments, help='the file pattern to include in the upload (default: dist/*)')
    parser.add_argument('--exclude', default='', type=separate_arguments, help='the file pattern to exclude from the upload (default: empty list)')
    args = parser.parse_args()
    return args

def upload_file(s3, bucket_name :str, file_path : str, key : str) -> None:
    """
    Uploads a file to an AWS S3 bucket using the regular upload method.

    Args:
        bucket_name (str): The name of the S3 bucket to upload the file to.
        file_path (str): The local file path of the file to upload.
        key (str): The S3 object key to use for the uploaded file.
    """
    s3.upload_file(str(file_path), bucket_name, key)

def upload_files_to_s3(bucket_name : str, region: str, files: list[pathlib.Path], upload_prefix : str, source_path: pathlib.Path) ->None:
    """
    Uploads each file in the given list to an AWS S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket to upload the files to.
        files (list[pathlib.Path]): A list of file paths to upload.
        upload_prefix (str): The S3 object key prefix to use for the uploaded files.
        source_path (pathlib.Path): The path of the directory containing the files for upload.
    """
    dotenv.load_dotenv()
    ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
    SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

    for file_path in files:
        key = (pathlib.Path(upload_prefix).joinpath(file_path.relative_to(source_path))).as_posix()
        logging.info(f'Uploading {file_path} to S3 bucket {bucket_name} with key {key}')
        upload_file(s3, bucket_name, file_path, key)
        logging.info(f'Uploading finished to: https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}&prefix={key}')

def construct_source_path_for_upload (source_dir : str) -> pathlib.Path:
    """
    Constructs the absolute path for the source directory of files to be uploaded.

    Args:
        source_dir (str): The relative path of the directory containing the files for upload.

    Returns:
        pathlib.Path: The absolute path of the directory containing the files for upload.
    """

    return pathlib.Path.cwd().joinpath(source_dir)

def construct_upload_prefix (upload_prefix: str, output_path_config : pathlib.Path) -> str:
    """
    Constructs the final upload prefix for the files in the AWS S3 bucket.

    Args:
        upload_prefix (str): A string representing the upload prefix.
        output_path_config (pathlib.Path): A pathlib.Path object representing the path to the output_path config file.

    Returns:
        str: The final upload prefix for the files in the AWS S3 bucket.
    """
    # we can expect that we will find output path in config file called output_path.txt
    output_path_config = pathlib.Path.cwd().joinpath(output_path_config)

    if upload_prefix:
        return upload_prefix
    elif output_path_config.is_file():
        logging.info(f'Loading upload prefix from config file: {output_path_config}')
        return output_path_config.read_text(encoding="utf-8")
    else:
        return ''

def is_excluded(file_path: pathlib.Path, exclude_patterns: list[str]) -> bool:
    """
    Determines whether a given file path should be excluded from the upload based on a list of exclude patterns.

    Args:
        file_path (pathlib.Path): The file path to check for exclusion.
        exclude_patterns (list[str]): A list of file patterns to exclude from the upload.

    Returns:
        bool: True if the file should be excluded, False otherwise.
    """
    # Iterate over each exclusion pattern
    for pattern in exclude_patterns:
        # Check if the file path matches the exclusion pattern
        if fnmatch.fnmatch(file_path, pattern):
            return True
        # Check if the relative path (from the file path's parent) matches the exclusion pattern
        # This helps handle exclusion patterns with subdirectories correctly
        elif fnmatch.fnmatch(file_path.relative_to(file_path.parent), pattern):
            return True
        # Check if the file path matches the exclusion pattern with ** wildcard for any number of subdirectories
        elif fnmatch.fnmatch(file_path, f"**/{pattern}"):
            return True
    # If none of the exclusion patterns match, return False (the file is not excluded)
    return False

def get_files_matching_pattern(source_path: pathlib.Path, pattern: str, exclude_patterns: list[str]) -> set[pathlib.Path]:
    """
    Retrieves a set of files in the source directory that match a given pattern.

    Args:
        source_path (pathlib.Path): The path of the directory containing the files for upload.
        pattern (str): The file pattern to match.
        exclude_patterns (list[str]): A list of file patterns to exclude from the upload.

    Returns:
        set[pathlib.Path]: A set of file paths that match the given pattern.
    """
    files = set()
    logging.info(f'Searching for files to upload in {source_path} ...')
    for file_path in source_path.rglob(pattern):
        if file_path.is_file() and not is_excluded(file_path, exclude_patterns):
            logging.info(f'File complies with include pattern: {file_path}.')
            files.add(file_path)
    return files

# Define the function to get the list of files to upload
def get_files_to_upload(source_path : pathlib.Path, include_patterns : list[str], exclude_patterns: list[str]) -> set[pathlib.Path]:
    """
    Retrieves a set of files in the source directory that match the include patterns.

    Args:
        source_path (pathlib.Path): The path of the directory containing the files for upload.
        include_patterns (list[str]): A list of file patterns to include in the upload.
        exclude_patterns (list[str]): A list of file patterns to exclude from the upload.

    Returns:
        set[pathlib.Path]: A set of file paths that match the include patterns.
    """

    files = set()
    for include_pattern in include_patterns:
        files.update(get_files_matching_pattern(source_path, include_pattern, exclude_patterns))
    logging.info(f'Found {len(files)} files to upload.')
    return files

def main(bucket_name : str, region : str, upload_prefix : str, upload_prefix_config_file : str, source_dir: str, include_pattern : str, exclude_pattern : str) -> None:
    """
    Main function that uploads files to an AWS S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket to upload the files to.
        upload_prefix (str): The S3 object key prefix to use for the uploaded files.
        upload_prefix_config_file (str): The path to the output_path config file containing the upload prefix.
        source_dir (str): The relative path of the directory containing the files for upload.
        include_pattern (str): A comma-separated string of file patterns to include in the upload.
    """
    logging.info('Starting S3 upload')
    logging.info(f'Bucket name: {bucket_name}')
    logging.info(f'Region: {region}')
    logging.info(f'source directory for upload: {source_dir}')
    logging.info(f'Include pattern: {include_pattern}')
    logging.info(f'Exclude pattern: {exclude_pattern}')
    # Get path to data for upload
    source_path : pathlib.Path = construct_source_path_for_upload(source_dir)
    # Get the list of files to upload
    files : list = get_files_to_upload(source_path, include_pattern, exclude_pattern)
    # create upload prefix
    final_upload_prefix : str = construct_upload_prefix(upload_prefix, upload_prefix_config_file)
    logging.info(f'Upload directory(prefix): {final_upload_prefix}')
    # Upload files
    upload_files_to_s3(bucket_name, region, files, final_upload_prefix, source_path)
    logging.info(f'Finished uploading all {len(files)} files to S3. https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}&prefix={final_upload_prefix}/')

if __name__ == "__main__":
    parsed_args = parse_args(sys.argv[1:])
    main(parsed_args.bucket_name, parsed_args.region, parsed_args.upload_prefix, parsed_args.upload_prefix_config_file, parsed_args.source_dir, parsed_args.include, parsed_args.exclude)