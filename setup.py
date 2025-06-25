from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "slap2_utils.fast_line_data",
        ["slap2_utils/fast_line_data.pyx"],
        include_dirs=[np.get_include()]
    )
]

setup(
    name="SLAP2_Utils",
    ext_modules=cythonize(extensions),
)