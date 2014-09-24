## Introduction

beast_whip is a project based on the original [beagle_optimiser](https://github.com/mtop/beagle_optimiser)
The object of the new project is to try and make it easier to run beast xml files.

It is composed of two primary pieces, beagle_optimiser and splitxml.

Beagle Optimiser will take an XML input file prepared for BEAST and run all available beagle options on that
file and then output the estimated time each of them would take to run.

splitxml is simply a script that will take a beast xml file and split it as evenly as possible into N pieces.
The idea is that each piece should be able to be run separately on different computers to hopefully parallelize
the run and then the results can be combined later using [LogCombiner](http://beast.bio.ed.ac.uk/)

## Requirements

All of the python packages should be mostly taken care of during the setup.py install.
lxml does require that the libxml-devel and libxslt-devel packages for your distribution are installed though
as they are required for compiling the python-c modules.

On Red Hat you can install them via:

```
su -c "yum install libxml2-devel libxslt-devel"
```

## Install

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

##### Quotes

It is very important that options that have more than 1 argument are enclosed in quotes otherwise they will be interpreted as 2 different exludes.

Example:

```
--exclude beagle_order 1
```

Will exclude all beagle_order options as well as any option that has 1 in it

```
--exclude 'beagle_order 1'
```

Will exclude only the beagle_order 1 option

##### Don't include the dash before an option you want to exclude

Including a dash before an exclude option essentially will make beagle_optimiser think you are passing another option on to it instead of specifying a string for the --exclude argument.

You shouldn't need to specify the dash for an exclude option anyways since you can just specify the option name

Example:

This will not work!

```
beagle_optimiser whip/test/beast.xml --exclude -beagle_SSE
```

This will work

```
beagle_optimiser whip/test/beast.xml --exclude beagle_SSE
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

## splitxml(in development)

The original concept of this is being re-worked as you cannot just pull out a subset of sequences and run them separately. You may be able to run a subset of the chainLength and parallelize that way though. That is being investigated now.

Splits a beast xml file into N files. At this point each file will just be named split_N.xml, where N is replaced with 1-N.
splitxml at this time will also find any <parameter...dimension="X"...> tags and replace the dimension="X" with how many taxon's are in each file - 1.
I don't know why there are length(taxon)-1, but it is what it is.

### Example Usage

#### Split an xml into 2 files

```
splitxml.py whip/test/benchmark1.xml
```
You will now have 2 xml files called split_1.xml and split_2.xml in the current directory

#### Specify how many files to generate

```
splitxml.py whip/test/benchmark1.xml --files 10
```
And just to verify
```
for f in split_*.xml; do echo -n "$f: "; grep '</taxon>' $f | wc -l; done;
split_10.xml: 136
split_1.xml: 145
split_2.xml: 145
split_3.xml: 145
split_4.xml: 145
split_5.xml: 145
split_6.xml: 145
split_7.xml: 145
split_8.xml: 145
split_9.xml: 145
```

## Complete Example

A good example/tutorial is to use the benchmark1.xml file that comes with beast. This file can be located in either beast_whip/whip/test/benchmark1.xml or under your BEAST/examples/Benchmark/benchmark1.xml.

1. Make a testing directory and copy benchmark1.xml into it

  ```
  cd beast_whip
  mkdir -p benchmark1 && cd benchmark1
  cp ../whip/test/benchmark1.xml .
  ```
  
2. Figure out what beagle option is the fastest for that file on your computer

  ```
  beagle_optimiser benchmark1.xml
  ```
  
  Output
  
  ```
  beagle_optimiser benchmark1.xml
  Running beast with -beagle_SSE
  -beagle_SSE estimate: 00:01:22.800000 (Time to generate: 00:01:29.180686)
  Running beast with -beagle_SSE -beagle_instances 2
  -beagle_SSE -beagle_instances 2 estimate: 00:01:13.800000 (Time to generate: 00:01:20.61046)
  Running beast with -beagle_SSE -beagle_instances 4
  -beagle_SSE -beagle_instances 4 estimate: 00:01:13.800000 (Time to generate: 00:01:02.846145)
  Running beast with -beagle_SSE -beagle_instances 6
  -beagle_SSE -beagle_instances 6 estimate: 00:01:15.600000 (Time to generate: 00:01:25.660735)
  Running beast with -beagle_SSE -beagle_instances 8
  None
  -beagle_SSE -beagle_instances 8 estimate: INF (Time to generate: 00:00:01.599601)
  
  Results sorted by estimated runtime:
      -beagle_SSE -beagle_instances 2 estimated to take 00:01:13.800000
      -beagle_SSE -beagle_instances 4 estimated to take 00:01:13.800000
      -beagle_SSE -beagle_instances 6 estimated to take 00:01:15.600000
      -beagle_SSE estimated to take 00:01:22.800000
      -beagle_SSE -beagle_instances 8 estimated to take INF
  ```
  
  You can see that the -beagle_SSE -beagle_instances 2 was the fastest runtime so we will use it.
  
3. Determine how many files to split benchmark1.xml into and split it
  
  This will be determined by how many computers you want to run it on. Just make sure you don't split it up too many
  times. You want to probably ensure that you don't dip below 100 taxon per file. For our example we will only split
  it up into 2 files(The default).

  ```
  splitxml.py benchmark1.xml
  ```

4. Then run beast on the files across your computers(eventually this might be automated inside of splitxml.py)

  This assumes passwordless ssh to each computer to make the example easier.
  
  1. Setup the list of nodes
  
  ```
  nodelist=( computername1 computername2 )
  ```
  
  2. Run xml in round robin across nodelist
  
    This requires that you have screen installed on each of your computer nodes so each run can be run inside of a
    screen session to ensure that a network blip does not cause beast to die.
  
    ```
    i=0
    xmllist=( $(ls split_*.xml) )
    for node in ${nodelist[@]}
    do
      xml=${xmllist[$i]}
      echo "Running $xml on $node"
      ssh ${node} "beast -beagle_SSE -beagle_instances 2 ${xml} > ${xml}.out 2>&1" &
      i=$((i+1))
    done
    ```

## TODO:

- beagle_optimiser: Output options that will be run so people can see in case they want to exclude some
