import pytest
import warnings
import logging
from table import Sphere, Cylinder,sphere_correct_p5,cylinder_correct_p5
import time
import pdb
import numpy as np
# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("pytest.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

global pixel_size
pixel_size=0.3

class TestBasic:
    @classmethod
    def setup_class(self):
        """Set up any state specific to the execution of the given class."""
        self.sphere_simulation = Sphere(50, pixel_size, 3)
        self.cylinder_simulation = Cylinder(50, pixel_size, 3, 50)
        # pdb.set_trace()
        logger.info("Setup Sphere and Cylinder simulation")
        logger.info("Sphere simulation shape is %s", self.sphere_simulation.shape)
        logger.info("Cylinder simulation shape is %s", self.cylinder_simulation.shape)
    @pytest.mark.order(3)
    # @pytest.mark.skip(reason="This Standard test is being skipped.")
    def test_standard(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", category=DeprecationWarning)
            warnings.simplefilter("ignore", category=RuntimeWarning)
            from AnACor.utils.utils_mp import worker_function
            from AnACor.utils.utils_rt import generate_sampling,myframe_2_dials,thetaphi_2_myframe
            from AnACor.param import set_parser
            # pdb.set_trace()
            arugments=set_parser()
            logger.info("======== test_standard starts========")
            t1 = time.time()
            low = 0
            dataset = 'pytest_standard'
            mu=0.01
            voxel_size = np.array([pixel_size,pixel_size,pixel_size])
            angle_list=np.linspace(start = 0,stop=180,num = 10,endpoint = True)
            selected_data=[]
            for angle in angle_list:
                data={}
                data['s1']=myframe_2_dials(thetaphi_2_myframe(angle / 180 * np.pi, 0))
                data['xyzobs.mm.value']=[0,0,0]
                selected_data.append(data)
            
            coefficients=np.array([0,0,mu,0])
            num_cls=3
            printing=True  
            arugments.openmp=False
            arugments.single_c=True
            store_paths=0
            full_iteration=0
            offset=0
            save_dir='./'
            F=np.array([[1., 0., 0.],
                        [0., 1., 0.],
                        [0., 0., 1.]])
            omega_axis=np.array([1,0,0]).astype(np.float64)
            axes_data=[{'axes': [[1.0, 0.0, 0.0], [0.6427876096865394, -0.766044443118978, 0.0], [1.0, 0.0, 0.0]], 'angles': [0.0, 0.0, -180.0], 'names': ['PHI', 'KAPPA', 'OMEGA'], 'scan_axis': 2}, {'direction': myframe_2_dials(thetaphi_2_myframe(180 / 180 * np.pi, 0)), 'wavelength': 3.0996, 'divergence': 0.0, 'sigma_divergence': 0.0, 'polarization_normal': [0.0, 1.0, 0.0], 'polarization_fraction': 0.999, 'flux': 47526395371.550964, 'transmission': 1.0}]
            
            coord_list=generate_sampling(self.sphere_simulation, sampling_ratio=0.1, method='even')
            corr=worker_function(t1, low,  dataset, selected_data, self.sphere_simulation ,
                        voxel_size, coefficients, F, coord_list,
                        omega_axis, axes_data, save_dir, arugments,
                        offset, full_iteration, store_paths, printing, num_cls,logger)
            per_diff = np.abs(corr - sphere_correct_p5) / sphere_correct_p5 *100
            print_out={}
            for i,angle in enumerate(angle_list):
                print_out[angle]=per_diff[i]
            logger.info("Sphere: Simulation results against the International table")
            logger.info("Sphere: scattering angle: percentage difference (%):")
            logger.info(print_out)
            logger.info("\n")
            # pdb.set_trace()
            coord_list=generate_sampling(self.cylinder_simulation, sampling_ratio=0.1, method='even')
            corr=worker_function(t1, low,  dataset, selected_data, self.cylinder_simulation ,
                        voxel_size, coefficients, F, coord_list,
                        omega_axis, axes_data, save_dir, arugments,
                        offset, full_iteration, store_paths, printing, num_cls,logger)
            
            per_diff = np.abs(corr -  cylinder_correct_p5 ) / cylinder_correct_p5 *100
            print_out={}
            for i,angle in enumerate(angle_list):
                print_out[angle]=per_diff[i]
            logger.info("cylinder: Simulation results against the International table")
            logger.info("cylinder: scattering angle: percentage difference (%):")
            logger.info(print_out)
            t2=time.time()
            logger.info("It takes {:.5f} seconds to run Standard ray-tracing test".format(t2-t1))
            logger.info("\n")
            logger.info("========test_standard is done========")
            logger.info("\n")
            # pdb.set_trace()