# stdfwriter

stdfwriter is a pythonic STDF(Standard Test Data Format, V4) writer.

# Installing

`clone https://github.com/Shawnice/stdfwriter.git`

# How to use

```from recheaders import *

inf = open("test.stdf", "wb")

far = FAR(CPU_TYPE=2, STDF_VER=4)  # create rec object
far.write_record(inf)  # write_record will write rec object to file

inf.close()
````

# Author

Lester Wu <wucean@gmail.com>

# License

GNU General Public License v3.0

