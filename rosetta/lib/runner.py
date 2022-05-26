#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from cmath import exp
from itertools import count
import sys
import argparse
import psutil
import subprocess
import pathlib
import os
import resource
import datetime
import json
import xml.etree.ElementTree as et
import colorama  
import cwcwidth
import math
from collections import defaultdict


# FIXME: Hack
colorama.Fore.BWHITE = colorama.ansi.code_to_chars(97)





class StrConcat: # Rename: Twine
    def __init__(self, args):
        self.args = list(args)

    def __add__(self, other):
        common = self.args + [other]
        return str_concat(*common)

    def printlength(self):
        return sum(printlength(a) for a in self.args)

    def normalize(self):
        # Optional: collapse nested StrConact
        # Optional: concat neighboring string

        # hoist StrAlign to topmost
        for i,a in enumerate(self.args):
            a = normalize(a)
            if isinstance(a,StrAlign):
                prefixlen = sum(printlength(a) for a in self.args[:i])
                return StrAlign(StrConcat(self.args[:i] + [a.s] + self.args[i+1:]), prefixlen+a.align)
        return self

    def consolestr(self):
        return ''.join(consolestr(a ) for a in self.args)


class StrColor:
    def __init__(self, s, style):
        self.s = s
        self.style = style

    def __add__(self, other):
        return str_concat(self,other)
    
    def printlength(self):
        return printlength(self.s)

    def normalize(self):
        a = normalize(self.s)
        if isinstance(a,StrAlign):
            return StrAlign(StrColor(a.s,self.style),a.align)
        if a is self.s:
            return self
        return StrColor(a, self.style)

    def consolestr(self):
        from colorama import Fore,Back,Style
        if self.style in {Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW,Fore. BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE, Fore.BWHITE}:
            reset = Fore.RESET
        elif self.style in {Back.BLACK, Back.RED, Back.GREEN, Back.YELLOW,Back. BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE}:
            reset = Back.RESET
        elif self.style in {Style.DIM, Style.NORMAL, Style.BRIGHT}:
            reset = Style.RESET_ALL
        else:
            reset = ''
        return self.style + consolestr(self.s) + reset





class StrAlign:
    def __init__(self, s, align=None):
        self.s = s
        self.align=align

    def __add__(self, other):
        return str_concat(self,other)

    def normalize(self):
        # StrAlign cannot be nested
        return self




def str_concat(*args):
    return StrConcat(args=args)

def consolestr(s):
    if isinstance(s, str):
        return s
    return s.consolestr()

def printlength(s):
    if isinstance(s, str):
        result = cwcwidth.wcswidth(s) 
        if result != len(s):
            pass
        return result
    return s.printlength()

def normalize(s):
    if isinstance(s, str):
        return s
    return s.normalize()




def default_formatter(v):
    return str(v)





class Table:
    def __init__(self):
        self.columns = []
        self.column_titles = dict()
        self.column_formatters = dict()
        self.rows = []

    def add_column(self, name, title=None, formatter=None):
        self.columns.append(name)
        if title is not None:
            self.column_titles[name] = title
        if formatter is not None:
            self.column_formatters[name] = formatter

    def add_row(self, **kwargs):
        self.rows .append(kwargs)

    def print(self):
        matrix=[]
        nrows = len(self.rows)
        ncols = len(self.columns)

        collen = []
        colleft = []
        titles = []
        for i,name in enumerate(self.columns):
            vals = [r.get(name) for r in self.rows] 
            strs = []

            title = self.column_titles.get(name) or name
            formatter = self.column_formatters.get(name) or default_formatter
            maxlen = printlength(title) 
            titles.append(title)
            maxleft  = 0
            maxright = 0
           
            for v in vals:  
                if v is None:
                    strs.append(None)
                else:
                    s = formatter(v) # TODO: support embedded newlines
                    s = normalize(s)
                    if isinstance(s,StrAlign):
                        l = printlength(s.s)
                        left = s.align
                        right = l - left
                        maxleft = max(maxleft,left)
                        maxright = max(maxright,right)
                    else:
                        l = printlength(s)
                        maxlen = max(maxlen,l)
                    strs.append(s)

            maxlen = max(maxlen, maxleft+maxright)
            collen.append(maxlen)
            colleft.append(maxleft)
            matrix.append(strs)


        # Printing...
        def centering(s,collen):
            printlen = printlength(s)
            half = (collen - printlen)//2
            return ' '*half + consolestr(s) + ' ' *(collen - printlen - half)
        def raggedright(s,collen):
            printlen = printlength(s)
            return consolestr(s)  + ' ' * (collen - printlen)
        def aligned(s,maxlen,maxleft,alignpos):
            printlen = printlength(s)
            indent = maxleft - alignpos
            cs = consolestr(s)
            return ' ' * indent + cs + ' '*(maxlen - printlen - indent)
        def linesep():
           print(*(colorama.Style.DIM + '-'*collen[i] + colorama.Style.RESET_ALL for i in range(ncols))) 
        print()
        #linesep()
        print(*(centering(titles[i],collen[i]) for i in range(ncols)))
        linesep()

        for j in range(nrows):
            def colval(i,name):
                maxlen = collen[i]
                maxleft = colleft[i]
                s = matrix[i][j]
               
                if s is None:
                    return ' ' * maxlen
                if isinstance(s,StrAlign):
                    return aligned(s.s,maxlen,maxleft,s.align)
                    cs = consolestr(s.s)
                    left = cs[:s.align]
                    right = cs[s.align:] 
                    return f"{left:>{maxleft}}{right:<{maxright}}"

               
                # Left align by default
                return raggedright(s,maxlen)

            print(*(colval(i,name) for i,name in enumerate(self.columns)))
        #linesep()




# Summary statistics
class Statistic:
    studentt_density_95 = list( {
1: 12.706, # 1
2: 4.303, # 2
3: 3.182, # 3
4: 2.776, # 4
5: 2.571, # 5
6: 2.447, # 6
7: 2.365, # 7
8: 2.306, # 8
9: 2.262, # 9
10: 2.228, # 10
11: 2.201, # 11
12: 2.179, # 12
13: 2.160, # 13
14: 2.145, # 14
15: 2.131, # 15
16: 2.120, # 16
17: 2.110, # 17
18: 2.101, # 18
19: 2.093, # 19
20: 2.086, # 20
21: 2.080, # 21
22: 2.074, # 22
23: 2.069, # 23
24: 2.064, # 24
25: 2.060, # 25
26: 2.056, # 26
27: 2.052, # 27
28: 2.048, # 28
29: 2.045, # 29
30: 2.042, # 30
35: 2.030, # 35
40: 2.021, # 40
45: 2.014, # 45
50: 2.009, # 50
60: 2.000, # 
70: 1.994, # 
80: 1.990, # 
90: 1.987, # 
100: 1.984, # 
150: 1.976, # 
200: 1.972, # 
250: 1.969, # 
300: 1.968, # 
400: 1.966, # 
500: 1.965, # 
600: 1.964, # 
800: 1.963, # 
1000: 1.962, # 
100000: 1.960, # 
    }.items())

    def __init__(self,samples,sum,sumabs,sumsqr,sumreciproc,geomean):
        self._samples = list(samples) # Assumed sorted
        self._sum = sum
        self._sumabs = sumabs
        self._sumsqr = sumsqr
        self._sumreciproc = sumreciproc
        self._geomean = geomean
 
    @property
    def is_empty(self):
        return not not self._samples

    @property
    def count(self):
        return len(self._samples)

    @property
    def minimum(self):
        return self._samples[0]

    @property
    def maximum(self):
        return self._samples[-1]


    # Location

    @property
    def mean(self):
        return self._sum/self.count

    @property
    def geomean(self):
        return self._geomean

    @property
    def harmonicmean(self):
        return self.count  / self._sumreciproc  

    @property
    def median(self):
        return self.quantile(1,2)
        n = self.count
        if n % 2 == 0:
            return (self.vals[n//2] + self.vals[n//2+1])/2
        else:
            return self.vals[n//2]

    @property 
    def midrange(self):
        return (self.minimum + self.maximum)/2

    def mode(self, boxsize):
        boxes = defaultdict(0)
        for v in self._samples:
            boxidx = round(v / boxsize)
            boxes[boxidx] += 1

        maxcount = 0
        boxids = []
        for boxidx,count in boxes.items():
            if count < maxcount:
                continue
            if count > maxcount:
                maxcount = count
                boxids.clear()
                continue
            boxids.append(boxids)
            
        if len(boxids) % 2 == 0:
            midboxid = (boxids[len(boxids)//2] + boxids[len(boxids)//2+1])/2
        else:
            midboxid = boxids[len(boxids)//2] 
        return midboxid * boxsize


    # Spread

    @property
    def variance(self):
        def sqr(x):
            return x * x
        n = self.count
        return self._sumsqr / n - sqr(self.mean)

    @property
    def corrected_variance(self):
        n = self.count
        return self.variance * n / (n-1)


    @property
    def stddev(self):
        return math.sqrt(self.variance)

    @property
    def corrected_stddev(self):
        return math.sqrt(self.corrected_variance)

    @property
    def relative_stddev(self):
        return self.stddev / abs(self.mean)

    @property 
    def range(self):        
        return self.maximum - self.minimum

    # Mean squared error/deviation
    @property 
    def mse(self):
        def sqr(x):
            return x * x
        e = self.median # Using median as estimator
        return  sum(sqr(x - e) for x in self._vals) / self.count

    # Root mean squared error/deviation
    @property 
    def rmse(self):
        return math.sqrt(self.mse)

    @property 
    def relative_rmse(self):
        return self.rmse / abs(self.median)

    # Mean absolute error/deviation
    @property 
    def mad(self):
        median = self.median
        return sum(abs(x - median) for x in self._vals) / self.count

    # Symmetric confidence interval around mean, assuming normal distributed samples
    def abserr(self,ratio=0.95):
        assert ratio == 0.95, r"Only supporting two-sided 95% confidence interval"
        n = self.count
        if n < 2:
            return None

        # Table lookup
        # TODO: bisect
        c = None
        for (n1,p1),(n2,p2) in zip(Statistic.studentt_density_95, Statistic.studentt_density_95[1:]):
            if n1 <= n <= n2:
                # Linear interpolation
                r = (n - n1) / (n2 - n1)
                c = r * p2 + (1 - r) * p1
                break
        if c is None:
            c = Statistic.studentt_density_95[-1][1]

        return c * self.corrected_variance / math.sqrt(n)

    def relerr(self,ratio=0.95):
        mean = self.mean 
        if not mean :
            return None
        return self.abserr(ratio=ratio) / self.mean 


    # Other

    def quantile(self,k,d):
        assert d >=1
        assert k >= 0 <= d
  
        if not self._vals:
            return None

        if k == 0:
            return self._vals[0]
        if k == n:
            return self._vals[-1]

        n = self.count
        if (k*n-1) % d == 0:
            return self._vals[(k*n-1)//d]
    

    def quartile(self,k:int):
        return self.quantile(k,4)

    def decile(self,k:int):
        return self.quantile(k,10)

    def percentile(self,k:int):
        return self.quantile(k,100)


def statistic(data):
    vals = sorted(d for d in data if d is not None)
    n = 0
    hasnonpos = False
    sum = 0
    sumabs = 0
    sumsqr = 0
    sumreciproc = 0
    prod = 1
    for v in vals:
        if v <= 0:
            hasnonpos = True
        sum += v
        sumabs = abs(v)
        sumsqr += v*v
        if not hasnonpos:
            sumreciproc += 1//v
            prod *= v
        n += 1
    
    if hasnonpos:
        geomean = None
        sumreciproc = None
    else:
        geomean = prod**(1/n)
    
    
    return Statistic(samples=vals,sum=sum,sumabs=sumabs,sumsqr=sumsqr,geomean=geomean,sumreciproc=sumreciproc)



class BenchVariants:
    def __init__(self, default_size, serial=None, cuda=None):
        None



class BenchResult:
    def __init__(self,name:str, count:int, wtime , utime ,ktime , acceltime,maxrss):
        self.name=name
        self.count=count
        self.wtime=wtime
        self.utime=utime
        self.ktime=ktime
        self.acceltime=acceltime
        self.maxrss=maxrss



def run_gbench(exe):
    start = datetime.datetime.now()
    p = subprocess.Popen([exe],stdout=subprocess.PIPE,universal_newlines=True)
    #print([exe])

    

    stdout = p.stdout.read()
    unused_pid, exitcode, ru = os.wait4(p.pid, 0)
    stop = datetime.datetime.now()
    wtime = max(stop - start,datetime.timedelta(0))
    utime = ru.ru_utime
    stime = ru.ru_stime
    maxrss = ru.ru_maxrss

    benchmarks = et.fromstring(stdout)

    count = 0
    for benchmark in benchmarks:
        name = benchmark.attrib['name']
        n = benchmark.attrib['n']
        count = len( benchmark)

        walltime = statistic( float(b.attrib['walltime']) for b in  benchmark)
        usertime = statistic ( float(b.attrib['usertime']) for b in  benchmark)
        kerneltime  = statistic ( float(b.attrib['kerneltime']) for b in  benchmark)
        acceltime  = statistic ( float(b.attrib['acceltime']) for b in  benchmark)

        yield BenchResult(name=name, count=count,wtime=walltime,utime=usertime,ktime=kerneltime,acceltime=acceltime, maxrss=maxrss) 
        


def align_decimal(s):
    # FIXME: Don't align in scientific notation?
    pos = s.find('.')
    if pos >= 0:
        return StrAlign(s, pos)
    return StrAlign(s, len(s))



def run_benchs(config:str=None,serial=[],cuda=[],omp_parallel=[],omp_task=[],omp_target=[]):
    results = []
    for e in serial:
        results += list(run_gbench(exe=e))

    for e in cuda:
        results += list(run_gbench(exe=e))

    for e in omp_parallel:
        results += list(run_gbench(exe=e))

    for e in omp_task:
        results += list(run_gbench(exe=e))

    for e in omp_target:
        results += list(run_gbench(exe=e))

    walltime_stat = statistic(r.wtime.mean for r in results)
    usertime_stat = statistic(r.utime.mean for r in results)
    kerneltime_stat = statistic(r.ktime.mean for r in results)
    acceltime_stat = statistic(r.acceltime.mean for r in results)

    table = Table()
    def path_formatter(v:pathlib.Path):
        if v is None:
            return None
        return StrColor(pathlib.Path(v).name,colorama.Fore.GREEN)
    def count_formatter(v:int):
        return StrColor(str(v),colorama.Fore.BLUE)
    def duration_formatter(best,worst):
        def formatter(s: Statistic):
            if s is None:
                return None
            v = s.mean
            d = s.relerr()
            def highlight_extremes(s):
                if best is not None and worst is not None and best < worst:
                    if v <= best:
                        return StrColor(s, colorama.Fore.GREEN)
                    if v >= worst:
                        return StrColor(s, colorama.Fore.RED)
                return s
        
            if d and d >= 0.0001:
                errstr = f"(±{d:.1%})"
                if d >= 0.02:
                    errstr = StrColor(errstr, colorama.Fore.RED)
                errstr = str_concat(' ',errstr)
            else:
                errstr = ''


            if v >= 1:
                return highlight_extremes(align_decimal(f"{v:.2}")) +StrColor("s", colorama.Style.DIM) + (str_concat(' ', errstr) if errstr else '')
            if v*1000 >= 1:
                return highlight_extremes(align_decimal(f"{v*1000:.2f}") )+ StrColor("ms", colorama.Style.DIM) + errstr
            if v*1000*1000 >= 1:
                return highlight_extremes(align_decimal(f"{v*1000*1000:.2f}")) + StrColor("µs", colorama.Style.DIM) + errstr
            return highlight_extremes(align_decimal(f"{v*1000*1000*1000:.2f}")) + StrColor( "ns", colorama.Style.DIM) + errstr
        return formatter

    table.add_column('program', title=StrColor("Benchmark", colorama.Fore.BWHITE),  formatter=path_formatter)
    table.add_column('n', title=StrColor("Repeats", colorama.Style.BRIGHT),formatter=count_formatter)
    table.add_column('wtime', title=StrColor( "Wall" , colorama.Style.BRIGHT),formatter=duration_formatter(walltime_stat.minimum,walltime_stat.maximum))
    table.add_column('utime', title=StrColor( "User" , colorama.Style.BRIGHT),formatter=duration_formatter(usertime_stat.minimum,usertime_stat.maximum))
    table.add_column('ktime', title=StrColor("Kernel" , colorama.Style.BRIGHT),formatter=duration_formatter(kerneltime_stat.minimum,kerneltime_stat.maximum))
    table.add_column('acceltime', title=StrColor("GPU" , colorama.Style.BRIGHT),formatter=duration_formatter(acceltime_stat.minimum,acceltime_stat.maximum))
    
    for r in results:
        # TODO: acceltime doesn't always apply
        table.add_row(program=r.name,n=r.count,wtime=r.wtime,utime=r.utime,ktime=r.ktime,acceltime=r.acceltime)

    
    table.print()



def main(argv):
    colorama.init()
    parser = argparse.ArgumentParser(description="Benchmark runner", allow_abbrev=False)
    #parser.add_argument('--exe',    action='append', default=[], type=pathlib.Path,  help="Google Benchmark Executable")
    #parser.add_argument('--exedir', action='append', default=[], type=pathlib.Path, help="Google Benchmark Executable")
    #parser.add_argument('gbenchexe',nargs='+', help="Google Benchmark Executables")
    parser.add_argument('--serial', action='append', default=[], help="Google Benchmark Executables")
    parser.add_argument('--cuda', action='append', default=[], help="Google Benchmark Executables")
    args = parser.parse_args(argv[1:])




if __name__ == '__main__':
    retcode = main(argv=sys.argv)
    if retcode:
        exit(retcode)
