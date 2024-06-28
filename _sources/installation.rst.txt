Installation
============

`SLAP2 Utils` can be installed with pip:

.. code-block:: shell

   pip install SLAP2-UTILS

You can also clone this repository by typing the following on the command prompt (provided that you have GitHub installed):

.. code-block:: shell

   git clone https://github.com/Peter-Hogg/SLAP2_Utils.git

The toolkit utilized many libraries. The user would need to install `numpy`, `scipy`. `h5py`, and `scikit-image`. Some functions in the toolkit would not work if these libraries are not installed. The installation of `cupy` are also highly recommended, as it is a library that enables many Python functions to run in GPU and thus speeds up the runtime of some functions (including motion correction). This is optional for non-GPU users. The functions are compatible with up-to-date versions of the mentioned Python libraries.
