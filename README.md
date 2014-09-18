# Introduction

beast_whip is a project based on the original [beagle_optimiser](https://github.com/mtop/beagle_optimiser)
The object of the new project is to take an XML input file prepared for BEAST and find
the beagle option that will result in the shortest analysis time of that file.

# Install

It is highly suggested that you install into a virtualenv environment
http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation

1. Clone beast_whip

  ```
  git clone https://github.com/necrolyte2/beast_whip.git
  ```
  
2. Enter the beast_whip directory
   
  ```
  cd beast_whip
  ```
  
3. Download and install virtualenv
   
  ```
  wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz#md5=f61cdd983d2c4e6aeabb70b1060d6f49 -O- |    tar xzf -
  python virtualenv-1.11.6/virtualenv.py bw 
  ```
  
4. Activate virtualenv
   
  ```
  . bw/bin/activate
  ```
  
5. Install beast_whip into virtualenv
  
  ```
  python setup.py install
  ```

After this finishes you will have installed and activated a new virtualenv called bw inside of the beast_whip directory. Then beast_whip will be installed into that virtualenv.
If you already have virtualenv then you can omit step 3 and replace step 4 with activating your existing virtualenv


# Example Usage

There are some example xml files inside of the whip/test directory that you can use. In this example we are going to use the very small testing xml file called beast.xml
We are also excluding any beagle option that would have the numbers 2-24 in them which should be all of them unless your computer has more than 24 CPU
```
beagle_optimiser whip/test/beast.xml --exclude {2..24}
```

# Output from the program looks like this:

# TODO:
- Output options that will be run so people can see in case they want to exclude some
- Somehow also include -beagle_order when there are 2 GPU
- Put time taken to generate the estimate beside each estimate
