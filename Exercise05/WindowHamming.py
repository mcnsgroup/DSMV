# WindowHamming computes the Hamming window and ENBW for a given number of data points.
# 
# Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
# Philipp Rahe (prahe@uni-osnabrueck.de)
# 20.01.2022, ver1.1
# 
# Changelog
#   - 20.01.2022: Ported to Python
#   - 25.05.2021: Initial version
#
# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation 
# files (the "Software"), to deal in the Software without 
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software 
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
# OTHER DEALINGS IN THE SOFTWARE.

import numpy as np

# Returns the Hamming window and its ENBW
# for a given number of data points.
# inputs:
#   N: Number of data points.
# outputs:
#   window: Window function
#   M_2overM_1square: effective noise bandwidth / sampling frequency
def WindowHamming(N):
    # Window function
    window = [0] * N
    for k in range(N):
        window[k] = 25/46 - 21/46 * np.cos(2 * np.pi * k / (N-1))
    factor = N/sum(window)
    # Window (normalized)
    window = np.multiply(window, factor)
    M_2overM_1square = sum(np.power(window, 2))/pow(sum(window), 2)
    return (window, M_2overM_1square)