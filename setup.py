from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.test import test as TestCommand
import subprocess
import os
import re
import sys

def get_gpu_model():
    try:
        result = subprocess.run(['nvidia-smi', '-L'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError("nvidia-smi command failed")
        print(result.stdout)
        # Example output: GPU 0: Tesla V100-SXM2-16GB (UUID: GPU-...)
        match = re.search(r'GPU \d+: ([\w\s-]+)', result.stdout)
        if match:
            return match.group(1).strip().lower().replace(' ', '')
        else:
            raise RuntimeError("Could not parse nvidia-smi output")
    except Exception as e:
        print(f"Error detecting GPU model: {e}")
        return None
 
class CustomBuild(build_ext):
    def run(self):
        gpu_model = get_gpu_model()
        if not gpu_model:
            raise RuntimeError("Failed to detect GPU model")
        print(f"GPU model {gpu_model} is found, compiling CUDA based on this Type")
        gpu_model.replace('nvidia','')
        # Change to the directory containing the Makefile
        os.chdir('./AnACor/src')
        # import pdb
        # pdb.set_trace() 
        # Run the make command with the detected GPU model
        subprocess.check_call(['make', f'ARCH={gpu_model}'])
        # Return to the original directory
        os.chdir('../../')
        super().run()

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args.split())
        sys.exit(errno)

setup(
    name='AnACor',
    version='2.0',
    packages=find_packages(),
    cmdclass={
        'build_ext': CustomBuild,
    },
    description='AnACor for analytical absorption correction by tomography reconstruction',
    author='Yishun Lu',
    author_email='yishun.lu@eng.ox.ac.uk, wes.armour@oerc.ox.ac.uk',
    entry_points={
        'console_scripts': [
            'anacor.preprocess = AnACor.preprocess_lite:main',
            'anacor.main = AnACor.main_lite:main',
            #  'anacor.postprocess = AnACor.postprocess:main',
            'anacor.preprocess_lite = AnACor.preprocess_lite:main',
            'anacor.main_lite = AnACor.main_lite:main',
            'anacor.mp_lite = AnACor.mp_lite:main',
            'anacor.mp = AnACor.mp_lite:main',
            'anacor.postprocess_lite = AnACor.postprocess_lite:main',
            'anacor.postprocess = AnACor.postprocess_lite:main',
            'anacor.init = AnACor.initialization:main',
        ],
    },
    install_requires=[
        'importlib-metadata; python_version >= "3.8"',
        'opencv-python>=4.6.0',
        'scikit-image<=0.19.0',
        'scikit-learn<=1.3.2',
        'numba',
        'imagecodecs',
        'PyYAML',
        'matplotlib',
        'tqdm',
        'requests',
        'scipy',
        'pytest',
        'pytest-order',
    ],
    tests_require=['pytest'],
)
