# AnACor2.0
***
AnACor2.0: A GPU-accelerated open-source software package for analytical absorption corrections in X-ray crystallography.



## Requirements

#### Minimum Hardware requirements

- RAM: 16 GB or more
- GPU: NVIDIA GPU with Pascal architecture (GTX 1000 series) or newer

#### Software requirements
The following packages are required by AnACor2.0. All testing has used the following versions, but later versions should also work.

	python >= 3.8
	cuda >= 11.6
	*gcc >= 11.0
  	gsl >= 2.7 #GNU Scientific Library (GSL)
  
Before running AnACor2.0, please make sure DIALS (version >=3.16) is installed https://dials.github.io/installation.html. AnACor needs to combine DIALS to finish data-scaling.

*If your GCC is lower than 11, GSL for interpolation is incompatible with AnACor, so you can't use Gridding method.

## Installation

#### How to install

You can either create a new environment 
```
conda create --name anacor python==3.8 # Recommended
or
python -m venv anacor
# Not Recommended, just in case conda doesn't work
# then you need to source /path/anacor/bin/activate to activate
```
Then install AnACor2.0:
```
pip install --upgrade pip
git clone https://github.com/yishunlu-222/AnACor2.0.git
cd AnACor2.0; pip install -e .
```
This Software is already installed in Beamline I23 Diamond Light Source. If you are working at I23, use following command:

```
source /dls/science/groups/i23/yishun/AnACor2.0/anacor2/bin/activate
``` 

#### PyTest
You can run pytest to check if all modules are working properly in your machine by:
```
cd ./AnACor/tests; pytest
```
A `pytest.log file` is generated, capturing the testing results and computational performance for all acceleration models used in simulating crystal models, specifically spherical and cylindrical shapes. The calculated absorption factors are compared with the results from the International Tables for Crystallography (Maslen, 2006), available at [International Tables for Crystallography](https://it.iucr.org/Cb/ch6o3v0001/sec6o3o1/).


## How to run
Firstly, input .yaml files are needed to be created:
```
anacor.init
```
This will create *default_preprocess_input.yaml* and *default_mpprocess_input.yaml* for your to enter parameters.

If you already have the prerequisites mentioned in  [Necessary Inputs for scaling](#2-scaling) for running AnACor2.0 as provided in the Test dataset [Test dataset](#testing), you can **skip** [Preprocessing](#1-preprocessing) and go straight to Scaling step [Scaling](#2-scaling)

#### 1. Preprocessing

Before running preprocessing, you need to edit *default_preprocess_input.yaml* to input necessary parameters/data paths.

- Necessary Inputs for preprocessing:
  - DIALS reflection and experiment files
  - Segmentation images directory 
  - Raw flat-fielded corrected image directory
  - DIALS dependancy (e.g. source /path/to/installation/directory/dials-dev/dials_env.sh) 

  
Then, if you don't have the 3D models, in the same directory, you edit the default_preprocess_input.yaml run (an example input file is in [./img](https://github.com/yishunlu-222/AnACor2.0/tree/main/img)):
```
anacor.preprocess 
```
This will create the outputs that are necessary for running AnACor2.0, and they are stored at **./XXX_save_data**.

#### 2. Scaling
- Necessary Inputs for scaling:
  - human-readable json files of DIALS reflection and experiment files, needed to be loaded in AnACor2.0 at the current stage
  - 3D segmentation model in .npy (numpy)
  - absorption coefficient 
  
The software configures the parameters from default_mpprocess_input.yaml and transfers them into a .bash file so the user can run locally or submit to the cluster.

If you are running this software in **Diamond Light Source I23**, this is easy. You just need to edit the default_mpprocess_input.yaml to change configuration of submission to the cluster, such as number of cores, running time and so on. Then run:
```
source /dls/science/groups/i23/yishun/AnACor2.0/anacor2/bin/activate
anacor.mp
```

If you are running on **others or your local machine**, after running ```anacor.mp```, you will have error messages. Then you can go to the directory **XXX_save_data**, there is a bash file **mpprocess_script.sh**. You can edit this and change the configuration to run as a normal .bash file. For example:


```
cd XXX_save_data
chmod +x mpprocess_script.sh
srun --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=4G --gres=gpu:1 ./mpprocess_script.sh
```



#### 3. Results and logs

Under the directory **XXX_save_data**, there are ResultData and Logging to store results of logs. 

## Testing

Here is a test dataset of Thaumatin of PDBID 1RQW, whose diffraction experiment was done in I23, Diamond Light Source:

https://drive.google.com/drive/folders/1wYZ3YONkAUyEGDyYYMkNoh5IY-6IghNx?usp=sharing

Due to the size of tomography images dataset, it only contains the Dials reflection and experiment files with its 3D segmented model, where the [Preprocessing](#1-preprocessing) is done for you.

Now you can download them and run it in DIALS with spherical harmonics correction to test the integrity of the data:

```
source /path/to/installation/directory/dials-dev/dials_env.sh
dials.scale Thaumatin_test.expt Thaumatin_test.refl anomalous=True absorption_level=high
```

Then, you can start a new *Shell and go straight to run [Scaling](#2-scaling) after `anacor.init`. With assigning the data paths and these absorption coefficients below, the I/sigma and R factors improve a lot compared to the spherical harmonics correction used in DIALS.

| Sample    | Crystal | Liquor  | Loop    |
|-----------|---------|---------|---------|
| Thaumatin | 0.01926 | 0.02019 | 0.01864 |

*DIALS env can have conflict with conda env

**<span style="font-size:1.5em;">Detailed documented manual is below for more options and parameters.</span>**:

https://yishunlu-222.github.io/anacor.github.io/

## Reference

- Maslen, E. N. (2006). International Tables for Crystallography, volume C, chapter 6.3.3, Absorption corrections, pages600–608. 3rd edition.

