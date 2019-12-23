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
from enum import Enum
from gnuradio import gr
import pmt
import utils

class State(Enum):
    SYNC = 1
    COPY = 2
    RESET = 3

LONG = numpy.array([
complex(-0.0455, -1.0679), complex( 0.3528, -0.9865), complex( 0.8594,  0.7348), complex( 0.1874,  0.2475),
complex( 0.5309, -0.7784), complex(-1.0218, -0.4897), complex(-0.3401, -0.9423), complex( 0.8657, -0.2298),
complex( 0.4734,  0.0362), complex( 0.0088, -1.0207), complex(-1.2142, -0.4205), complex( 0.2172, -0.5195),
complex( 0.5207, -0.1326), complex(-0.1995,  1.4259), complex( 1.0583, -0.0363), complex( 0.5547, -0.5547),
complex( 0.3277,  0.8728), complex(-0.5077,  0.3488), complex(-1.1650,  0.5789), complex( 0.7297,  0.8197),
complex( 0.6173,  0.1253), complex(-0.5353,  0.7214), complex(-0.5011, -0.1935), complex(-0.3110, -1.3392),
complex(-1.0818, -0.1470), complex(-1.1300, -0.1820), complex( 0.6663, -0.6571), complex(-0.0249,  0.4773),
complex(-0.8155,  1.0218), complex( 0.8140,  0.9396), complex( 0.1090,  0.8662), complex(-1.3868, -0.0000),
complex( 0.1090, -0.8662), complex( 0.8140, -0.9396), complex(-0.8155, -1.0218), complex(-0.0249, -0.4773),
complex( 0.6663,  0.6571), complex(-1.1300,  0.1820), complex(-1.0818,  0.1470), complex(-0.3110,  1.3392),
complex(-0.5011,  0.1935), complex(-0.5353, -0.7214), complex( 0.6173, -0.1253), complex( 0.7297, -0.8197),
complex(-1.1650, -0.5789), complex(-0.5077, -0.3488), complex( 0.3277, -0.8728), complex( 0.5547,  0.5547),
complex( 1.0583,  0.0363), complex(-0.1995, -1.4259), complex( 0.5207,  0.1326), complex( 0.2172,  0.5195),
complex(-1.2142,  0.4205), complex( 0.0088,  1.0207), complex( 0.4734, -0.0362), complex( 0.8657,  0.2298),
complex(-0.3401,  0.9423), complex(-1.0218,  0.4897), complex( 0.5309,  0.7784), complex( 0.1874, -0.2475),
complex( 0.8594, -0.7348), complex( 0.3528,  0.9865), complex(-0.0455,  1.0679), complex( 1.3868, -0.0000),
])

class sync_long(gr.basic_block):
    """
    docstring for block sync_long
    """

    def __init__(self, sync_length, verbose):
        gr.basic_block.__init__(self,
            name="sync_long",
            in_sig=[numpy.complex64, numpy.complex64],
            out_sig=[numpy.complex64])
        self.d_state = State.SYNC
        self.d_offset = 0
        self.d_logger = self.d_logger = utils.get_logger('sync_long', verbose)
        self.d_sync_length = sync_length
        self.d_fir = gr.filter.kernel.fir_filter_ccc(1, LONG)

        self.d_cor = []
        self.d_freq_offset_short = 0
        self.d_frame_start = 0
        self.d_freq_offset = 0
        self.d_count = 0

        set_tag_propagation_policy(gr.block.TPP_DONT)

    def forecast(self, noutput_items, ninput_items_required):
        if self.d_state == State.SYNC:
            ninput_items_required[0] = 64
            ninput_items_required[1] = 64
        else:
            ninput_items_required[0] = noutput_items
            ninput_items_required[1] = noutput_items

    def search_frame_start(self):
        assert len(self.d_cor) == self.d_sync_length
        cor = numpy.abs(self.d_cor)
        indices = numpy.argsort(cor)[::-1]

        for i in range(3):
            for k in range(i+1, 4):
                if indices[i] >= indices[k]:
                    first = cor[indices[i]]
                    second = cor[indices[k]]
                else:
                    first = cor[indices[k]]
                    second = cor[indices[i]]
                diff = abs(indices[i] - indices[k])
                if diff == 64:
                    # best match
                    self.d_frame_start = min(indices[i], indices[k])
                    self.d_freq_offset = numpy.angle(first * numpy.conj(second)) / 64
                    return
                elif diff == 63 or diff == 65:
                    self.d_frame_start = min(indices[i], indices[k])
                    self.d_freq_offset = numpy.angle(first * numpy.conj(second)) / diff

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        in_delayed = input_items[1]
        out = output_items[0]
        noutput = len(output_items[0])
        # <+signal processing here+>
        self.d_logger.debug('LONG ninput[0]: {}, ninput[1]: {}, noutput: {}, state: {}'.format(
            len(input_items[0]), len(input_items[1]), len(output_items[0]), self.d_state))

        ninput = min(min(len(input_items[0]), len(input_items[1])), 8192)
        nread = nitems_read(0)  # get absolute index
        tags = get_tags_in_range(0, nread, nread + ninput)  # get tages of this samples
        if len(tags):
            tags = sorted(tags, key=lambda tag: tag.offset)
            offset = tags[0].offset

            if offset > nread:
                ninput = offset - nread
            else:
                if self.d_offset and self.d_state == State.SYNC:
                    raise Exception("wtf")
                if self.d_state == State.COPY:
                    self.d_state = State.RESET
                self.d_freq_offset_short = pmt.to_double(tags[0].value)

        #
        i = 0
        o = 0
        if self.d_state == State.SYNC:
            cor = self.d_fir.filterN(in0, min(self.d_sync_length, max(ninput - 63, 0)))
            while i + 63 < ninput:
                self.d_cor.append(cor[i])
                i += 1
                self.d_offset += 1

                if self.d_offset == self.d_sync_length:
                    self.search_frame_start()
                    self.d_logger.debug('LONG: frame start at {}'.format(self.d_frame_start))
                    self.d_offset = 0
                    self.d_count = 0
                    self.d_state = State.COPY
                    break

        elif self.d_state == State.COPY:
            while i < ninput and o < noutput:
                rel = self.d_offset - self.d_frame_start
                if not rel:
                    add_item_tag(0, nitems_written(0),
                                 pmt.intern('wifi_start'),
                                 pmt.from_double(self.d_freq_offset_short - self.d_freq_offset),
                                 pmt.intern(name()))
                if rel >= 0 and (rel < 128 or ((rel - 128) % 80) > 15):
                    out[o] = in_delayed[i] * numpy.exp(complex(0, self.d_offset * self.d_freq_offset))
                    o += 1
                i += 1
                self.d_offset += 1

        elif self.d_state == State.RESET:
            while o < noutput:
                if (self.d_count + o) % 64 == 0:
                    self.d_offset = 0
                    self.d_state = State.SYNC
                    break
                else:
                    out[o] = 0
                    o += 1
        self.d_logger.debug('produced: {}, consumed: {}'.format(o, i))
        self.d_count += o
        comsume_each(i)
        # out[:] = in0
        return o

