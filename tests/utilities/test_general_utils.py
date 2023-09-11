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
