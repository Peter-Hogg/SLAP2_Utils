
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()



setup(

    name='slap2utils', 
    version='0.0.3',  

    
    description='Code to support using a SLAP2 Microscope',  

    url='https://github.com/Peter-Hogg/SLAP2_Utils',  

    
    author='Peter Hogg',  

    
    author_email='peter.hogg@ubc.ca',  
    
    classifiers=[ 
        
        'Development Status :: 4 - Beta',


        'Intended Audience :: Researchers',

   
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],


    keywords='python two photon microscope', 

    
    packages=find_packages(exclude=['*.test']), 


    install_requires=required,  


)