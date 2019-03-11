#include <boost/filesystem.hpp>
#include <iostream>

int main(int argc, char *argv[])
{
	std::cout << "boostuse1: " << boost::filesystem::file_size(argv[0]) << std::endl;
	return 0;
}