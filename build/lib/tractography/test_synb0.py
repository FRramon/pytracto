import os
from python_on_whales import docker

freesurfer_bin_path = '/Users/francoisramon/freesurfer'
FS_license_file = os.path.join(freesurfer_bin_path, 'license.txt')

input_synb0 = '/Users/francoisramon/Desktop/Thèse/dMRI_pipeline/test_synthb0/inputs'
output_synb0 = '/Users/francoisramon/Desktop/Thèse/dMRI_pipeline/test_synthb0/outputs'
           
output_generator = docker.run(
    "leonyichencai/synb0-disco:v3.0",
    ["--user", str(os.getuid()) + ":" + str(os.getgid())],
    volumes=[(input_synb0, "/INPUTS"), (output_synb0, "/OUTPUTS"), (FS_license_file, "/extra/freesurfer/license.txt")],
    remove=True, stream=True,
    )
for stream_type, stream_content in output_generator:
    print(f"Stream type: {stream_type}, stream content: {stream_content}")



