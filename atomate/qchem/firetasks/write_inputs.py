# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

"""
This module defines tasks for writing Qchem
"""

from fireworks import FiretaskBase, explicit_serialize

__author__ = 'Shyam Dwaraknath'
__email__ = 'shyamd@lbl.gov'


@explicit_serialize
class WriteQchemFromIOSet(FiretaskBase):
    """
    Creatre QChem input files using pymatgen's
    
    Required params:
        qc_input (QcInput): Qchem Input Object
    """
    required_params = ["qc_input"]

    def run_task(self, fw_spec):
        self.qc_input.write_file("qc.in")