#!/usr/bin/env python
# encoding: utf-8
# Author: guoxudong
import datetime
import json
import traceback

import demjson
from aliyunsdkr_kvstore.request.v20150101.DescribeInstancesRequest import DescribeInstancesRequest

from cli.aliyun_base import AliyunBase, readj2


class AliyunRedis(AliyunBase):

    def __init__(self, clent):
        super(AliyunRedis, self).__init__()
        self.clent = clent
        self.request = DescribeInstancesRequest()
        self.product = 'redis'

    def load_all(self, ):
        try:
            self.set_params()
            response = json.loads(self.clent.do_action_with_exception(self.request))
            RedisList = response.get('Instances').get('KVStoreInstance')
            redis_list = []
            for item in RedisList:
                redis_list.append({"id": item['InstanceId'], "name": item['InstanceName']})
            return redis_list
        except Exception as e:
            print('请求阿里云失败，%s', str(e))
            print('%s %s %s' % (datetime.datetime.now(), str(e), traceback.format_exc()))

    def GenerateRedisDashboard(self, redis_list, line_template, panels_template, metric_list):
        dashboard_lines = []
        for index, metric in enumerate(metric_list):
            panels_lines = []
            for i, redis in enumerate(redis_list):
                template = readj2(line_template)
                panels_lines.append(
                    self.line_template(template=template, line_name=redis['name'], line_id=redis['id'], ycol="Average",
                                       metric=metric['field'], project="acs_kvstore"))
            template = readj2(panels_template)
            dashboard_lines.append(
                self.panels_template(index=index, template=template, title=metric['name'], format=metric['format'],
                                     redline=metric['redline'], targets=demjson.encode(panels_lines)))
        dashboard_template = readj2("dashboard.json.j2")
        resultjson = dashboard_template.render(panels_card=demjson.encode(dashboard_lines), title="redis资源监控",
                                               tag="Redis")
        # print(resultjson)
        return {'cms-{0}.json'.format(self.product): resultjson}

    def action(self, ):
        print('Generating Redis config')
        # metric_list = [
        #     {"field": "StandardCpuUsage", "name": "CPU 使用率", "format": "percent", "redline": "80"},
        #     {"field": "StandardMemoryUsage", "name": "内存使用率", "format": "percent", "redline": "80"},
        #     {"field": "StandardQPSUsage", "name": "QPS使用率", "format": "percent", "redline": "80"},
        #     {"field": "StandardConnectionUsage", "name": "连接数使用率", "format": "percent", "redline": "80"},
        #     {"field": "StandardUsedConnection", "name": "已用连接数", "format": "short", "redline": "1000"},
        #     {"field": "StandardUsedQPS", "name": "平均每秒访问次数", "format": "short", "redline": "1000"},
        #     {"field": "StandardAvgRt", "name": "平均响应时间", "format": "µs", "redline": "1000"},
        #     {"field": "StandardMaxRt", "name": "最大响应时间", "format": "µs", "redline": "5000"},
        #     {"field": "StandardIntranetIn", "name": "流入带宽", "format": "bps", "redline": "1000"},
        #     {"field": "StandardIntranetInRatio", "name": "流入带宽使用率", "format": "percent", "redline": "80"},
        #     {"field": "StandardIntranetOut", "name": "流出带宽", "format": "bps", "redline": "80"},
        #     {"field": "StandardKeys", "name": "缓存内 Key 数量", "format": "short", "redline": "80000"},
        # ]
        metric_list = self.read_metric_config_map('redis')
        redis_list = self.load_all()
        print("build success!")
        return self.GenerateRedisDashboard(redis_list, "line.json.j2", "linePanels.json.j2", metric_list)