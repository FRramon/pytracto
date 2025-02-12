.. _structural_connectivity:

Structural Connectivity Matrix Construction
===================================================

1. Pipeline Adaptation According to MRI Data Type
---------------------------------------------------------
The initial functions of the pipeline are responsible for verifying the nature of the data. The user only needs to input the dimensions of the structural and diffusion MRI. These verifications include:

- Checking the number of unique **b-values**: single-shell or multi-shell data.
- Verifying the presence of required files.
- Validating MRI dimensions.

Several workflows have been developed to accommodate different cases:

- Multi-shell data & single phase encoding reversal.
- Multi-shell data & multiple phase encoding reversals.
- Multi-shell data with **b = 0** missing phase encoding reversal.
- Single-shell data.
- Single-shell data with **b = 0** missing phase encoding reversal.

The differences between these workflows are presented in subsequent steps.

2. Preprocessing
-----------------------
Diffusion MRI preprocessing consists of four steps:

1. **Denoising** using the MP-PCA method, reducing thermal noise.
2. **Gibbs ringing correction** [7], addressing artifacts appearing during the inverse Fourier transform in **k-space** to image space transition (ref).
3. **Susceptibility artifact correction** using FSL's **topup and eddy** algorithms (ref, [8]), applied when reversed-phase **b = 0 s/mm²** images are available. If unavailable (multi-shell synth & single-shell synth workflows), they are synthetically generated using **synb0-Disco** (ref) from the T1w image and **b = 0 s/mm²**.
4. **B1 field bias correction** is applied.

Workflow Differences Table::

    +--------------+----------------+------------------+------------+
    | Workflow     | Preprocessing  | FOD Estimation   | Tracking   |
    +==============+================+==================+============+
    | Multi 1 AP   | Eddy           | CSD MSMT        | SD_Stream  |
    +--------------+----------------+------------------+------------+
    | Multi n AP   | Eddy           | CSD MSMT        | SD_Stream  |
    +--------------+----------------+------------------+------------+
    | Multi Synth  | Synb0 + Eddy   | CSD MSMT        | SD_Stream  |
    +--------------+----------------+------------------+------------+
    | Single       | Eddy           | CSD             | SD_Stream  |
    +--------------+----------------+------------------+------------+
    | Single Synth | Synb0 + Eddy   | CSD             | SD_Stream  |
    +--------------+----------------+------------------+------------+

3. T1w Image Parcellation & Atlas Mapping
----------------------------------------------
T1-weighted anatomical images are parcellated using **Freesurfer 7.4.1’s recon-all algorithm** [9]. Cortical reconstruction enables the projection of cortical atlases such as **Schaefer 400** [10], as well as cortical/subcortical atlases like the **Destrieux Atlas** [11].

4. White Matter Tractography
-----------------------------------
White matter fiber reconstruction follows anatomical constraints, using **Constrained Spherical Deconvolution (CSD)** [12] and a **white matter/gray matter interface mask** for streamline initialization. Ten million streamlines are generated using two models:

- **Probabilistic Reconstruction**: iFOD2 [13].
- **Deterministic Reconstruction**: SD_Stream.

A **Spherical-deconvolution Informed Filtering of Tractogram (SIFT)** algorithm [14] refines results by adjusting streamline density to match expected fiber densities.

FOD Estimation and Tracking Table::

    +--------------+----------------------+------------------+----------------+
    | Workflow     | Response Estimation | FOD Estimation  | Tracking       |
    +==============+======================+==================+================+
    | Multi-Shell  | Dhollander           | CSD MSMT        | SD_Stream & iFOD2 |
    +--------------+----------------------+------------------+----------------+
    | Single-Shell | Tournier             | CSD             | SD_Stream      |
    +--------------+----------------------+------------------+----------------+

5. Microstructural Maps
------------------------------
Microstructural maps extract diffusion-related indices:

- **Diffusion Tensor Imaging (DTI)**: axial diffusivity (AD), radial diffusivity (RD), mean diffusivity (MD), fractional anisotropy (FA).
- **Multi-compartment models (for multi-shell data, b >= 2500 s/mm²)**: NODDI, SANDI, ActiveAx ([15], ref, ref). The **NODDI model** computes **neurite density index (NDI), free water fraction (FWF), and orientation dispersion index (ODI)** using **AMICO** [16].

6. Connectivity Matrix Construction
------------------------------------------
Connectivity matrices are generated using the **Destrieux Atlas**, mapped to diffusion space via nearest-neighbor interpolation. Streamlines connecting each pair of gray matter regions are counted, constructing a weighted connectivity matrix. Alternative weightings apply microstructural indices (FA, RD, NDI, etc.) along streamlines to characterize connectivity properties.

