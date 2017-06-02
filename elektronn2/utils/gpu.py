# -*- coding: utf-8 -*-
# ELEKTRONN2 Toolkit
# Copyright (c) 2015 Marius Killinger
# All rights reserved
# This Code is adapted from Sven Dorkenwald

from __future__ import absolute_import, division, print_function
from builtins import filter, hex, input, int, map, next, oct, pow, range, \
    super, zip

import sys
import subprocess
import time


def initgpu(gpu, prefix='cuda'):
    if gpu is None:
        gpu = 'none'
    no_gpu = ['none', 'None']
    gpu = str(gpu)
    import theano.gpuarray

    # try:
    if gpu.lower() == 'auto':
        gpu = str(get_free_gpu())
        print("Automatically assigning free GPU %s" % (gpu,))

    if gpu in no_gpu and gpu != '0':
        return 'cpu'
    else:
        try:
            if gpu.isdigit():  # If int, prepend prefix
                gpu = '{}{}'.format(prefix, gpu)
                theano.gpuarray.use(gpu)
            else:
                theano.gpuarray.use(gpu)
            print("Initialising GPU to %s" % gpu)
            return gpu

        except:
            sys.excepthook(*sys.exc_info())
            raise RuntimeError("Failed to init GPU {}. Aborting...".format(gpu))

    # except:
    #     if gpu in no_gpu and gpu != 0:
    #         pass
    #     else:
    #         print("'--gpu' argument is not 'none' but CUDA is not available. "
    #               "Falling back to CPU.")


def _check_if_gpu_is_free(nb_gpu):
    try:
        process_output = subprocess.Popen(
            'nvidia-smi -i %d -q -d PIDS' % nb_gpu,
             stdout=subprocess.PIPE,
             shell=True
        ).communicate()[0]
    except Exception as e:
        print('nvidia-smi can\'t be executed.\n'
              'Please make sure CUDA is available on your machine.\n')
        raise e
    if b"Process ID" in process_output and b"Used GPU Memory" in process_output:
        return False
    else:
        return True


def _get_number_gpus():
    try:
        process_output = subprocess.Popen(
            'nvidia-smi -L', stdout=subprocess.PIPE, shell=True
        ).communicate()[0].decode()
    except Exception as e:
        print('nvidia-smi can\'t be executed.\n'
              'Please make sure CUDA is available on your machine.\n')
        raise e
    nb_gpus = 0
    while True:
        if "GPU %d" % nb_gpus in process_output:
            nb_gpus += 1
        else:
            break
    return nb_gpus


def get_free_gpu(wait=0, nb_gpus=-1, prefix='cuda'):
    if nb_gpus==-1:
        nb_gpus = _get_number_gpus()
    while True:
        for nb_gpu in range(nb_gpus):
            if _check_if_gpu_is_free(nb_gpu):
                return '{}{}'.format(prefix, nb_gpu)
        if wait > 0:
            time.sleep(2)
        else:
            return -1
