Installation
============

`SLAP2 Utils` can be installed with pip:

.. code-block:: shell

   pip install SLAP2-UTILS

You can also clone this repository by typing the following on the command prompt (provided that you have GitHub installed):

.. code-block:: shell

   git clone https://github.com/Peter-Hogg/SLAP2_Utils.git

All dependencies for `SLAP2 Utils` will be installed during installation with the exception of Cupy.
Users must manually install Cupy for GPU accelerated functions to work.

Installing Cupy
================

GPU Supported functions use the Python Library Cupy. This library has the following requirements:

   * NVIDIA CUDA GPU with the Compute Capability 3.0 or larger.

   * CUDA Toolkit: v11.2 / v11.3 / v11.4 / v11.5 / v11.6 / v11.7 / v11.8 / v12.0 / v12.1 / v12.2 / v12.3 / v12.4


Try installing Cupy using a wheel that matches your CUDA Toolkit version ie:

.. code-block:: shell
   
   pip install cupy-cuda12x


For more information on installing Cupy see the installation documentation `HERE <https://docs.cupy.dev/en/stable/install.html>`_.