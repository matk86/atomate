def get_nmr_vasp_fw(fwid, copy_contcar, istep, nick_name, parameters, priority, structure, additional_run_tags):
    spec = snl_to_nmr_spec(structure, istep, parameters, additional_run_tags)
    trackers = [Tracker('FW_job.out'), Tracker('FW_job.error'), Tracker('vasp.out'), Tracker('OUTCAR'),
                Tracker('OSZICAR'), Tracker('OUTCAR.relax1'), Tracker('OUTCAR.relax2')]
    spec['_priority'] = priority
    spec['_queueadapter'] = QA_VASP
    spec['_trackers'] = trackers
    tasks = [DictVaspSetupTask()]
    functional = parameters.get("functional", "PBE")
    spec["functional"] = functional
    if functional != "PBE":
        tasks.append(ScanFunctionalSetupTask())
    tasks.append(get_custodian_task(spec))
    vasp_fw = Firework(tasks, spec, name=get_slug(nick_name + '--' + spec['task_type']),
                       fw_id=fwid)
    return vasp_fw


def get_nmr_db_fw(nick_name, fwid, prev_task_type, priority, task_class):
    trackers_db = [Tracker('FW_job.out'), Tracker('FW_job.error')]
    spec = {'task_type': 'VASP db insertion', '_priority': priority * 2,
            '_allow_fizzled_parents': True, '_queueadapter': QA_DB, "_dupefinder": DupeFinderDB().to_dict(),
            '_trackers': trackers_db}
    db_fw = Firework([task_class(parameters={"update_input": False})], spec, name=get_slug(nick_name + '--' + spec['task_type'] +
                                                         '--' + prev_task_type),
                     fw_id=fwid)
    return db_fw