"""Fast reader for ngspice wrdata output (header line of vector names, then whitespace-separated rows)."""
import numpy as np
def read(path):
    """Returns (names, array[rows, cols])."""
    with open(path,'rb') as f:
        names=f.readline().decode().split(); body=f.read()
    a=np.fromstring(body,sep=' ')
    return names, a.reshape(-1,len(names))
