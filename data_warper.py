from cdn.PngEncoder import PngEncoder
from cdn.AliApi import AliApi
import requests

encoder = PngEncoder()
api = AliApi()


class NetworkError(Exception): pass


class CodecError(Exception): pass


def get_and_decode(url):
    try:
        picture_content = requests.get(url).content
        data = encoder.decode_png(picture_content)
    except requests.exceptions:
        raise NetworkError
    except:
        raise CodecError
    return data


def encode_and_upload(data):
    prepared_picture_content = encoder.encode_png(data)
    try:
        upload_result = api.image_upload(prepared_picture_content)
    except requests.exceptions:
        raise NetworkError
    if upload_result['code'] == 0:
        return upload_result['data']
    else:
        raise NetworkError
        # return b"https://"  # 返回的是二进制编码的url。
