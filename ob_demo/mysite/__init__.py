import tensorflow as tf

# sess = tf.Session(config = tf.ConfigProto(gpu_options = ))

PATH_TO_FROZEN_GRAPH = 'app/model/frozen_inference_graph.pb'

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

config = tf.ConfigProto()
config.gpu_options.visible_device_list = "1"
session = tf.Session(config=config, graph = detection_graph)