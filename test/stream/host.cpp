#include <iostream>
#include <string>
#include <vector>

#include "xcl2.hpp"
#define CHANNEL_NAME(n) n | XCL_MEM_TOPOLOGY

// u280 memory channels
const int HBM[32] = {
    CHANNEL_NAME(0),  CHANNEL_NAME(1),  CHANNEL_NAME(2),  CHANNEL_NAME(3),  CHANNEL_NAME(4),
    CHANNEL_NAME(5),  CHANNEL_NAME(6),  CHANNEL_NAME(7),  CHANNEL_NAME(8),  CHANNEL_NAME(9),
    CHANNEL_NAME(10), CHANNEL_NAME(11), CHANNEL_NAME(12), CHANNEL_NAME(13), CHANNEL_NAME(14),
    CHANNEL_NAME(15), CHANNEL_NAME(16), CHANNEL_NAME(17), CHANNEL_NAME(18), CHANNEL_NAME(19),
    CHANNEL_NAME(20), CHANNEL_NAME(21), CHANNEL_NAME(22), CHANNEL_NAME(23), CHANNEL_NAME(24),
    CHANNEL_NAME(25), CHANNEL_NAME(26), CHANNEL_NAME(27), CHANNEL_NAME(28), CHANNEL_NAME(29),
    CHANNEL_NAME(30), CHANNEL_NAME(31)
};
const int DDR[2] = {CHANNEL_NAME(32), CHANNEL_NAME(33)};

// u280 device names
const std::string DEVICE_NAME = "xilinx_u280_gen3x16_xdma_1_202211_1"; // used in sw_emu and hw_emu
const std::string DEVICE_XSA = "xilinx_u280_gen3x16_xdma_base_1"; // only used when running on hardware

int main(int argc, char** argv) {
    // usage: host <xclbin_path> <vector size>
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << "<exec mode> <xclbin_path> <vector size>" << std::endl;
        return 1;
    }
    const std::string exec_mode = argv[1];
    const std::string xclbin = argv[2];
    const unsigned size = std::stoi(argv[3]);

    // first see if we are in sw_emu, hw_emu, or hw
    if (exec_mode == "hw") {
        unsetenv("XCL_EMULATION_MODE");
    } else {
        setenv("XCL_EMULATION_MODE", exec_mode.c_str(), 1);
    }

    // find device
    std::string device_name = (exec_mode == "hw") ? DEVICE_XSA : DEVICE_NAME;
    bool found_device = false;
    auto devices = xcl::get_xil_devices();
    cl::Device device;
    for (size_t i = 0; i < devices.size(); i++) {
        if (devices[i].getInfo<CL_DEVICE_NAME>() == device_name) {
            device = devices[i];
            found_device = true;
            break;
        }
    }
    if (!found_device) {
        std::cerr << "[ERROR]: Failed to find " << device_name << ", exit!" << std::endl;
        return 1;
    }

    // create opencl context
    cl_int err = CL_SUCCESS;
    cl::Context context(device, NULL, NULL, NULL, &err);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to create context, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // program the device
    auto file_buf = xcl::read_binary_file(xclbin);
    cl::Program::Binaries binaries{{file_buf.data(), file_buf.size()}};
    err = CL_SUCCESS;
    cl::Program program(context, {device}, binaries, NULL, &err);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to program device, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // create opencl command queue
    err = CL_SUCCESS;
    cl::CommandQueue command_q(
        context, device,
        CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE | CL_QUEUE_PROFILING_ENABLE,
        &err
    );
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to create command queue, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // obtain a kernel handler
    err = CL_SUCCESS;
    cl::Kernel put(program, "put", &err);
    cl::Kernel get(program, "get", &err);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to create kernel, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // prepare test data
    srand(0x12345678);
    std::vector<char> src(size);
    std::vector<char> dst(size);
    std::vector<char> dst_ref(size);
    for (unsigned i = 0; i < size; ++i) {
        src[i] = rand() % (126 - 33) + 33;
        dst_ref[i] = src[i];
    }

    // allocate device memory
    cl_mem_ext_ptr_t src_ext;
    src_ext.flags = HBM[0];
    src_ext.obj = src.data();
    src_ext.param = 0;
    err = CL_SUCCESS;
    cl::Buffer src_buf(
        context,
        CL_MEM_EXT_PTR_XILINX | CL_MEM_USE_HOST_PTR | CL_MEM_READ_ONLY,
        size * sizeof(char),
        &src_ext,
        &err
    );
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to allocate device memory for src, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    cl_mem_ext_ptr_t dst_ext;
    dst_ext.flags = HBM[0];
    dst_ext.obj = dst.data();
    dst_ext.param = 0;
    err = CL_SUCCESS;
    cl::Buffer dst_buf(
        context,
        CL_MEM_EXT_PTR_XILINX | CL_MEM_USE_HOST_PTR | CL_MEM_WRITE_ONLY,
        size * sizeof(char),
        &dst_ext,
        &err
    );
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to allocate device memory for dst, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // move data to device
    err = command_q.enqueueMigrateMemObjects(
        {src_buf, dst_buf},
        0 // 0 means from host to device
    );
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to migrate data to device, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = command_q.finish();
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to finish command queue, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // pass arguments to kernel
    err = get.setArg(0, src_buf);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to set get.src, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = get.setArg(2, size);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to set get.size, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = put.setArg(1, dst_buf);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to set put.dst, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = put.setArg(2, size);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to set put.size, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // launch kernel
    err = command_q.enqueueTask(put);
    err = command_q.enqueueTask(get);
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to launch kernel, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = command_q.finish();
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to finish command queue, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    // move results back to host
    err = command_q.enqueueMigrateMemObjects(
        {dst_buf},
        CL_MIGRATE_MEM_OBJECT_HOST
    );
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to migrate data to host, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }
    err = command_q.finish();
    if (err != CL_SUCCESS) {
        std::cerr << "[ERROR]: Failed to finish command queue, exit!" << std::endl;
        std::cerr << "         Error code: " << err << std::endl;
        return 1;
    }

    if (size < 80) {
        std::cout << "    src: ";
        for (unsigned i = 0; i < size; ++i) {
            std::cout << src[i];
        }
        std::cout << std::endl;
        std::cout << "    dst: ";
        for (unsigned i = 0; i < size; ++i) {
            std::cout << dst[i];
        }
        std::cout << std::endl;
        std::cout << "dst_ref: ";
        for (unsigned i = 0; i < size; ++i) {
            std::cout << dst_ref[i];
        }
        std::cout << std::endl;
    }

    // check results
    bool pass = true;
    for (unsigned i = 0; i < size; ++i) {
        if (dst[i] != dst_ref[i]) {
            std::cerr << "[ERROR]: Result mismatch at index " << i << "!" << std::endl;
            std::cerr << "         Expected: " << dst_ref[i] << ", got: " << dst[i] << std::endl;
            pass = false;
            break;
        }
    }

    if (pass) {
        std::cout << "Test passed!" << std::endl;
    } else {
        std::cout << "Test failed!" << std::endl;
    }

    return (pass) ? 0 : 1;
}
