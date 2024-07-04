# AnACor/configure.py
import os
import subprocess
import re

# Dictionary mapping GPU names to their SM numbers
GPU_SM_MAPPING = {
    # Kepler
    'generic kepler': '30',
    'geforce 700': '30',
    'gt 730': '30',
    'tesla k40': '35',
    'tesla k80': '37',
    # Maxwell
    'tesla m': '50',
    'quadro m': '50',
    'quadro m6000': '52',
    'geforce 900': '52',
    'gtx 970': '52',
    'gtx 980': '52',
    'gtx titan x': '52',
    'tegra x1': '53',
    'drive cx': '53',
    'drive px': '53',
    'jetson nano': '53',
    # Pascal
    'quadro gp100': '60',
    'tesla p100': '60',
    'dgx-1': '60',
    'gtx 1080': '61',
    'gtx 1070': '61',
    'gtx 1060': '61',
    'gtx 1050': '61',
    'gtx 1030': '61',
    'gt 1010': '61',
    'titan xp': '61',
    'tesla p40': '61',
    'tesla p4': '61',
    'discrete gpu': '61',
    'tegra tx2': '62',
    # Volta
    'dgx-1 with volta': '70',
    'tesla v100': '70',
    'gtx 1180': '70',
    'titan v': '70',
    'quadro gv100': '70',
    'jetson agx xavier': '72',
    'drive agx pegasus': '72',
    'xavier nx': '72',
    # Turing
    'gtx 1660 ti': '75',
    'rtx 2060': '75',
    'rtx 2070': '75',
    'rtx 2080': '75',
    'titan rtx': '75',
    'quadro rtx 4000': '75',
    'quadro rtx 5000': '75',
    'quadro rtx 6000': '75',
    'quadro rtx 8000': '75',
    'quadro t1000': '75',
    'quadro t2000': '75',
    'tesla t4': '75',
    # Ampere
    'a100': '80',
    'dgx a100': '80',
    'rtx 3080': '86',
    'rtx 3090': '86',
    'a2000': '86',
    'a3000': '86',
    'rtx a4000': '86',
    'a5000': '86',
    'a6000': '86',
    'a40': '86',
    'rtx 3060': '86',
    'rtx 3070': '86',
    'rtx 3050': '86',
    'rtx a10': '86',
    'rtx a16': '86',
    'rtx a40': '86',
    'a2 tensor core gpu': '86',
    'a800 40gb': '86',
    'jetson agx orin': '87',
    'drive agx orin': '87',
    # Ada Lovelace
    'rtx 4090': '89',
    'rtx 4080': '89',
    'rtx 6000 ada': '89',
    'tesla l40': '89',
    'l40s ada': '89',
    'l4 ada': '89',
    # Hopper
    'h100': '90',
    'gh100': '90',
    'h200': '90',
    # Blackwell
    'b100': '100',
    'gb100': '100',
    'b200': '100',
    'gb202': '100',
    'gb203': '100',
    'gb205': '100',
    'gb206': '100',
    'gb207': '100',
    'geforce rtx 5090': '100',
    'rtx 5080': '100',
    'b40': '100'
}

def normalize_gpu_name(gpu_name):
    # Normalize the GPU name to match the keys in the dictionary
    gpu_name = gpu_name.replace('NVIDIA', '').strip().lower()
    gpu_name = re.sub(r'\s+', ' ', gpu_name)
    return gpu_name

def get_gpu_model():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_name', '--format=csv,noheader'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError("nvidia-smi command failed")
        print(result.stdout)
        gpu_name = result.stdout.strip().lower()
        normalized_gpu_name = normalize_gpu_name(gpu_name)
        
        for key in GPU_SM_MAPPING:
            if key in normalized_gpu_name:
                sm_number = GPU_SM_MAPPING[key]
                return gpu_name, sm_number
        
        raise RuntimeError("Could not find SM number for GPU model. Probably not supported by AnACor.")
    except Exception as e:
        print(f"Error detecting GPU model: {e}")
        return None, None

def configure():
    gpu_model, sm_number = get_gpu_model()
    if not gpu_model:
        raise RuntimeError("Failed to detect GPU model")
    print(f"GPU model {gpu_model} is found, compiling CUDA based on this Type with SM {sm_number}")
    if not sm_number:
        raise RuntimeError(f"SM number for GPU model {gpu_model} not found")
    abs_path = os.path.abspath(os.path.dirname(__file__))
    os.chdir(os.path.join(abs_path,'./src'))
    subprocess.check_call(['make', f'SM={sm_number}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.chdir('../../')

if __name__ == '__main__':
    configure()
