import os
import tempfile

e='asd'
with open(os.path.join('facial_recog_dataset','user',e), 'wb') as fd:
    print(fd)


# print(__file__)
# print(os.path.dirname(__file__))
# print(os.path.join(os.path.dirname(__file__), 'static', 'tmp'))
# static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# # os.makedirs(static_tmp_path)
# ext='jpg'
# with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
#     print(tf)