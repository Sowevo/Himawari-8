import os
import requests
import threading
import json
import sys
import platform
import shutil
from sys import argv
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta


# 倍数
scale = 4

base = "http://himawari8-dl.nict.go.jp/himawari8/img/D531106/%sd/550" % (scale)
cdn = 'http://res.cloudinary.com/dpltrw8c1/image/fetch/'

wallpaper_path = "F://earth/"
wallpaper_path_temp = wallpaper_path + "temp/"

# 宽高应该是固定的
width = 550
height = 550

# 拼接后的图像
png = Image.new('RGB', (width * scale, height * scale))

# 请求的session
sess = requests.Session()


# 从接口获取最后的版本信息
def get_latest():
    url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
    response = requests.request("GET", url)
    data = json.loads(response.text)
    time = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
    return time


# 生成路径
def get_path(time, x, y):
    return "%s/%s/%02d/%02d/%02d%02d00_%s_%s.png" \
           % (cdn + base, time.year, time.month, time.day, time.hour, (time.minute // 10) * 10, x, y)


# 下载图片,各种异常处理
def get_img_data(path):
    try:
        r = sess.get(path)
        if r.status_code != 200:
            # 缓存找不到这个文件,尝试直接从主站获取
            print('缓存无此文件!!!')
            path = path.replace(cdn, '')
            img_data = get_img_data(path)
            print(path)
        else:
            img_data = r.content
        # 文件内容为空,尝试重新获取
        if img_data == "":
            print('获取图像失败,尝试重新获取')
            img_data = get_img_data(path)
    # 连接失败,尝试重新获取数据
    except BaseException as e:
        print(e)
        img_data = get_img_data(path)
    return img_data


def get_imgs(time, x, y,):
    img_path = get_path(time, x, y)
    img_data = get_img_data(img_path)
    temp_png = Image.open(BytesIO(img_data))
    temp_png.save("%s%s%02d%02d-%02d%02d00_%s_%s.png" % (
        wallpaper_path_temp, time.year, time.month, time.day, time.hour, (time.minute // 10) * 10, y, x), 'PNG')
    png.paste(temp_png, (width * x, height * y, width * (x + 1), height * (y + 1)))
    print(img_path)


def set_wallpaper(bmp_path):
    if platform.system() == 'Windows':
        import win32api, win32con, win32gui, winsound

        # 打开指定注册表路径
        reg_key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, win32con.KEY_SET_VALUE)
        # 最后的参数:2拉伸,0居中,6适应,10填充,0平铺
        win32api.RegSetValueEx(reg_key, "WallpaperStyle", 0, win32con.REG_SZ, "6")
        # 最后的参数:1表示平铺,拉伸居中等都是0
        win32api.RegSetValueEx(reg_key, "TileWallpaper", 0, win32con.REG_SZ, "0")
        # 刷新桌面
        win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, bmp_path, 1+2)
        winsound.PlaySound("*", winsound.SND_ALIAS)


def main():
    if os.path.exists(wallpaper_path):
        shutil.rmtree(wallpaper_path)
    os.makedirs(wallpaper_path_temp)

    # 增加指定时间的参数
    if len(argv) > 1:
        try:
            time = datetime.strptime(argv[1] + " " + argv[2], '%Y-%m-%d %H:%M:%S')
        except BaseException:
            print('参数错误!!!!')
            sys.exit()
    else:
        # 从当前时间推算最后的图片不精确,尝试从api获取最后的版本,cloudinary的cdn还有延迟
        time = get_latest() - timedelta(minutes=0)
    print(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S") + ' 获取====>>' +
          datetime.strftime(time, "%Y-%m-%d %H:%M:%S") + ' ========>>Start!')
    img_path_list = []
    threads = []
    for x in range(scale):
        for y in range(scale):
            img_path_list.append([get_path(time, x, y), x, y])
            tt = threading.Thread(target=get_imgs, args=(time, x, y,))
            tt.setDaemon(True)
            tt.start()
            tt.join()
            threads.append(tt)

    file = "%s%s%02d%02d-%02d%02d00.png" % (
        wallpaper_path, time.year, time.month, time.day, time.hour, (time.minute // 10) * 10)
    png.save(file, 'png')
    set_wallpaper(file)
    print(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S") + ' 获取====>>' +
          datetime.strftime(time, "%Y-%m-%d %H:%M:%S") + ' ========>>Done!!')


if __name__ == '__main__':
    main()
