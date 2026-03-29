import os
import glob
import _init_paths

def gen_data_path_mft_edge(root_path):
    mot_path = 'mft_edge/images/train'
    real_path = os.path.join(root_path, mot_path)
    seq_names = [s for s in sorted(os.listdir(real_path))]
    with open('/data3/data/TIDE/src/data/mft_edge.train', 'w') as f:
        for seq_name in seq_names:
            seq_path = os.path.join(real_path, seq_name)
            seq_path = os.path.join(seq_path, 'img1')
            images = sorted(glob.glob(seq_path + '/*.PNG'))
            len_all = len(images)
            for i in range(len_all):
                image = images[i]
                print(image[33:], file=f)
    f.close()

def gen_data_path_mft_edge_half(root_path):
    mot_path = 'mft_edge/images/train'
    real_path = os.path.join(root_path, mot_path)
    seq_names = [s for s in sorted(os.listdir(real_path))]
    with open('/data3/data/TIDE/src/data/mft_edge.half', 'w') as f:
        for seq_name in seq_names:
            seq_path = os.path.join(real_path, seq_name)
            seq_path = os.path.join(seq_path, 'img1')
            images = sorted(glob.glob(seq_path + '/*.PNG'))
            len_all = len(images)
            len_half = int(len_all / 2)
            for i in range(len_half):
                image = images[i]
                print(image[33:], file=f)
    f.close()

def gen_data_path_mft_edge_val(root_path):
    mot_path = 'mft_edge/images/train'
    real_path = os.path.join(root_path, mot_path)
    seq_names = [s for s in sorted(os.listdir(real_path))]
    with open('/data3/data/TIDE/src/data/mft_edge.val', 'w') as f:
        for seq_name in seq_names:
            seq_path = os.path.join(real_path, seq_name)
            seq_path = os.path.join(seq_path, 'img1')
            images = sorted(glob.glob(seq_path + '/*.PNG'))
            len_all = len(images)
            len_half = int(len_all / 2)
            for i in range(len_half, len_all):
                image = images[i]
                print(image[33:], file=f)
    f.close()

def gen_data_path_mft_edge_emb(root_path):
    mot_path = 'mft_edge/images/train'
    real_path = os.path.join(root_path, mot_path)
    seq_names = [s for s in sorted(os.listdir(real_path))]
    with open('/data3/data/TIDE/src/data/mft_edge.emb', 'w') as f:
        for seq_name in seq_names:
            seq_path = os.path.join(real_path, seq_name)
            seq_path = os.path.join(seq_path, 'img1')
            images = sorted(glob.glob(seq_path + '/*.PNG'))
            len_all = len(images)
            len_half = int(len_all / 2)
            for i in range(len_half, len_all, 3):
                image = images[i]
                print(image[33:], file=f)
    f.close()


if __name__ == '__main__':
    root = '/data3/data/DATASETS'
    gen_data_path_mft_edge(root)     
    gen_data_path_mft_edge_half(root)
    gen_data_path_mft_edge_val(root)  
    gen_data_path_mft_edge_emb(root)  