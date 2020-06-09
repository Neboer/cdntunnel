from cdn.PngEncoder import PngEncoder
from cdn.AliApi import AliApi
import requests
from PIL import UnidentifiedImageError
from time import sleep

encoder = PngEncoder()
api = AliApi()


class NetworkError(Exception): pass


class CodecError(Exception): pass


def get_and_decode(url):
    for upload_times in range(10):
        try:
            picture_content = requests.get(url).content
            data = encoder.decode_png(picture_content)
        except UnidentifiedImageError:  # 出现了罕见的图床错误，这个时候怎么办？
            with open('temp.png', "w") as tempfile:
                tempfile.write(data)
        except requests.exceptions:  # 网络错误
            sleep(upload_times * 0.1)
            continue
        except:  # 只要出现问题……
            return None
    return data


def encode_and_upload(data):
    prepared_picture_content = encoder.encode_png(data)
    for upload_times in range(10):
        try:
            upload_result = api.image_upload(prepared_picture_content)
        except requests.exceptions:
            sleep(upload_times * 0.1)
            continue
        except:
            return None
        if upload_result['code'] == 0:
            return upload_result['data']
        else:
            sleep(upload_times * 0.1)
            continue
        # return b"https://"  # 返回的是二进制编码的url。
    # 如果十次上传都没有成功，那么这个tcp连接将面临被关闭的命运
    return None
