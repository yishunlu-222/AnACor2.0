import os
import json
import yaml
import pdb
import numpy as np
import sys
import re

parent_dir =os.path.dirname( os.path.abspath(__file__))
sys.path.append(parent_dir)


from anacor_logging import setup_logger
import argparse
try:
    from AnACor.utils.image_process import Image2Model
    from AnACor.utils.absorption_coefficient import RunAbsorptionCoefficient
    from AnACor.utils.gui import *
except:
        from utils.image_process import Image2Model
        from utils.absorption_coefficient import RunAbsorptionCoefficient
        from utils.gui import *




def str2bool ( v ) :
    if isinstance( v , bool ) :
        return v
    if v.lower( ) in ('yes' , 'true' , 't' , 'y' , '1') :
        return True
    elif v.lower( ) in ('no' , 'false' , 'f' , 'n' , '0') :
        return False
    else :
        raise argparse.ArgumentTypeError( 'Boolean value expected.' )


def set_yaml ( input_file ) :
    parser = argparse.ArgumentParser( description = "analytical absorption correction data preprocessing" )
    with open( input_file , 'r' ) as f :
        config = yaml.safe_load( f )
    for key , value in config.items( ) :
        parser.add_argument( '--{}'.format( key ) , default = value )

    args = parser.parse_args( )

    return args

def set_parser ( ) :

    parser = argparse.ArgumentParser( description = "analytical absorption correction data preprocessing" )
    parser.add_argument(
        "--input-file" ,
        type = str ,
        default='./default_preprocess_input.yaml',
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

    for key , value in config.items( ) :
        parser.add_argument( '--{}'.format( key ) , default = value )


    args = parser.parse_args( )

    return args


# if args.a:
#     if args.b:
#         print("Both arguments are entered")
#     else:
#         print("arg b is required when arg a is entered")
# else:
#     print("arg a is not entered")

def preprocess_dial_lite ( args,refl_path ,expt_path, save_dir,logger ) :
    # from dials.util.filter_reflections import *
    
    if os.path.isfile(expt_path) is False:
        logger.error("The experiment file is not found")
        return None
    if os.path.isfile(refl_path) is False:
        logger.error("The reflection table is not found")
        return None
    import subprocess
    # logger.info( "\npreprocessing dials data.....\n" )
    print('preprocessing dials data.....')
    with open( os.path.join( save_dir , "preprocess_script.sh" ) , "w" ) as f :
        f.write( "#!/bin/bash \n" )
        
        f.write( "expt_pth=\'{}\' \n".format( expt_path) )
        f.write( "refl_pth=\'{}\' \n".format( refl_path ) )
        f.write( "store_dir=\'{}\' \n".format( save_dir ) )
        f.write( "full={} \n".format( args.full_reflection ) )
        f.write( "{} \n".format( args.dials_dependancy ) )
        f.write( "dials.python {} " 
                 " --refl-filename ${{refl_pth}} " 
                 "--expt-filename ${{expt_pth}} --full ${{full}} "
                 "--save-dir ${{store_dir}}\n".format(os.path.join(os.path.dirname(os.path.abspath(__file__)),'utils/refl_2_json.py')) )

    subprocess.run( ["chmod" , "+x" , os.path.join( save_dir , "preprocess_script.sh" )] )
    try :
        result = subprocess.run( ["bash" , os.path.join( save_dir , "preprocess_script.sh" )] , check = True ,
                                 capture_output = True )
        # print( result.stdout.decode( ) )
        logger.info( result.stdout.decode( ) )
    except subprocess.CalledProcessError as e :
        logger.error( "Error: " , e )
        print( "Error: " , e )


def preprocess_dial ( reflections , reflection_path , save_dir , args ) :
    # from dials.util.filter_reflections import *
    from dials.algorithms.scaling.scaler_factory import ScalerFactory

    filename = os.path.basename( reflection_path )

    scaler = ScalerFactory( )
    refls = scaler.filter_bad_reflections( reflections )
    excluded_for_scaling = refls.get_flags( refls.flags.excluded_for_scaling )
    refls.del_selected( excluded_for_scaling )

    filename = "rejected_" + str( args.dataset ) + "_" + filename
    path = os.path.join( save_dir , "reflections" , filename )

    refls.as_file( path )
    return refls

def create_save_dir ( save_dir ) :
    # save_dir = os.path.join( args.store_dir , '{}_save_data'.format( args.dataset ) )
    if os.path.exists( save_dir ) is False :
        os.makedirs( save_dir )
        os.makedirs( os.path.join( save_dir , "Logging" ) )
    result_path = os.path.join( save_dir , 'ResultData' )

    # with open(os.path.join( save_dir , "Logging" , 'preprocess_lite.log') , 'w' ) as f :
    #     # Redirect standard output to the file
    #     sys.stdout = f
    #
    #
    #     sys.stdout = sys.__stdout__


    if os.path.exists( result_path ) is False :
        os.makedirs( os.path.join( save_dir , 'ResultData' ) )
        os.makedirs( os.path.join( result_path , "absorption_factors" ) )
        os.makedirs( os.path.join( result_path , "absorption_coefficient" ) )
        # os.makedirs( os.path.join( result_path , "dials_output" ) )


# if __name__ == "__main__":
def main (input_file=None):
    if input_file is None:
        args = set_parser( )
    else:
        args = set_yaml(input_file)
    
    dataset = args.dataset
    save_dir = os.path.join( args.store_dir , '{}_save_data'.format( args.dataset ) )
    result_path = os.path.join( save_dir , 'ResultData' )




    model_name = './{}_.npy'.format( dataset )
    # segimg_path="D:/lys/studystudy/phd/absorption_correction/dataset/13304_segmentation_labels_tifs/dls/i23" \
    #             "/data/2019/nr23571-5/processing/tomography/recon/13304/avizo/segmentation_labels_tiffs"

    # ModelGenerator = Image2Model(segimg_path , model_name ).run()
    create_save_dir( save_dir )
    save_dir = os.path.join( args.store_dir , '{}_save_data'.format( args.dataset ) )
    global logger
    logger = setup_logger( os.path.join( save_dir , "Logging" , 'preprocess.log') )
    # logger.setLevel( logging.INFO )

    # handler = logging.FileHandler( os.path.join( save_dir , "Logging" , 'preprocess_lite.log') ,
    #                                mode = "w+" , delay=True)
    # handler.setLevel( logging.INFO )

    # formatter = logging.Formatter( '%(asctime)s - %(levelname)s - %(message)s' )
    # handler.setFormatter( formatter )
    # logger.addHandler( handler )
    logger.info( "\nResultData directory is created... \n")
    
    # this process can be passed in the future

    model_path = os.path.join( save_dir , model_name )
    model_storepath = args.model_storepath
    if args.create3D is True :
        ModelGenerator = Image2Model( args.segimg_path , model_path,logger )
        model_storepath = ModelGenerator.run( )

        with open('./default_preprocess_input.yaml', 'r' ) as f0 :
                pre_config = yaml.safe_load( f0 )
        try:
            model_storepath.replace('./','')
        except:
            pass

        pre_config[ 'model_storepath' ] = model_storepath

        with open( './default_preprocess_input.yaml' , 'w' ) as file :
            yaml.dump( pre_config , file, default_flow_style=False, sort_keys=False, indent=4)
            
    coe_list=[0,0,0,0]
    logger.info( "\n3D model file is already created... \n" )
    if args.cal_coefficient is True :
        
        if args.model_storepath is not None and args.model_storepath.isspace() is not True\
                and args.model_storepath !='' :
            pass
        else:
            models_list = []
            for file in os.listdir(save_dir ):
                  if str(dataset) in file and ".npy" in file:
                      models_list.append(file)

            try:
                model_storepath = os.path.join( save_dir, models_list[0] )
            except:
                logger.error("The 3D model is not defined or run by create3D by this program")
                raise RuntimeError( "The 3D model is not defined or run by create3D by this program" )
        try:
            coefficient_viewing= args.coefficient_viewing
        except:
            coefficient_viewing=0

        if hasattr(args, 'coe_li'):
            pass
        else:
            args.coe_li = 0.0
        if hasattr(args, 'coe_lo'):
            pass
        else:
            args.coe_lo = 0.0
        if hasattr(args, 'coe_cr'):
            pass
        else:
            args.coe_cr = 0.0
        if hasattr(args, 'coe_bu'):
            pass
        else:
            args.coe_bu = 0.0
        if hasattr(args, 'abs_base_cls'):
            pass
        else:
            args.abs_base_cls = 'li'
        if hasattr(args, 'crop'): # '20,:,:,:' in I23
            args.crop = list(args.crop)
        else:
            args.crop = None
        if hasattr(args, 'padding'):
            args.padding = list(args.padding)
        else:
            args.padding = None
        if hasattr(args, 'kernel_square'):
            
            args.kernel_square = tuple(args.kernel_square)
            print(f"kernel square for morphological transformation is {args.kernel_square}")
        else:
            args.kernel_square = (5 , 5) 
        if hasattr(args, 'yx_shift'):
            
            args.yx_shift = tuple(args.yx_shift)
            print(f"kernel square for morphological transformation is {args.yx_shift}")
        else:
            args.yx_shift = [0,0]
        if hasattr(args, 'GUIselectFiles'):
            args.GUIselectFiles = str2bool(args.GUIselectFiles)
        else:
            args.GUIselectFiles = False
        # pdb.set_trace()
        coe_list=[0,0,0,0]
        try:
            coefficient_model = RunAbsorptionCoefficient( args.rawimg_path , model_storepath ,
                                                     coe_li= args.coe_li ,
                                                     coe_lo= args.coe_lo ,
                                                        coe_cr= args.coe_cr ,
                                                        coe_bu= args.coe_bu ,
                                                      logger=logger,
                                                      auto_orientation = args.coefficient_auto_orientation ,
                                                      auto_viewing= args.coefficient_auto_viewing ,
                                                      save_dir = os.path.join( result_path ,
                                                                               "absorption_coefficient" ) ,
                                                      offset = args.coefficient_orientation ,
                                                      angle = coefficient_viewing ,
                                                      kernel_square = args.kernel_square ,
                                                      full = False , thresholding = args.coefficient_thresholding,
                                                      flat_fielded=args.flat_field_name,base=args.abs_base_cls, crop=args.crop,padding=args.padding,yx_shift=args.yx_shift)
            coe_li,coe_lo,coe_cr,coe_bu=coefficient_model.run( )
            coe_list = [coe_li,coe_lo,coe_cr,coe_bu]
        except Exception as e:
            logger.error("The absorption coefficient calculation is failed")
            logger.error(e)
            raise RuntimeError("The absorption coefficient calculation is failed")
    else:
        if hasattr(args, 'coe_li'):
            coe_list[0]=args.coe_li 
        else:
            logger.error("The absorption coefficient for Liquor is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like liac: 0.01, otherwise it was set as 0 by default")
            # raise RuntimeError("The absorption coefficient for Liquor is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like coe_li: 0.01")
        if hasattr(args, 'coe_lo'):
            coe_list[1]=args.coe_lo
        else:
            logger.error("The absorption coefficient for Loop is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like loac: 0.01, otherwise it was set as 0 by default")
            # raise RuntimeError("The absorption coefficient for Loop is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like coe_lo: 0.01")
        if hasattr(args, 'coe_cr'):
            coe_list[2]=args.coe_cr
        else:
            logger.error("The absorption coefficient for Crystal is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like crac: 0.01, otherwise it was set as 0 by default")
            # raise RuntimeError("The absorption coefficient for Crystal is not calculated (cal_coefficient: False), Please define it in the preprocess_input yaml as something like coe_cr: 0.01")

        if hasattr(args, 'coe_bu'):
            coe_list[3]=args.coe_bu
        else:
            pass


    
    if args.GUIselectFiles:
        selected_paths = select_multiple_folders()
        
        # selected_paths=["/dls/i23/data/2024/cm37273-1/processed/TestThermolysin/tlys_2/3p0_4/11e51352-2757-4efd-9c1d-bbe6112d0b03/","/dls/i23/data/2024/cm37273-1/processed/TestThermolysin/tlys_2/3p5_1/43a5dd73-db37-46fd-8a20-31144e6cb956/","/dls/i23/data/2024/cm37273-1/processed/TestThermolysin/tlys_2/3p5_4/70396634-b7ab-4d63-a37e-8c2af6219479/"]
        # print("The follwing files are selected")
        for path in selected_paths:
            print(path)
        print('\n')
        all_preprocessed_path=[]
        counter=0
        all_pairs=[]
        for i,path in enumerate(selected_paths):
            refl_dict = {}
            expt_dict = {}
            matched_pairs = []
            for filename in os.listdir(path):
                if filename.endswith(".refl") and "scaled" not in filename:
                    base = os.path.splitext(filename)[0]
                    refl_dict[base] = os.path.join(path, filename)
                elif filename.endswith(".expt") and "scaled" not in filename:
                    base = os.path.splitext(filename)[0]
                    expt_dict[base] = os.path.join(path, filename)

            # Find common keys in both refl and expt
            for base_name in refl_dict.keys() & expt_dict.keys():
                matched_pairs.append((refl_dict[base_name], expt_dict[base_name]))
            all_pairs.append(matched_pairs)
            for pairs in matched_pairs:
                counter+=1
                refl_path, expt_path = pairs
                # pdb.set_trace()
                logger.info(f"In path: {path}")
                logger.info(f"Found Reflection files: {refl_path}")
                logger.info(f"Found Experiment files: {expt_path}")          
                save_name= os.path.basename(os.path.dirname(refl_path)) + "_" + os.path.splitext( os.path.basename(refl_path))[0]
                preprocess_dial_lite(args, refl_path ,expt_path  , save_dir,logger )
                new_yaml = os.path.join(save_dir, f'{save_name}.yaml')
                dataset_match = f"anacor_data_{counter}"
             
                with open('./default_mpprocess_input.yaml', 'r' ) as f3 :
                        old_config = yaml.safe_load( f3 )
                mp_config = old_config.copy()
                
                mp_config[ 'refl_path' ] = os.path.join(save_dir, save_name + "_" + "refl"  "_"+"False"+'.json')
                mp_config[ 'expt_path' ] = os.path.join(save_dir, save_name + "_" + "expt"  "_"+"False"+'.json')
                mp_config[ 'store_dir' ] = save_dir   
                mp_config[ 'dataset' ] = dataset_match   
                mp_config[ 'model_storepath' ] = model_storepath

                mp_config[ 'liac' ] =coe_list[0]
                mp_config[ 'loac' ] =coe_list[1]
                mp_config[ 'crac' ] =coe_list[2]
                mp_config[ 'buac' ] =coe_list[3]
        
        
                with open( new_yaml , 'w' ) as file :
                    yaml.dump( mp_config , file, default_flow_style=False, sort_keys=False, indent=4)
                    print(f"input setting of {save_name} is finished")
                all_preprocessed_path.append(new_yaml)
            # dataset_ =f"anacor_{re.findall(pattern, path)[0]}"
            # dataset_ = f"anacor_{i}"
            # dataset_match = f"{dataset_}_save_data"
            # dataset_match= f"data_{i+1}"
            # new_save_dir =os.path.dirname(save_dir)
            # new_save_dir = os.path.join(new_save_dir,dataset_match)
            # all_preprocessed_path.append(new_save_dir)
            # create_save_dir(new_save_dir)
            
            # new_logger = setup_logger(os.path.join(new_save_dir, "Logging", 'preprocess.log'))
            # new_refl_files, new_expt_files = find_reflexp(path)
            # if len(new_expt_files)==0 or len(new_refl_files) ==0:
            #     raise RuntimeError(f"The reflection or experiment files are not found in {path}")
            # assert len(new_refl_files) == 1, "Only one reflection file is allowed, but found {}".format(new_refl_files)
            # assert len(new_expt_files) == 1, "Only one experiment file is allowed, but found {}".format(new_expt_files)
            # new_refl_pth = os.path.join(new_save_dir, new_refl_files[0])
            # new_expt_pth = os.path.join(new_save_dir, new_expt_files[0])
            # new_logger.info(f"In path: {path}")
            # new_logger.info(f"Found Reflection files: {new_refl_pth}")
            # new_logger.info(f"Found Experiment files: {new_expt_pth}")            
            # preprocess_dial_lite(args, new_refl_pth ,new_expt_pth  , new_save_dir,dataset_match,new_logger )
            # new_yaml = os.path.join(new_save_dir, 'default_mpprocess_input.yaml')


            # new_refl_files, new_expt_files = find_reflexp(path)
            # if len(new_expt_files)==0 or len(new_refl_files) ==0:
            #     raise RuntimeError(f"The reflection or experiment files are not found in {path}")
            # assert len(new_refl_files) == 1, "Only one reflection file is allowed, but found {}".format(new_refl_files)
            # assert len(new_expt_files) == 1, "Only one experiment file is allowed, but found {}".format(new_expt_files)
            # new_refl_pth = os.path.join(save_dir, new_refl_files[0])
            # new_expt_pth = os.path.join(save_dir, new_expt_files[0])

    
        return all_pairs,all_preprocessed_path
    else:
        preprocess_dial_lite(args, args.refl_path ,args.expt_path  , save_dir,dataset,logger )

    
        with open('./default_mpprocess_input.yaml', 'r' ) as f3 :
                mp_config = yaml.safe_load( f3 )

        mp_config[ 'refl_path' ] = args.refl_path
        mp_config[ 'expt_path' ] = args.expt_path
        mp_config[ 'dataset' ] = args.dataset      
        mp_config[ 'model_storepath' ] = model_storepath

        # for file in os.listdir(save_dir):
        #     if '.json' in file:
        #         if 'expt' in file:
        #             expt_filename=os.path.join(save_dir,file)
        #         if 'refl' in file:
        #             refl_filename = os.path.join(save_dir,file)

        # mp_config[ 'refl_path' ] = refl_filename
        # mp_config[ 'expt_path' ] = expt_filename

        mp_config[ 'liac' ] =coe_list[0]
        mp_config[ 'loac' ] =coe_list[1]
        mp_config[ 'crac' ] =coe_list[2]
        mp_config[ 'buac' ] =coe_list[3]
        
        with open( 'default_mpprocess_input.yaml' , 'w' ) as file :
            yaml.dump( mp_config , file, default_flow_style=False, sort_keys=False, indent=4)
            print("The selected files are written in the default_mpprocess_input.yaml file")
        return None
if __name__ == '__main__' :
    main( )

