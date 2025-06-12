import os
import json
import xml.etree.ElementTree as ET

def convert_voc_to_labelstudio(xml_path, img_base_url):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    filename = root.find("filename").text
    img_url = os.path.join(img_base_url, filename)

    width = int(root.find("size/width").text)
    height = int(root.find("size/height").text)

    results = []

    for obj in root.findall("object"):
        label = obj.find("name").text
        bndbox = obj.find("bndbox")
        xmin = int(bndbox.find("xmin").text)
        ymin = int(bndbox.find("ymin").text)
        xmax = int(bndbox.find("xmax").text)
        ymax = int(bndbox.find("ymax").text)

        x = xmin / width * 100
        y = ymin / height * 100
        w = (xmax - xmin) / width * 100
        h = (ymax - ymin) / height * 100

        results.append({
            "from_name": "label",
            "to_name": "image",
            "type": "rectanglelabels",
            "value": {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "rectanglelabels": [label]
            }
        })

    return {
        "data": {"image": img_url},
        "annotations": [{"result": results}]
    }

# 批量转换
input_dir = "C:/Users/MECHREUO/stomatal traits/Tipscope_maize_stomata_dataset/Annotations"
img_base_url = "C:/Users/MECHREUO/stomatal traits/Tipscope_maize_stomata_dataset/JPEGImages"
output = []

for filename in os.listdir(input_dir):
    if filename.endswith(".xml"):
        xml_file = os.path.join(input_dir, filename)
        item = convert_voc_to_labelstudio(xml_file, img_base_url)
        output.append(item)

# 保存为 label-studio 可导入的 JSON
with open("labelstudio_tasks.json", "w") as f:
    json.dump(output, f, indent=2)
