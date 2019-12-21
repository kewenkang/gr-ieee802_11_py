#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

def get_logger(name, verbose):
    if verbose == 'INFO':
        logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)s: %(message)s')
    elif verbose == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)-15s %(levelname)s: %(message)s')
    return logging.getLogger(name)
