import inspect
import sys

SAFE_SYMBOLS = ["list", "dict", "tuple", "set", "long", "float", "object",
                "bool", "callable", "True", "False", "dir",
                "frozenset", "getattr", "hasattr", "abs", "cmp", "complex",
                "divmod", "id", "pow", "round", "slice", "vars",
                "hash", "hex", "int", "isinstance", "issubclass", "len",
                "map", "filter", "max", "min", "oct", "chr", "ord", "range",
                "reduce", "repr", "str", "type", "zip", "xrange", "None",
                "Exception", "KeyboardInterrupt"]
# Also add the standard exceptions
__bi = __builtins__
if type(__bi) is not dict:
    __bi = __bi.__dict__
for k in __bi:
    if k.endswith("Error") or k.endswith("Warning"):
        SAFE_SYMBOLS.append(k)
del __bi

class ProxyMeta(type):
    def __init__(cls, name, bases, d):
        return type.__new__(cls, name, bases, d)

    def __new__(cls, name, bases, d):
        for e,t in d.iteritems():
            if inspect.isfunction(t):
                code = inspect.getsourcelines(t)
                if t.func_name == "__init__":
                    newcode[0] = code[0][0][4:]
                    newcode[1] = "    self.proxy = ClientProxy(bootstrap)\n"
                    source_code = ''.join(newcode)
                else:
                    args = code[0][0][4:].split('self')[1]
                    args = args.strip()
                    if args[0] != ')':
                        # there are arguments
                        args = args.strip(',')
                        args = args.strip()
                    args = args.strip('):')
                    newcode = ['','']
                    newcode[0] = code[0][0][4:]
                    if args:
                        newcode[1] = "    return proxy.invoke_command('%s', %s)\n" % (t.func_name, args)
                    else:
                        newcode[1] = "    return proxy.invoke_command('%s')\n" % t.func_name
                    source_code = ''.join(newcode)
                    byte_code = compile(source_code, "<string>", 'exec')
                    bis   = dict() # builtins
                    globs = dict()
                    locs  = dict()

                    bis["locals"]  = lambda: locs
                    bis["globals"] = lambda: globs
                    globs["__builtins__"] = bis
                    globs["__name__"] = "SUBENV"
                    globs["__doc__"] = source_code

                    if type(__builtins__) is dict:
                        bi_dict = __builtins__
                    else:
                        bi_dict = __builtins__.__dict__

                    # Include the safe symbols
                    for k in SAFE_SYMBOLS:
                        # try from current locals
                        try:
                            locs[k] = locals()[k]
                            continue
                        except KeyError:
                            pass
                        # Try from globals
                        try:
                            globs[k] = globals()[k]
                            continue
                        except KeyError:
                            pass
                        # Try from builtins
                        try:
                            bis[k] = bi_dict[k]
                        except KeyError:
                            # Symbol not available anywhere: silently ignored
                            pass

                    additional_symbols = dict(clientproxy='concoord.clientproxy')
                    globs.update(additional_symbols)
                    # Finally execute the def __TheFunction__ statement:
                    eval(byte_code, globs, locs)
                    # As a result, the function is defined as the item __TheFunction__
                    # in the locals dictionary
                    fct = locs[t.func_name]
                    # Attach the function to the globals so that it can be recursive
                    del locs[t.func_name]
                    globs[t.func_name] = fct
                    # Attach the actual source code to the docstring
                    fct.__doc__ = source_code
                    t = fct
        return type.__new__(cls, name, bases, d)

    def __call__(cls, *args, **kwds):
        return type.__call__(cls, *args, **kwds)

