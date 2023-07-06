# -*- coding: utf-8 -*-

import sys

if not sys.version_info >= (3, 9):
    print("Requires python 3.9 or later", file=sys.stderr)
    print(f"Python interpreter {sys.executable} reports version {sys.version}", file=sys.stderr)
    sys.exit(1)


import argparse
import configparser
import pathlib

from rosetta.util.support import *
import rosetta.runner as runner
from rosetta import registry


def cquote(s):
    # TODO: More escaping
    s = str(s)
    s = s.replace("\\", "\\\\")
    s = s.replace("\n", "\\n")
    return '"' + s + '"'


def gen_config(output, benchname, problemsizefile, resultsdir, compiler, compilerflags, configname, buildtype, pbsize):
    config = configparser.ConfigParser()
    config.read(problemsizefile)
    n = config.getint(benchname, 'n')

    # Consider a static initializer which calls into the rosetta library if global symbols are problematic.
    content = f"""/* autogenerated by Rosetta gen-stage2.py */
#include <cstdint>

// Configuration properties
const char *rosetta_default_results_dir = {cquote(resultsdir)};
const char *rosetta_configname = {cquote(configname)};
const char *rosetta_compiler = {cquote(compiler)};
const char *rosetta_compiler_flags = {cquote(compilerflags)};
const char *bench_buildtype = {cquote(buildtype)};

// Benchmark properties
const char *bench_name = {cquote(benchname)};
int64_t bench_default_problemsize = {pbsize};
"""

    # TODO: Don't replace if identical for ninja to know there's no recompile needed
    with output.open('w+') as f:
        f.write(content)


def gen_benchpropfile(bench: runner.Benchmark, config: str, resultsdir: pathlib.Path):
    benchproptempl = bench.benchpropfile
    benchpropfile = mkpath(benchproptempl.replace('$<CONFIG>', config))
    # print(benchpropfile)

    configname = bench.configname
    compiler = bench.compiler
    compilerflags = bench.compilerflags
    buildtype = bench.buildtype
    benchname = bench.name

    content = f"""/* autogenerated by Rosetta genconfig.py */
#include <cstdint>

// Configuration properties
const char *rosetta_default_results_dir = {cquote(resultsdir)};
const char *rosetta_configname = {cquote(configname)};
const char *rosetta_compiler = {cquote(compiler)};
const char *rosetta_compiler_flags = {cquote(compilerflags)};
const char *bench_buildtype = {cquote(buildtype)};

// Benchmark properties
const char *bench_name = {cquote(benchname)};
int64_t bench_default_problemsize = {bench.pbsize};
"""

    benchpropfile = bench.benchpropfile
    # print(f"{benchpropfile=}")
    updatefile(benchpropfile, content)


def gen_stage2(builddir, benchdir, benchlistfile, config, resultsdir):
    # print("gen_stage2")

    # Load all available benchmarks
    registry.load_register_file(benchlistfile)

    for bench in registry.benchmarks:
        gen_benchpropfile(bench, config=config, resultsdir=resultsdir)


def main():
    # print("stage2 argv", sys.argv)
    parser = argparse.ArgumentParser(description="Generate make-time files", allow_abbrev=False)
    parser.add_argument('--builddir', type=pathlib.Path)
    parser.add_argument('--benchdir', type=pathlib.Path)
    parser.add_argument('--resultsdir', type=pathlib.Path)
    parser.add_argument('--benchfile', type=pathlib.Path)
    parser.add_argument('--config')
    args = parser.parse_args()

    builddir = args.builddir
    benchdir = args.benchdir
    benchfile = args.benchfile
    config = args.config

    gen_stage2(builddir=builddir, benchdir=benchdir, benchlistfile=benchfile, config=config, resultsdir=args.resultsdir)


if __name__ == '__main__':
    retcode = main()
    if retcode:
        exit(retcode)
