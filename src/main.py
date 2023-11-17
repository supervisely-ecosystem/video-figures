import os
from os.path import join

from dotenv import load_dotenv

import supervisely as sly

# for convenient debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api()

# check the workspace exists
workspace_id = sly.env.workspace_id()
workspace = api.workspace.get_info_by_id(workspace_id)
if workspace is None:
    print("you should put correct workspaceId value to local.env")
    raise ValueError(f"Workspace with id={workspace_id} not found")

################################    Part 1    ######################################
###################    create empty project and dataset    #########################
############################     upload video    ###################################

# create empty project and dataset on server
project = api.project.create(
    workspace.id,
    name="Demo",
    type=sly.ProjectType.VIDEOS,
    change_name_if_conflict=True,
)
dataset = api.dataset.create(project.id, name="orange & kiwi")
print(f"Project has been sucessfully created, id={project.id}")


# upload video to the dataset on server
video_path = "data/orange_kiwi.mp4"
video_name = sly.fs.get_file_name_with_ext(video_path)
video_info = api.video.upload_path(dataset.id, video_name, video_path)
print(f"Video has been sucessfully uploaded, id={video_info.id}")


# create annotation classes
kiwi_obj_cls = sly.ObjClass("kiwi", sly.Rectangle, color=[0, 0, 255])
orange_obj_cls = sly.ObjClass("orange", sly.Bitmap, color=[255, 255, 0])


# create project meta with all classes and upload them to server
project_meta = sly.ProjectMeta(obj_classes=[kiwi_obj_cls, orange_obj_cls])
api.project.update_meta(project.id, project_meta.to_json())


################################    Part 2    #######################################
######################  Create object figures on frames. #############################
################### Create collections of objects and frames.  #######################


# prepare path with masks
masks_dir = "data/masks"

# prepare rectangle points for 10 demo frames
points = [
    [136, 632, 350, 817],
    [139, 655, 355, 842],
    [145, 672, 361, 864],
    [158, 700, 366, 885],
    [153, 700, 367, 885],
    [156, 724, 375, 914],
    [164, 745, 385, 926],
    [177, 770, 396, 944],
    [189, 793, 410, 966],
    [199, 806, 417, 980],
]

# create VideoObjects
orange = sly.VideoObject(orange_obj_cls)
kiwi = sly.VideoObject(kiwi_obj_cls)

# create frames and figures
frames = []
for mask in os.listdir(masks_dir):
    fr_index = int(sly.fs.get_file_name(mask).split("_")[-1])
    mask_path = join(masks_dir, mask)

    bitmap = sly.Bitmap.from_path(mask_path)
    bbox = sly.Rectangle(*points[fr_index])

    mask_figure = sly.VideoFigure(orange, bitmap, fr_index)
    bbox_figure = sly.VideoFigure(kiwi, bbox, fr_index)

    frame = sly.Frame(fr_index, figures=[mask_figure, bbox_figure])
    frames.append(frame)

objects = sly.VideoObjectCollection([kiwi, orange])
frames = sly.FrameCollection(frames)


################################    Part 3    #####################################
###########################  Create video annotation  #############################
################ and upload annotation to the video on server #####################

frame_size, vlength = sly.video.get_image_size_and_frames_count(video_path)

# create result video annotation
video_ann = sly.VideoAnnotation(
    img_size=frame_size,
    frames_count=vlength,
    objects=objects,
    frames=frames,
)

# upload annotation to the video on server
api.video.annotation.append(video_info.id, video_ann)
print(f"Annotation has been sucessfully uploaded to the video {video_name}")

# download annotation from server by video ID
key_id_map = sly.KeyIdMap() # required to convert annotations downloaded from server
video_ann_json = api.video.annotation.download(video_info.id)
video_ann = sly.VideoAnnotation.from_json(video_ann_json, project_meta, key_id_map)
