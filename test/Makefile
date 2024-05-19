HLS_VERSION = 2022.1
BACKEND_VERSION = 2022.1
SVPP = svpp
VERSION_FLAGS = --hls-version $(HLS_VERSION) --backend-version $(BACKEND_VERSION)
DEVICE = xilinx_u280_gen3x16_xdma_1_202211_1
TARGET = hw

BUILD_DIR = build_$(TARGET)_$(shell echo $(DEVICE) | cut -d'_' -f2)
VPP_FLAGS = -t $(TARGET) --platform $(DEVICE) --save-temps --temp_dir $(BUILD_DIR)

vvadd.xo: vvadd.cpp
	$(SVPP) $(VERSION_FLAGS) -c $(VPP_FLAGS) -k vvadd -o $@ $<

vvadd.xclbin: vvadd.xo
	$(SVPP) $(VERSION_FLAGS) -l $(VPP_FLAGS) -o $@ $<

.PHONY: clean cleanall
clean:
	rm -rf *.log *.jou *.str *.compile_summary *.link_summary
	rm -rf .run *.ltx

cleanall: clean
	rm -rf *.xo *.xclbin *.xclbin.info
	rm -rf build_* .ipcache .Xil