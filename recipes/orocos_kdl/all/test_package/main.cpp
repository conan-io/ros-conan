#include <kdl/frames.hpp>
#include <iostream>

int main() {
    KDL::Vector v(1.0, 2.0, 3.0);
    std::cout << v.Norm() << "\n";
    return 0;
}
