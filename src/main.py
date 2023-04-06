import os

import supervisely as sly
from dotenv import load_dotenv
from os.path import join
from supervisely.video_annotation.key_id_map import KeyIdMap

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
################################    ------    ######################################

# create empty project and dataset on server
project = api.project.create(
    workspace.id,
    name="Demo",
    type=sly.ProjectType.VIDEOS,
    change_name_if_conflict=True,
)
dataset = api.dataset.create(project.id, name="orange & kiwi")
print(f"Project has been sucessfully created, id={project.id}")

# create ObjClasses and VideoObjects
kiwi_obj_cls = sly.ObjClass("kiwi", sly.Rectangle, color=[0, 0, 255])
orange_obj_cls = sly.ObjClass("orange", sly.Bitmap, color=[255, 255, 0])

orange = sly.VideoObject(orange_obj_cls)
kiwi = sly.VideoObject(kiwi_obj_cls)

# create project meta with all classes and upload them to server
project_meta = sly.ProjectMeta(obj_classes=[kiwi_obj_cls, orange_obj_cls])
api.project.update_meta(project.id, project_meta.to_json())


################################    Part 2    ######################################
####################    create rectangle, mask    #########################
######################  on video "data/orange_kiwi.mp4"   ##########################

# prepare demo video (there are 10 frames in this demo video)
video_path = "data/orange_kiwi.mp4"

# prepare path with masks
masks_dir = "data/masks"

# prepare rectangle points for 10 demo frames
points = [
    [632, 136, 817, 350],
    [655, 139, 842, 355],
    [672, 145, 864, 361],
    [700, 158, 885, 366],
    [700, 153, 885, 367],
    [724, 156, 914, 375],
    [745, 164, 926, 385],
    [770, 177, 944, 396],
    [793, 189, 966, 410],
    [806, 199, 980, 417],
]


# create frames and figures
figures = []
for fr_index, mask in enumerate(os.listdir(masks_dir)):
    mask_path = join(masks_dir, mask)

    bitmap = sly.Bitmap.from_path(mask_path)
    bbox = sly.Rectangle(*points[fr_index])

    mask_figure = sly.VideoFigure(orange, bitmap, fr_index)
    bbox_figure = sly.VideoFigure(kiwi, bbox, fr_index)

    frame = sly.Frame(fr_index, figures=[mask_figure, bbox_figure])
    figures.append(frame)

img_size, vlength = sly.video.get_image_size_and_frames_count(video_path)
objects = sly.VideoObjectCollection([kiwi, orange])
frames = sly.FrameCollection(figures)

# result video annotation
video_ann = sly.VideoAnnotation(
    img_size=img_size,
    frames_count=vlength,
    objects=objects,
    frames=frames,
)

# upload video to the dataset on server
video_name = sly.fs.get_file_name_with_ext(video_path)
video_info = api.video.upload_path(dataset.id, video_name, video_path)
print(f"Video has been sucessfully uploaded, id={video_info.id}")

# upload annotation to the video on server
api.video.annotation.append(video_info.id, video_ann)
print(f"Annotation has been sucessfully uploaded to the video {video_name}")
