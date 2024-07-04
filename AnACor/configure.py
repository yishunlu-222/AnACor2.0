# AnACor/configure.py
import os
import subprocess
import re
import pdb
# Dictionary mapping GPU names to their SM numbers
GPU_SM_MAPPING = {
    # Kepler
    'generickepler': '30',
    'geforce700': '30',
    'gt-730': '30',
    'teslak40': '35',
    'teslak80': '37',
    # Maxwell
    'teslam': '50',
    'quadrom': '50',
    'quadrom6000': '52',
    'geforce900': '52',
    'gtx-970': '52',
    'gtx-980': '52',
    'gtxtitanx': '52',
    'tegrax1': '53',
    'drivcx': '53',
    'drivpx': '53',
    'jetsonnano': '53',
    # Pascal
    'quadrogp100': '60',
    'teslap100': '60',
    'dgx-1': '60',
    'gtx1080': '61',
    'gtx1070': '61',
    'gtx1060': '61',
    'gtx1050': '61',
    'gtx1030': '61',
    'gt1010': '61',
    'titanxp': '61',
    'teslap40': '61',
    'teslap4': '61',
    'discretegpu': '61',
    'tegratx2': '62',
    # Volta
    'dgx-1volta': '70',
    'teslav100': '70',
    'gtx1180': '70',
    'titanv': '70',
    'quadrovg100': '70',
    'jetsonagxxavier': '72',
    'driveagxpegasus': '72',
    'xaviernx': '72',
    # Turing
    'gtx1660ti': '75',
    'rtx2060': '75',
    'rtx2070': '75',
    'rtx2080': '75',
    'titanrtx': '75',
    'quadrortx4000': '75',
    'quadrortx5000': '75',
    'quadrortx6000': '75',
    'quadrortx8000': '75',
    'quadro1000': '75',
    'quadro2000': '75',
    'teslat4': '75',
    # Ampere
    'a100': '80',
    'dgxa100': '80',
    'rtx3080': '86',
    'rtx3090': '86',
    'a2000': '86',
    'a3000': '86',
    'rtxa4000': '86',
    'a5000': '86',
    'a6000': '86',
    'a40': '86',
    'rtx3060': '86',
    'rtx3070': '86',
    'rtx3050': '86',
    'rtxa10': '86',
    'rtxa16': '86',
    'rtxa40': '86',
    'a2tensorcoregpu': '86',
    'a80040gb': '86',
    'jetsonagxorin': '87',
    'driveagxorin': '87',
    # Ada Lovelace
    'rtx4090': '89',
    'rtx4080': '89',
    'rtx6000ada': '89',
    'teslal40': '89',
    'l40sada': '89',
    'l4ada': '89',
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
    'geforcertx5090': '100',
    'rtx5080': '100',
    'b40': '100'
}

def get_gpu_model():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_name', '--format=csv,noheader'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError("nvidia-smi command failed")
        print(result.stdout)
        match =result.stdout.strip().lower().split(' ')[-1]
        for i,key in enumerate(GPU_SM_MAPPING.keys()):
            if match in key:
                sm=GPU_SM_MAPPING[key]
        
        if sm:
            return result.stdout,sm
        else:
            raise RuntimeError("Could not parse nvidia-smi output")
    except Exception as e:
        print(f"Error detecting GPU model: {e}")
        return None,None    

def configure():
    gpu_model,sm_number = get_gpu_model()
    if not gpu_model:
        raise RuntimeError("Failed to detect GPU model")
    
    if not sm_number:
        raise RuntimeError(f"SM number for GPU model {gpu_model} not found")
    
    print(f"GPU model {gpu_model} with SM number {sm_number} is found, compiling CUDA based on this Type")
    # abs_path = os.path.abspath(__file__)
    os.chdir('./src')
    
    subprocess.check_call(['make', f'SM={sm_number}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.chdir('../../')

if __name__ == '__main__':
    configure()
