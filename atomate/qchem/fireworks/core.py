# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

"""
Defines standardized Fireworks that can be chained easily to perform various
sequences of QChem calculations.
"""

from fireworks import Firework
from pymatgen.io.qchem import QcInput, QcTask

from atomate.qchem.firetasks.write_inputs import WriteQchemFromIOSet
from atomate.common.firetasks.run_calc import RunCommand
from atomate.common.firetasks.parse_outputs import ToDbTask
from atomate.qchem.drones import QChemDrone


class OptimizeFW(Firework):
    def __init__(self, molecule, name="structure optimization", qchem_cmd="qchem", db_file=None, parents=None,
                 **kwargs):
        """
        Optimize the given molecule
        
        Args:
            molecule (Molecule): Input molecule
            name (str) : Name for the firework
            qchem_cmd(str): Command to run Qchem
            db_file (str): Path to file specifying db credentials to place output parsing.
            parents ([Firework]): Parents of this particular Firework.
            \*\*kwargs: Other kwargs that are passed to Firework.__init__.
        """

        t = []
        t.append(WriteQchemFromIOSet(qc_input=QcInput(jobs=QcTask(molecule=molecule, jobtype='opt'))))
        t.append(RunCommand(cmd=qchem_cmd))
        t.append(ToDbTask(db_file=db_file, additional_fields={"task_label": name}, drone=QChemDrone(),
                          mmdb="atomate.utils.database.CalcDb"))
        super(OptimizeFW, self).__init__(t, parents=parents, name=name, **kwargs)