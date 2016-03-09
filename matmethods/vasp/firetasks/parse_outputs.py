import json
import os

import zlib

import gridfs
from monty.json import MontyEncoder
from monty.os.path import zpath
from pymongo import MongoClient

from fireworks import FireTaskBase
from fireworks.utilities.fw_serializers import DATETIME_HANDLER
from fireworks.utilities.fw_utilities import explicit_serialize
from matgendb.creator import VaspToDbTaskDrone
from matgendb.util import get_settings
from matmethods.utils.utils import env_chk
from pymatgen.io.vasp import Vasprun

__author__ = 'Anubhav Jain <ajain@lbl.gov>'


@explicit_serialize
class VaspToDbTask(FireTaskBase):
    """
    Enter a VASP run into the database. By default, the VASP directory is assumed to be the current directory.

    Optional params:
        db_file (str): path to file containing the database credentials. Supports env_chk. Default: write data to JSON file.
        vasp_dir (str): path to dir (on current filesystem) that contains VASP output files. Default: use current working directory.
        vasp_loc (str OR bool): if True will set most recent vasp_loc. If str search for the most recent vasp_loc with the matching name
        parse_dos (bool): whether to parse the DOS and store in GridFS. Defaults to False.
        bandstructure_mode (str): Set to "uniform" for uniform band structure. Set to "line" for line mode. If not set, band structure will not be parsed.
        additional_fields (dict): dict of additional fields to add
    """

    def run_task(self, fw_spec):

        # get the directory that contains the VASP dir to parse
        vasp_dir = os.getcwd()

        if "vasp_dir" in self:
            vasp_dir = self["vasp_dir"]
        elif self.get("vasp_loc"):
            if isinstance(self["vasp_loc"], basestring):
                for doc in reversed(fw_spec["vasp_locs"]):
                    if doc["name"] == self["vasp_loc_name"]:
                        vasp_dir = doc["path"]
                        break
            else:
                vasp_dir = fw_spec["vasp_locs"][-1]["path"]

        # parse the VASP directory
        print("PARSING DIRECTORY: {}".format(vasp_dir))

        # get the database connection
        db_file = env_chk(self.get('db_file'), fw_spec)

        # TODO: Many important options of VaspToDbTaskDrone are not yet supported

        if not db_file:
            drone = VaspToDbTaskDrone(simulate_mode=True)
            task_doc = drone.get_task_doc(vasp_dir)
            with open("task.json", "w") as f:
                f.write(json.dumps(task_doc, default=DATETIME_HANDLER))

        else:
            d = get_settings(db_file)
            drone = VaspToDbTaskDrone(host=d["host"], port=d["port"],  database=d["database"], user=d.get("admin_user"),
                                      password=d.get("admin_password"), collection=d["collection"], additional_fields=self.get("additional_fields"),
                                      parse_dos=self.get("parse_dos", False), compress_dos=1)
            t_id = drone.assimilate(vasp_dir)
            print("Finished parsing with task_id: {}".format(t_id))

            if self.get("bandstructure_mode"):
                print("Attempting to parse band structure...")
                # connect to output database for further processing
                conn = MongoClient(d["host"], d["port"])
                db = conn[d["database"]]
                if "admin_user" in d:
                    db.authenticate(d["admin_user"], d["admin_password"])
                tasks = db[d["collection"]]

                state = tasks.find_one({"task_id": t_id}, {"state": 1})["state"]
                if state != "successful":
                    print "Skipping band structure insertion; task was not successful"
                else:
                    vasprun = Vasprun(zpath(os.path.join(vasp_dir, "vasprun.xml")), parse_eigen=True, parse_projected_eigen=True)
                    bs=vasprun.get_band_structure(line_mode=(self["bandstructure_mode"] == "line"))
                    bs_json = json.dumps(bs.as_dict(), cls=MontyEncoder)
                    bs_compress = zlib.compress(bs_json, 1)
                    fs = gridfs.GridFS(db, "bandstructure_fs")
                    bs_id = fs.put(bs_compress)
                    tasks.find_one_and_update({"task_id": t_id}, {"$set": {"calculations.0.bandstructure_fs_id": bs_id, "calculations.0.bandstructure_compression": "zlib"}})
                    print("Finished parsing band structure.")