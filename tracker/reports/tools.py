#!/usr/env python3

def __get_nums(item):
    return item[len('release-'):].replace('.t', '').split('.', 2)

def __num(number):
    return -1 * int(number)

def sort_versions(versions):
    return sorted(versions, key=lambda x: (__num(__get_nums(x)[0]), __num(__get_nums(x)[1]), __num(__get_nums(x)[2])))