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

TCL_BODY = [
    "proc add_reg { name parent_addrblk offset size description } {\n",
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
    'add_reg "IP_ISR" $addrblk 12 32 "IP Interrupt Status Register"\n',
    "\n",
]

def argument_tcl(arg:KernelArgument) -> List[str]:
    '''
        Returns the tcl commands to add a register for the argument,
        using the defined `add_reg` procedure in `TCL_BODY`.
    '''
    tcl = [
        f'add_reg "{arg.name}" $addrblk {arg.offset} {arg.size*8} "{arg.name}_DATA"\n',
    ]
    if arg.is_pointer:
        tcl.extend(f'bind_to_gmem "{arg.name}" "{arg.port_name}" $addrblk\n')

    return tcl + ["\n"]


def prepare_pack_xo(build_dir:str, kernel_name:str) -> str:
    '''
        Copy the HLS-generated Verilog to a new directory and
        generate the tcl script for packaging the `.xo` file.
    '''
    pack_dir = os.path.join(build_dir, "pack")
    os.makedirs(pack_dir, exist_ok=True)

    verilog_dir = os.path.join(pack_dir, "src")
    hls_verilog_dir = os.path.join(build_dir, kernel_name, kernel_name, kernel_name)

    master_tcl = os.path.join(SVPP_ROOT, "scripts", "pack_xo.tcl")
    os.system(f"cp {master_tcl} {pack_dir}")

    xml = os.path.join(build_dir, kernel_name, kernel_name, kernel_name, "kernel.xml")
    signature = KernelSignature(ET.parse(xml).getroot())
    tcl = TCL_BODY.copy()
    for arg in signature.args:
        tcl.extend(argument_tcl(arg))
    with open(os.path.join(pack_dir, "krenel_regs.tcl"), "w") as f:
        f.writelines(tcl)

    return pack_dir
