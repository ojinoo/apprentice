import numpy as np
# https://arcpy.wordpress.com/2012/05/11/sorting-alphanumeric-strings-in-python/


def read_limitsandfixed(fname):
    """
    Read a text file e.g.
    PARAM1  0         1   # interpreted as fixed param
    PARAM2  0.54444       # interpreted as limits
    """
    limits, fixed = {}, {}
    if fname is not None:
        with open(fname) as f:
            for l in f:
                if not l.startswith("#"):
                    temp = l.split()
                    if len(temp) == 2:
                        fixed[temp[0]] = float(temp[1])
                    elif len(temp) == 3:
                        limits[temp[0]] = (float(temp[1]), float(temp[2]))
    return limits, fixed


import re
def sorted_nicely( l ):
    """ Sorts the given iterable in the way that is expected.

    Required arguments:
    l -- The iterable to be sorted.

    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)


# Documentation?
def fast_chi(lW2, lY, lRA, lE2, nb):
    s=0
    for i in range(nb):
        s += lW2[i]*(lY[i] - lRA[i])*(lY[i] - lRA[i])*lE2[i] # errors are reciprocal
    return s

def least_square(y_data,y_mod,sigma2,w):
    return w/sigma2 * (y_mod-y_data)**2

def least_squares(y_data,y_mod,sigma2,w,idxs):
    """
    Least squares calculation for problem at hand, i.e. length of individual arguments is number of total bins.
    :param y_data: Data.
    :param y_mod: Model evaluations at data locations.
    :param sigma2: Measurement variances.
    :param w: Weights.
    :param idxs: Indices corresponding to observables
    :return:
    """
    n_o = len(idxs) # number of observables
    chi2 = np.zeros(n_o)
    V = 0.
    for i in range(n_o):
        i1 = idxs[i][0]; i2 = idxs[i][-1]
        chi2[i] = np.sum(np.array(least_square(y_data[i1:i2], y_mod[i1:i2], sigma2[i1:i2], 1.)))
        V += w[i1]*chi2[i] # weights are for all the bins the same in one observable, thus we just take the first one
    return V, chi2




def numNonZeroCoeff(app, threshold=1e-6):
    """
    Determine the number of non-zero coefficients for an approximation app.
    """
    n=0
    for p in app._pcoeff:
        if abs(p)>threshold: n+=1

    if hasattr(app, '_qcoeff'):
        for q in app._qcoeff:
            if abs(q)>threshold: n+=1

    return n


def numNLPoly(dim, order):
    if order <2: return 0
    else:
        return numCoeffsPoly(dim, order) - numCoeffsPoly(dim, 1)

def numNL(dim, order):
    """
    Number of non-linearities.
    """
    m, n = order
    if n ==0 : return numNLPoly(dim, m)
    if m <2 and n <2: return 0
    elif m<2 and n>=2:
        return numCoeffsPoly(dim, n) - numCoeffsPoly(dim, 1)
    elif n<2 and m>=2:
        return numCoeffsPoly(dim, m) - numCoeffsPoly(dim, 1)
    else:
        return numCoeffsRapp(dim, order) -  numCoeffsRapp(dim, (1,1))

def numCoeffsPoly(dim, order):
    """
    Number of coefficients a dim-dimensional polynomial of order order has.
    """
    ntok = 1
    r = min(order, dim)
    for i in range(r):
      ntok = ntok*(dim+order-i)/(i+1)
    return int(ntok)

def numCoeffsRapp(dim, order):
    """
    Number of coefficients a dim-dimensional rational approximation of order (m,n) has.
    """
    return numCoeffsPoly(dim, order[0]) + numCoeffsPoly(dim, order[1])

def maxOrder(N, dim):
    """
    Utility function to find highest order polynomial
    for dataset with N dim-dimensional points.
    Intended to be used when constructing max ONB
    """
    from scipy.special import comb
    omax = 0
    while comb(dim + omax+1, omax+1) + 1 <= N: # The '+1' stands for a order 0 polynomial's dof
        omax+=1
    return omax


def readH5(fname, idx=[0], xfield="params", yfield="values"):
    """
    Read X,Y values etc from HDF5 file.
    By default, only the first object is read.
    The X and Y-value dataset names depend on the file of course, so we allow
    specifying what to use. yfield can be values|errors with the test files.
    Returns a list of tuples of arrays : [ (X1, Y1), (X2, Y2), ...]
    The X-arrays are n-dimensional, the Y-arrays are always 1D
    """
    import numpy as np
    import h5py

    with h5py.File(fname, "r") as f:
        indexsize = f.get("index").size

    # A bit of logic here --- if idx is passed an empty list, ALL data is read from file.
    # Otherwise we need to check that we are not out of bounds.

    # pnames = [p for p in f.get(xfield).attrs["names"]]
    if len(idx)>0:
        assert(max(idx) <= indexsize)
    else:
        idx=[i for i in range(indexsize)]

    ret = []
    f = h5py.File(fname, "r")

    # Read parameters
    _X=np.array(f.get(xfield))

    # Read y-values
    for i in idx:
        _Y=np.atleast_1d(f.get(yfield)[i])
        USE = np.where( (~np.isinf(_Y))  & (~np.isnan(_Y)) )
        ret.append([ _X[USE], _Y[USE] ])

    f.close()

    return ret

# TODO rewrite such that yfield is a list of datasetnames, e.g. yfield=["values", "errors"]

def readH52(fname, idx=[0], xfield="params", yfield1="values", yfield2="errors"):
    """
    Read X,Y, erros values etc from HDF5 file.
    By default, only the first object is read.
    The X and Y-value dataset names depend on the file of course, so we allow
    specifying what to use. yfield can be values|errors with the test files.
    Returns a list of tuples of arrays : [ (X1, Y1, E1), (X2, Y2, E2), ...]
    The X-arrays are n-dimensional, the Y-arrays are always 1D
    """
    import numpy as np
    import h5py

    with h5py.File(fname, "r") as f:
        indexsize = f.get("index").size

    # A bit of logic here --- if idx is passed an empty list, ALL data is read from file.
    # Otherwise we need to check that we are not out of bounds.

    # pnames = [p for p in f.get(xfield).attrs["names"]]
    if len(idx)>0:
        assert(max(idx) <= indexsize)
    else:
        idx=[i for i in range(indexsize)]

    ret = []
    f = h5py.File(fname, "r")

    # Read parameters
    _X=np.array(f.get(xfield))

    # Read y-values
    for i in idx:
        _Y=np.atleast_1d(f.get(yfield1)[i])
        _E=np.atleast_1d(f.get(yfield2)[i])
        USE = np.where( (~np.isinf(_Y))  & (~np.isnan(_Y)) & (~np.isinf(_E))& (~np.isnan(_E)) )
        ret.append([ _X[USE], _Y[USE], _E[USE] ])

    f.close()

    return ret

def readPnamesH5(fname, xfield):
    """
    Get the parameter names from the hdf5 files params dataset attribute
    """
    import numpy as np
    import h5py

    with h5py.File(fname, "r") as f:
        pnames = [p.astype(str) for p in f.get(xfield).attrs["names"]]

    return pnames

def readData(fname, delimiter=","):
    """
    Read CSV formatted data. The last column is interpreted as
    function values while all other columns are considered
    parameter points.
    """
    import os
    if not os.path.exists(fname): raise Exception("File {} not found".format(fname))
    import numpy as np
    D = np.loadtxt(fname, delimiter=delimiter)
    X=D[:,0:-1]
    Y=D[:,-1]
    USE = np.where( (~np.isinf(Y))  & (~np.isnan(Y)) )
    return X[USE], Y[USE]

def readApprentice(fname):
    """
    Read an apprentice JSON file. We abuse try except here to
    figure out whether it's a rational or polynomial approximation.
    """
    import apprentice
    import os
    if not os.path.exists(fname): raise Exception("File {} not found".format(fname))
    try:
        app = apprentice.RationalApproximation(fname=fname)
    except:
        app = apprentice.PolynomialApproximation(fname=fname)
    return app

def getPolyGradient(coeff, X, dim=2, n=2):
    from apprentice import monomial
    import numpy as np
    struct_q = monomial.monomialStructure(dim, n)
    grad = np.zeros(dim,dtype=np.float64)

    for coord in range(dim):
        """
        Partial derivative w.r.t. coord
        """
        der = [0.]
        if dim==1:
            for s in struct_q[1:]: # Start with the linear terms
                der.append(s*X[0]**(s-1))
        else:
            for s in struct_q[1:]: # Start with the linear terms
                if s[coord] == 0:
                    der.append(0.)
                    continue
                term = 1.0
                for i in range(len(s)):
                    # print(s[i])
                    if i==coord:
                        term *= s[i]
                        term *= X[i]**(s[i]-1)
                    else:
                        term *= X[i]**s[i]
                der.append(term)
        grad[coord] = np.dot(der, coeff)
    return grad

def possibleOrders(N, dim, mirror=False):
    """
    Utility function to find all possible polynomials
    orders for dataset with N points in N dimension
    """
    from scipy.special import comb
    omax = 0
    while comb(dim + omax+1, omax+1) + 1 <= N: # The '+1' stands for a order 0 polynomial's dof
        omax+=1

    combs = []
    for m in reversed(range(omax+1)):
        for n in reversed(range(m+1)):
            if comb(dim + m, m) + comb(dim+n,n) <= N:
                combs.append((m,n))

    if mirror:
        temp=[tuple(reversed(i)) for i in combs]
        for t in temp:
            if not t in combs:
                combs.append(t)
    return combs

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    # Fix size, sometimes there is spillover
    # TODO: replace with while if problem persists
    if len(out)>num:
        out[-2].extend(out[-1])
        out=out[0:-1]

    if len(out)!=num:
        raise Exception("something went wrong in chunkIt, the target size differs from the actual size")

    return out
# Todo add binwidth in data model
def readExpData(fname, binids):
    import json
    import numpy as np
    with open(fname) as f: dd = json.load(f)
    Y = np.array([dd[b][0] for b in binids])
    E = np.array([dd[b][1] for b in binids])
    return dict([(b, (y, e)) for b,y,e in zip(binids,Y,E)])

def readTuneResult(fname):
    import json
    with open(fname) as f:
        return json.load(f)

def readApprox(fname):
    import json, apprentice
    with open(fname) as f: rd = json.load(f)
    # binids = sorted(rd.keys())
    binids = sorted_nicely(rd.keys()) #sorted(rd.keys(), key=lambda item: (int(item.partition(' ')[0])
                               # if item[0].isdigit() else float('inf'), item))
    APP = {}
    for b in binids:
        try:
            APP[b]=apprentice.RationalApproximation(initDict=rd[b])
        except:
            APP[b]=apprentice.PolynomialApproximation(initDict=rd[b])
    return binids, [APP[b] for b in binids]

def mkCov(yerrs):
    import numpy as np
    return np.atleast_2d(yerrs).T * np.atleast_2d(yerrs) * np.eye(yerrs.shape[0])


class TuningObjective(object):
    def __init__(self, f_weights, f_data, f_approx, restart_filter=None, debug=False, limits=None):
        import apprentice
        import numpy as np
        matchers=apprentice.weights.read_pointmatchers(f_weights)
        binids, RA = apprentice.tools.readApprox(f_approx)
        if debug: print("Initially we have {} bins".format(len(binids)))
        hnames = [b.split("#")[0] for b in binids]
        bnums  = [int(b.split("#")[1]) for b in binids]

        self._debug = debug

        weights = []
        for hn, bnum in zip(hnames, bnums):
            pathmatch_matchers = [(m,wstr) for m,wstr in matchers.items() if m.match_path(hn)]
            posmatch_matchers  = [(m,wstr) for (m,wstr) in pathmatch_matchers if m.match_pos(bnum)]
            w = float(posmatch_matchers[-1][1]) if posmatch_matchers else 0 #< NB. using last match
            weights.append(w)

        # TODO This should be passed from the outside for performance
        if restart_filter is not None:
            FMIN = [r.fmin(restart_filter) for r in RA]
            FMAX = [r.fmax(restart_filter) for r in RA]
        else:
            FMIN=[-1e101 for r in RA]
            FMAX=[ 1e101 for r in RA]

        # TODO This needs to be a property
        # Filter here to use only certain bins/histos
        # TODO put the filtering in readApprox?
        dd = apprentice.tools.readExpData(f_data, [str(b) for b in  binids])
        Y  = np.array([dd[b][0] for b in binids])
        E  = np.array([dd[b][1] for b in binids])
        # Also filter for not enveloped data
        good = []
        for num, bid in enumerate(binids):
            # good.append(num)
            # if FMIN[num]<= Y[num] and FMAX[num]>= Y[num] and weights[num]>0: good.append(num)
            if weights[num]>0: good.append(num)

        # TODO --- upon calling a def filter() --- these should be properties
        self._RA     = [RA[g]     for g in good]
        self._binids = [binids[g] for g in good]
        self._E      = E[good]
        self._Y      = Y[good]
        self._W2     = np.array([w*w for w in np.array(weights)[good]])

        self._E2 = np.array([1./e**2 for e in self._E])
        self._SCLR = RA[0]._scaler # Replace with min/max limits things
        self._hnames = sorted(list(set([b.split("#")[0] for b in self._binids])))
        hdict, _ = history_dict(self._binids, self._hnames)
        self._hdict = hdict
        self._wdict = weights_dict(self._W2, self._hdict)
        self._idxs = indices(self._hnames, self._hdict)
        self._bounds = self._SCLR.box
        if limits is not None:
            lim, fix = read_limitsandfixed(limits)
            for num, pn in enumerate(self.pnames):
                if pn in lim:
                    self._bounds[num] = lim[pn]
            # print("New bounds: {}".format(self._bounds))

        if debug: print("After filtering: len(binids) = {}".format(len(self._binids)))

    def setWeights(self, wdict):
        """
        Convenience function to update the bins weights.
        """
        if type(wdict) == dict:
            self._wdict = {k:[] for k in wdict.keys()}
            for num, b in enumerate(self._binids):
                for hn, w in wdict.items():
                    if hn in b:
                        self._W2[num] = w*w
                        self._wdict[hn].append(w)
        else:
            wdict2 = {hn: _x for hn, _x in zip(self.hnames, wdict)}
            self.setWeights(wdict2)

    def weights_obs(self):
        """
        Get weights for individual observables.
        :return: Weights of first bin in each observable.
        """
        return [w[0] for w in self._wdict.values()]

    def obsGoF(self, hname, x):
        """
        Convenience function to get the (unweighted) contribution to the gof for obs hname at point x
        """
        import numpy as np
        _bids = [num for num, b in enumerate(self._binids) if hname in b]
        return fast_chi(np.ones(len(_bids)), self._Y[_bids], [self._RA[i](x) for i in _bids], self._E2[_bids] , len(_bids))

    def meanCont(self, x):
        """
        Convenience function that return a list if the obsGof for all hnames at x
        """
        return [self.obsGoF(hn, x) for hn in self.hnames]

    @property
    def hnames(self): return self._hnames

    @property
    def pnames(self): return self._SCLR.pnames

    def _objective_obs(self, x):
        """
        Return objective and individual contributions of observables.
        :param x:
        :return:
        """
        return least_squares(self._Y, [f(x) for f in self._RA], 1/self._E2, np.sqrt(self._W2), self._idxs) # E2 is reciprocal

    def objective(self, x):
        return fast_chi(np.sqrt(self._W2), self._Y, [f(x) for f in self._RA], self._E2 , len(self._binids))

    def startPoint(self, ntrials):
        import numpy as np
        _PP = np.random.uniform(low=self._SCLR._Xmin,high=self._SCLR._Xmax,size=(ntrials, self._SCLR.dim))
        _CH = [self.objective(p) for p in _PP]
        if self._debug: print("StartPoint: {}".format(_PP[_CH.index(min(_CH))]))
        return _PP[_CH.index(min(_CH))]

    def minimize(self, nstart,nrestart):
        from scipy import optimize
        minobj = np.Infinity
        finalres = None
        for t in range(nrestart):
            res = optimize.minimize(self.objective, self.startPoint(nstart), bounds=self._bounds)
            if res["fun"] < minobj:
                minobj = res["fun"]
                finalres = res
        return finalres

    def __call__(self, x):
        return self.objective(x)


def history_dict(binids, hnames=None):
    if hnames is None:
        hnames = [b.split("#")[0] for b in binids]
    hdict = dict([(h, []) for h in hnames])
    for b in binids:
        hname, bid = b.split("#")
        hdict[hname].append(bid)
    return hdict, hnames

def weights_dict(w2_bins, hdict):
    """
    Transform bin weights to weights dictionary.
    :param w2_bins: Squared weights of bins.
    :param hdict: History dictionary.
    :return: Weights dictionary.
    """
    wdict = {k:np.zeros(len(v)) for (k,v) in zip(hdict.keys(),hdict.values())}
    i = 0
    for (k,v) in zip(wdict.keys(),wdict.values()):
        n = len(v)
        wdict[k][:] = np.sqrt(np.array(w2_bins[i:i+n]))
        i += n
    return wdict

def indices(hnames, dict):
    """
    Returns indices with indices corresponding to observables.
    :param hnames: Names of observables. This is important as this determines the order of the observables! The dictionaries of the object, i.e. hdict and wdict, might be unordered. -> TODO: Use OrderedDict() instead?
    :param dict: Either weights or history dict.
    :return: Indices dictionary.
    """
    idxs = [[0,0] for _ in hnames]
    i = 0
    for (k,v) in zip(range(len(hnames)),dict.values()):
        n = len(v)
        idxs[k][:] = [i,i + n]
        i += n
    return idxs



def artificial_data_from_RA(approximation_file,p0,eps,outfile=None,eps_model=0.):
    """
    Create in-silico data from rational approximation file corrupting the data with zero mean Gaussian noise.
    :param approximation_file: Approximation json file.
    :param p0: True parameter value.
    :param eps: Variance factor (multiplied by the data value at the corresponding bin).
    :param outfile: Output json file path.
    :param eps_model: Variance factor for model error (zero mean Gaussian noise, default: 0)
    :return: Experimental data json file.
    """
    import json
    binids, RA = readApprox(approximation_file)
    hdict, _ = history_dict(binids)
    hnames = hdict.keys()
    if len(hnames) != len(p0) or len(hnames) != len(eps):
        n_o = len(hnames)
        raise TypeError("Lengths of p0, eps and number of observables have to be the same. There are {} observables.".format(n_o))
    RA_dict = dict([(b, r) for (b,r) in zip(binids,RA)])
    data = dict([(b, []) for b in binids])

    for (h,p,e) in zip(hnames,p0,eps):
        for i in hdict[h]:
            bid = "{h}#{i}".format(h=h,i=i)
            r = RA_dict[bid]
            mu = r(p)
            sigma2 = e*abs(mu)
            sigma2_model = eps_model*abs(mu)
            d = mu + np.random.normal(0.0, np.sqrt(sigma2_model)) + np.random.normal(0.0, np.sqrt(sigma2))
            data[bid] = [d, sigma2]

    if outfile is None:
        outfile = 'test123.json'
    with open(outfile, 'w') as f:
        json.dump(data, f)

