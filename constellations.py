import re

import numpy as np
import matplotlib.pyplot as mpl
import soslines as sos


def read_bsc():
    with open('bsc5.dat') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        try:
            num = int(line[0:4])
            name = line[4:14].strip()
            #print(line[90:107])
            glon = float(line[90:96])
            glat = float(line[96:102])
            vmag = float(line[102:107])
            #print(num, '*', name, '*', glon, '*', glat, '*', vmag)
            t = (num, name, glon, glat, vmag)
            data.append(t)
        except:
            #print('fail')
            #print(line)
            pass
    return data


def read_bsc2():
    with open('bsc5.dat') as f:
        lines = f.readlines()
    data = {} 
    for line in lines:
        try:
            num = int(line[0:4])
            name = line[4:14].strip()
            #print(line[90:107])
            glon = float(line[90:96])
            if glon > 180:
                glon = glon - 360.0
            glat = float(line[96:102])
            vmag = float(line[102:107])
            data[num] = (glon, glat, name, vmag)
        except:
            #print('fail')
            #print(line)
            pass
    return data


def foo():
    data = read_bsc()
    num = [x[0] for x in data]
    name = [x[1] for x in data]
    glat = np.array([x[3] for x in data])
    glon = np.array([x[2] for x in data])
    vmag = np.array([x[4] for x in data])

    mpl.scatter(-glon, glat, c=-vmag, s=(8-vmag)*5)
    g = np.where(vmag < 4)[0]
    for index in g:
        mpl.text(-glon[index], glat[index], ('%d:'%num[index])+name[index])
    mpl.colorbar()
    mpl.xlim(-360, 0)
    mpl.ylim(-90, 90)
    mpl.tight_layout()
    mpl.show()


def foo2():
    data = read_bsc()
    name = [x[1] for x in data]
    ind = np.array([i for i, x in enumerate(name) if re.search('Ori', x)])

    num = [data[i][0] for i in ind]
    name = [data[i][1] for i in ind]
    glon = np.array([data[i][2] for i in ind])
    glat = np.array([data[i][3] for i in ind])
    vmag = np.array([data[i][4] for i in ind])

    h = {}
    for i in ind:
        h[data[i][0]] = (-data[i][2], data[i][3])
    pairs = [(2061, 1839), (1839, 1790), (1839, 1879), 
        (2061, 1948), (1948, 1903), (1903, 1852), (1790, 1852),
        (1852, 1788), (1788, 1713), (2004, 1948), (2061, 2124),
        (2199, 2159), (2124, 2199), (2199, 2135), (2135, 2047), (2159, 2047),
        (1790, 1543), (1601, 1567), (1567, 1552), (1552, 1543),
        (1543, 1544), (1544, 1570), (1570, 1580)]

    for p in pairs:
        a = h[p[0]]
        b = h[p[1]]
        neglon = (a[0], b[0])
        lat = (a[1], b[1])
        mpl.plot(neglon, lat, '--k', alpha=0.5)

    mpl.scatter(-glon, glat, c=-vmag, s=(8-vmag)*5)
    g = np.where(vmag < 5)[0]
    for index in g:
        mpl.text(-glon[index], glat[index], ('%d:'%num[index])+name[index])
    mpl.colorbar()
    mpl.tight_layout()
    mpl.show()


def foo3():
    data = read_bsc()
    name = [x[1] for x in data]
    #ind = np.array([i for i, x in enumerate(name) if re.search('Ori', x)])
    #ind = np.array([i for i, x in enumerate(name) if re.search('Gem', x)])
    #ind = np.array([i for i, x in enumerate(name) if re.search('Cas', x)])
    #ind = np.array([i for i, x in enumerate(name) if re.search('UMa', x)])
    #ind = np.array([i for i, x in enumerate(name) if re.search('UMi', x)])
    ind = np.array([i for i, x in enumerate(name) if re.search('Dra', x)])

    num = [data[i][0] for i in ind]
    name = [data[i][1] for i in ind]
    glon = np.array([data[i][2] for i in ind])
    glat = np.array([data[i][3] for i in ind])
    vmag = np.array([data[i][4] for i in ind])

    h = {}
    for i in ind:
        h[data[i][0]] = (-data[i][2], data[i][3])

    with open('constellations.txt') as f:
        lines = f.readlines()
    pairs = [[int(x) for x in line.split()] for line in lines if not re.search('#', line)]

    for p in pairs:
        try:
            a = h[p[0]]
            b = h[p[1]]
            neglon = (a[0], b[0])
            lat = (a[1], b[1])
            mpl.plot(neglon, lat, '--k', alpha=0.5)
        except:
            pass

    mpl.scatter(-glon, glat, c=-vmag, s=(8-vmag)*5)
    g = np.where(vmag < 5)[0]
    for index in g:
        mpl.text(-glon[index], glat[index], ('%d:'%num[index])+name[index])
    mpl.colorbar()
    mpl.tight_layout()
    mpl.show()


def foo4():
    data = read_bsc2()

    with open('constellations.txt') as f:
        lines = f.readlines()
    pairs = [[int(x) for x in line.split()] for line in lines if not re.search('#', line)]

    c = sos.Canvas(height=2048)

    for p in pairs:
        print(p)
        a = data[p[0]]
        b = data[p[1]]
        lon = np.array((a[0], b[0]))
        lat = np.array((a[1], b[1]))
        mpl.plot(-lon, lat, '--k', alpha=0.5)
        c.line(a[1], -a[0], b[1], -b[0], line_width=0.5)
    c.imsave('constellations1.png')
    mpl.show()
    



if __name__ == "__main__":
    #read_bsc()
    #foo()
    #foo2()
    #foo3()
    foo4()
