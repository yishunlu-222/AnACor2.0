



pth := ./
gpu_pth := ./gpu/
# Default paths, can be overridden by environment variables
CUDA_HOME ?= /usr/local/cuda
GSL_INCLUDE ?= /usr/local/include
GSL_LIB ?= /usr/local/lib

# Compiler and linker flags
INC := -I$(CUDA_HOME)/include
LIB := -L$(CUDA_HOME)/lib64 -lcudart -lcufft -lcuda
LDFLAGS := -fopenmp
GCC = gcc
NVCC = $(CUDA_HOME)/bin/nvcc

# Determine the architecture flag based on the GPU model
# ifneq ($(findstring h100,$(ARCH)),)
#   SM_ARCH = sm_90
# else ifneq ($(findstring a100,$(ARCH)),)
#   SM_ARCH = sm_80
# else ifneq ($(findstring v100,$(ARCH)),)
#   SM_ARCH = sm_70
# else ifneq ($(findstring titanx,$(ARCH)),)
#   SM_ARCH = sm_61
# else
#   # Default architecture
#   SM_ARCH = sm_70
# endif
SM_ARCH=sm_${SM}
NVCCFLAGS = -O3 -w -arch=$(SM_ARCH) --ptxas-options=-v -Xcompiler -Wextra -Xcompiler -fPIC -lineinfo
NVCCFLAGS_D = -O0 -arch=$(SM_ARCH) --ptxas-options=-v -Xcompiler -Wextra -Xcompiler -fPIC -G -g

# Compiler options
GCC_OPTS = -O3 -w -fPIC -Wall -Wextra $(LDFLAGS) $(INC)
GCC_OPTS_D = -O0 -fPIC -Wall -Wextra $(INC) $(LDFLAGS) -g
GCC_OPTS_gridding = -O3 -fPIC -Wall -Wextra $(LDFLAGS) -L$(GSL_LIB) -I$(GSL_INCLUDE) -lgsl -lgslcblas -lm

ANALYZE = FFT.exe

all: clean sharedlibrary_cpu sharedlibrary_gpu sharedlibrary_interpolation
debug: clean sharedlibrary_cpu_d sharedlibrary_gpu_d sharedlibrary_interpolation_d
clean: clean
cpu:  sharedlibrary_cpu sharedlibrary_interpolation
gpu:  sharedlibrary_gpu
grid: sharedlibrary_interpolation

sharedlibrary_cpu: ray_tracing.o ray_tracing_basic.o bisection.o testkit.o Makefile
	$(GCC) -shared -o ray_tracing_cpu.so -fPIC -std=c99 $(GCC_OPTS) $(LDFLAGS) ray_tracing.o ray_tracing_basic.o bisection.o testkit.o

ray_tracing.o: $(pth)ray_tracing.c
	$(GCC) -c $(pth)ray_tracing.c -fPIC -std=c99 $(GCC_OPTS) $(LDFLAGS) -o ray_tracing.o

ray_tracing_basic.o: $(pth)ray_tracing_basic.c
	$(GCC) -c $(pth)ray_tracing_basic.c -fPIC -std=c99 $(GCC_OPTS) $(LDFLAGS) -o ray_tracing_basic.o

bisection.o: $(pth)bisection.c
	$(GCC) -c $(pth)bisection.c -fPIC -std=c99 $(GCC_OPTS) $(LDFLAGS) -o bisection.o

testkit.o: $(pth)testkit.c
	$(GCC) -c $(pth)testkit.c -fPIC -std=c99 $(GCC_OPTS) $(LDFLAGS) -o testkit.o

sharedlibrary_cpu_d: ray_tracing_d.o ray_tracing_basic_d.o bisection_d.o testkit_d.o
	$(GCC) -shared -o ray_tracing_cpu.so -fPIC -std=c99 $(GCC_OPTS_D) $(LDFLAGS) ray_tracing_d.o ray_tracing_basic_d.o bisection_d.o testkit_d.o

ray_tracing_d.o: $(pth)ray_tracing.c
	$(GCC) -c $(pth)ray_tracing.c $(GCC_OPTS_D) -o ray_tracing_d.o

ray_tracing_basic_d.o: $(pth)ray_tracing_basic.c
	$(GCC) -c $(pth)ray_tracing_basic.c $(GCC_OPTS_D) -o ray_tracing_basic_d.o

bisection_d.o: $(pth)bisection.c
	$(GCC) -c $(pth)bisection.c $(GCC_OPTS_D) -o bisection_d.o

testkit_d.o: $(pth)testkit.c
	$(GCC) -c $(pth)testkit.c $(GCC_OPTS_D) -o testkit_d.o

sharedlibrary_gpu: ray_tracing_c.o ray_tracing_gpu.o
	$(NVCC) $(NVCCFLAGS) -shared -o ray_tracing_gpu.so ray_tracing_c.o ray_tracing_gpu.o

ray_tracing_c.o: ray_tracing_gpu.c
	g++ -c ray_tracing_gpu.c $(GCC_OPTS) -o ray_tracing_c.o

ray_tracing_gpu.o: $(gpu_pth)ray_tracing_gpu.cu
	$(NVCC) -c $(gpu_pth)ray_tracing_gpu.cu $(NVCCFLAGS) -o ray_tracing_gpu.o

sharedlibrary_gpu_d: ray_tracing_c_d.o ray_tracing_gpu_d.o
	$(NVCC) $(NVCCFLAGS_D) -shared -o ray_tracing_gpu.so ray_tracing_c_d.o ray_tracing_gpu_d.o

ray_tracing_c_d.o: ray_tracing_gpu.c
	g++ -c ray_tracing_gpu.c $(GCC_OPTS_D) -o ray_tracing_c_d.o

ray_tracing_gpu_d.o: $(gpu_pth)ray_tracing_gpu.cu
	$(NVCC) -c $(gpu_pth)ray_tracing_gpu.cu $(NVCCFLAGS_D) -o ray_tracing_gpu_d.o

sharedlibrary_interpolation: gridding_interpolation.c ray_tracing_basic.o
	$(GCC) -shared -o gridding_interpolation.so -fPIC -std=c99 $(GCC_OPTS_gridding) gridding_interpolation.c ray_tracing_basic.o

sharedlibrary_interpolation_d: gridding_interpolation.c ray_tracing_basic.o
	$(GCC) -shared -o gridding_interpolation.so -fPIC -std=c99 $(GCC_OPTS_gridding) gridding_interpolation.c ray_tracing_basic.o

clean:
	rm -f *.o *.~ $(ANALYZE)
