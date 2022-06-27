# PyFDAConvertCPP converts a .csv file defining an IIR filter from the pyFDA to a .h file for c++ programming.
# 
# The .csv file used is specified with the first input argument when running the script.
# The .h output file can be named with the second input argument when running the script.
# If no name is given, its name will be fdacoeffs.h.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 27.06.2022, version 0.3
# 
# Changelog
#   - 27.06.2022: Added functionality to specify source and destination,
#                 changed data format from double to float
#   - 21.06.2022: Fixed a bug that caused the .h file to miss semicolons after array definitions
#   - 07.03.2022: Initial version

# import modules
import csv
import sys

args = sys.argv

# Check if input arguments are present
if len(args) == 1:
    print("You have to specify a .csv file to convert.")
    quit()

# Get file path
pathInput = args[1]
# open the raw file
rawFile = None
try:
    rawFile = open(pathInput, 'r')
except FileNotFoundError:
    print("Could not find source file: " + str(pathInput))
    quit()

reader = csv.reader(rawFile)

# get the number of coefficients
rowLen = 0
for row in reader:
    rowLen = len(row)
    break

# go back to the start
rawFile.seek(0)

# create .h file
newName = "fdacoeffs.h"
if len(args) == 3:
    newName = args[2]
hFile = open(newName, "w")

# write contents to .h file
hFile.write("const int Nb = ")
hFile.write(str(rowLen))
hFile.write(";\nconst int Na = ")
hFile.write(str(rowLen))
hFile.write(";\n\nconst float bn[Nb] = {\n")
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
hFile.write("\n};\n\nconst float an[Na] = {\n")
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
