import os, sys

def purge_path(env_var, keyword:str):
    """
    Remove all paths containing the keyword from the given environment variable.
    Only works for the PATH and LD_LIBRARY_PATH environment variables.
    """
    if env_var not in ["PATH", "LD_LIBRARY_PATH"]:
        raise ValueError(f"Invalid environment variable name: {env_var}."
                         "Must be 'PATH' or 'LD_LIBRARY_PATH'.")
    path_env = os.environ.get(env_var, "")
    paths = path_env.split(":")
    new_paths = []
    for p in paths:
        if keyword not in p:
            new_paths.append(p)
    new_path_env = ":".join(new_paths)
    os.environ[env_var] = new_path_env

def purge_env():
    """
    Remove all Xilinx-related environment variables.
    """
    for env_var in ["PATH", "LD_LIBRARY_PATH"]:
        purge_path(env_var, "Vitis")
        purge_path(env_var, "vitis")
