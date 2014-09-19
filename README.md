### Introduction

beast_whip is a project based on the original [beagle_optimiser](https://github.com/mtop/beagle_optimiser)
The object of the new project is to try and make it easier to run beast xml files.

It is composed of two primary pieces, beagle_optimiser and splitxml.

Beagle Optimiser will take an XML input file prepared for BEAST and run all available beagle options on that
file and then output the estimated time each of them would take to run.

splitxml is simply a script that will take a beast xml file and split it as evenly as possible into N pieces.
The idea is that each piece should be able to be run separately on different computers to hopefully parallelize
the run and then the results can be combined later using [LogCombiner](http://beast.bio.ed.ac.uk/)

### Requirements

All of the python packages should be mostly taken care of during the setup.py install.
lxml does require that the libxml-devel and libxslt-devel packages for your distribution are installed though
as they are required for compiling the python-c modules.

On Red Hat you can install them via:

```
su -c "yum install libxml2-devel libxslt-devel"
```

### Install

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

After this finishes you will have installed and activated a new virtualenv called bw inside of the beast_whip directory.
If you already have virtualenv then you can omit step 3 and replace step 4 with activating your existing virtualenv.


## beagle_optimiser

### Example Usage

#### Get the full help usage as well as available beagle options

```
beagle_optimiser --help
```
The epilog of the help will display the available beagle options that will be used. Here is an example:

```
Available beagle options to be run:
-beagle_SSE
-beagle_SSE -beagle_instances 2
-beagle_SSE -beagle_instances 4
-beagle_SSE -beagle_instances 6
-beagle_SSE -beagle_instances 8
```

#### Excluding options

There are some example xml files inside of the whip/test directory that you can use. In this example we are going to use the very small testing xml file called beast.xml
As you can see in the previous example, the computer had 8 CPU's. beagle_optimiser will test -beagle_instances with every even number between 2 and CPU_COUNT. Sometimes this is not ideal as if you have a GPU(or maybe 2) it will end up running many many tests which would take to long.
You can use the --exclude option to specify any substring of a beagle option to exclude.
In this example we are going to exclude all options that have beagle_instances. This would run only -beagle_SSE from our available options.

```
beagle_optimiser whip/test/beast.xml --exclude beagle_instances
```

If you wanted to run say instances 2 and 8 you could do an exclude pattern like this

```
beagle_optimiser whip/test/beast.xml --exclude \
  'beagle_instances 4' \
  'beagle_instances 6'
```
-- or --
```
beagle_optimiser whip/test/beast.xml --exclude {4,6}
```

### Output from beagle_optmiser

```
bash$ > beagle_optimiser whip/test/beast.xml
Running beast with -beagle_SSE
-beagle_SSE estimate: 00:00:00.961200
Running beast with -beagle_SSE -beagle_instances 2
-beagle_SSE -beagle_instances 2 estimate: 00:00:03.600000
Running beast with -beagle_SSE -beagle_instances 4
-beagle_SSE -beagle_instances 4 estimate: 00:00:03.600000
Running beast with -beagle_SSE -beagle_instances 6
-beagle_SSE -beagle_instances 6 estimate: 00:00:03.600000
Running beast with -beagle_SSE -beagle_instances 8
-beagle_SSE -beagle_instances 8 estimate: 00:00:03.600000

Results sorted by estimated runtime:
	-beagle_SSE estimated to take 00:00:00.961200
	-beagle_SSE -beagle_instances 2 estimated to take 00:00:03.600000
	-beagle_SSE -beagle_instances 4 estimated to take 00:00:03.600000
	-beagle_SSE -beagle_instances 6 estimated to take 00:00:03.600000
	-beagle_SSE -beagle_instances 8 estimated to take 00:00:03.600000
```

As each beagle option is run with beast it will output what option it is running. When the first hours/million states line is encountered beagle_optimiser will kill the beast process and use the chainLength from the given xml file and the hours/million states from the output to compute the estimated run time in #days HH:MM:SS.milliseconds

### TODO:

- Output options that will be run so people can see in case they want to exclude some
- Somehow also include -beagle_order when there are 2 GPU
- Put time taken to generate the estimate beside each estimate
- Document xmlsplit.py
