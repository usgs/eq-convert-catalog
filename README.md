Introduction
------------

eq-convert-catalog is a project designed to make it easy(er) to create QuakeML from a simple(ish) dictionary structure 
defining an earthquake origin, focal mechanism, or moment tensor.  

Installation and Dependencies
-----------------------------

To install:

pip install -U git+git://github.com/usgs/eq-convert-catalog.git

Uninstalling and Updating
-------------------------

To uninstall:

pip uninstall eq-convert-catalog

To update:

pip install -U git+git://github.com/usgs/eq-convert-catalog.git

Application Programming Interface (API) Usage
----------------------------------------------------- 


Usage for convertcat
--------
<pre>
usage: convertcat [-h] [--catalog CATALOG] [--contributor CONTRIBUTOR]
                  module folder datafiles [datafiles ...]

Convert input files to QuakeML and write to output folder.

positional arguments:
  module                The catalog format to parse. Supported file formats
                        are: dict_keys(['ndk', 'mloc', 'iscgem'])
  folder                The folder where output QuakeML should be written.
  datafiles             Specify the file or files that are to be parsed

optional arguments:
  -h, --help            show this help message and exit
  --catalog CATALOG     Specify the catalog to be inserted in the QuakeML.
  --contributor CONTRIBUTOR
                        Specify the contributor to be inserted in the QuakeML.
</pre>


