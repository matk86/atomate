# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

"""
This module defines the NMR workflow
"""

from fireworks.core.firework import FWAction, Firework, Workflow

from atomate.utils.utils import get_logger
from atomate.vasp.fireworks import OptimizeFW, StaticFW


__author__ = 'Kiran Mathew'
__email__ = 'kmathew@lbl.gov'

logger = get_logger(__name__)


def get_wf_nmr(structure, vasp_input_set=None, db_file=None, user_vasp_settings=None):
    fws = []
    name = ""
    metadata = {}

    # for specifying quad moments
    structure = structure.get_sorted_structure()

    # Optimize: Triple Jump Relaxation to Converge to a Very Small Force (needed?)
    potcar_functional = "PBE"
    user_incar_settings_1 = {"EDIFF": -1e-6,
                             "EDIFFG": -0.1,
                             "ENCUT_ENHANCE_RATIO": 0.05,
                             "IBRION": 1,
                             "ISTART": 0,
                             "LCHARG": False,
                             "NELMIN": 5,
                             "NSW": 200,
                             "POTIM": 0.3,
                             "SIGMA": 0.1}
    user_incar_settings_2 = user_incar_settings_1.update({"ADDGRID": True,
                                                          "EDIFF": -1e-8,
                                                          "EDIFFG": -0.01,
                                                          "ENCUT_ENHANCE_RATIO": 0.2,
                                                          "IBRION": 3,
                                                          "IOPT": 7,
                                                          "ISYM": 0,
                                                          "POTIM": 0,
                                                          "SIGMA": 0.03})
    user_incar_settings_3 = user_incar_settings_2.update({"EDIFF": -1e-10,
                                                          "EDIFFG": -0.002,
                                                          "ENCUT_ENHANCE_RATIO": 0.3,
                                                          "FTIMEMAX": 0.1,
                                                          "MAXMOVE": 0.02,
                                                          "NELMIN": 10,
                                                          "NSW": 100,
                                                          "TIMESTEP": 0.01,
                                                          "FNMIN": 3,
                                                          "SIGMA": 0.01})
    opt_vasp_params_1 = {'user_incar_settings': user_incar_settings_1,
                         'user_kpoints_settings': {"length": 16},
                         'potcar_functional': potcar_functional}
    opt_vasp_params_2 = {'user_incar_settings': user_incar_settings_2,
                         'user_kpoints_settings': {"length": 24},
                         'potcar_functional': potcar_functional}
    opt_vasp_params_3 = {'user_incar_settings': user_incar_settings_2,
                         'user_kpoints_settings': {"length": 32},
                         'potcar_functional': potcar_functional}
    # TODO: add copy vasp outputs
    fw_opt_1 = OptimizeFW(structure, override_default_vasp_params=opt_vasp_params_1)
    fw_opt_2 = OptimizeFW(structure, override_default_vasp_params=opt_vasp_params_2, parents=fw_opt_1)
    fw_opt_3 = OptimizeFW(structure, override_default_vasp_params=opt_vasp_params_3, parents=fw_opt_2)

    fws.extend([fw_opt_1, fw_opt_2, fw_opt_3])

    # Compute chemical shift tensor
    cs_user_incar_settings = {"DQ": 0.001,
                              "EDIFF": -1.0e-10,
                              "ENCUT_ENHANCE_RATIO": 0.3,
                              "ICHIBARE": 1,
                              "ISMEAR": -5,
                              "ISTART": 0,
                              "ISYM": 0,
                              "LCHARG": False,
                              "LCHIMAG": True,
                              "LNMR_SYM_RED": True,
                              "LREAL": "AUTO",
                              "LWAVE": False,
                              "NELMIN": 10,
                              "NSLPLINE': True,"
                              "PREC": "ACCURATE",
                              "SIGMA": 0.01}
    cs_vasp_params = {'user_incar_settings': cs_user_incar_settings,
                      'user_kpoints_settings': {"length": 32},
                      'potcar_functional': potcar_functional}

    # Compute EFG tensor

    quad_efg = [get_nuclear_quadrupole_moment(el) for el in structure.types_of_specie]
    efg_user_incar_settings = {"ALGO": "FAST",
                               "EDIFF": -1.0e-10,
                               "ENCUT_ENHANCE_RATIO": 0.3,
                               "ISMEAR": -5,
                               "ISTART": 0,
                               "ISYM": 0,
                               "LCHARG": False,
                               "LEFG": True,
                               "QUAD_EFG": quad_efg,
                               "LREAL": "AUTO",
                               "LWAVE": False,
                               "NELMIN": 10,
                               "PREC": "ACCURATE",
                               "SIGMA": 0.01}
    efg_vasp_params = {'user_incar_settings': efg_user_incar_settings,
                      'user_kpoints_settings': {"length": 32},
                      'potcar_functional': potcar_functional}
    fw_cs = StaticFW(structure, vasp_input_set_params=cs_vasp_params, prev_calc_loc=True, parents=fw_opt_3)
    fw_efg = StaticFW(structure, vasp_input_set_params=efg_vasp_params, prev_calc_loc=True, parents=fw_opt_3)

    fws.extend([fw_cs, fw_efg])

    return Workflow(fws, name=name, metadata=metadata)


def get_nuclear_quadrupole_moment(element, isotope=None):
    QUAD_MOM = {
        "H": {"H-2": 2.860},
        "Li": {"Li-6": -0.808, "Li-7": -40.1},
        "Be": {"Be-9": 52.88},
        "B": {"B-10": 84.59, "B-11": 40.59},
        "C": {"C-11": 33.27},
        "N": {"N-14": 20.44},
        "O": {"O-17": -25.58},
        "F": {"F-19": -94.2},
        "Ne": {"Ne-21": 101.55},
        "Na": {"Na-23": 104.1},
        "Mg": {"Mg-25": 199.4},
        "Al": {"Al-27": 146.6},
        "S": {"S-33": -67.8, "S-35": 47.1},
        "Cl": {"Cl-35": -81.65, "Cl-37": -64.35},
        "K": {"K-39": 58.5, "K-40": -73.0, "K-41": 71.1},
        "Ca": {"Ca-41": -66.5, "Ca-43": -40.8},
        "Sc": {"Sc-45": -220.2},
        "Ti": {"Ti-47": 302.10, "Ti-49": 247.11},
        "V": {"V-50": 210.40, "V-51": -52.10},
        "Cr": {"Cr-53": -150.50},
        "Mn": {"Mn-55": 330.10},
        "Fe": {"Fe-57": 160.0},
        "Co": {"Co-59": 420.30},
        "Ni": {"Ni-61": 162.15},
        "Cu": {"Cu-63": -220.15, "Cu-65": -204.14},
        "Zn": {"Zn-67": 150.15},
        "Sr": {"Sr-87": 305.2},
        "In": {"In-113": 759.8, "In-115": 770.8},
        "Sn": {"Sn-119": -132.1},
        "Sb": {"Sb-121": -543.11, "Sb-123": -692.14},
        "I": {"I-127": -696.12, "I-129": -604.10},
        "La": {"La-139": 200.6},
        "Hg": {"Hg-201": 387.6},
        "Ra": {"Ra-223": 1210.3}}

    if element not in QUAD_MOM:
        return 0.0

    d = QUAD_MOM[element]

    if  len(d) > 1:
        if isotope is not None:
            if isotope in list(d.keys()):
                return d[isotope]
            else:
                raise ValueError(isotope)
        else:
            isotopes = list(d.keys())
            isotopes.sort(key=lambda x: int(x.split("-")[1]), reverse=False)
            return d[isotopes[0]]
    else:
        return list(d.values())[0]
