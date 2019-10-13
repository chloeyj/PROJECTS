from module import *
from utils import visualization_utils as vis_util
from PIL import Image
import scipy.misc
from utils import label_map_util
import os
from django.conf import settings

# LABEL MAP PATH
PATH_TO_LABELS = 'data/deepfashion_label_map_fine2.pbtxt'
# READ LABEL MAP
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)

# load a (frozen) Tensorflow model into memory

def detect_image(fname):

    # initialize object_detection class variable
    ob = object_detection()

    # open image
    image = Image.open(fname)

    # convert image into numpy array
    try :
        image_np = ob.load_image_into_numpy_array(image)
    except ValueError as e:
        return None, None

    # run detection
    output_dict = ob.run_inference_for_single_image(image_np)

    category_dict = {1 : "Blouse", 2 : "Tee", 3 : "Shorts", 4 : "Skirt", 5 : "Dress"}
    detection_scores = output_dict['detection_scores'] >= 0.5 # IoU threshold : .5
    idx = [x for x, value in enumerate(detection_scores) if value == True]

    detection_classes = output_dict['detection_classes']
    detection_classes = [item for x, item in enumerate(detection_classes) if x in idx]
    detection_categories = [category_dict[item] for item in detection_classes]
    detection_scores = [item for x, item in enumerate(output_dict['detection_scores']) if x in idx]

    # visualize boxes and labels on image
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        instance_masks=output_dict.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=8)

    file_type = fname.split(".")[-1]
    path = "result.{file_type}".format(file_type = file_type)
    result_img_path = os.path.join(settings.MEDIA_ROOT, path)
    scipy.misc.imsave(result_img_path, image_np) # save detected image

    return detection_categories, list(detection_scores)