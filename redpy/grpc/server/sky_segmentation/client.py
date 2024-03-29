import cv2
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED

from redpy.grpc import CommonClient

def infer():
    image = cv2.imread('/share/wangqixun/workspace/github_project/redpy/test/data/WX20230420-175738@2x.png')
    client = CommonClient(
        ip='10.4.200.42',
        port='30125',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )
    res = client.run([image])
    # cv2.imwrite('/share/wangqixun/workspace/tmp/0000.jpg', res)
    return res


if __name__ == '__main__':
    # img = cv2.imread('/share/wangqixun/workspace/github_project/redpy/test/data/beauty.jpg')

    t1 = time.time()
    with ThreadPoolExecutor(max_workers=10) as t:
        all_task = [t.submit(infer, ) for i in range(10)]
        wait(all_task, return_when=ALL_COMPLETED)
    t2 = time.time()

    total = 10
    cost = t2 - t1
    print("cost: {}, total: {}, qps: {}".format(cost, total, (total/cost)))





