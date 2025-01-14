/*
 * @Author: chamip
 * @Date: 2023-02-02 11:50:41
 * @LastEditTime: 2023-02-03 14:36:32
 * @LastEditors: chamip
 * @FilePath: /cmake-cookbook/chapter-02/recipe-03/cxx-example/hello-world.cpp
 */
#include <cstdlib>
#include <iostream>
#include <string>

std::string say_hello() {
#ifdef IS_INTEL_CXX_COMPILER
  // only compiled when Intel compiler is selected
  // such compiler will not compile the other branches
  return std::string("Hello Intel compiler!");
#elif IS_GNU_CXX_COMPILER
  // only compiled when GNU compiler is selected
  // such compiler will not compile the other branches
  return std::string("Hello GNU compiler!");
#elif IS_PGI_CXX_COMPILER
  // etc.
  return std::string("Hello PGI compiler!");
#elif IS_XL_CXX_COMPILER
  return std::string("Hello XL compiler!");
#elif IS_AppleClang_CXX_COMPILER
  return std::string("Hello AppleClang compiler!");
#else
  return std::string("Hello unknown compiler - have we met before?");
#endif
}

int main() {
  std::cout << say_hello() << std::endl;
  std::cout << "compiler name is " COMPILER_NAME << std::endl;
  return EXIT_SUCCESS;
}
