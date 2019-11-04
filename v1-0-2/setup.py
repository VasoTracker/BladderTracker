import cx_Freeze
import sys
import matplotlib
import os
import glob
import json

#base = None
base = None#'Win32GUI'

#if sys.platform == 'Win32':
#    base = 'Win32GUI'

PythonPath = os.path.split(sys.executable)[0] #get python path

os.environ['TCL_LIBRARY'] = os.path.join(PythonPath,"tcl","tcl8.5")
os.environ['TK_LIBRARY']  = os.path.join(PythonPath,"tcl","tk8.5")

mkl_files_json_file = glob.glob(os.path.join(PythonPath, "conda-meta", "mkl-[!service]*.json"))[0] #json files that has mkl files list (exclude the "service" file)

mkl_omp_files_relative_path = os.path.join("Library", "bin")
mkl_omp_files = glob.glob(os.path.join(PythonPath, mkl_omp_files_relative_path, "libiomp*.dll")) #Without these, this error would appear: Intel MKL FATAL ERROR: Cannot load mkl_intel_thread.dll.

qt_platform_files_relative_path = os.path.join("Library", "plugins", "platforms")
qt_platform_files = glob.glob(os.path.join(PythonPath, qt_platform_files_relative_path, "*.dll")) #Qt necessary files

with open(mkl_files_json_file) as file:
    mkl_files_json_data = json.load(file)

numpy_mkl_dlls = mkl_files_json_data["files"] #get the list of files from the json data file

np_dlls_fullpath = list(map(lambda currPath: os.path.join(PythonPath, currPath), numpy_mkl_dlls)) #get the full path of these files

qt_platform_files_include_pairs = list(map(lambda currPath: (currPath, os.path.join("platforms", os.path.basename(currPath))), qt_platform_files)) #get the full path of these files


executables = [cx_Freeze.Executable("BladderTracker.py", base=base, icon="bladder_ICON.ico")]
additional_mods = ['cv2','atexit','numpy.core._methods', 'numpy.lib.format', "matplotlib.backends.backend_tkagg"]
excludes = ["winpty"]
#buildOptions = dict(include_files = ['SampleData/']) #folder,relative path. Use tuple like in the single file to set a absolute path.
includefiles = ["bladder_ICON.ico", "Start_up.bat",'SampleData/', 'BladderTracker_Temperature_Controller_Code', 'BladderTracker_Pressure_Monitor_V2/','Results/', 'Bladder_SPLASH.gif', 'OpenCV.cfg', 'MMConfig.cfg',
                'opencv_ffmpeg310_64.dll', 'opencv_ffmpeg320_64.dll'] + np_dlls_fullpath + qt_platform_files_include_pairs + mkl_omp_files

cx_Freeze.setup(
        name = "BladderTracker",
        options = {"build_exe": {"excludes": excludes,'includes': additional_mods, 
                    "packages":['skimage',"tkFileDialog","scipy","cv2","Tkinter", "matplotlib", "Queue","cytoolz"], 
                    "include_files":includefiles}},
        version = "1.0.2",
        description = "BladderTracker bladder imaging software",
        executables = executables    )


