
from __future__ import print_function, absolute_import # Compatibility with python 2 and 3
import sys
import numpy, scipy.constants
import os
import logging
logger = logging.getLogger('condor')
logger.setLevel("WARNING")

import condor

SAVE_OUTPUT = False

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
MAP3D_LOCATION = os.path.join(TESTS_DIR, "..", "examples", "map3d.h5")


def test_compare_spheroid_with_map(tolerance = 0.15):
    """
    Compare the output of two diffraction patterns, one simulated with the direct formula and the other one from a 3D refractive index map on a regular grid
    """
    src = condor.Source(wavelength=0.1E-9, pulse_energy=1E-3, focus_diameter=1E-6)
    det = condor.Detector(distance=0.5, pixel_size=750E-6, nx=100, ny=100, cx=45, cy=59)
    angle_d = 72.
    angle = angle_d/360.*2*numpy.pi
    rotation_axis = numpy.array([0.43,0.643,0.])
    rotation_axis = rotation_axis / condor.utils.linalg.length(rotation_axis)
    quaternion = condor.utils.rotation.quat(angle,rotation_axis[0],rotation_axis[1], rotation_axis[2])
    rotation_values = numpy.array([quaternion])
    rotation_formalism = "quaternion"
    rotation_mode = "extrinsic"
    short_diameter = 25E-9*12/100.
    long_diameter = 2*short_diameter
    spheroid_diameter   = condor.utils.spheroid_diffraction.to_spheroid_diameter(short_diameter/2.,long_diameter/2.)
    spheroid_flattening = condor.utils.spheroid_diffraction.to_spheroid_flattening(short_diameter/2.,long_diameter/2.)
    # Ideal spheroid
    par = condor.ParticleSpheroid(diameter=spheroid_diameter, material_type="water", flattening=spheroid_flattening, rotation_values=rotation_values, rotation_formalism=rotation_formalism, rotation_mode=rotation_mode)
    s = "particle_spheroid"
    E = condor.Experiment(src, {s : par}, det)
    res = E.propagate()
    F_ideal = res["entry_1"]["data_1"]["data_fourier"]
    # Map (spheroid)
    par = condor.ParticleMap(diameter=spheroid_diameter, material_type="water", flattening=spheroid_flattening, geometry="spheroid", rotation_values=rotation_values, rotation_formalism=rotation_formalism, rotation_mode=rotation_mode)
    s = "particle_map_spheroid"
    E = condor.Experiment(src, {s : par}, det)
    res = E.propagate()
    F_map = res["entry_1"]["data_1"]["data_fourier"]
    # Compare
    I_ideal = abs(F_ideal)**2
    I_map = abs(F_map)**2
    if SAVE_OUTPUT:
        import matplotlib.pyplot as pypl
        pypl.imsave("./Ispheroid_sph.png", abs(I_ideal))
        pypl.imsave("./Ispheroid_map.png", abs(I_map))
    diff = I_ideal-I_map
    err = abs(diff).sum() / ((I_ideal.sum()+I_map.sum())/2.)
    assert err < tolerance

def test_compare_atoms_with_map(tolerance = 0.1):
    """
    Compare the output of two diffraction patterns, one simulated with descrete atoms (spsim) and the other one from a 3D refractive index map on a regular grid.
    """
    src = condor.Source(wavelength=0.1E-9, pulse_energy=1E-3, focus_diameter=1E-6)
    det = condor.Detector(distance=0.5, pixel_size=750E-6, nx=100, ny=100, cx=45, cy=59)
    angle_d = 72.
    angle = angle_d/360.*2*numpy.pi
    rotation_axis = numpy.array([0.43,0.643,0.])
    rotation_axis = rotation_axis / condor.utils.linalg.length(rotation_axis)
    quaternion = condor.utils.rotation.quat(angle,rotation_axis[0],rotation_axis[1], rotation_axis[2])
    rotation_values = numpy.array([quaternion])
    rotation_formalism = "quaternion"
    rotation_mode = "extrinsic"
    short_diameter = 25E-9*12/100.
    long_diameter = 2*short_diameter
    N_long = 20
    N_short = int(round(short_diameter/long_diameter * N_long))
    dx = long_diameter/(N_long-1)
    massdensity = condor.utils.material.get_atomic_mass("H")*scipy.constants.value("atomic mass constant")/dx**3
    # Map
    map3d = numpy.zeros(shape=(N_long,N_long,N_long))
    map3d[:N_short,:,:N_short] = 1.
    map3d[N_short:N_short+N_short,:N_short,:N_short] = 1.
    par = condor.ParticleMap(diameter=long_diameter, material_type="custom", massdensity=massdensity, atomic_composition={"H":1.}, geometry="custom", map3d=map3d, dx=dx, rotation_values=rotation_values, rotation_formalism=rotation_formalism, rotation_mode=rotation_mode)
    s = "particle_map_custom"
    E = condor.Experiment(src, {s : par}, det)
    res = E.propagate()
    F_map = res["entry_1"]["data_1"]["data_fourier"]
    # Atoms
    Z1,Y1,X1 = numpy.meshgrid(numpy.linspace(0, short_diameter, N_short),
                              numpy.linspace(0, long_diameter,   N_long),
                              numpy.linspace(0, short_diameter, N_short),
                              indexing="ij")
    Z2,Y2,X2 = numpy.meshgrid(numpy.linspace(0, short_diameter, N_short) + long_diameter/2.,
                              numpy.linspace(0, short_diameter, N_short),
                              numpy.linspace(0, short_diameter, N_short),
                              indexing="ij")
    Z = numpy.concatenate((Z1.ravel(),Z2.ravel()))
    Y = numpy.concatenate((Y1.ravel(),Y2.ravel()))
    X = numpy.concatenate((X1.ravel(),X2.ravel()))
    atomic_positions = numpy.array([[x,y,z] for x,y,z in zip(X.ravel(),Y.ravel(),Z.ravel())])
    atomic_numbers   = numpy.ones(atomic_positions.size//3, dtype=numpy.int16)
    par = condor.ParticleAtoms(atomic_positions=atomic_positions, atomic_numbers=atomic_numbers, rotation_values=rotation_values, rotation_formalism=rotation_formalism, rotation_mode=rotation_mode)
    s = "particle_atoms"
    E = condor.Experiment(src, {s : par}, det)
    res = E.propagate()
    F_atoms = res["entry_1"]["data_1"]["data_fourier"]
    # Compare
    I_atoms = abs(F_atoms)**2
    I_map = abs(F_map)**2
    diff = I_atoms-I_map
    err = abs(diff).sum() / ( ( I_atoms.sum() + I_map.sum() ) / 2. )
    if SAVE_OUTPUT:
        import matplotlib.pyplot as pypl
        pypl.imsave("./Iatoms_mol.png", abs(I_atoms))
        pypl.imsave("./Iatoms_map.png", abs(I_map))
    assert err < tolerance
    
# DEVELOPMENT (CURRENTLY WITHOUT INTERPOLATION)
def test_map_interpolation(tolerance=0.1):
    import logging
    logger = logging.getLogger("condor")
    logger.setLevel("DEBUG")
    src = condor.Source(wavelength=10.0E-9, pulse_energy=1E-3, focus_diameter=1E-6)
    det = condor.Detector(distance=1.0, pixel_size=300E-6, nx=256, ny=256)
    par = condor.ParticleMap(diameter=600E-9, material_type="cell", geometry="custom",
                             map3d_filename=MAP3D_LOCATION, map3d_dataset="data", dx=5E-9)
    s = "particle_map"
    E = condor.Experiment(src, {s : par}, det)
    res0 = E.propagate()
    I0 = res0["entry_1"]["data_1"]["data"]
    # Now without interpolation
    print("NOW WITHOUT INTERPOLATION")
    condor.particle.particle_map.ENABLE_MAP_INTERPOLATION = False
    src = condor.Source(wavelength=10.0E-9, pulse_energy=1E-3, focus_diameter=1E-6)
    det = condor.Detector(distance=1.0, pixel_size=300E-6, nx=256, ny=256)
    par = condor.ParticleMap(diameter=600E-9, material_type="cell", geometry="custom",
                             map3d_filename=MAP3D_LOCATION, map3d_dataset="data", dx=5E-9)
    s = "particle_map"
    E = condor.Experiment(src, {s : par}, det)
    res1 = E.propagate()
    I1 = res1["entry_1"]["data_1"]["data"]
    if SAVE_OUTPUT:
        import matplotlib.pyplot as pypl
        pypl.imsave("./Imap_interp.png", abs(I0), vmin=0, vmax=I0.max())
        pypl.imsave("./Imap_no_interp.png", abs(I1), vmin=0, vmax=I0.max())
    err = abs(I0-I1).sum() / ((I0+I1).sum() / 2.)
    assert err < tolerance
