# PyFDAConvertCPP converts a .csv file defining an IIR filter from the pyFDA to a .h file for c++ programming.
# 
# The .csv file used will be the first one in the directory of this programm in alphabetical order.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 21.06.2022, version 0.2
# 
# Changelog
#   - 21.06.2022: Fixed a bug that caused the .h file to miss semicolons after array definitions
#   - 07.03.2022: Initial version

# import modules
import csv
import glob
import os

# Get file path
dir = os.path.relpath(__file__)
dir = dir[0:len(dir)-18]
pathFiles=glob.glob(dir + "*.csv")

# open the raw file
rawFile = open(pathFiles[0], 'r')
reader = csv.reader(rawFile)

# get the number of coefficients
rowLen = 0
for row in reader:
    rowLen = len(row)
    break

# go back to the start
rawFile.seek(0)

# create .h file
# new file name
newName = pathFiles[0][0:len(pathFiles[0])-4] + ".h"
hFile = open(newName, "w")

# write contents to .h file
hFile.write("const int Nb = ")
hFile.write(str(rowLen))
hFile.write(";\nconst int Na = ")
hFile.write(str(rowLen))
hFile.write(";\n\nconst double bn[Nb] = {\n")
for row in reader:
    for item in row:
        hFile.write(str(item))
        hFile.write(",\n")
    break
hFile.close()
hFile = open(newName, "r")
data = hFile.read()
hFile.close()
hFile = open(newName, "w")
hFile.write(data[:-2])
hFile.write("\n};\n\nconst double an[Na] = {\n")
for row in reader:
    for item in row:
        hFile.write(str(item))
        hFile.write(",\n")
hFile.close()
hFile = open(newName, "r")
data = hFile.read()
hFile.close()
hFile = open(newName, "w")
hFile.write(data[:-2])
hFile.write("\n};")
