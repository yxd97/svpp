# SVPP: Mixing HLS and Backend Versions in Vitis
`vpp` means `v++`, the command-line binary for building FPGA bitstreams
in the [Vitis Unified Software Platform](https://www.xilinx.com/products/design-tools/vitis.html)
from AMD.
`v++` will make use of both Vitis HLS and Vivado to trun a C++ kernel into a
runnable FPGA bitstream, but it requires the versions of HLS and Vivado to be
the same, and is supported the version of the board shell.

However, the behavior of the tools will change from version to version, and
sometimes we want to use stable features of an old HLS version with more advanced
physical implementation support from the latest Vivado version;
or maybe in your setup, the version of the deivice shell is fixed, and you would like
to explore features of new tools.

This tool, `svpp`, is designed to help you mix the versions of HLS and
backend tools in Vitis, by providing a wrapper above the `v++` compiler.

> What does "s" stands for? Could be "super", "switch", "separate", ("sweet", "smile", ...);
there are lots of good words that start with "s"!

## Dependencies
`svpp` is fully in Python, and tested on Python 3.12. It should also work with older Python versions.
It also require you to have the desired versions of Vitis installed.

## Installation and setup
Simply clone this repository, and add the path to this repo to your `PATH` environment variable.
`svpp` will read the `config.json` file in the same directory as the script, where you specify the
commands to setup versions of Vitis. Here is the example included in this repo:
```json
{
    "supported versions" :{
        "2020.2": "/work/shared/common/vitis_setup_scripts/2020.2.sh",
        "2022.1": "/work/shared/common/vitis_setup_scripts/2022.1.sh"
    },
    "default version":"2022.1"
}
```
The json file **must** contain 2 keys: "supported versions" and "default version".
The "supported versions" key is a dictionary, where the key is the version string, and the value is the path to the setup script. The "default version" key is a string, which specifies the default version of Vitis to use.

> You will also need to prepare the setup scripts for each version of Vitis, according to how you install those tools. The requirement is that after running the setup script, the `v++` and `vivado` commands should be available in the terminal.

## Usage
`svpp` is fully compatiable with all `v++` options, with two additional command-line options:
- `--hls-version <version string>`: specify the version of HLS to use. If not specified, the default version will be used.
- `--backend-version <version string>`: specify the version of Vivado to use. If not specified, the version of HLS will be used.

Therefore, you can use `svpp` as a drop-in replacement for `v++`, and specify the versions of HLS and backend tools to use. For example, if the following is your original build commands:
```
v++ -c -k kernel_name -t hw --platform /path/to/platform.xpfm -o kernel_name.xo kernel_name.cpp
v++ -l -t hw --platform /path/to/platform.xpfm -o kernel_name.xclbin kernel_name.xo
```
Just replace `v++` with `svpp`, and add the version options:
```
svpp --hls-version 2020.2 --backend-version 2022.1 -c -k kernel_name -t hw --platform /path/to/platform.xpfm -o kernel_name.xo kernel_name.cpp
svpp --hls-version 2020.2 --backend-version 2022.1 -l -t hw --platform /path/to/platform.xpfm -o kernel_name.xclbin kernel_name.xo
```
and everything should work seamlessly!

> Note that the `--platform` option should point to the platform file that is supported by the selected
version of HLS or Vivado, which may be different in `-c` (compilation) and `-l` (linking) steps.