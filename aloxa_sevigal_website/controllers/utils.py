#-*- econding: utf-8 -*-

def Int2RGB(RGBint):
    return ((RGBint >> 16) & 255, (RGBint >> 8) & 255, RGBint & 255)
