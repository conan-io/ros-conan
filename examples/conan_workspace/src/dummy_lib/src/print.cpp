#include <cstdio>

#include "dummy_lib/print.hpp"

namespace dummy_lib
{

void print_hello()
{
  std::puts("[dummy_lib] hello from library");
}

}  // namespace dummy_lib
