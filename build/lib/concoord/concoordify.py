'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Creates concoord objects
@copyright: See LICENSE
'''
import argparse
import ast, _ast
import os, sys, time, shutil
from time import sleep,time
from optparse import OptionParser
from concoord.safetychecker import *
from concoord.proxygenerator import *

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--objectfilepath", action="store", dest="objectfilepath",
                    help="client object file path")
parser.add_argument("-c", "--classname", action="store", dest="classname",
                    help="main class name")
parser.add_argument("-s", "--safe", action="store_true", dest="safe", default=False,
                    help="safety checking on/off")
parser.add_argument("-t", "--token", action="store", dest="securitytoken", default=None,
                    help="security token")
parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=None,
                    help="verbose option")
args = parser.parse_args()

def check_object(clientcode):
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe
