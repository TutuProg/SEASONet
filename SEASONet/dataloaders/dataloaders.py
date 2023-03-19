import torch.utils.data as data
import torch
from Data.LabelTargetProcessor import LabelTarget
import os
import numpy as np
from os.path import join
from Data.ImageProcessor import Images, Labels

def make_dataset(filepath, split=[0.7, 0.1, 0.2], test_only=False, buffer_assist=False):
    '''
    :param filepath: the root dir of img, lab and ssn
    :param split: the data will be distributed according to this param for training, validating and testing
    :param test_only: if now in test mode
    :return: img, lab
    '''
    if not os.path.exists(filepath):
        raise ValueError('The path of the dataset does not exist.')
    else:
        img = [join(filepath, 'image', 'optical', name) for name in os.listdir(join(filepath, 'image', 'optical'))]
        ssn = [join(filepath, 'image', 'season', 'all', name) for name in
               os.listdir(join(filepath, 'image', 'season', 'all'))]

        lab = [join(filepath, 'label', name) for name in os.listdir(join(filepath, 'label'))]
        if buffer_assist:
            pre = [join(filepath, 'pred', name) for name in os.listdir(join(filepath, 'pred'))]

        vvh = [join(filepath, 'image', 'VVVH', name) for name in os.listdir(join(filepath, 'image', 'VVVH'))]

        spr = [join(filepath, 'image', 'season', 'spring', name) for name in
               os.listdir(join(filepath, 'image', 'season', 'spring'))]
        smr = [join(filepath, 'image', 'season', 'summer', name) for name in
               os.listdir(join(filepath, 'image', 'season', 'summer'))]
        fal = [join(filepath, 'image', 'season', 'fall', name) for name in
               os.listdir(join(filepath, 'image', 'season', 'fall'))]
        wnt = [join(filepath, 'image', 'season', 'winter', name) for name in
               os.listdir(join(filepath, 'image', 'season', 'winter'))]


    assert len(img) == len(lab)
    if not test_only:
        assert len(img) == len(vvh)
        assert len(img) == len(ssn)
    if buffer_assist:
        assert len(pre) == len(img)
        pre.sort()
        pre = np.array(pre)
    assert len(img) == len(spr)
    assert len(img) == len(smr)
    assert len(img) == len(fal)
    assert len(img) == len(wnt)

    img.sort()
    ssn.sort()
    lab.sort()
    vvh.sort()

    spr.sort()
    smr.sort()
    fal.sort()
    wnt.sort()

    num_samples = len(img)
    img = np.array(img)
    ssn = np.array(ssn)
    lab = np.array(lab)
    vvh = np.array(vvh)

    spr = np.array(spr)
    smr = np.array(smr)
    fal = np.array(fal)
    wnt = np.array(wnt)
    if test_only:
        vvh = img
        ssn = img
    # generate sequence
    # load the path
    seqpath = join(filepath, 'seq.txt')
    if os.path.exists(seqpath):
        seq = np.loadtxt(seqpath, delimiter=',')
    else:
        seq = np.random.permutation(num_samples)
        np.savetxt(seqpath, seq, fmt='%d', delimiter=',')
    seq = np.array(seq, dtype='int32')

    num_train = int(num_samples * split[0])  # the same as floor
    num_val = int(num_samples * split[1])

    train = seq[0:num_train]
    val = seq[num_train:(num_train + num_val)]
    test = seq[num_train + num_val:]

    imgt = np.vstack((img[train], ssn[train], vvh[train],
                      spr[train], smr[train], fal[train], wnt[train])).T
    labt = lab[train]

    imgv = np.vstack((img[val], ssn[val], vvh[val],
                      spr[val], smr[val], fal[val], wnt[val])).T
    labv = lab[val]

    imgte = np.vstack((img[test], ssn[test], vvh[test],
                       spr[test], smr[test], fal[test], wnt[test])).T
    labte = lab[test]

    if buffer_assist:
        pret = pre[train]
        prev = pre[val]
        prete = pre[test]
        return imgt, labt, imgv, labv, imgte, labte, pret, prev, prete

    return imgt, labt, imgv, labv, imgte, labte


class MaskRcnnDataloader(data.Dataset):
    def __init__(self, imgpath, labpath, prepath=None,
                 augmentations=False, area_thd=4,
                 label_is_nos=True, footprint_mode=False, seasons_mode: str = None, sar_data=False, RGB_mode=False,
                 if_buffer=False, buffer_storeylevel=0, buffer_assist=False):  # data loader #params nrange
        assert seasons_mode in ['compress', 'intact', 'Spring', 'Summer', 'Autumn', 'Winter', 'seasons', None, 'None'], 'season mode must in [compress, intact], names of seasons or None'
        super(MaskRcnnDataloader, self).__init__()
        self.imgpath = imgpath
        self.labpath = labpath
        if buffer_assist:
            assert prepath is not None
            self.prepath = prepath
        self.augmentations = augmentations
        self.area_thd = area_thd
        self.label_is_nos = label_is_nos
        self.footprint_mode = footprint_mode
        self.seasons_mode = seasons_mode
        self.sar_data = sar_data
        self.RGB_mode = RGB_mode
        self.if_buffer = if_buffer
        self.buffer_storeylevel = buffer_storeylevel
        self.buffer_assist = buffer_assist

    def __getitem__(self, index):
        muxpath_ = self.imgpath[index, 0]
        mux_img = Images(img_path=muxpath_)
        mux_img.normalize(method='mean_std')
        img = Images(img_data=mux_img.img_data)

        lab_img = Labels(lab_path=self.labpath[index])
        lab = lab_img.img_data
        if self.seasons_mode == 'intact' or self.seasons_mode == 'seasons':
            spr_img = Images(img_path=self.imgpath[index, 3])
            spr_img.normalize(method='mean_std')
            smr_img = Images(img_path=self.imgpath[index, 4])
            smr_img.normalize(method='mean_std')
            fal_img = Images(img_path=self.imgpath[index, 5])
            fal_img.normalize(method='mean_std')
            wnt_img = Images(img_path=self.imgpath[index, 6])
            wnt_img.normalize(method='mean_std')
            cat_data_list = [smr_img.img_data, fal_img.img_data, wnt_img.img_data]
            spr_img.cat_images(cat_datas=cat_data_list)
            ssn = spr_img.img_data
            if self.seasons_mode == 'intact':
                img.cat_image(ssn)
            elif self.seasons_mode == 'seasons':
                img.img_data = ssn


        if self.seasons_mode == 'compress':
            ssn_img = Images(img_path=self.imgpath[index, 1])
            ssn_img.normalize(method='mean_std')
            ssn = ssn_img.img_data
            img.cat_image(ssn)

        if self.seasons_mode == 'Spring':
            spr_img = Images(img_path=self.imgpath[index, 3])
            spr_img.normalize(method='mean_std')
            img.img_data = spr_img.img_data
        if self.seasons_mode == 'Summer':
            smr_img = Images(img_path=self.imgpath[index, 4])
            smr_img.normalize(method='mean_std')
            img.img_data = smr_img.img_data
        if self.seasons_mode == 'Autumn':
            fal_img = Images(img_path=self.imgpath[index, 5])
            fal_img.normalize(method='mean_std')
            img.img_data = fal_img.img_data
        if self.seasons_mode == 'Winter':
            wnt_img = Images(img_path=self.imgpath[index, 6])
            wnt_img.normalize(method='mean_std')
            img.img_data = wnt_img.img_data

        if self.footprint_mode:
            footprint = lab_img.get_footprint(background=0)
            img.cat_image(footprint, cat_pos='before')

        if self.sar_data:
            vvh_img = Images(img_path=self.imgpath[index, 2])
            vvh_img.normalize(method='mean_std')
            img.cat_image(vvh_img.img_data)

        if self.RGB_mode:
            img.img_data = mux_img.img_data[:, :, 0:3]

        label_class = LabelTarget(label_data=lab)

        if self.buffer_assist:
            pre_img = Labels(lab_path=self.prepath[index])
            pre = pre_img.img_data
            label_class = LabelTarget(label_data=lab, pre_data=pre)

        # if self.augmentations:
        #     img, lab = my_segmentation_transforms(img, lab)  # transform are set inside MaskRCNN

        target = label_class.to_target(image_id=lab_img.image_id,
                                       file_name=lab_img.file_name,
                                       if_buffer_proposal=self.if_buffer,
                                       area_thd=self.area_thd,
                                       mask_mode='value',
                                       background=0,
                                       label_is_value=self.label_is_nos,
                                       buffer_storeylevel = self.buffer_storeylevel,
                                       buffer_assist = self.buffer_assist
                                       )
        img = img.img_data
        assert (np.isnan(img)).any() is not True, 'NaN in Data!'
        img = img.transpose((2, 0, 1))  # H W C => C H W
        img = torch.tensor(img.copy(), dtype=torch.float)
        return img, target

    def __len__(self):
        return len(self.imgpath)

    def collate_fn(self, batch):
        img_list, target_list = [], []
        for img, target in batch:
            img_list.append(img)
            target_list.append(target)
        return img_list, target_list
