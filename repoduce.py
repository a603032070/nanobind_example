import subprocess
import nanobind.stubgen
import importlib
import sys

# the commandline interface yields the stub as the code do below:
sys.path.insert(0, "build")
m = importlib.import_module("ext_foo")
sg = nanobind.stubgen.StubGen(m)
sg.put(m)
res = sg.get()
not_desired = (
    '\n\ndef do(bar: "Bar") -> None: ...\n\ndef do2(bar: bar.Bar)->None: ...\n'
)
desired = 'import ext_foo_bar\n\n\ndef do(bar: "Bar") -> None: ...\n\ndef do2(bar: ext_foo_bar.Bar)->None: ...\n'
assert res == not_desired

# try to make a monkey patch here.

# `simplify_types` `import_object`is just copied from the orginal stubgen code,
# but lineno(672):
# `if full_name.startswith(self.module.__name__):`
# replaced by:
# `if is_submodule(full_name, self.module.__name__):`
# and lineno(882):
# `if module.startswith(self.module.__name__):`
# replaced by:
# `if is_submodule(module, self.module.__name__):`


def is_submodule(sub_mod: str, mod: str):
    if sub_mod == mod:
        return True
    return sub_mod.startswith(f"{mod}.")


from nanobind.stubgen import *


def simplify_types(self, s: str) -> str:
    """
    Process types that occur within a signature string ``s`` and simplify
    them. This function applies the following rules:

    - "local_module.X" -> "X"

    - "other_module.X" -> "other_module.XX"
        (with "import other_module" added at top)

    - "builtins.X" -> "X"

    - "NoneType" -> "None"

    - "ndarray[...]" -> "Annotated[ArrayLike, dict(...)]"

    - "collections.abc.X" -> "X"
        (with "from collections.abc import X" added at top)

    - "typing.X" -> "X"
        (with "from typing import X" added at top, potentially
        changed to 'collections.abc' on newer Python versions)
    """

    # Process nd-array type annotations so that MyPy accepts them
    def process_ndarray(m: Match[str]) -> str:
        s = m.group(2)

        ndarray = self.import_object("numpy.typing", "ArrayLike")
        assert ndarray
        s = re.sub(r"dtype=([\w]*)\b", r"dtype='\g<1>'", s)
        s = s.replace("*", "None")

        if s:
            annotated = self.import_object("typing", "Annotated")
            return f"{annotated}[{ndarray}, dict({s})]"
        else:
            return ndarray

    s = self.ndarray_re.sub(process_ndarray, s)

    if sys.version_info >= (3, 9, 0):
        s = self.abc_re.sub(r"collections.abc.\1", s)

    # Process other type names and add suitable import statements
    def process_general(m: Match[str]) -> str:
        full_name, mod_name, cls_name = m.group(0), m.group(1)[:-1], m.group(2)

        if mod_name == "builtins":
            # Simplify builtins
            return cls_name if cls_name != "NoneType" else "None"
        # if full_name.startswith(self.module.__name__):
        if is_submodule(full_name, self.module.__name__):
            # Strip away the module prefix for local classes
            return full_name[len(self.module.__name__) + 1 :]
        elif mod_name == "typing" or mod_name == "collections.abc":
            # Import frequently-occurring typing classes and ABCs directly
            return self.import_object(mod_name, cls_name)
        else:
            # Import the module and reference the contained class by name
            self.import_object(mod_name, None)
            return full_name

    s = self.id_seq.sub(process_general, s)

    return s


def import_object(
    self, module: str, name: Optional[str], as_name: Optional[str] = None
) -> str:
    """
    Import a type (e.g. typing.Optional) used within the stub, ensuring
    that this does not cause conflicts. Specify ``as_name`` to ensure that
    the import is bound to a specified name.

    When ``name`` is None, the entire module is imported.
    """
    if module == "builtins" and name and (not as_name or name == as_name):
        return name

    # Rewrite module name if this is relative import from a submodule
    # if module.startswith(self.module.__name__):
    if is_submodule(module, self.module.__name__):
        module_short = module[len(self.module.__name__) :]
        if not name and as_name and module_short[0] == ".":
            name = as_name = module_short[1:]
            module_short = "."
    else:
        module_short = module

    # Query a cache of previously imported objects
    imports_module: Optional[ImportDict] = self.imports.get(module_short, None)
    if not imports_module:
        imports_module = {}
        self.imports[module_short] = imports_module

    key = (name, as_name)
    final_name = imports_module.get(key, None)
    if final_name:
        return final_name

    # Cache miss, import the object
    final_name = as_name if as_name else name

    # If no as_name constraint was set, potentially adjust the name to
    # avoid conflicts with an existing object of the same name
    if name and not as_name:
        test_name = name
        while True:
            # Accept the name if there are no conflicts
            if not hasattr(self.module, test_name):
                break
            value = getattr(self.module, test_name)
            try:
                if module == ".":
                    mod_o = self.module
                else:
                    mod_o = importlib.import_module(module)

                # If there is a conflict, accept it if it refers to the same object
                if getattr(mod_o, name) is value:
                    break
            except ImportError:
                pass

            # Prefix with an underscore
            test_name = "_" + test_name
        final_name = test_name

    imports_module[key] = final_name
    return final_name if final_name else ""


# make patch
nanobind.stubgen.StubGen.simplify_types = simplify_types
nanobind.stubgen.StubGen.import_object = import_object

sg = nanobind.stubgen.StubGen(m)
sg.put(m)
res = sg.get()
assert res == desired

# now the problem has gone.
