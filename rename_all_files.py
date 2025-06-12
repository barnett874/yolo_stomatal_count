import json
import csv

# 读取 rename_list.csv 到字典
rename_dict = {}
with open("rename_list.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rename_dict[row["old_name"]] = row["rename"]

# 加载 labelstudio_tasks.json
with open("labelstudio_tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

# 替换 image 字段中的文件名
for task in tasks:
    image_path = task.get("data", {}).get("image", "")
    if image_path:
        old_name = image_path.split("/")[-1]  # 取文件名部分
        if old_name in rename_dict:
            new_name = rename_dict[old_name]
            new_path = image_path.rsplit("/", 1)[0] + "/" + new_name
            task["data"]["image"] = new_path

# 保存修改后的 JSON 文件
with open("labelstudio_tasks_renamed.json", "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

print("已完成重命名并保存为 labelstudio_tasks_renamed.json")
