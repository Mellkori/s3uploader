from .s3uploader import main, parse_args

import sys

if __name__ == "__main__":
    parsed_args = parse_args(sys.argv[1:])
    main(parsed_args.bucket_name, parsed_args.region, parsed_args.upload_prefix, parsed_args.upload_prefix_config_file, parsed_args.source_dir, parsed_args.include, parsed_args.exclude)