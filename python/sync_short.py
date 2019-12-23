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
import pmt
import utils
from enum import Enum

class State(Enum):
    SEARCH = 1
    COPY = 2

MIN_GAP = 480
MAX_SAMPLES = 540 * 80

class sync_short(gr.basic_block):
    """
    docstring for block sync_short
    """
    def __init__(self, threshold, min_plateau, verbose):
        gr.basic_block.__init__(self,
            name="sync_short",
            in_sig=[numpy.complex64, numpy.complex64, numpy.float],
            out_sig=[numpy.complex64])
        self.d_logger = utils.get_logger('sync_short', verbose)
        self.d_threshold = threshold
        self.d_min_plateau = min_plateau
        self.d_state = State.SEARCH
        self.d_plateau = 0
        self.d_freq_offset = 0
        self.d_copied = 0
        # set_tag_propagation_policy(gr.block.)

    def insert_tag(self, item, freq_offset, input_item):
        self.d_logger.debug('frame start at in: {} out: {}'.format(input_item, item))

        key = pmt.intern('wifi_start')
        value = pmt.from_double(freq_offset)
        srcid = pmt.intern(name())
        add_item_tag(0, item, key, value, srcid)

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        in_abs = input_items[1]
        in_cor = input_items[2]
        out = output_items[0]

        noutput = len(output_items[0])
        ninput = min(min(len(input_items[0]), len(input_items[1])), len(input_items[2]))

        if self.d_state == State.SEARCH:
            i = 0
            while i < ninput:
                if in_cor[i] > self.d_threshold:
                    if self.d_plateau < self.d_min_plateau:
                        self.d_plateau += 1
                    else:
                        self.d_state = State.COPY
                        self.d_copied = 0
                        self.d_plateau = 0
                        self.d_freq_offset = numpy.angle(in_abs[i]) / 16
                        self.insert_tag(nitems_written(0), self.d_freq_offset, nitems_read(0)+i)
                        self.d_logger.info('SHORT Frame!')
                        break
                else:
                    self.d_plateau = 0
                i += 1
            consume_each(i)
            return 0
        elif self.d_state == State.COPY:
            o = 0
            while o < ninput and o < noutput and self.d_copied < MAX_SAMPLES:
                if in_cor[o] > self.d_threshold:
                    if self.d_plateau < self.d_min_plateau:
                        self.d_plateau += 1
                    # there is another frame
                    elif self.d_copied > MIN_GAP:
                        # self.d_state = State.COPY
                        self.d_copied = 0
                        self.d_plateau = 0
                        self.d_freq_offset = numpy.angle(in_abs[o]) / 16
                        self.insert_tag(nitems_written(0) + o, self.d_freq_offset, nitems_read(0) + o)
                        self.d_logger.info('SHORT Frame!')
                        break
                else:
                    self.d_plateau = 0

                out[o] = in0[o] * numpy.exp(complex(0, - self.d_freq_offset * self.d_copied))
                o += 1
                self.d_copied += 1
            if self.d_copied == MAX_SAMPLES:
                self.d_state = State.SEARCH
            self.d_logger.debug('SHORT copied: {}'.format(o))
            consume_each(o)
            return o

        raise Exception('sync short: unknown state')
        # <+signal processing here+>

        # out[:] = in0
        # return len(output_items[0])

