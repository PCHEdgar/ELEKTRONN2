# -*- coding: utf-8 -*-

# Inspired by "3D U-Net", Özgün Çiçek et al.,
# (https://arxiv.org/abs/1606.06650). For a more faithful (but much heavier)
# implementation, refer to examples/unet_3d.py.

save_path = '~/elektronn2_training/'
preview_data_path = '~/neuro_data_zxy/preview_cubes.h5'
preview_kwargs    = {
    'export_class': [1],
    'max_z_pred': 3
}
initial_prev_h = 1.0  # hours: time after which the first preview is made
prev_save_h = 1.0  # hours: time interval between planned previews.
data_class = 'BatchCreatorImage'
background_processes = 2
data_init_kwargs = {
    'd_path' : '~/neuro_data_zxy/',
    'l_path': '~/neuro_data_zxy/',
    'd_files': [('raw_%i.h5' %i, 'raw') for i in range(3)],
    'l_files': [('barrier_int16_%i.h5' %i, 'lab') for i in range(3)],
    'aniso_factor': 2,
    'valid_cubes': [2],
}
data_batch_args = {
    'grey_augment_channels': [0],
    'warp': 0.5,
    'warp_args': {
        'sample_aniso': True,
        'perspective': True
    }
}
n_steps = 1000000
max_runtime = 14 * 24 * 3600 # in seconds
history_freq = 200
monitor_batch_size = 30
optimiser = 'Adam'
optimiser_params = {
    'lr': 0.0005,
    'mom': 0.9,
    'beta2': 0.999,
    'wd': 0.5e-4
}
schedules = {
    'lr': {'dec': 0.995}, # decay (multiply) lr by this factor every 1000 steps
}
batch_size = 1


def create_model():
    from elektronn2 import neuromancer as nm

    in_sh = (None,1,22,140,140)
    inp = nm.Input(in_sh, 'b,f,z,x,y', name='raw')  # high res

    # Convolution, downsampling of intermediate features
    conv0  = nm.Conv(inp,  32,  (1,3,3))
    conv1  = nm.Conv(conv0, 32,  (1,3,3))
    down0  = nm.Pool(conv1, (1,2,2), mode='max')  # mid res
    conv2  = nm.Conv(down0, 64,  (1,3,3))
    conv3  = nm.Conv(conv2, 64,  (1,3,3))
    down1  = nm.Pool(conv3, (1,2,2), mode='max')  # low res
    conv4  = nm.Conv(down1, 128,  (1,3,3))
    conv5  = nm.Conv(conv4, 128,  (1,3,3))
    down2  = nm.Pool(conv5, (1,2,2), mode='max')  # very low res
    conv6  = nm.Conv(down2, 256,  (3,3,3))
    conv7  = nm.Conv(conv6, 256,  (3,3,3))

    # Merging very low-res features with low-res features
    mrg0   = nm.UpConvMerge(conv5, conv7, 512)
    mconv0 = nm.Conv(mrg0, 256,  (1,3,3))
    mconv1 = nm.Conv(mconv0, 256,  (1,3,3))

    # Merging low-res with mid-res features
    mrg1   = nm.UpConvMerge(conv3, mconv1, 256)
    mconv2 = nm.Conv(mrg1, 128,  (3,3,3))
    mconv3 = nm.Conv(mconv2, 128,  (3,3,3))

    # Merging mid-res with high-res features
    mrg2   = nm.UpConvMerge(conv1, mconv3, 128)
    mconv4 = nm.Conv(mrg2, 64,  (3,3,3))
    mconv5 = nm.Conv(mconv4, 64,  (3,3,3))

    barr   = nm.Conv(mconv5, 2, (1,1,1), activation_func='lin', name='barr')
    probs  = nm.Softmax(barr)

    target = nm.Input_like(mconv5, override_f=1, name='target')

    loss_pix = nm.MultinoulliNLL(probs, target, target_is_sparse=True, name='nll_barr')

    loss = nm.AggregateLoss(loss_pix , name='loss')
    errors = nm.Errors(probs, target, target_is_sparse=True)

    model = nm.model_manager.getmodel()
    model.designate_nodes(
        input_node=inp,
        target_node=target,
        loss_node=loss,
        prediction_node=probs,
        prediction_ext=[loss, errors, probs]
    )
    return model


if __name__ == '__main__':
    print('Testing and visualising model...\n(If you want to train with this '
          'config file instead, run '
          '"$ elektronn2-train {}".)\n'.format(__file__))
    import traceback

    model = create_model()

    try:
        model.test_run_prediction()
    except Exception as e:
        traceback.print_exc()
        print('Test run failed.\nIn case your GPU ran out of memory, the '
              'principal setup might still be working')

    try:
        from elektronn2.utils.d3viz import visualise_model
        import getpass

        user_name = getpass.getuser()
        filename_noext = __file__.split('.')[-2]
        vispath = '/tmp/{}_{}_model-graph'.format(user_name, filename_noext)
        visualise_model(model, vispath)
        print('Visualisation files are saved at {}'.format(
            vispath + '.{png,html}'))
        # import webbrowser
        # webbrowser.open(vispath + '.png')
        # webbrowser.open(vispath + '.html')
    except Exception as e:
        traceback.print_exc()
        print('Could not visualise model graph.\n'
              'Are pydotplus and graphviz properly installed?')
