# tests/conftest.py
import warnings
import pytest
import logging
import os
import glob

def pytest_sessionfinish(session, exitstatus):
    """
    Hook to run after the entire test session finishes.
    Cleans up all .json files in the test directory.
    """
    test_dir = os.path.dirname(__file__) 
    json_files = glob.glob(os.path.join(test_dir, '*.json'))
    for json_file in json_files:
        try:
            os.remove(json_file)
            # print(f"Removed {json_file}")
        except OSError as e:  
            pass
            # print(f"Error removing {json_file}: {e}")
    npy_files = glob.glob(os.path.join(test_dir, '*.npy'))
    for npy_file in npy_files:
        try:
            os.remove(npy_file)
            # print(f"Removed {npy_file}")
        except OSError as e:
            pass
            # print(f"Error removing {npy_file}: {e}")
# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("pytest.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)
def pytest_configure(config):
    warnings.filterwarnings("ignore", category=DeprecationWarning)
