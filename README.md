# AnACor2.0
***
AnACor2.0: A GPU-accelerated open-source software package for analytical absorption corrections in X-ray crystallography.


### Install
You can either create a new environment 
```
conda create --name anacor python==3.8
```
or install in your currnet environment
```
git clone https://github.com/yishunlu-222/AnACor2.0.git
cd AnACor2.0; pip install -e .
```
This Software is already installed in Beamline I23 Diamond Light Source. If you are using this at I23, go straight to [Scaling Step](#2-scaling)
### Requirements

The following packages are required by AnACor2.0. All testing has used the following versions, but later versions should also work.

	python_version >= 3.8
	opencv-python>=4.6.0
	scikit-image<=0.19.0
	numba==0.59.0
	imageio==2.33.1
	scipy==1.10.1
	numpy==1.24.4
	PyYAML==6.0.1l

Before running AnACor2.0, please make sure DIALS is installed https://dials.github.io/installation.html. AnACor needs to combine DIALS to finish data-scaling.
 
## How to run
Firstly, input files are needed to be created:
```
anacor.init
```
This will create *default_preprocess_input.yaml* and *default_mpprocess_input.yaml* for your to enter parameters.
#### 1. Preprocessing

- Inputs:
  - DIALS reflection and experiment files
  - Segmentation images directory 
  - Raw flat-fielded corrected image directory
  - DIALS dependancy (e.g. source /path/to/installation/directory/dials-dev/dials_env.sh) 
- Outputs:
  - human-readable json files of DIALS reflection and experiment files
  - 3D segmentation model in .npy (numpy)
  - absorption coefficient 
  
Then, if you don't have the 3D models, in the same directory, you edit the default_preprocess_input.yaml run (an example input file is in ./img):
```
anacor.preprocess 
```
#### 2. Scaling

If you are running this software in **Diamond Light Source I23**, this is easy. You need to edit the default_mpprocess_input.yaml to change configuration of submission to the cluster, such as number of cores, running time and so on. Then run:
```
source /dls/science/groups/i23/yishun/dials_317/dials
anacor.mp
```

If you are running on **others or your local machine**, after running ```anacor.mp```, you will have error messages. Then you can go to the directory **XXX_save_data**, there is a bash file **mpprocess_script.sh**. You can edit this and change the configuration to run as a normal .bash file. For example:
```
cd XXX_save_data
chmod +x mpprocess_script.sh
srun --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=4G ./mpprocess_script.sh
```

#### 3. Results and logs

Under the directory **XXX_save_data**, there are ResultData and Logging to store results of logs.

## Test dataset

Here is a test dataset of Thaumatin of PDBID 1RQW, whose diffraction experiment was done in I23, Diamond Light Source:

https://drive.google.com/drive/folders/1wYZ3YONkAUyEGDyYYMkNoh5IY-6IghNx?usp=sharing

It contains the Dials reflection and experiment files with it 3D segmented model, so you run Step 2. scaling directly after `anacor.init`. With assigning the data paths and these absorption coefficients below, the I/sigma and R factors improve a lot compared to spherical harmonics correction used in Dials.

| Sample    | Crystal | Liquor  | Loop    |
|-----------|---------|---------|---------|
| Thaumatin | 0.01926 | 0.02019 | 0.01864 |

**<span style="font-size:1.5em;">Detailed documented manual is below for more options and parameters.</span>**:

https://yishunlu-222.github.io/anacor.github.io/

