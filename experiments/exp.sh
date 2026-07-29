## Training Sample
python train.py cmot \
--exp_id YOUR-EXP-NAMES --data_cfg '../src/lib/cfg/mft_edge.json' \
--lr 5e-4 --batch_size 16 --wh_weight 0.5 \
--arch 'tides/tidel' --num_epochs 30 --reid_dim 64

## Testing Sample
python track.py cmot \
--val_MFT_Edge True \
--data_dir /DATASETS/MFT \
--load_model ../exp/cmot/YOUR-EXP-NAMES/model_best.pth \
--arch 'tides/tidel' \ 
--conf_thres 0.4