# tests/test_sampling.py

import pytest
import warnings
import logging
from table import Sphere, Cylinder
import time
import pdb
import os
# Configure logging

logger = logging.getLogger(__name__)

global pixel_size
pixel_size=0.3
class TestBasic:
    @classmethod
    def setup_class(self):
        """Set up any state specific to the execution of the given class."""
        self.sphere_simulation = Sphere(10, pixel_size, 3)
        self.cylinder_simulation = Cylinder(10, pixel_size, 3, 10)
        # pdb.set_trace()
        # logger.info("Setup Sphere and Cylinder simulation")
        # logger.info("Sphere simulation shape is %s", self.sphere_simulation.shape)
        # logger.info("Cylinder simulation shape is %s", self.cylinder_simulation.shape)

    @pytest.mark.order(1)
    def test_import(self):
        logger.info("========test_import starts========")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", category=DeprecationWarning)
            import AnACor
            from AnACor.utils.utils_mp import worker_function
            from AnACor.utils.utils_rt import generate_sampling

            assert AnACor is not None
            assert worker_function is not None
            assert generate_sampling is not None
            assert self.sphere_simulation is not None
            assert self.cylinder_simulation is not None
        compile_files=["ray_tracing_gpu.so","ray_tracing_cpu.so","gridding_interpolation.so"]
        abs_pth = os.path.abspath(os.path.join(os.path.dirname(__file__),"../"))
        compile_pth = ["./src"]
        for file in compile_files:
            for pth in compile_pth:
                try:
                    
                    assert os.path.exists(os.path.join(pth,file))
                except:
                    logger.error(f"Cannot find {file} in {pth}")
        
        logger.info("========test_import is done========")
        logger.info("\n")
    @classmethod
    def sampling_t(self, coord_list,method):
            if method == 'even':
                papermethod = 'Systematic'
            if method == 'random':
                papermethod = 'Random'
            if method == 'evenrandom':
                papermethod = 'Randomised systematic'
            if method == 'stratified':
                papermethod = 'Stratified'
            from AnACor.utils.utils_rt import generate_sampling
            sampling_ratio = 0.1
            logger.info(f"Testing sampling Sphere with {papermethod} sampling and sampling_ratio of 0.1%:")
            t1=time.time()
            coord_list_e = generate_sampling(coord_list, sampling_ratio=sampling_ratio, method=method)
            t2=time.time()
            logger.info("It takes {:.5f} seconds to generate this sampling list".format(t2-t1))
            logger.info("\n")
            return coord_list_e
    @pytest.mark.order(2)
    # @pytest.mark.skip(reason="This Sampling test is being skipped.")
    def test_sampling(self):
        
        logger.info("========test_sampling starts========")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", category=DeprecationWarning)
            from AnACor.utils.utils_rt import generate_sampling

            coord_list_e = self.sampling_t(self.sphere_simulation,'even')
            coord_list_r = self.sampling_t(self.sphere_simulation,'random')
            coord_list_rs = self.sampling_t(self.sphere_simulation,'evenrandom')
            coord_list_st = self.sampling_t(self.sphere_simulation,'stratified')
            assert coord_list_e is not None
            assert coord_list_r is not None
            assert coord_list_rs is not None
            assert coord_list_st is not None

            coord_list_e = self.sampling_t(self.cylinder_simulation,'even')
            coord_list_r = self.sampling_t(self.cylinder_simulation,'random')
            coord_list_rs = self.sampling_t(self.cylinder_simulation,'evenrandom')
            coord_list_st = self.sampling_t(self.cylinder_simulation,'stratified')
            
            assert coord_list_e is not None
            assert coord_list_r is not None
            assert coord_list_rs is not None
            assert coord_list_st is not None
        
        
        logger.info("========test_sampling is done========")
        logger.info("\n")