import cv2
import os
from pathlib import Path
import numpy as np

def rotate_and_scale_no_padding(image, angle, scale=2.0):
    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    rotated = cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w_box, h_box = cv2.boundingRect(contours[0])
        cropped = rotated[y:y + h_box, x:x + w_box]
    else:
        cropped = rotated
    if scale != 1.0:
        new_w = int(cropped.shape[1] * scale)
        new_h = int(cropped.shape[0] * scale)
        cropped = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    return cropped

def sliding_window_with_yolo_labels(image_path, label_path, output_dir, crop_size=640, overlap=0.2, angle=0, scale=1.0):
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 跳过无效图像: {image_path}")
        return 0
    if angle != 0 or scale != 1.0:
        image = rotate_and_scale_no_padding(image, angle, scale)

    h, w = image.shape[:2]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    abs_boxes = []
    with open(label_path, "r") as f:
        for line in f:
            cls, x, y, bw, bh = map(float, line.strip().split())
            cx = x * w
            cy = y * h
            bw *= w
            bh *= h
            abs_boxes.append((cls, cx, cy, bw, bh))

    stride = int(crop_size * (1 - overlap))
    base_name = Path(image_path).stem
    count = 0
    for y0 in range(0, h - crop_size + 1, stride):
        for x0 in range(0, w - crop_size + 1, stride):
            crop = image[y0:y0+crop_size, x0:x0+crop_size]
            crop_boxes = []
            for cls, cx, cy, bw, bh in abs_boxes:
                x1 = cx - bw / 2
                y1 = cy - bh / 2
                x2 = cx + bw / 2
                y2 = cy + bh / 2
                ix1 = max(x1, x0)
                iy1 = max(y1, y0)
                ix2 = min(x2, x0 + crop_size)
                iy2 = min(y2, y0 + crop_size)
                if ix2 > ix1 and iy2 > iy1:
                    new_cx = (ix1 + ix2) / 2 - x0
                    new_cy = (iy1 + iy2) / 2 - y0
                    new_bw = ix2 - ix1
                    new_bh = iy2 - iy1
                    crop_boxes.append(
                        f"{int(cls)} {new_cx / crop_size:.6f} {new_cy / crop_size:.6f} {new_bw / crop_size:.6f} {new_bh / crop_size:.6f}"
                    )
            if crop_boxes:
                crop_img_name = f"{base_name}_crop_{count:04d}.jpg"
                crop_txt_name = f"{base_name}_crop_{count:04d}.txt"
                cv2.imwrite(str(output_dir / crop_img_name), crop)
                with open(output_dir / crop_txt_name, "w") as f:
                    f.write("\n".join(crop_boxes))
                count += 1
    return count

def batch_cut_folder(image_dir, label_dir, output_dir, crop_size=640, overlap=0.2, angle=0, scale=1.0):
    image_dir = Path(image_dir)
    label_dir = Path(label_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for img_file in image_dir.glob("*.*"):
        if img_file.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
            continue
        label_file = label_dir / (img_file.stem + ".txt")
        if not label_file.exists():
            print(f"⚠️ 未找到对应标签: {label_file}")
            continue
        n = sliding_window_with_yolo_labels(img_file, label_file, output_dir, crop_size, overlap, angle, scale)
        print(f"✅ {img_file.name} -> 生成 {n} 个 patch")
        total += n
    print(f"\n🎉 总计生成 {total} 个切割图像及标签")
