import tarfile
import io
from capsulecorp.utilities import general_utils


def test_read_tar_from_bytes():
    # Create a tar archive in memory with some test files
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        file_data1 = "Hello, world!".encode('utf-8')
        file_data2 = "Python is awesome.".encode('utf-8')
        file1 = tarfile.TarInfo(name='file1.txt')
        file1.size = len(file_data1)
        file2 = tarfile.TarInfo(name='file2.txt')
        file2.size = len(file_data2)
        tar.addfile(file1, io.BytesIO(file_data1))
        tar.addfile(file2, io.BytesIO(file_data2))
    # Get the byte content of the tar archive
    tar_bytes = tar_stream.getvalue()
    # Call the function to read the tar archive
    result = general_utils.read_tar_from_bytes(tar_bytes)
    # Check that the function correctly reads the files in the tar archive
    assert result['file1.txt'] == 'Hello, world!'
    assert result['file2.txt'] == 'Python is awesome.'


def test_write_dict_to_tar_bytes():
    # Create a dictionary with file names and contents
    file_dict = {
        'file1.txt': 'Hello, world!',
        'file2.txt': 'Python is awesome.'
    }
    # Call the function to write the dictionary to a tar archive
    tar_bytes = general_utils.write_dict_to_tar_bytes(file_dict)
    # Read the tar archive using the read_tar_from_bytes function
    result = general_utils.read_tar_from_bytes(tar_bytes)
    # Check that the function correctly writes the files to the tar archive
    assert result['file1.txt'] == 'Hello, world!'
    assert result['file2.txt'] == 'Python is awesome.'
