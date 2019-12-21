#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2019 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy
from gnuradio import gr
import utils
from enum import Enum

class State(Enum):
    SEARCH = 1
    COPY = 2

class sync_short(gr.block):
    """
    docstring for block sync_short
    """
    def __init__(self, threshold, min_plateau, verbose):
        gr.block.__init__(self,
            name="sync_short",
            in_sig=[numpy.complex64, numpy.complex64, numpy.float],
            out_sig=[numpy.complex64])
        self.logger = utils.get_logger('sync_short', verbose)
        self.threshold = threshold
        self.min_plateau = min_plateau
        self.state = State.SEARCH
        self.plateau = 0
        self.freq_offset = 0
        self.copied = 0
        set_tag_propagation_policy(gr.block.)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        # <+signal processing here+>
        out[:] = in0
        return len(output_items[0])

