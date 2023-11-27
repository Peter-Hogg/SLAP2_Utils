import tifffile
import numpy as np
import matplotlib.pyplot as plt
from cellpose import models


def returnSoma2D(plane):
    # Provide 2D projection and returns labels
    model = models.Cellpose(gpu=True, model_type='cyto2')
    masks, _, _, _ = model.eval(std_projection, diameter=38, channels=[0,0], flow_threshold=0.8)
    return masks
