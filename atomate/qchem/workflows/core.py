# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

"""
This module defines the base qchem workflows
"""


from atomate.utils.utils import get_logger, append_fw_wf
from fireworks.core.firework import Workflow
from atomate.qchem.fireworks.core import OptimizeFW
__author__ = 'Shyam Dwaraknath'
__email__ = 'shyamd@lbl.gov'


logger = get_logger(__name__)


def get_wf_optimize(molecule):

    wfname ="Molecule Optimization: {}".format(molecule.composition.formula)
    fws = [OptimizeFW(molecule,qchem_cmd="<<qchem>>",db_file="<<db_file>>")]
    return Workflow(fws, name=wfname)