# ----------------------------------------------------------------------------------------------------- 
# CONDOR 
# Simulator for diffractive single-particle imaging experiments with X-ray lasers
# http://xfel.icm.uu.se/condor/
# ----------------------------------------------------------------------------------------------------- 
# Copyright 2014 Max Hantke, Filipe R.N.C. Maia, Tomas Ekeberg
# Condor is distributed under the terms of the GNU General Public License
# ----------------------------------------------------------------------------------------------------- 
# General note:
#  All variables are in SI units by default. Exceptions explicit by variable name.
# ----------------------------------------------------------------------------------------------------- 

import sys, os, numpy, types, pickle, time, math, logging
logging.basicConfig(format='%(levelname)s: %(message)s')
logger = logging.getLogger('Condor')
from scipy import constants

def init_configuration():
    # Some global configuration variables
    #=============
    # are those really still needed?
    global PROPAGATION_MODE_PROJECTION
    PROPAGATION_MODE_PROJECTION = 0
    global PROPAGATION_MODE_3DSAMPLING
    PROPAGATION_MODE_3DSAMPLING = 1
    global CONDOR_DIR
    CONDOR_DIR = os.path.dirname(os.path.realpath(__file__))
    #=============
    # Load global dictionaries
    init_global_dictionaries()
    # Add path of Condor to sys.path
    sys.path.append(CONDOR_DIR+"/utils")
    
def init_global_dictionaries():
    # Load scattering factors and atomic masses from Henke tables
    unpickle_scattering_factors()
    # Realative atomic compositions of certain material types (order: H,C,N,O,P,S,Au)
    global DICT_atomic_composition
    DICT_atomic_composition = {'protein':[86,52,13,15,0,3,0],
                               'cell':[23,3,1,10,0,1,0], # Bergh et al. 2008
                               'latex':[1,1,0,0,0,0,0], 
                               'water':[2,0,0,1,0,0,0], 
                               'dna':[11,10,4,6,1,0,0],
                               'lipid':[69,36,0,6,1,0,0],
                               'genophore':[205,134,38,48,3,6,0],
                               'virus':[72.43,49.85,16.32,24.49,2.57,1.39,0],
                               'mimivirus':[23,3,1,10,0,1,0],
                               'carboxysome':[0.51,0.30,0.07,0.10,0.,0.02,0],
                               'sucrose':[22,12,0,11,0,0,0],
                               'gold':[0,0,0,0,0,0,1]}
    # Estimated mass densities of certain material types
    global DICT_massdensity
    DICT_massdensity = {'protein':1350,
                        'cell':1000,
                        'latex':1050,
                        'water':998,
                        'gold':19300,
                        'dna':1700,
                        'lipid':1000,
                        'genophore':1560,
                        'virus':1381,
                        'mimivirus':1100,
                        'carboxysome':1250,
                        'sucrose':1587}
    # More documentation needed!
    # The following material types should be defined more properly:
    # - 'virus': density = 1455 (Filipe's webpage)
    # - 'carboxysome' density = 1250 (guessed by Dirk, atomic composition deduced assuming protein and water being the only two components)
    global DICT_atomic_number
    DICT_atomic_number = {'H':1,
                          'He':2,
                          'Li':3,
                          'Be':4,
                          'B':5,
                          'C':6,
                          'N':7,
                          'O':8,
                          'F':9,
                          'Ne':10,
                          'Na':11,
                          'Mg':12,
                          'Al':13,
                          'Si':14,
                          'P':15,
                          'S':16,
                          'Cl':17,
                          'Ar':18,
                          'K':19,
                          'Ca':20,
                          'Sc':21,
                          'Ti':22,
                          'V':23,
                          'Cr':24,
                          'Mn':25,
                          'Fe':26,
                          'Co':27,
                          'Ni':28,
                          'Cu':29,
                          'Zn':30,
                          'Ga':31,
                          'Ge':32,
                          'As':33,
                          'Se':34,
                          'Br':35,
                          'Kr':36,
                          'Rb':37,
                          'Sr':38,
                          'Y':39,
                          'Zr':40,
                          'Nb':41,
                          'Mo':42,
                          'Tc':43,
                          'Ru':44,
                          'Rh':45,
                          'Pd':46,
                          'Ag':47,
                          'Cd':48,
                          'In':49,
                          'Sn':50,
                          'Sb':51,
                          'Te':52,
                          'I':53,
                          'Xe':54,
                          'Cs':55,
                          'Ba':56,
                          'La':57,
                          'Ce':58,
                          'Pr':59,
                          'Nd':60,
                          'Pm':61,
                          'Sm':62,
                          'Eu':63,
                          'Gd':64,
                          'Tb':65,
                          'Dy':66,
                          'Ho':67,
                          'Er':68,
                          'Tm':69,
                          'Yb':70,
                          'Lu':71,
                          'Hf':72,
                          'Ta':73,
                          'W':74,
                          'Re':75,
                          'Os':76,
                          'Ir':77,
                          'Pt':78,
                          'Au':79,
                          'Hg':80,
                          'Tl':81,
                          'Pb':82,
                          'Bi':83,
                          'Po':84,
                          'At':85,
                          'Rn':86,
                          'Fr':87,
                          'Ra':88,
                          'Ac':89,
                          'Th':90,
                          'Pa':91,
                          'U':92,
                          'Np':93,
                          'Pu':94,
                          'Am':95,
                          'Cm':96,
                          'Bk':97,
                          'Cf':98,
                          'Es':99,
                          'Fm':100,
                          'Md':101,
                          'No':102,
                          'Lr':103,
                          'Rf':104,
                          'Db':105,
                          'Sg':106,
                          'Bh':107,
                          'Hs':108,
                          'Mt':109,
                          'Ds':110,
                          'Rg':111,
                          'Cp':112,
                          'Uut':113,
                          'Uuq':114,
                          'Uup':115,
                          'Uuh':116,
                          'Uus':117,
                          'Uuo':118}


    # Physical constants [SI-units]
    global DICT_physical_constants
    DICT_physical_constants = {'e'    : constants.e,
                               'c'    : constants.c,
                               'h'    : constants.h,
                               're'   : constants.value("classical electron radius"),
                               'barn' : 1E-28,
                               'u'    : constants.value("atomic mass constant") }


def unpickle_scattering_factors():
    global DICT_atomic_mass
    DICT_atomic_mass = {}
    global DICT_scattering_factors
    DICT_scattering_factors = {}
    this_dir = os.path.dirname(os.path.realpath(__file__))
    ELEMENTS_FILE = open('%s/data/elements.dat' % this_dir,'r')
    DICT_atomic_mass,DICT_scattering_factors = pickle.load(ELEMENTS_FILE)
    F_MIN_ENERGY_EV = 0
    F_MAX_ENERGY_EV = 0
    for var in DICT_scattering_factors.values():
        if F_MIN_ENERGY_EV < var[0,0] or F_MIN_ENERGY_EV == 0: F_MIN_ENERGY_EV = var[0,0]
        if F_MAX_ENERGY_EV > var[-1,0] or F_MAX_ENERGY_EV == 0: F_MAX_ENERGY_EV = var[-1,0]