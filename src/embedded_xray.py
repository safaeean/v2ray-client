import base64
import tempfile
import os
import stat

def extract_xray_to_tmp():
    # Read xray binary as bytes
    data_path = os.path.join(os.path.dirname(__file__), 'assets', 'xray')
    with open(data_path, 'rb') as f:
        binary_data = f.read()

    # Save to temp file
    tmp_fd, tmp_path = tempfile.mkstemp()
    os.write(tmp_fd, binary_data)
    os.close(tmp_fd)

    # Make it executable
    os.chmod(tmp_path, stat.S_IRWXU)

    return tmp_path
