cd src

CUDA_VISIBLE_DEVICES='0' python3 track.py cmot \
--val_mft_edge True \
--data_dir /datadir \
--load_model ../exp/bst.pth \
--arch sbt/lbT

cd ..