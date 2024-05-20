import os
import xml.etree.ElementTree as ET
from typing import List
from kernel_signature import KernelSignature, KernelArgument, Port

if "SVPP_ROOT" not in os.environ:
    raise ValueError(
        "Please set the SVPP_ROOT environment variable"
        " to the root of the svpp repository."
    )
SVPP_ROOT = os.environ["SVPP_ROOT"]

TCL_FUNCS_FOR_MM = [
    "proc add_reg { name parent_addrblk offset size description } {\n",
    "    puts [format \"INFO: \[User Message\] Adding register %s to %s\" $name $parent_addrblk]\n",
    "    ipx::add_register $name $parent_addrblk\n",
    "    set_property display_name $name [ipx::get_registers $name -of_objects $parent_addrblk]\n",
    "    set_property description $description [ipx::get_registers $name -of_objects $parent_addrblk]\n",
    "    set_property size $size [ipx::get_registers $name -of_objects $parent_addrblk]\n",
    "    set_property address_offset $offset [ipx::get_registers $name -of_objects $parent_addrblk]\n",
    "}\n",
    "\n",
    "proc bind_to_gmem { reg_name gmem_name reg_addrblk } {\n",
    '    puts [format "INFO: \[User Message\] Binding %s of %s to %s" $reg_name $reg_addrblk $gmem_name]\n',
    '    puts [ipx::get_registers $reg_name -of_objects $reg_addrblk]\n',
    "    ipx::add_register_parameter ASSOCIATED_BUSIF [ipx::get_registers $reg_name -of_objects $reg_addrblk]\n",
    "    set_property value $gmem_name [ipx::get_register_parameters ASSOCIATED_BUSIF -of_objects [ipx::get_registers $reg_name -of_objects $reg_addrblk]]\n",
    "}\n",
    "\n",
    "set addrblk [ipx::get_address_blocks reg0 -of_objects [ipx::get_memory_maps s_axi_control -of_objects [ipx::current_core]]]\n"
    "\n",
    'add_reg "CTRL"   $addrblk 0 32 "Control Register"\n',
    'add_reg "GIER"   $addrblk 4 32 "Global Interrupt Enable Register"\n',
    'add_reg "IP_IER" $addrblk 8 32 "IP Interrupt Enable Register"\n',
    'add_reg "IP_ISR" $addrblk 12 32 "IP Interrupt Status Register"\n'
]

def prepare_pack_xo(build_dir:str, kernel_name:str) -> str:
    '''
        Copy the HLS-generated Verilog to a new directory and
        generate the tcl script for packaging the `.xo` file.
    '''
    pack_dir = os.path.join(build_dir, f"pack_{kernel_name}")
    os.makedirs(pack_dir, exist_ok=True)

    hls_verilog_dir = os.path.join(
        build_dir, kernel_name, kernel_name, kernel_name,
        "solution", "impl", "verilog"
    )
    verilog_dir = os.path.join(pack_dir, "src")
    os.makedirs(verilog_dir, exist_ok=True)
    os.system(f"cp {hls_verilog_dir}/*.v {verilog_dir}")

    master_tcl = os.path.join(SVPP_ROOT, "scripts", "create_proj.tcl")
    os.system(f"cp {master_tcl} {pack_dir}")

    xml = os.path.join(build_dir, kernel_name, kernel_name, kernel_name, "kernel.xml")
    signature = KernelSignature(ET.parse(xml).getroot())

    # associate clock to interfaces
    # stream interface use the same name as its argument, plus a "_V" suffix
    # we rename it to the variable name in the kernel function
    # so that the sc tags still work
    tcl_rename_stream = [
        f"set_property name {arg.name} [ipx::get_bus_interfaces {arg.name}_V -of_objects [ipx::current_core]]\n"
        for arg in signature.args if arg.is_stream
    ]
    tcl_set_clk_stream = [
        f"ipx::associate_bus_interfaces -busif {arg.name} -clock ap_clk [ipx::current_core]\n"
        for arg in signature.args if arg.is_stream
    ]

    # memory mapped interface use lowercase port name
    tcl_set_clk_mm = [
        f"ipx::associate_bus_interfaces -busif {port.name.lower()} -clock ap_clk [ipx::current_core]\n"
        for port in signature.ports.values() if port.type == "addressable"
    ]
    tcl_reg_map = [
        f"add_reg {arg.name} $addrblk {arg.offset} {arg.size*8} {arg.name}_DATA\n"
        for arg in signature.args if not arg.is_stream
    ]
    tcl_reg_map += [
        f"bind_to_gmem {arg.name} {arg.port_name.lower()} $addrblk\n"
        for arg in signature.args if not arg.is_stream and arg.is_pointer
    ]

    with open(os.path.join(pack_dir, "kernel_regs.tcl"), "w") as f:
        f.writelines(tcl_rename_stream)
        f.writelines(tcl_set_clk_stream)
        # free-running kernel does not have register mapping
        if signature.protocol != "ap_ctrl_none":
            f.writelines(TCL_FUNCS_FOR_MM)
            f.writelines(tcl_set_clk_mm)
            f.writelines(tcl_reg_map)

    return pack_dir
