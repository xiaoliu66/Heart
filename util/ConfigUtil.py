import json


def modify_config_file(str):
    str_json = json.loads(str)
    # 读取JSON文件
    with open("setting.json", "r") as file:
        data = json.load(file)

    # 修改JSON数据
    data["uuid"] = str_json["uuid"]

    # 将修改后的数据写回文件中
    with open("setting.json", "w") as file:
        json.dump(data, file, indent=2)

    print("JSON文件已成功修改。")


def default_config():
    # 读取JSON文件
    with open("setting.json", "r") as file:
        data = json.load(file)

    # 修改JSON数据
    data["uuid"] = data["default"]["uuid"]

    # 将修改后的数据写回文件中
    with open("setting.json", "w") as file:
        json.dump(data, file, indent=2)

    print("JSON文件已成功修改。")
