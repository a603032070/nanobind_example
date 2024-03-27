#include <nanobind/nanobind.h>
#include "foo_bar.hpp"

namespace nb = nanobind;

using namespace nb::literals;

const char *desired_sig = "def do2(bar: ext_foo_bar.Bar)->None";
NB_MODULE(ext_foo, m)
{
    m.def(
        "do", [](Bar bar) {},
        "bar"_a);
    m.def(
        "do2", [](Bar bar) {},
        "bar"_a, nb::sig(desired_sig));
}
