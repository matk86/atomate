# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

"""
First attempt at QChem Drone for atomate
"""

import os

from fnmatch import fnmatch
from collections import OrderedDict



from pymatgen.apps.borg.hive import AbstractDrone

from matgendb.creator import get_uri

from atomate.utils.utils import get_logger
from pymatgen.io.qchem import QcInput, QcOutput

__author__ = 'Shyam Dwaraknath'
__email__ = 'shyamd@lbl.gov
__date__ = 'Mar 27, 2016'
__version__ = "0.1.0"

logger = get_logger(__name__)


class QChemDrone(AbstractDrone):
    """
    Simple Qchem drone
    """

    __version__ = 0.1  # note: the version is inserted into the task doc

    # Schema def of important keys and sub-keys; used in validation
    schema = {
        "root": {
            "schema", "dir_name", "inputs", "outputs", "version",
        }
    }

    def __init__(self, additional_fields=None, use_full_uri=True):
        self.additional_fields = additional_fields or {}
        self.use_full_uri = use_full_uri


    def assimilate(self, path):
        """
        Adapted from matgendb.creator
        Parses vasp runs(vasprun.xml file) and insert the result into the db.
        Get the entire task doc from the vasprum.xml and the OUTCAR files in the path.
        Also adds some post-processed info.

        Args:
            path (str): Path to the directory containing vasprun.xml and OUTCAR files

        Returns:
            (dict): a task dictionary
        """

        input_files = [QcInput.from_file(f) for f in self.filter_files(path,file_pattern="qc.in")]
        output_files = [QcOutput.from_file(f) for f in self.filter_files(path,file_pattern="qc.out")]
        logger.info("Getting task doc for base dir :{}".format(path))

        return self.generate_doc(path,input_files,output_files)



    def filter_files(self, path, file_pattern="vasprun.xml"):
        """
        Find the files that match the pattern in the given path and
        return them in an ordered dictionary. The searched for files are
        filtered by the run types defined in self.runs. e.g. ["relax1", "relax2", ...].
        Only 2 schemes of the file filtering is enabled: searching for run types
        in the list of files and in the filenames. Modify this method if more
        sophisticated filtering scheme is needed.

        Args:
            path (string): path to the folder
            file_pattern (string): files to be searched for

        Returns:
            OrderedDict of the names of the files to be processed further.
            The key is set from list of run types: self.runs
        """
        processed_files = OrderedDict()
        files = os.listdir(path)
        for r in self.runs:
            # try subfolder schema
            if r in files:
                for f in os.listdir(os.path.join(path, r)):
                    if fnmatch(f, "{}*".format(file_pattern)):
                        processed_files[r] = os.path.join(r, f)
            # try extension schema
            else:
                for f in files:
                    if fnmatch(f, "{}.{}*".format(file_pattern, r)):
                        processed_files[r] = f
        if len(processed_files) == 0:
            # get any matching file from the folder
            for f in files:
                if fnmatch(f, "{}*".format(file_pattern)):
                    processed_files['standard'] = f
        return processed_files

    def generate_doc(self, dir_name, inputs,outputs):
        """
        Adapted from matgendb.creator.generate_doc
        """

        try:
            # basic properties, incl. calcs_reversed and run_stats
            fullpath = os.path.abspath(dir_name)
            if self.use_full_uri:
                fullpath = get_uri(dir_name)
            d = {k: v for k, v in self.additional_fields.items()}
            d["schema"] = {"code": "atomate", "version": QchemDrone.__version__}
            d["dir_name"] = fullpath
            d["inputs"] = [input.as_dict() for input in inputs]
            d["outputs"] = [output.as_dict() for output in outputs]
            return d
        
        except Exception:
            import traceback
            logger.error(traceback.format_exc())
            logger.error("Error in " + os.path.abspath(dir_name) + ".\n" + traceback.format_exc())
            return None


    def as_dict(self):
        init_args = {
            "additional_fields": self.additional_fields,
            "use_full_uri": self.use_full_uri}

        return {"@module": self.__class__.__module__,
                "@class": self.__class__.__name__,
                "version": self.__class__.__version__,
                "init_args": init_args
                }

    @classmethod
    def from_dict(cls, d):
        return cls(**d["init_args"])
