import argparse
import os
import shutil
import warnings

import torch
import torch.nn.functional as F
from tensorboardX import SummaryWriter
from torch.utils.data import DataLoader
from torchmetrics import AUROC, AveragePrecision

from constant import RESIZE_SHAPE, NORMALIZE_MEAN, NORMALIZE_STD, ALL_CATEGORY
from data.mvtec_dataset import MVTecDataset
from model.destseg import DeSTSeg
from model.metrics import AUPRO, IAPS

warnings.filterwarnings("ignore")


def evaluate(args, category, model, visualizer, global_step=0):
    model.eval()

    with torch.no_grad():
        dataset = MVTecDataset(
            is_train=False,
            mvtec_dir=args.mvtec_path + category + "/test/",
            resize_shape=RESIZE_SHAPE,
            normalize_mean=NORMALIZE_MEAN,
            normalize_std=NORMALIZE_STD,
        )
        dataloader = DataLoader(
            dataset, batch_size=args.bs, shuffle=False, num_workers=args.num_workers
        )
        de_st_IAPS = IAPS().cuda()
        de_st_AUPRO = AUPRO().cuda()
        de_st_AUROC = AUROC().cuda()
        de_st_AP = AveragePrecision().cuda()
        de_st_detect_AUROC = AUROC().cuda()
        seg_IAPS = IAPS().cuda()
        seg_AUPRO = AUPRO().cuda()
        seg_AUROC = AUROC().cuda()
        seg_AP = AveragePrecision().cuda()
        seg_detect_AUROC = AUROC().cuda()

        output_segmentation_samples = []
        for _, sample_batched in enumerate(dataloader):
            img = sample_batched["img"].cuda()
            mask = sample_batched["mask"].to(torch.int64).cuda()

            output_segmentation, output_de_st, output_de_st_list = model(img)

            output_segmentation = F.interpolate(
                output_segmentation,
                size=mask.size()[2:],
                mode="bilinear",
                align_corners=False,
            )
            output_de_st = F.interpolate(
                output_de_st, size=mask.size()[2:], mode="bilinear", align_corners=False
            )

            mask_sample = torch.max(mask.view(mask.size(0), -1), dim=1)[0]
            output_segmentation_sample, _ = torch.sort(
                output_segmentation.view(output_segmentation.size(0), -1),
                dim=1,
                descending=True,
            )
            output_segmentation_sample = torch.mean(
                output_segmentation_sample[:, : args.T], dim=1
            )
            output_de_st_sample, _ = torch.sort(
                output_de_st.view(output_de_st.size(0), -1), dim=1, descending=True
            )
            output_de_st_sample = torch.mean(output_de_st_sample[:, : args.T], dim=1)

            de_st_IAPS.update(output_de_st, mask)
            de_st_AUPRO.update(output_de_st, mask)
            de_st_AP.update(output_de_st.flatten(), mask.flatten())
            de_st_AUROC.update(output_de_st.flatten(), mask.flatten())
            de_st_detect_AUROC.update(output_de_st_sample, mask_sample)


            file_names = [path.split("MVTec-AD_test/")[-1] for path in dataset.imageDir]
            output_segmentation_samples.append(output_segmentation_sample)
            scores=torch.cat(output_segmentation_samples)

            # seg_IAPS.update(output_segmentation, mask)
            # seg_AUPRO.update(output_segmentation, mask)
            # seg_AP.update(output_segmentation.flatten(), mask.flatten())
            # seg_AUROC.update(output_segmentation.flatten(), mask.flatten())
            #seg_detect_AUROC.update(output_segmentation_sample, mask_sample)

        with open("anomaly_scores_with_names1.txt", 'a') as f:
            # f.write("Image Name, Anomaly Score\n")  # 写入标题
            # 使用字符串分割
            # parts = dir.split("/")
            # category = parts[-4]  # 获取倒数第三个元素
            # f.write(f"{category}\n")
            for name, score in zip(file_names, scores):
                f.write(f"{name}, {score:.10f}\n")  # 所以分数以普通小数格式写入


#        iap_de_st, iap90_de_st = de_st_IAPS.compute()
#         aupro_de_st, ap_de_st, auc_de_st, auc_detect_de_st = (
#             de_st_AUPRO.compute(),
#             de_st_AP.compute(),
#             de_st_AUROC.compute(),
#             de_st_detect_AUROC.compute(),
#         )

        print("-------------------------------------")

# #        iap_seg, iap90_seg = seg_IAPS.compute()
#         aupro_seg, ap_seg, auc_seg, auc_detect_seg = (
#             seg_AUPRO.compute(),
#             seg_AP.compute(),
#             seg_AUROC.compute(),
#             seg_detect_AUROC.compute(),
#         )

        # visualizer.add_scalar("DeST_IAP", iap_de_st, global_step)
        # visualizer.add_scalar("DeST_IAP90", iap90_de_st, global_step)
        # visualizer.add_scalar("DeST_AUPRO", aupro_de_st, global_step)
        # visualizer.add_scalar("DeST_AP", ap_de_st, global_step)
        # visualizer.add_scalar("DeST_AUC", auc_de_st, global_step)
        # visualizer.add_scalar("DeST_detect_AUC", auc_detect_de_st, global_step)

        # visualizer.add_scalar("DeSTSeg_IAP", iap_seg, global_step)
        # visualizer.add_scalar("DeSTSeg_IAP90", iap90_seg, global_step)
        # visualizer.add_scalar("DeSTSeg_AUPRO", aupro_seg, global_step)
        # visualizer.add_scalar("DeSTSeg_AP", ap_seg, global_step)
        # visualizer.add_scalar("DeSTSeg_AUC", auc_seg, global_step)
        # visualizer.add_scalar("DeSTSeg_detect_AUC", auc_detect_seg, global_step)

        print("Eval at step", global_step)
        print("================================")
        # print("Denoising Student-Teacher (DeST)")
        # print("pixel_AUC:", round(float(auc_de_st), 4))
        # print("pixel_AP:", round(float(ap_de_st), 4))
        # print("PRO:", round(float(aupro_de_st), 4))
        # print("image_AUC:", round(float(auc_detect_de_st), 4))
        # print("IAP:", round(float(iap_de_st), 4))
        # print("IAP90:", round(float(iap90_de_st), 4))
        # print()
        # print("Segmentation Guided Denoising Student-Teacher (DeSTSeg)")
        # print("pixel_AUC:", round(float(auc_seg), 4))
        # print("pixel_AP:", round(float(ap_seg), 4))
        # print("PRO:", round(float(aupro_seg), 4))
        # print("image_AUC:", round(float(auc_detect_seg), 4))
        # print("IAP:", round(float(iap_seg), 4))
        # print("IAP90:", round(float(iap90_seg), 4))
        # print()

        de_st_IAPS.reset()
        de_st_AUPRO.reset()
        de_st_AUROC.reset()
        de_st_AP.reset()
        de_st_detect_AUROC.reset()
        seg_IAPS.reset()
        seg_AUPRO.reset()
        seg_AUROC.reset()
        seg_AP.reset()
        seg_detect_AUROC.reset()


def test(args, category):
    if not os.path.exists(args.log_path):
        os.makedirs(args.log_path)

    run_name = f"DeSTSeg_MVTec_test_{category}"
    if os.path.exists(os.path.join(args.log_path, run_name + "/")):
        shutil.rmtree(os.path.join(args.log_path, run_name + "/"))

    visualizer = SummaryWriter(log_dir=os.path.join(args.log_path, run_name + "/"))

    model = DeSTSeg(dest=True, ed=True).cuda()
    assert os.path.exists(
        os.path.join(args.checkpoint_path, args.base_model_name + category + ".pckl")
    )
    model.load_state_dict(
        torch.load(
            os.path.join(
                args.checkpoint_path, args.base_model_name + category + ".pckl"
            )
        )
    )

    evaluate(args, category, model, visualizer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--gpu_id", type=int, default=0)
    parser.add_argument("--num_workers", type=int, default=16)

    parser.add_argument("--mvtec_path", type=str, default="/media/xujiajin/HardDisk/MVTec-AD/")
    parser.add_argument("--dtd_path", type=str, default="./datasets/dtd/images/")
    parser.add_argument("--checkpoint_path", type=str, default="./saved_model/")
    parser.add_argument("--base_model_name", type=str, default="DeSTSeg_MVTec_5000_")
    parser.add_argument("--log_path", type=str, default="./logs/")

    parser.add_argument("--bs", type=int, default=32)
    parser.add_argument("--T", type=int, default=100)  # for image-level inference

    parser.add_argument("--category", nargs="*", type=str, default=ALL_CATEGORY)
    args = parser.parse_args()

    obj_list = args.category
    for obj in obj_list:
        assert obj in ALL_CATEGORY

    with torch.cuda.device(args.gpu_id):

        # obj="bottle"
        # print(obj)
        # test(args, obj)

       for obj in obj_list:
            print(obj)
            test(args, obj)
