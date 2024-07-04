import argparse
import subprocess
import json
import os
import pdb
import yaml
import sys

parent_dir =os.path.dirname( os.path.abspath(__file__))
sys.path.append(parent_dir)
from anacor_logging import setup_logger
try:
    from AnACor.preprocess_lite import create_save_dir,preprocess_dial_lite
except:
    from preprocess_lite import create_save_dir,preprocess_dial_lite

def str2bool ( v ) :
    if isinstance( v , bool ) :
        return v
    if v.lower( ) in ('yes' , 'true' , 't' , 'y' , '1') :
        return True
    elif v.lower( ) in ('no' , 'false' , 'f' , 'n' , '0') :
        return False
    else :
        raise argparse.ArgumentTypeError( 'Boolean value expected.' )

import os
import requests
import json




# def preprocess_dial_lite ( args , save_dir ) :
#     # from dials.util.filter_reflections import *
#     import subprocess
#     print('preprocessing dials data.....')
#     with open( os.path.join( save_dir , "preprocess_script.sh" ) , "w" ) as f :
#         f.write( "#!/bin/bash \n" )
#         f.write( "{} \n".format( args.dials_dependancy ) )
#         f.write( "expt_pth=\'{}\' \n".format( args.expt_path) )
#         f.write( "refl_pth=\'{}\' \n".format( args.refl_path ) )
#         f.write( "store_dir=\'{}\' \n".format( save_dir ) )
#         f.write( "dataset={} \n".format( args.dataset ) )
#         f.write( "full={} \n".format( args.full_reflection ) )
#         f.write( "dials.python {}  --dataset ${{dataset}} " 
#                  " --refl-filename ${{refl_pth}} " 
#                  "--expt-filename ${{expt_pth}} --full ${{full}} "
#                  "--save-dir ${{store_dir}}\n".format(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lite/refl_2_json.py')) )

#     subprocess.run( ["chmod" , "+x" , os.path.join( save_dir , "preprocess_script.sh" )] )
#     try :
#         result = subprocess.run( ["bash" , os.path.join( save_dir , "preprocess_script.sh" )] , check = True ,
#                                  capture_output = True )
#         print( result.stdout.decode( ) )

#     except subprocess.CalledProcessError as e :
#         print( "Error: " , e )

def set_parser ( ) :
    parser = argparse.ArgumentParser( description = "analytical absorption correction data preprocessing" )
    parser.add_argument(
        "--input-file" ,
        type = str ,
        default='default_mpprocess_input.yaml',
        help = "the path of the input file of all the flags" ,
    )

    directory = os.getcwd( )
    global ar
    ar = parser.parse_args( )

    try:
        with open( ar.input_file , 'r' ) as f :
            config = yaml.safe_load( f )
    except:
        with open( os.path.join(directory,ar.input_file) , 'r' ) as f :
            config = yaml.safe_load( f )


    # # Add an argument for each key in the YAML file
    # for key, value in config.items():
    #     # Check if the key is "auto-sampling"
    #     if key == "auto-sampling":
    #         # If so, overwrite the default value with the value from the YAML file
    #         parser.add_argument(
    #             "--{}".format(key),
    #             type=str2bool,
    #             default=value,
    #             help="pixel size of tomography",
    #         )
    #     else:
    #         # Otherwise, use the default value from the add_argument method
    #         parser.add_argument("--{}".format(key), default=value)

    # Add an argument for each key in the YAML file
    for key , value in config.items( ) :
        parser.add_argument( '--{}'.format( key ) , default = value )

    global args
    args = parser.parse_args( )

    return args

def submit_job_slurm(hour, minute, second, num_cores, save_dir,logger,dataset,user, token,args):
    slurm_api_url = "https://slurm-rest.diamond.ac.uk:8443/slurm/v0.0.38/job/submit"
    headers = {
        "X-SLURM-USER-NAME": user,
        "X-SLURM-USER-TOKEN": token,
        "Content-Type": "application/json",
    }
    # store_dir=args.store_dir
    job_script = os.path.join(save_dir, "mpprocess_script.sh")
    stdout_log = os.path.join(save_dir, "Logging/mp_lite_output.log")
    stderr_log = os.path.join(save_dir, "Logging/mp_lite_error.log")
    makefile=os.path.join(os.path.dirname( os.path.abspath( __file__ )),'src') 
    job_params = {
            "job": {
                "name": f"AnACor_{dataset}",
                "ntasks": 1,
                "nodes": 1,
                "cpus_per_task": num_cores,
                "gres": "gpu:1",
                "partition": "cs05r",  # Adjust this as needed
                "current_working_directory": save_dir,
                "standard_input": "/dev/null",
                "standard_output": stdout_log,
                "standard_error": stderr_log,
                "environment": {
                # "PATH": os.getenv("PATH"),
                    "PATH": "/dls_sw/apps/GPhL/autoPROC/20240123/autoPROC/bin/linux64:/dls_sw/apps/GPhL/autoPROC/20240123/autoPROC/ruby/linux64/bin:/dls_sw/apps/gnuplot/4.6.3/bin:/dls_sw/apps/wxGTK/2.9.2.4/64/bin:/dls_sw/apps/adxv/1.9.13:/dls_sw/apps/dials/dials-v3-18-1/build/bin:/dls_sw/epics/R3.14.12.7/base/bin/linux-x86_64:/dls_sw/epics/R3.14.12.7/extensions/bin/linux-x86_64:/dls_sw/prod/tools/RHEL7-x86_64/defaults/bin:/dls_sw/apps/cuda/12.2.0/bin:/dls_sw/apps/mx/bin:/dls_sw/apps/xdsstat/2013-03-01:/dls_sw/apps/XDS/etc:/dls_sw/apps/XDS/20230630-extra:/dls_sw/apps/XDS/20230630:/dls_sw/apps/ccp4/8.0.019/arp_warp_8.0/bin/bin-x86_64-Linux:/dls_sw/apps/ccp4/8.0.019/ccp4-8.0/etc:/dls_sw/apps/ccp4/8.0.019/ccp4-8.0/bin:/dls_sw/apps/python/anaconda/4.6.14/64/envs/r-3.6/bin:/usr/share/Modules/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/cfengine/bin:/home/i23user/bin:/home/i23user/bin/XZuiichi:/home/i23user/bin/Sagasu:/home/i23user/bin/Sagasu:/home/i23user/bin:/home/i23user/bin/XZuiichi:/home/i23user/bin/Sagasu:/home/i23user/bin/Sagasu",
        "LD_LIBRARY_PATH": "/lib/:/lib64/:/usr/local/lib"
                }
            },
            "script": 
                    f"""#!/bin/bash\n 
                    #SBATCH --mem=50GB
                    #module load gcc
                    #module load cuda
                    cd {makefile}
                    make 
                    chmod 755 {job_script}\n  
                    bash {job_script}""" # f"#!/bin/bash\n echo 'testing'"  cd {makefile}  make
            
        }

    if args.gpu:
        job_params["job"]["cpus_per_task"] = 1
        job_params["job"]["gres"] = "gpu:1"
    else:
        job_params["job"]["cpus_per_task"] = num_cores
        job_params["job"].pop("gres", None)
    
    response = requests.post(slurm_api_url, headers=headers, data=json.dumps(job_params))
    
    if response.status_code == 200:
        print("Job submitted successfully. Response: %s", response.json())
        logger.info("Job submitted successfully. Response: %s", response.json())
    else:
        print("Failed to submit job. Status code: %d", response.status_code)
        logger.error("Failed to submit job. Status code: %d", response.status_code)
        print("Response: %s", response.text)
        logger.error("Response: %s", response.text)
    
def get_slurm_token():
    user = os.getenv("USER")
    result = subprocess.run(["ssh", "wilson", "scontrol token lifespan=259200"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    token = None
    for line in output.split("\n"):
        if line.startswith("SLURM_JWT"):
            token = line.split("=")[1].strip()
    return user, token


def detect_file_type(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.json':
        return "JSON"
    else:
        return file_extension.lower()

def main ( ) :
    args = set_parser( )

    ### define the default values of some optional arguments  ###
    
    if hasattr(args, 'openmp'):
            pass
    else:
        args.by_c=False

    if hasattr(args, 'full_iter'):
            pass
    else:
        args.full_iter=0
        
    if hasattr(args, 'full_reflection'):
            pass
    else:
        args.full_reflection=False
        
    if hasattr(args, 'single_c'):
            pass
    else:
        args.single_c=False
    
    if hasattr(args, 'sampling_method'):
            pass
    else:
        args.sampling_method='even'

    if hasattr(args, 'sampling_ratio'):
            pass
    else:
        args.sampling_ratio=0.05

    if hasattr(args, 'gpu'):
            pass
    else:
        args.gpu=True

    if hasattr(args, 'openmp'):
            pass
    else:
        args.openmp=True

    if hasattr(args, 'absorption_map'):
            pass
    else:
        args.absorption_map=False

    # if hasattr(args, 'sampling_num'):
    #         pass
    # else:
    #     args.sampling_num=10000
    if hasattr(args, 'bisection'):
            pass
    else:
        args.bisection=False
#     cluster bash file
    if hasattr(args, 'partial_illumination'):
        args.openmp=False
        args.single_c=False
        args.gpu=False
        args.bisection=False
    else:
        args.partial_illumination=False

    save_dir = os.path.join( args.store_dir , '{}_save_data'.format( args.dataset ) )
    create_save_dir(args)
    if args.model_storepath == 'None' or len(args.model_storepath) < 2 :
        models_list = []
        for file in os.listdir( save_dir ) :
            if args.dataset in file and ".npy" in file :
                models_list.append( file )

        if len( models_list ) == 1 :
            model_storepath = os.path.join( save_dir , models_list[0] )
        elif len( models_list ) == 0 :
            raise RuntimeError(
                "\n There are no 3D models of sample {} in this directory \n  Please create one by command python setup.py \n".format(
                    args.dataset ) )
        else :
            raise RuntimeError(
                "\n There are many 3D models of sample {} in this directory \n  Please delete the unwanted models \n".format(
                    args.dataset ) )
    else :
        model_storepath = args.model_storepath
        

        
    for file in os.listdir( save_dir ) :
        if '.json' in file :
            if args.full_reflection:
                if 'expt' in file and 'True' in file :
                    expt_path = os.path.join( save_dir , file )
                if 'refl' in file and 'True' in file:
                    refl_path = os.path.join( save_dir , file )
            else:
                if 'expt' in file :
                    expt_path = os.path.join( save_dir , file )
                if 'refl' in file:
                    refl_path = os.path.join( save_dir , file )
        else:
            expt_path= args.expt_path 
            refl_path= args.refl_path
    py_pth = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , 'main_lite.py' )
    logger = setup_logger(os.path.join(save_dir,'Logging' ,'mpprocess.log'))
    
    if detect_file_type(expt_path) != "JSON" or detect_file_type(refl_path) != "JSON":
        preprocess_dial_lite( args , save_dir,logger )
        for file in os.listdir( save_dir ) :
            if '.json' in file :
                if args.full_reflection:
                    if 'expt' in file and 'True' in file :
                        expt_path = os.path.join( save_dir , file )
                    if 'refl' in file and 'True' in file:
                        refl_path = os.path.join( save_dir , file )
                else:
                    if 'expt' in file :
                        expt_path = os.path.join( save_dir , file )
                    if 'refl' in file:
                        refl_path = os.path.join( save_dir , file )
        
    try :
        with open( expt_path ) as f2 :
            axes_data = json.load( f2 )
        print( f"experimental data is found at {expt_path}... \n" )
        logger.info( f"experimental data is found at {expt_path}... \n" )
        with open( refl_path,'r' ) as f1 :
            data = json.load( f1 )
        print( f"reflection table is found at {refl_path}... \n" )
        logger.info( f"reflection table is found at {refl_path}... \n" )
    except :
        logger.error( 'no reflections or experimental files in JSON format detected'
                                    'please use --refl_path --expt-filename to specify' )
        raise RuntimeError( 'no reflections or experimental files in JSON format detected'
                                    'please use --refl_path --expt-filename to specify' )
        # if args.refl_path is None or args.expt_path is None:
        #     logger.error( 'no reflections or experimental files inputed'
        #                         'please use --refl_path --expt-filename to specify' )
        # else:
        #     try :
        #         with open( args.expt_path ) as f2 :
        #             axes_data = json.load( f2 )
        #         print( "experimental data is given and loaded... \n" )
        #         logger.info( "experimental data is given and loaded... \n" )
        #         with open( args.refl_path ) as f1 :
        #             data = json.load( f1 )
        #         print( "reflection table is given and loaded... \n" )
        #         logger.info( "reflection table is given and loaded... \n" )
        #     except :
        #         logger.error( 'no reflections or experimental files in JSON format detected'
        #                             'please use --refl_path --expt-filename to specify' )
        #         logger.info("converting refl and expt files into JSON files")
        #         from .preprocess_lite import preprocess_dial_lite
        #         preprocess_dial_lite( args , save_dir,logger )
        #         with open( args.refl_path ) as f1 :
        #             data = json.load( f1 )




    with open( os.path.join( save_dir , "mpprocess_script.sh" ) , "w" ) as f :

        f.write( "#!/bin/sh\n" )
        f.write( "{}\n".format( args.dials_dependancy ) )
        # f.write( "source /dls/science/groups/i23/yishun/dials_yishun/dials \n" )
        # f.write("module load python/3.9 \n")
        f.write( "num={}\n".format( args.num_cores ) )
        f.write( "sampling_method={}\n".format( args.sampling_method ) )
        f.write( "dataset={}\n".format( args.dataset ) )
        f.write( "offset={}\n".format( args.offset ) )
        f.write( "crac={}\n".format( args.crac ) )
        f.write( "liac={}\n".format( args.liac ) )
        f.write( "loac={}\n".format( args.loac ) )
        f.write( "buac={}\n".format( args.buac ) )
        f.write( "end={}\n".format( len( data ) ) )
        f.write( "py_file={}\n".format( py_pth ) )
        f.write("partial_illumination={}\n".format(args.partial_illumination))
        f.write( "model_storepath={}\n".format( model_storepath ) )
        f.write( "full_iter={} \n".format( args.full_iter ) )
        f.write( "openmp={} \n".format( args.openmp ) )
        f.write("single_c={} \n".format( args.single_c ))
        f.write("bisection={} \n".format( args.bisection ))
        f.write("gpu={} \n".format( args.gpu ))
        f.write("sampling_ratio={} \n".format( args.sampling_ratio ))
        # f.write("sampling_num={} \n".format( args.sampling_num ))
        f.write("absorption_map={} \n".format( args.absorption_map ))
        try :
            f.write( "refl_pth={}\n".format( refl_path ) )
            f.write( "expt_pth={}\n".format( expt_path ) )
        except :
            f.write( "refl_pth={}\n".format( args.refl_path ) )
            f.write( "expt_pth={}\n".format( args.expt_path ) )
        f.write( "store_dir={}\n".format(args.store_dir  ) )
        f.write( "logging_dir={}\n".format( os.path.join( save_dir , 'Logging' ) ) )
        f.write("set -e \n")
        f.write( f'nohup {sys.executable} -u  ${{py_file}}  --dataset ${{dataset}} '
                 '--loac ${loac} --liac ${liac} --crac ${crac}  --buac ${buac} --offset ${offset} '
                 ' --store-dir ${store_dir} --refl-path ${refl_pth} --expt-path ${expt_pth}  '
                 '--model-storepath ${model_storepath} --full-iteration ${full_iter} --num-workers ${num}  '
                 ' --openmp ${openmp} --single-c ${single_c} '
                 ' --sampling-method ${sampling_method} --gpu ${gpu} --sampling-ratio ${sampling_ratio} '
                    ' --absorption-map ${absorption_map} --bisection ${bisection} --partial-illumination ${partial_illumination} '
                 ' > ${logging_dir}/running_details_${dataset}_${counter}.out\n' )
        f.write( "echo \"${dataset} is finished\" \n" )
        # f.write( "bash dialsprocess_script.sh \n" )
    # f.close( )
        
        if args.post_process is True:
            # with open( os.path.join( save_dir , "dialsprocess_script.sh" ) , "w" ) as f :
                # f.write( "#!/bin/sh\n" )
            dataset = args.dataset
            save_dir = os.path.join( args.store_dir , '{}_save_data'.format( dataset ) )
            result_path = os.path.join( save_dir , 'ResultData' , 'absorption_factors' )
            dials_dir = os.path.join( save_dir , 'ResultData' , 'dials_output' )
            dials_save_name = 'anacor_{}.refl'.format( dataset )
            stackingpy_pth = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , 'utils','stacking.py' )
            intoflexpy_pth = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , 'utils', 'into_flex.py' )
            f.write( "{}\n".format( args.dials_dependancy ) )
            f.write( "\n" )
            f.write(
                "dials.python {} --save-dir {} --dataset {} \n".format( stackingpy_pth , result_path , args.dataset ) )
            f.write( "\n" )
            f.write( "dials.python {0} "
                    "--save-number {1}  --refl-filename {2}  "
                    "--full {3} --with-scaling {4} "
                    "--dataset {5} "
                    "--target-pth {6} --store-dir {7}  \n".format( intoflexpy_pth , args.dataset ,
                                                                    args.refl_path , args.full_reflection ,
                                                                    args.with_scaling , dataset , dials_dir ,
                                                                    args.store_dir
                                                                    ) )
            f.write( "cd {} \n".format( dials_dir ) )
            f.write( "\n" )
            f.write( "dials.scale  {0} {1} "
                    "anomalous={3}  physical.absorption_correction=False physical.analytical_correction=True "
                    "output.reflections=result_{2}_ac.refl  output.html=result_{2}_ac.html "
                    "output{{log={2}_ac_log.log}} output{{unmerged_mtz={2}_unmerged_ac.mtz}} output{{merged_mtz={2}_merged_ac.mtz}} "
                    "\n".format( os.path.join( dials_dir , dials_save_name ) , args.expt_path , dataset,args.anomalous ) )
            f.write( "\n" )
            f.write( "dials.scale  {0} {1}  "
                    "anomalous={3}  physical.absorption_level=high physical.analytical_correction=True "
                    "output.reflections=result_{2}_acsh.refl  output.html=result_{2}_acsh.html "
                    "output{{log={2}_acsh_log.log}}  output{{unmerged_mtz={2}_unmerged_acsh.mtz}} "
                    "output{{merged_mtz={2}_merged_acsh.mtz}} "
                    "\n".format( os.path.join( dials_dir , dials_save_name ) , args.expt_path , dataset,args.anomalous ) )
            f.write( "{} \n".format( args.mtz2sca_dependancy ) )
            f.write( "mtz2sca {}_merged_acsh.mtz   \n".format( dataset ) )
            f.write( "mtz2sca {}_merged_ac.mtz   \n".format( dataset ) )
        f.write("set +e \n")
        f.close( )
        """new slurm cluster command"""
    
        user, token = get_slurm_token()
        submit_job_slurm(args.hour, args.minute, args.second, args.num_cores, save_dir,logger=logger,dataset=args.dataset,user=user, token=token,args=args)
        
        """new slurm cluster command"""

"""old sge cluster command"""
    # cluster_command = "qsub -S /bin/sh -l h_rt={0}:{1}:{2} -pe smp {3}  -o {5} -e {6} {4}".format(
    #     str( args.hour ).zfill( 2 ) ,
    #     str( args.minute ).zfill( 2 ) ,
    #     str( args.second ).zfill( 2 ) ,
    #     args.num_cores ,
    #     os.path.join( save_dir , "mpprocess_script.sh" ) ,
    #     os.path.join( save_dir , "Logging/mp_lite_output.log" ) ,
    #     os.path.join( save_dir , "Logging/mp_lite_error.log" ) )

    # logger.info( "submitting job to cluster..." )
    # if args.hpc_dependancies is not None :
    #     all_command = [args.hpc_dependancies] + [cluster_command]
    # else :
    #     all_command = cluster_command
    # command = ""
    # for c in all_command :
    #     command += c + " " + ";" + " "

    # result = subprocess.run( command , shell = True , stdout = subprocess.PIPE , stderr = subprocess.PIPE )




    # result = subprocess.run( ["qsub ","-S","","","h_rt={}:{}:{}".format(args.time[0],args.time[1],args.time[2]),
    #                           "-pe","smp", "{}".format(args.num_cores),
    #                           os.path.join(save_dir,"mpprocess_script.sh"),
    #                           "-o",os.path.join(save_dir,"Logging"),
    #                           "-e",os.path.join(save_dir,"Logging"),
    #                           ],
    #                          shell = True , stdout = subprocess.PIPE , stderr = subprocess.PIPE )
    # print( result.returncode )
    # # pdb.set_trace( )
    # # logger.info( result.returncode  )
    # # logger.info( result.stdout.decode( ) )
    # # logger.info( result.stderr.decode( ) )
    # print( result.stdout.decode( ) )
    
    # print( result.stderr.decode( ) )
"""old sge cluster command"""

if __name__ == '__main__' :
    main( )