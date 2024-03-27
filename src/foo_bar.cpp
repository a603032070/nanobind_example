#include <nanobind/nanobind.h>
#include "foo_bar.hpp"
namespace nb = nanobind;

using namespace nb::literals;
NB_MODULE(ext_foo_bar, m)
{
    nb::class_<Bar>(m, "Bar");
}
