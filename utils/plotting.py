import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import AutoMinorLocator

from mpl_toolkits.axes_grid1 import make_axes_locatable



def set_colour_cycle(lib, cycle_type: str = 'colour'):
    '''
    Sets a colour cycle for matplotlib and returns the list of colours
    '''
    if cycle_type.lower() == 'color' or cycle_type.lower() == 'colour':
        colour_list  = ['#6699CC', # blue
                        '#F99157', # orange
                        '#98c379', # green
                        '#C594C5', # purple
                        '#e06c75', # red
                        '#5FB3B3', # turquoise
                        '#FAC863'] # yellow
    elif cycle_type.lower() == 'gray' or cycle_type.lower() == 'grey':
        colour_list  = ['#090a0a', #'#1B2B34', # black
                        '#22272b',
                        '#3b434a',
                        '#65737E',
                        '#A7ADBA',
                        '#C0C5CE',
                        '#CDD3DE'] # white
    else:
        raise Exception('Unknown cycle_type: ' + cycle_type)
    
    lib.rcParams['axes.prop_cycle'] = mpl.cycler(color=colour_list)
    return colour_list



def set_plot_font(lib, font_family='STIXGeneral', font_set='cm'):
    '''
    Sets the rcParams font for matplotlib
    to the given font family and mathtext.fontset
    '''
    lib.rcParams['mathtext.fontset'] = font_set
    lib.rcParams['font.family']      = font_family



def set_axis_ticks(axis, x_subticks = None, y_subticks = None, font_size = 18):
    '''
    Sets up x and y axis tick style
    '''
    if x_subticks is not None:
        axis.xaxis.set_minor_locator(AutoMinorLocator(x_subticks))
    if y_subticks is not None:
        axis.yaxis.set_minor_locator(AutoMinorLocator(y_subticks))

    axis.tick_params(bottom=True, top=False, left=True, right=False)
    axis.tick_params(axis='both', which='both', top=True, bottom=True,
                     left=True, right=True, length=6, direction='in',
                     labelsize=font_size)
    axis.tick_params(axis='both', which='minor', top=True, bottom=True,
                     left=True, right=True, length=3, direction='in',
                     labelsize=font_size)