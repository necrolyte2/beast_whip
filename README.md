# Introduction

Beagle_optimiser is a program written in Python that takes an XML input file prepared for BEAST, and finds the beagle option that will result in the shortest analysis time of that file. 

# Install

It is highly suggested that you install into a virtualenv environment
http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation

## Setup virtualenv

```
cd beagle_optimiser
wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz#md5=f61cdd983d2c4e6aeabb70b1060d6f49 -O- | tar xzf -
python virtualenv-1.11.6/virtualenv.py bo
. bo/bin/activate
python setup.py install
```

# Output from the program looks like this:

# TODO:
- Output options that will be run so people can see in case they want to exclude some
- Somehow also include -beagle_order when there are 2 GPU
- Put time taken to generate the estimate beside each estimate