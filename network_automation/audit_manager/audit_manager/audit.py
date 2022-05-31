import network_automation.audit_manager.audit_manager.getConfig as get_config

def do_audit(username, password, depth_levels=3):
    get_config.get_config(username, password, depth_levels)
    