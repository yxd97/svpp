# Definition of include file locations
xrt_path = $(XILINX_XRT)

OPENCL_INCLUDE := $(xrt_path)/include

VIVADO_INCLUDE := $(XILINX_VIVADO)/include
opencl_CXXFLAGS = -I$(OPENCL_INCLUDE) -I$(VIVADO_INCLUDE)
OPENCL_LIB := $(xrt_path)/lib
opencl_LDFLAGS = -L$(OPENCL_LIB) -lOpenCL -lpthread
