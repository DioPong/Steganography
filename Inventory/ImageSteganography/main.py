from PIL import Image
import argparse
from os import path


class PicEvent:
    @staticmethod
    def make_image_event(image):
        """
        取得一个 PIL 图像并且更改所有值为偶数（使最低有效位为0）
        """
        # 得到一个这样的列表：[(r,g,b,t),(r,g,b,t)...]
        pixels = list(image.getdata())
        # 更改所有值为偶数（魔法般的移位）
        even_pixels = [(r >> 1 << 1, g >> 1 << 1, b >> 1 << 1, t >> 1 << 1) for [r, g, b, t] in pixels]
        # 创建一个相同大小的图片副本
        even_image = Image.new(image.mode, image.size)
        # 把上面的像素放入到图片副本
        even_image.putdata(even_pixels)
        return even_image

    @staticmethod
    def const_len_bin(_int):
        """
        内置函数bin()的替代，返回固定长度的二进制字符串
        """
        # 去掉bin()返回的二进制字符串中的'0b'，并在左边补足'0'直到字符串长度为8
        binary = "0" * (8 - (len(bin(_int)) - 2)) + bin(_int).replace('0b', '')
        return binary

    @classmethod
    def encode_data_in_image(cls, image, _data):
        """
        将字符串编码到图片中
        """
        # 获得最低有效位为 0 的图片副本
        even_image = cls.make_image_event(image)
        # 将需要被隐藏的字符串转换成二进制字符串
        binary = ''.join(map(cls.const_len_bin, bytearray(_data, 'utf-8')))
        if len(binary) > len(image.getdata()) * 4:
            # 如果不可能编码全部数据，跑出异常
            raise Exception(f"Error: Can't encode more than {len(even_image.getdata()) * 4} bits in this image.")
        # 将binary中的二进制字符串信息编码进像素里
        encoded_pixels = [(r + int(binary[index * 4 + 0]), g + int(binary[index * 4 + 1]),
                           b + int(binary[index * 4 + 2]), t + int(binary[index * 4 + 3])) if index * 4 < len(
            binary) else (r, g, b, t) for index, (r, g, b, t) in enumerate(list(even_image.getdata()))]
        # 创建新图片以存放编码后的像素
        encoded_image = Image.new(even_image.mode, even_image.size)
        # 添加编码后的数据
        encoded_image.putdata(encoded_pixels)
        return encoded_image

    @staticmethod
    def binary_to_string(binary):
        """
        从二进制字符串转为 UTF-8 字符串
        """
        index = 0
        string = []
        rec = lambda x, i: x[2:8] + (rec(x[8:], i - 1) if i > 1 else '') if x else ''
        fun = lambda x, i: x[i + 1:8] + rec(x[8:], i - 1)
        while index + 1 < len(binary):
            chartype = binary[index:].index('0')  # 存放字符所占字节数，一个字节的字符会存为0
            length = chartype * 8 if chartype else 8
            string.append(chr(int(fun(binary[index:index + length], chartype), 2)))
            index += length
        return ''.join(string)

    @classmethod
    def decode_image(cls, image):
        """
        解码隐藏数据
        """
        pixels = list(image.getdata())  # 获得像素列表
        # 提取图片中所有最低有效位中的数据
        binary = ''.join([str(int(r >> 1 << 1 != r)) + str(int(g >> 1 << 1 != g)) + str(int(b >> 1 << 1 != b)) + str(
            int(t >> 1 << 1 != t)) for (r, g, b, t) in pixels])
        # 找到数据截止处的索引
        location_double_null = binary.find('0000000000000000')
        end_index = location_double_null + (
                8 - (location_double_null % 8)) if location_double_null % 8 != 0 else location_double_null
        _data = cls.binary_to_string(binary[0:end_index])
        return _data


# PicEvent.encode_data_in_image(image=Image.open("pic.png"), data="123").save('encodeImage.png')
# print(PicEvent.decode_image(image=Image.open("encodeImage.png")))

wc = """
------------------------- Steganography -------------------------
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=wc)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-e",
                       help="Merge image and image (PNG support only)",
                       nargs=2)
    group.add_argument("-d",
                       help="Extract info from image")

    arg = parser.parse_args()

    encode = arg.e
    decode = arg.d

    # Mode switcher
    if decode:
        if not path.exists(decode):
            raise FileNotFoundError
        print(PicEvent.decode_image(image=Image.open(decode)))
    elif encode:
        file_path, data = encode[0], encode[1]
        if not path.exists(file_path):
            raise FileNotFoundError
        # specify whether is png or not
        if (file_type := path.splitext(file_path)[1]) != ".png":
            raise Exception(f"File \"{file_type}\" not support")
        (filepath, filename) = path.split(file_path)
        new_full_path = filepath + filename.replace(".png", "-Steganography.png")
        PicEvent.encode_data_in_image(image=Image.open(arg.e[0]), _data=data).save(new_full_path)

        print(f">>> {new_full_path} had been created")
