
from importlib import reload
import kntr.kntr_tigerFinalize
import kntr.kntr_slenderLorisFinalize
import utils
import tools


def reload_kntr():
    reload(kntr)
    print("✅ Reloaded kntr.kntr_tigerFinalize")

# UTILS

def dev_reload_all():
    import importlib
    import kntr, utils, tools
    from bootstrap import reload_package
    reload_package(utils)
    reload_package(tools)
    reload_package(kntr)
    importlib.reload(main)
    print("🔁 All tools reloaded.")



# CORE

def rigx_tagManager():
    ui.rigx_tagTeam_UI.show_tag_manager()




def displayMode():
    utils.rigx_displayMode.ModelVisibilityTool()


def dynMatrixParent():
    utils.rigx_dynamicMatrixParent.MatrixDynParent()


def rigxRename():
    tools.rigx_renameTool.launch_renameTool()


def mirrorVolumeJoint():
    utils.rigx_mirrorVolumeJoint.show_mirror_ui()

def coreFinalize(asset_name):
    utils.rigx_publishFinalize.rigx_publish(asset_name)
    utils.rig.utils_rig.rigx_create_anim_set()


# FOR KNTR
# def kntr_tigerFinalize():
#     kntr.kntr_tigerFinalize.kntr_tigerFinalize()

# def kntr_slenderLorisFinalize():
#     kntr.kntr_slenderLorisFinalize.kntr_slenderLorisFinalize()

# def kntr_bisonFinalize():
#     kntr.kntr_bisonFinalize.kntr_bisonFinalize()
