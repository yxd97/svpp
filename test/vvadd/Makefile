# for xclbin
HLS_VERSION = 2020.2
BACKEND_VERSION = 2022.1
SVPP = svpp
VERSION_FLAGS = --hls-version $(HLS_VERSION) --backend-version $(BACKEND_VERSION)
DEVICE_HLS = /work/shared/common/CAD_tool/xilinx/platforms/xilinx_u280_xdma_201920_3/xilinx_u280_xdma_201920_3.xpfm
DEVICE_BACKEND = xilinx_u280_gen3x16_xdma_1_202211_1
TARGET = hw

BUILD_DIR = build_$(TARGET)_$(shell basename $(DEVICE_BACKEND) | cut -d'_' -f2)
VPP_FLAGS = -t $(TARGET)  --save-temps --temp_dir $(BUILD_DIR)

vvadd.xo: vvadd.cpp
	$(SVPP) $(VERSION_FLAGS) --platform $(DEVICE_HLS) -c $(VPP_FLAGS) -k vvadd -o $@ $<

vvadd.xclbin: vvadd.xo
	$(SVPP) $(VERSION_FLAGS) --platform $(DEVICE_BACKEND) -l $(VPP_FLAGS) -o $@ $<

.PHONY: clean cleanall
clean:
	rm -rf *.log *.jou *.str *.compile_summary *.link_summary
	rm -rf .run *.ltx

cleanall: clean
	rm -rf *.xo *.xclbin *.xclbin.info
	rm -rf build_* .ipcache .Xil
	rm -rf host

# for host
CXX = g++

include ../opencl/opencl.mk
HOST_SRCS += $(opencl_SRCS)
CC_FLAGS += $(opencl_CXXFLAGS)
LD_FLAGS += $(opencl_LDFLAGS)

XCL2_LIB_DIR := ../xcl2
include $(XCL2_LIB_DIR)/xcl2.mk
HOST_SRCS += $(xcl2_SRCS)
CC_FLAGS += $(xcl2_CXXFLAGS)
LD_FLAGS += $(xcl2_LDFLAGS)

HOST_SRCS += host.cpp

CC_FLAGS += -std=c++11

host: $(HOST_SRCS)
	$(CXX) $(CC_FLAGS) $(HOST_SRCS) -o $@ $(LD_FLAGS)