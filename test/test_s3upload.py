import unittest
import pathlib
import shutil
import argparse
import tempfile
from unittest.mock import MagicMock, patch, Mock
from src.s3uploader.s3uploader import upload_files_to_s3, get_files_to_upload, upload_file, separate_arguments, parse_args, construct_upload_prefix, is_excluded, get_files_matching_pattern

class TestConstructUploadPrefix(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to test the function
        self.temp_dir = pathlib.Path('./temp_dir')
        self.temp_dir.mkdir()
        # Create a temporary output_path.txt file
        self.output_path_file = self.temp_dir.joinpath('output.txt')
        self.output_path_file.write_text('test_output_path', encoding='utf-8')

    def tearDown(self):
        # Clean up the temporary directory and files
        self.output_path_file.unlink()
        self.temp_dir.rmdir()

    def test_construct_upload_prefix_valid_prefix(self):
        # Call the function with the temporary directory path
        # act
        result = construct_upload_prefix('support', '')
        # Check if the function returns the correct output path
        # assert
        self.assertEqual(result, 'support')

    def test_construct_upload_prefix_empty_prefix_valid_config(self):
        # Call the function with the temporary directory path
        # act
        result = construct_upload_prefix('', 'temp_dir/output.txt')
        # Check if the function returns the correct output path
        # assert
        self.assertEqual(result, 'test_output_path')

    def test_construct_upload_prefix_empty_prefix_empty_config(self):
        # Call the function with the temporary directory path
        # act
        result = construct_upload_prefix('', '')
        # Check if the function returns the correct output path
        # assert
        self.assertEqual(result, '')

    def test_construct_upload_prefix_non_empty_prefix_non_empty_config(self):
        # Call the function with a non-empty prefix and a non-empty config file path
        # act
        result = construct_upload_prefix('my-prefix', 'temp_dir/output.txt')
        # Check if the function returns the non-empty prefix when both prefix and config file path are given
        # assert
        self.assertEqual(result, 'my-prefix')

class TestS3Upload(unittest.TestCase):

    @patch('src.s3uploader.s3uploader.boto3.client')
    def test_upload_file(self, mock_client):
        # arrange
        mock_upload = MagicMock()
        mock_client.return_value.upload_file = mock_upload
        bucket_name = 'test-bucket'
        file_path = '/path/to/file'
        key = 'path/to/key'
        # act
        upload_file(mock_client.return_value, bucket_name, file_path, key)
        # assert
        mock_upload.assert_called_once_with(file_path, bucket_name, key)

    @patch('src.s3uploader.s3uploader.boto3.client')
    def test_upload_file_error(self, mock_client):
        # tests for error scenario when the boto3 client raises an exception during the file upload.
        # arrange
        mock_client.return_value.upload_file.side_effect = Exception('Upload failed')
        bucket_name = 'test-bucket'
        file_path = '/path/to/file'
        key = 'path/to/key'
        # act
        with self.assertRaises(Exception, msg='Upload failed'):
            upload_file(bucket_name, file_path, key)

class TestSeparateArguments(unittest.TestCase):

    def test_separate_arguments(self):
        # arrange
        parameters = "1.txt,2.txt"
        expected_result = ['1.txt','2.txt']
        # act
        result = separate_arguments(parameters)
        self.assertEqual(result, expected_result)

    def test_separate_arguments_single_string(self):
        # arrange
        parameters = ["1.txt"]
        expected_result = ["1.txt"]
        # act
        result = separate_arguments(parameters)
        self.assertEqual(parameters, expected_result)

    def test_separate_arguments_empty_string(self):
        # arrange
        parameters = ""
        expected_result = ['']
        # act
        result = separate_arguments(parameters)
        self.assertEqual(result, expected_result)

    def test_separate_arguments_extra_commas(self):
        # arrange
        parameters = "1.txt,,2.txt,"
        expected_result = ['1.txt', '2.txt']
        # act
        result = separate_arguments(parameters)
        self.assertEqual(result, expected_result)

    def test_separate_arguments_spaces(self):
        # arrange
        parameters = " 1.txt , 2.txt "
        expected_result = ['1.txt', '2.txt']
        # act
        result = separate_arguments(parameters)
        self.assertEqual(result, expected_result)

class TestIsExcluded(unittest.TestCase):

    def test_no_exclude_patterns(self):
        # Test that a file is not excluded when no exclude patterns are given.
        # arrange
        file_path = pathlib.Path("test_file.txt")
        exclude_patterns = []
        # act
        result = is_excluded(file_path, exclude_patterns)
        # assert
        self.assertFalse(result, "File should not be excluded when no exclude patterns are given.")

    def test_exclude_pattern_matches(self):
        # Test that a file is excluded when the exclude pattern matches the file path.
        # arrange
        file_path = pathlib.Path("test_file.txt")
        exclude_patterns = ["*.txt"]
        # act
        result = is_excluded(file_path, exclude_patterns)
        # assert
        self.assertTrue(result, "File should be excluded when the exclude pattern matches.")

    def test_exclude_pattern_does_not_match(self):
        # Test that a file is not excluded when the exclude pattern does not match the file path.
        # arrange
        file_path = pathlib.Path("test_file.txt")
        exclude_patterns = ["*.pdf"]
        # act
        result = is_excluded(file_path, exclude_patterns)
        # assert
        self.assertFalse(result, "File should not be excluded when the exclude pattern does not match.")

    def test_multiple_exclude_patterns(self):
        # Test that a file is excluded when at least one of multiple exclude patterns matches the file path.
        # arrange
        file_path = pathlib.Path("test_file.txt")
        exclude_patterns = ["*.pdf", "*.txt"]
         # act
        result = is_excluded(file_path, exclude_patterns)
        # assert
        self.assertTrue(result, "File should be excluded when at least one exclude pattern matches.")

    def test_exclude_pattern_with_subdirectory(self):
        # Test that a file is excluded when the exclude pattern contains a subdirectory and matches the file path.
        # arrange
        file_path = pathlib.Path("subdir/test_file.txt")
        exclude_patterns = ["*dir/*.txt"]
        # act
        result = is_excluded(file_path, exclude_patterns)
        # assert
        self.assertTrue(result, "File should be excluded when the exclude pattern with a subdirectory matches.")

class TestGetFilesMatchingPattern(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary directory with test files for use in the test cases.
        """
        self.tempdir = pathlib.Path(tempfile.mkdtemp())
        (self.tempdir / "subdir").mkdir()
        self.file_paths = [
            self.tempdir / "test_file1.txt",
            self.tempdir / "test_file2.txt",
            self.tempdir / "test_file.pdf",
            self.tempdir / "test_file.md",
            self.tempdir / "subdir" / "test_file.zip"
        ]

        for file_path in self.file_paths:
            with open(file_path, "w") as f:
                f.write("Test content")

    def tearDown(self):
        # Clean up the temporary directory after the test cases are finished.
        shutil.rmtree(self.tempdir)

    def test_files_matching_pattern(self):
        # Test that the function retrieves the correct files matching the given pattern.
        pattern = "*.txt"
        exclude_patterns = []
        # act
        result = get_files_matching_pattern(self.tempdir, pattern, exclude_patterns)
        expected_result = {self.file_paths[0], self.file_paths[1]}
        # assert
        self.assertEqual(result, expected_result, "Should retrieve the correct files matching the given pattern.")

    def test_files_matching_pattern_with_exclusions(self):
        # Test that the function retrieves the correct files matching the given pattern, excluding those that match the exclude patterns.
        pattern = "*"
        exclude_patterns = ["*.txt", "*.md", "*.zip"]
        # act
        result = get_files_matching_pattern(self.tempdir, pattern, exclude_patterns)
        expected_result = {self.file_paths[2]}
        # assert
        self.assertEqual(result, expected_result, "Should retrieve the correct files matching the given pattern, excluding those that match the exclude patterns.")

    def test_files_matching_pattern_with_subdirectory(self):
        # Test that the function retrieves the correct files matching the given pattern with a subdirectory.
        pattern = "subdir/*.zip"
        exclude_patterns = []
        # act
        result = get_files_matching_pattern(self.tempdir, pattern, exclude_patterns)
        expected_result = {self.tempdir / "subdir/test_file.zip"}
        # assert
        self.assertEqual(result, expected_result, "Should retrieve the correct files matching the given pattern with a subdirectory.")

class TestGetFilesToUpload(unittest.TestCase):

    def setUp(self):
        # Set up a temporary directory structure for testing
        self.root_dir = pathlib.Path.cwd().joinpath('test_dir')
        self.root_dir.mkdir()
        (self.root_dir / 'file1.txt').touch()
        (self.root_dir / 'file2.dat').touch()
        subdir = self.root_dir / 'subdir'
        subdir.mkdir()
        (subdir / 'file3.txt').touch()
        (subdir / 'file4.dat').touch()

    def tearDown(self):
        # Clean up the temporary directory structure
        shutil.rmtree(self.root_dir)

    def test_get_files_to_upload_all_files(self):
        # Test the function with an include pattern of '*'
        # act
        result = get_files_to_upload(self.root_dir, {'*'}, '')
        str_result = {(element.relative_to(self.root_dir)) for element in result}
        expected = {pathlib.Path('file1.txt'), pathlib.Path('file2.dat'), pathlib.Path('subdir/file3.txt'), pathlib.Path('subdir/file4.dat')}
        # assert
        self.assertEqual(str_result, expected)

    def test_get_files_to_upload_txt_files(self):
        # Test the function with an include pattern of '*.txt'
        # act
        result = list(get_files_to_upload(self.root_dir, {'*.txt'}, ''))
        str_result = {element.relative_to(self.root_dir) for element in result}
        expected = {pathlib.Path('file1.txt'), pathlib.Path('subdir/file3.txt')}
        # assert
        self.assertEqual(str_result, expected)

    def test_get_files_to_upload_dir(self):
        # Test the function with an include pattern of '*.txt'
        # act
        result = list(get_files_to_upload(self.root_dir, {'subdir/*'}, ''))
        str_result = {element.relative_to(self.root_dir) for element in result}
        expected = {pathlib.Path('subdir/file3.txt'), pathlib.Path('subdir/file4.dat')}
        # assert
        self.assertEqual(str_result, expected)

    def test_get_files_to_upload_with_exclusions(self):
        # Test the function with an include pattern of '*' and an exclude pattern of '*.dat'
        # act
        result = get_files_to_upload(self.root_dir, ['*'], ['*.dat'])
        str_result = {element.relative_to(self.root_dir) for element in result}
        expected = {pathlib.Path('file1.txt'), pathlib.Path('subdir/file3.txt')}
        # assert
        self.assertEqual(str_result, expected)

    def test_get_files_to_upload_empty_directory(self):
        # Test the function with an empty source directory
        # Set up an empty temporary directory
        empty_dir = pathlib.Path.cwd().joinpath('empty_dir')
        empty_dir.mkdir()

        try:
            # act
            result = get_files_to_upload(empty_dir, {'*'}, '')
            str_result = {element.relative_to(empty_dir) for element in result}
            expected = set()
            # assert
            self.assertEqual(str_result, expected)
        finally:
            # Clean up the empty temporary directory
            empty_dir.rmdir()

class TestParseArgs(unittest.TestCase):

    def test_parse_args_with_all_args(self):
        with patch('argparse.ArgumentParser.parse_args', return_value=Mock(bucket_name='my-bucket', upload_prefix='my-path', upload_prefix_config_file='output_path.txt', source_dir='dist', include='*.txt')):
            args = parse_args(['--bucket_name', 'my-bucket', '--upload_prefix', 'my-path', '--upload_prefix_config_file', 'output_path.txt', '--source_dir', 'dist', '--include', '*.txt'])
            self.assertEqual(args.bucket_name, 'my-bucket')

    def test_parse_args_without_optional_args(self):
        with patch('argparse.ArgumentParser.parse_args', return_value=Mock(bucket_name='my-bucket', upload_prefix=None, upload_prefix_config_file=None, source_dir='dist', include='*.txt')):
            args = parse_args(['--bucket_name', 'my-bucket', '--source_dir', 'dist', '--include', '*.txt'])
            self.assertIsNone(args.upload_prefix)
            self.assertIsNone(args.upload_prefix_config_file)

    def test_parse_args_with_only_upload_prefix_config_file(self):
        with patch('argparse.ArgumentParser.parse_args', return_value=Mock(bucket_name='my-bucket', upload_prefix=None, upload_prefix_config_file='output_path.txt', source_dir='dist', include='*.txt')):
            args = parse_args(['--bucket_name', 'my-bucket', '--upload_prefix_config_file', 'output_path.txt', '--source_dir', 'dist', '--include', '*.txt'])
            self.assertIsNone(args.upload_prefix)
            self.assertEqual(args.upload_prefix_config_file, 'output_path.txt')

        def test_parse_args_with_no_args(self):
            with self.assertRaises(SystemExit):
                args = parse_args([])
