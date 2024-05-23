import os, re
from typing import Tuple

__PATTERNS = {
    "kernel_xml"       : r'set kernel_xml .*',
    "solution_dir"     : r'set solution_dir ".*"',
    "debug_dir"        : r'set debug_dir ".*"',
    "output_xo"        : r'set kernel_xo ".*"',
    "vhdl_path"        : r'set VhdlFiles .*',
    "verilog_path"     : r'set VerilogFiles .*',
    "swdriver_path"    : r'set SWDriverFiles .*',
    "subcore_path"     : r'set SubcoreFiles .*',
    "doc_path"         : r'set DocumentFiles .*',
    "bd_path"          : r'set BDFiles .*',
    "constraints_path" : r'set ConstraintFiles .*',
    "misc_path"        : r'set MiscFiles .*',
}

__TEMPLATES = {
    "kernel_xml"       : 'set kernel_xml "{}"\n',
    "solution_dir"     : 'set solution_dir "{}"\n',
    "debug_dir"        : 'set debug_dir "{}"\n',
    "output_xo"        : 'set kernel_xo "{}"\n',
    "vhdl_path"        : 'set VhdlFiles [sort_file_names [glob -nocomplain {}/*] ${{Top}}.vhd]\n',
    "verilog_path"     : 'set VerilogFiles [sort_file_names [glob -nocomplain {}/*] ${{Top}}.v]\n',
    "swdriver_path"    : 'set SWDriverFiles [sort_file_names [glob-r {}]]\n',
    "subcore_path"     : 'set SubcoreFiles [sort_file_names [glob -nocomplain {}/*]]\n',
    "doc_path"         : 'set DocumentFiles [sort_file_names [glob -nocomplain {}/*]]\n',
    "bd_path"          : 'set BDFiles [sort_file_names [glob -nocomplain {}/*]]\n',
    "constraints_path" : 'set ConstraintFiles [sort_file_names [glob -nocomplain {}/*]]\n',
    "misc_path"        : 'set MiscFiles [sort_file_names [glob -nocomplain {}/*]]\n',
}


def prepare_pack_xo(build_dir:str, kernel_name:str) -> Tuple[str, str, str]:
    '''
        Copy the HLS-generated Verilog to a new directory and
        generate the tcl script for packaging the `.xo` file.

        Returns : `(pack_dir, ippack_tcl, output_xo)`
        The path to the pack working directory,
        and paths (relative to the working directory)
        to the tcl script and the `.xo` file.
    '''
    pack_dir = os.path.join(build_dir, f"pack_{kernel_name}")
    os.makedirs(pack_dir, exist_ok=True)

    # move the hls solution to the packing dir
    hls_proj = os.path.join(
        build_dir, kernel_name, kernel_name, kernel_name
    )
    os.system(
        "cp -r "
        f"{os.path.join(hls_proj, 'solution')} "
        f"{pack_dir}"
    )

    # set some paths
    ip_dir = os.path.join(pack_dir, 'solution', 'impl', 'ip')
    correct_paths = {
        "kernel_xml"       : os.path.join(ip_dir, "..", "kernel", "kernel.xml"),
        "solution_dir"     : os.path.join(pack_dir, 'solution'),
        "debug_dir"        : os.path.join(pack_dir, 'solution', ".debug"),
        "output_xo"        : os.path.join(pack_dir, "export", f"{kernel_name}.xo"),
        "vhdl_path"        : os.path.join(ip_dir, "hdl", "vhdl"),
        "verilog_path"     : os.path.join(ip_dir, "hdl", "verilog"),
        "swdriver_path"    : os.path.join(ip_dir, "drivers"),
        "subcore_path"     : os.path.join(ip_dir, "subcore"),
        "doc_path"         : os.path.join(ip_dir, "doc"),
        "bd_path"          : os.path.join(ip_dir, "bd"),
        "constraints_path" : os.path.join(ip_dir, "constraints"),
        "misc_path"        : os.path.join(ip_dir, "misc"),
    }

    # turn them into absolute paths since vivado will be switching working directory
    abs_correct_paths = {key: os.path.abspath(path) for key, path in correct_paths.items()}

    # format updates
    updates = {key: template.format(abs_correct_paths[key]) for key, template in __TEMPLATES.items()}

    # join patterns with updates (use pattern as key)
    lines_to_update = {__PATTERNS[key]: updates[key] for key in updates.keys()}

    # modify the tcl script to generate the `.xo` file
    ippack_tcl = os.path.join(ip_dir, 'run_ippack.tcl')
    with open(ippack_tcl, "r") as f:
        content = f.readlines()

    updated = {key: False for key in lines_to_update.keys()}

    for i in range(len(content)):
        for pattern, new_content in lines_to_update.items():
            if not updated[pattern] and re.match(pattern, content[i]):
                content[i] = new_content
                updated[pattern] = True
        if all(updated.values()):
            break

    with open(ippack_tcl, "w") as f:
        f.writelines(content)

    return pack_dir, os.path.relpath(ippack_tcl, start=pack_dir), os.path.relpath(correct_paths["output_xo"], start=pack_dir)

