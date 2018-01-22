# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

"""
This module defines the NMR workflow
"""

from fireworks.core.firework import FWAction, Firework, Workflow

from atomate.utils.utils import get_logger
from atomate.vasp.fireworks import OptimizeFW


__author__ = 'Kiran Mathew'
__email__ = 'kmathew@lbl.gov'

logger = get_logger(__name__)


def get_wf_nmr(structure, vasp_input_set=None, db_file=None, user_vasp_settings=None):
    fws = []
    name = ""
    metadata = {}

    #Composition(snl.structure.composition.reduced_formula).alphabetical_formula

    # Optimize: Triple Jump Relaxation to Converge to a Very Small Force (needed?)
    for istep in [1, 2, 3]:
        fw = OptimizeFW(structure)
        fws.append(fw)
        #fw = VaspToDb()
        #fws.append(fw)
        # Geometry Optimization
        #copy_contcar = istep >= 2
        #vasp_fw = get_nmr_vasp_fw(geom_calc_fwid, copy_contcar, istep, nick_name,
        #                          copy.deepcopy(parameters), priority, copy.deepcopy(structure),
        #                          additional_run_tags)
        # insert into DB
        #task_class = TripleJumpRelaxVaspToDBTask
        #db_fw = get_nmr_db_fw(nick_name, geom_db_fwid, prev_task_type, priority, task_class)

    # Compute CS and EFG tensors
    fw_cs = NMRFW(structure)
    fw_efg = NMRFW(structure)
    fws.extend([fw_cs, fw_efg])

    #vasp_fw = get_nmr_vasp_fw(nmr_calc_fwid, True, istep, nick_name, copy.deepcopy(parameters),
    #                              priority, copy.deepcopy(structure), additional_run_tags)

    return Workflow(fws, name=name, metadata=metadata)
