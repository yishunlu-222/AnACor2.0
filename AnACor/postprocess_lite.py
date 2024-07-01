import argparse
import subprocess
import json
import os
import pdb
import yaml

def str2bool ( v ) :
    if isinstance( v , bool ) :
        return v
    if v.lower( ) in ('yes' , 'true' , 't' , 'y' , '1') :
        return True
    elif v.lower( ) in ('no' , 'false' , 'f' , 'n' , '0') :
        return False
    else :
        raise argparse.ArgumentTypeError( 'Boolean value expected.' )


def set_parser ( ) :
    parser = argparse.ArgumentParser( description = "analytical absorption correction data preprocessing" )
    parser.add_argument(
        "--input-file" ,
        type = str ,
        default='default_postprocess_input.yaml',
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

    # Load the YAML configuration file
    # with open( os.path.join(directory,'default_postprocess_input.yaml') , 'r' ) as f :
    #     config = yaml.safe_load( f )

    # Add an argument for each key in the YAML file
    for key , value in config.items( ) :
        parser.add_argument( '--{}'.format( key ) , default = value )
    
    global args
    args = parser.parse_args( )

    return args


def main ( ) :
    args = set_parser( )
    dataset=args.dataset
    save_dir = os.path.join(  args.store_dir, '{}_save_data'.format( dataset ) )
    result_path  =os.path.join(  save_dir,'ResultData','absorption_factors')
    refl_dir = os.path.join(  save_dir,'ResultData','reflections')
    dials_dir = os.path.join( save_dir , 'ResultData' , 'dials_output' )


    stackingpy_pth = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , 'utils', 'stacking.py' )
    intoflexpy_pth = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , 'utils', 'into_flex.py' )
    dials_save_name='anacor_{}.refl'.format(args.dataset)

    with open( os.path.join( save_dir , "dialsprocess_script.sh" ) , "w" ) as f :

        f.write( "#!/bin/sh\n" )
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
        
        f.close( )

    result = subprocess.run( "bash {}".format(os.path.join( save_dir , "postprocess_script.sh" ) ),
                             shell = True , stdout = subprocess.PIPE , stderr = subprocess.PIPE )
    print( result.returncode )
    print( result.stdout.decode( ) )
    print( result.stderr.decode( ) )



if __name__ == '__main__' :
    main( )