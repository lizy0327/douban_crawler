#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
# @Time    : 2021/10/6 14:42
# @Author  : lizy
# @Email   : lizy0327@gmail.com
# @File    : dou_friend.py
# @Software: PyCharm


import requests
import time
import json
import random
import jieba
from collections import Counter
from pyecharts.charts import Geo, Bar
from pyecharts.globals import ChartType
from pyecharts import options as opts
# 有2种wordcloud的方法
from pyecharts.charts import WordCloud as wcps
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import cpca
import re
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from io import BytesIO
import urllib
import os
import codecs


class DouBanBiaoBai(object):
    # topic url，start使用{}变量，后面使用format进行拼接
    url_basic = "https://m.douban.com/rexxar/api/v2/gallery/topic/18306/items?from_web=1&sort=hot&start={}&" \
                "count=20&status_full_text=1&guest_only=0&ck=d8p4"
    # 用来存放爬取的文字数据
    content = []

    # 创建保存图片的目录
    if not os.path.exists('./images'):
        os.mkdir('./images')

    # 自定义屏蔽关键字列表
    remove_words = [u'的', u'，', u'和', u'是', u'着', u'对于', u'对', u'等', u'能', u'都', u'。', u' ', u'、', u'中',
                    u'在', u'了', u'常', u'果', u'们', u'要', u'把', u'但', u'？', u'!', u'...', u'有', u'做', u'大',
                    u'个', u'些', u'：', u'我', u'不', u'你', u'也', u'人', u'就', u'年', u'来', u'多', u'…', u'；', u'后',
                    u'！', u'会', u'去', u'很', u'好', u'看', u'想', u'（', u'）', u'（', u'还', u'+', u'他', u'']

    # 打开控制面板 F12,找到带items的连接，然后复制整个RequestHeaders到代码中，采用复制cookie的方式登录豆瓣
    my_header1 = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'bid=_lw5J3_BiSI; ll="108288"; __utmv=30149280.10132; douban-fav-remind=1; push_noty_num=0; '
                  'push_doumail_num=0; __utmc=30149280; dbcl2="101321320:jJWkA359zsE"; ck=d8p4; '
                  'frodotk="2137f09797c96fae63a7d1c6c75c4f0a"; ap_v=0,6.0; __utmt=1; '
                  'ct=y; __utma=30149280.1918870861.1622312405.1633501996.1633502142.21; '
                  '__utmz=30149280.1633502142.21.13.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; '
                  '__utmb=30149280.2.10.1633502142',
        'Host': 'm.douban.com',
        'Origin': 'https://www.douban.com',
        'Referer': 'https://www.douban.com/gallery/topic/18306/',
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/94.0.4606.61 Safari/537.36'
    }

    # 在下载图片时必须替换默认header，否则会触发了网站的反扒机制（418）进而导致下载的图片（0字节）打不开的情况
    my_header2 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.106 Safari/537.36"
    }

    def get_content(self, url_basic, my_header, content_name):
        '''
        爬取的最终内容存放到douban.txt里
        :url_basic 就是可以返回列表 json 的地址，只有 start 参数在随鼠标下滑翻页改变。
        :param url_basic:
        :param my_header:
        :return:
        '''

        for i in range(0, 500):
            try:
                # 使用format对url进行拼接，主要作用是通过改变url的start位置
                res = requests.get(url=url_basic.format(i * 20 + 1), headers=my_header)
                res_json = json.loads(res.text)
            # 如果出现了json错误，说明已经爬到最后一页了，可以执行下面的步骤了
            except json.decoder.JSONDecodeError:
                continue
            # 如果request没有出现错误，可以执行解析操作
            else:
                index = 0
                for item in res_json.get('items'):
                    target = item.get('target')
                    status = target.get('status')
                    print("这里是第 {} 个".format((i * 20 + 1) + index))
                    index = index + 1
                    '''
                    写入数据时需要注意，默认情况下会把网络数据流以unicode的方式进行保存，如果想把unicode还原为中文的话，需要2个步骤进行还原：
                    1.在open时指定utf-8编码
                    2.在写数据时指定ensure_ascii=False
                    '''
                    with open(content_name, 'a+', encoding='utf8') as f:
                        f.write(json.dumps(status, ensure_ascii=False) + '\n')
                    # with open('douban.txt', 'a+') as f:
                    #     f.write(json.dumps(status) + '\n')
                sleeptime = random.randint(1, 10)
                time.sleep(sleeptime)

    # 根据爬下来的数据，去找image对应的url并进行下载
    def down_picture(self, my_header, content_name):
        file_object = open(content_name, 'r', encoding='utf8')
        sum_image = 0
        for line in file_object:
            item = json.loads(line)
            if item is None:
                continue
            images = item['images']
            id = item['id']
            name = item['author']['name']

            index = 0
            for i in images:
                sum_image = sum_image + 1
                index = index + 1
                url = i.get('large').get('url')
                print(url)

                '''
                :保存图片的几种方法
                ：with open('./images/{}.jpg'.format(id), 'wb') as f:
                '''

                # 第1种
                r = requests.get(url, headers=my_header)
                with open('./images/' + name + '_' + id + '_' + url.split('-')[1:][0], mode='wb') as f:
                    f.write(r.content)
                    f.close()

                # 第2种
                # req = urllib.request.Request(url, headers = header2)
                # bytes = urllib.request.urlopen(req)
                # f = codecs.open(r'./images/' + name + '_' + id + '_' + url.split('-')[1:][0], mode='wb')
                # f.write(bytes.read())
                # f.flush()
                # f.close()

                # 第3种(速度很慢）
                # r = requests.get(url, headers = header2, stream=True);
                # with open('./images/'+ name + '_' + id + '_' + url.split('-')[1:][0], mode = 'wb') as f:
                #     for chunk in r.iter_content():
                #         f.write(chunk)

                # 第4种
                # r = requests.get(url);
                # image = Image.open(BytesIO(r.content))
                # image.save(r'./images/' + str(index) + '.jpg')

                sleeptime = random.randint(1, 5)
                time.sleep(sleeptime)
            print('图片总计：%s张' % sum_image)

    def jieba_cut(self, remove_words, content_name):
        '''
        :根据爬下来的内容使用jieba进行单词的截取工作，并返回2种list
        : 第1种after_remove_words_list是使用Counter统计过词频的list(里面又包含set)，给pyecharts生成词云
        : 第2种text_list是被cut后纯文字的list，没有统计词频的数据，给wordcloud生成词云
        :return:after_remove_words_list, text_list
        '''

        text_list = []
        after_remove_words_list = []
        file_object = open(content_name, 'r', encoding='utf8')
        for line in file_object:
            item = json.loads(line)
            if item is None:
                continue
            text = item['text']
            # 去掉英文，保留中文
            resultword = re.sub("[A-Za-z0-9\[\`\~\!\@\#\$\^\&\*\(\)\=\|\{\}\'\:\;\'\,\[\]\.\<\>\/\?\~\。\@\#\\\&\*\%]",
                                "", text)
            '''
            :cut有3种模式，以"我来到北京清华大学"为例，3种模式匹配结果如下：
            :全模式:我/来到/北京/清华/清华大学/华大/大学
            :精确模式:我/来到/北京/清华大学(推荐）
            :搜索引擎模式：我/来/来到/北京/清华/大学/清华大学/
            :cut_all=False 表示采用精确模式
            :return:返回一个generator
            '''
            wordlist_after_jieba = jieba.cut(resultword, cut_all=False)
            text_list.extend(wordlist_after_jieba)
        # 剔除列表中空格和换行的数据
        text_list = [x.strip() for x in text_list if x.strip() != '']
        # 词频统计,使用Count计数方法
        words_counter = Counter(text_list)
        # 将Counter类型转换为列表
        words_list = words_counter.most_common()
        # 剔除自定义关键字后的列表
        for i in words_list:
            if i[0] not in remove_words:
                after_remove_words_list.append(i)
        return after_remove_words_list, text_list

    def ci_yun1(self, words_list):
        '''
        :生成词云图
        :使用pyecharts生成词云的方法,此方法最终生成的是一个html文件，并且在鼠标悬浮的时候可以显示这个单词出现的次数
        :缺点：分词不太准确，有很多标点符号也被识别为单词了
        :如果最终生成的画布里显示的词云不够多，有2种方法进行调整，1是调大画布面积，2是缩小词云字体大小
        '''
        (
            wcps(init_opts=opts.InitOpts(width="1200px", height="500px"))
                .add(series_name="", data_pair=words_list, word_size_range=[20, 80])
                .set_global_opts(title_opts=opts.TitleOpts(title="豆瓣-WordCloud"))
                .render("词云.html")
        )
        # 上面的代码和下面的代码是等价的
        # wd = wcps(init_opts=opts.InitOpts(width="1200px", height="500px"))
        # wd.add(series_name="", data_pair=words_list, word_size_range=[20, 80])
        # wd.set_global_opts(title_opts=opts.TitleOpts(title="豆瓣-WordCloud"))
        # wd.render("词云.html")

    # 生成柱状图（Bar）
    def bar_map(self, words_list):
        # 获取固定排名区间的词
        bar_data_list20 = words_list[1:21]
        bar_data_list40 = words_list[21:41]
        bar_data_list60 = words_list[41:61]
        bar_data_list80 = words_list[61:81]
        bar_data_list100 = words_list[81:101]
        # print(remove_words_list[1:21])
        # 存放x坐标数据，但是目前还没找到x坐标存放多组数据的方法
        x_data_1 = []
        x_data_2 = []
        # 存放y坐标数据
        y_data_1 = []
        y_data_2 = []

        '''
        : 1.9版本的pyecharts使用柱状图（Bar）时，已经不支持add方法了，网上很多教程都是错的，准确的教程可以参考
        ：https://github.com/pyecharts/pyecharts/
        : 目的是想通过点击不同标题，可以显示多个区间的值，但是x的单词不会跟着变化，也就是x轴只能有一种数据，暂时还没找到解决方法
        : 也行没有这么用的吧
        '''
        for i in range(len(bar_data_list20)):
            x_data_1.append(bar_data_list20[i][0])
            y_data_1.append(bar_data_list20[i][1])
        for i in range(len(bar_data_list40)):
            x_data_2.append(bar_data_list40[i][0])
            y_data_2.append(bar_data_list40[i][1])

        (
            Bar(init_opts=opts.InitOpts(width="1200px", height="500px"))
                # python的链式调用方法，相当于shell里面的管道符的功能
                .add_xaxis(x_data_1)
                # .add_xaxis(x_data_2)
                .add_yaxis("排名前20的词汇", y_data_1)
                .add_yaxis("排名前40的词汇", y_data_2)
                .set_global_opts(title_opts=opts.TitleOpts(title="单词频率统计", subtitle="副标题"))
                .render("Bar.html")
        )

        # (
        #     Bar(init_opts=opts.InitOpts(width="1200px", height="500px"))
        #         # python的链式调用方法，相当于shell里面的管道符的功能
        #         .add_xaxis(x_data)
        #         .add_yaxis("40", y_data)
        #         .set_global_opts(title_opts=opts.TitleOpts(title="出现频率最高的20个单词"))
        #         .render("Bar.html")
        # )

    # 根据爬下来的数据生成词云
    def ci_yun2(self, text_list):
        '''
        :第2种使用WordCloud生成词云的方法，这种方法最终生成的就是一个图片，不能显示单词出现的次数
        :缺点：在图上面不能显示每个单词出现的频率
        :优点：分词更精确，可以自动过滤掉非文字的统计（比如标点符号）
        '''
        # 读入背景图片
        back_groud = np.array(Image.open('cartoon.png'))

        # 设置屏蔽关键字
        sw = set(STOPWORDS)
        sw.update(['的', '我', '去', '在', '人'])

        # 设置wordcloud属性
        my_wordcloud = WordCloud(
            # 图片缩放比，数字越大图片越清晰，但是对电脑资源要求比较高
            scale=4,
            stopwords=sw,
            # 设置使用系统默认字体，否则中文显示乱码
            font_path=r"C:\\Windows\\Fonts\\msyh.ttc",
            background_color='white',
            # 默认width=400,height=200
            width=1200,
            height=600,
            # 词间距
            # margin=0,
            max_words=500,
            min_font_size=10,
            max_font_size=60,
            # default=True,是否包括两个词的搭配
            collocations=False,
            # 如果参数为空，则使用二维遮罩绘制词云。如果 mask 非空，设置的宽高值将被忽略，遮罩形状被 mask 取代。除全白（#FFFFFF）的部分将不会
            # 绘制，其余部分会用于绘制词云。如：bg_pic = imread('读取一张图片.png')，背景图片的画布一定要设置为白色（#FFFFFF），然后显示的
            # 形状为不是白色的其他颜色。可以用ps工具将自己要显示的形状复制到一个纯白色的画布上再保存，就ok了。
            mask=back_groud,
            # 为每个单词返回一个PIL颜色
            random_state=42
        )
        # cut后的list内容，使用逗号进行连接
        wd_space_join = ",".join(text_list)
        # 使用词云对文本进行分词和词云的生成
        wd_cut = my_wordcloud.generate(wd_space_join)
        # wd_cut = my_wordcloud.generate(text_list)
        # wd_cut = my_wordcloud.generate_from_text(wl_space_split)
        # 获取背景图片的颜色(配合mask一起使用)
        image_color = ImageColorGenerator(back_groud)
        # 修改字体颜色为背景色(配合mask一起使用)
        wd_cut.recolor(color_func=image_color)
        # plt生成的词云
        plt.imshow(wd_cut, interpolation="bilinear")
        # 关闭坐标
        plt.axis("off")
        # 交互式展示词云图
        plt.show()
        # 保存生成的图片
        wd_cut.to_file('词云.jpg')

    # 根据爬下来的数据生成热力地图
    def geo_heat_map(self, text_list):
        # 以字典的方式存放省市信息及频率
        addr_dic = {}
        # 通过cpca的transform方法从list中获取地址信息，返回的是DataForm格式的数据
        addr_df = cpca.transform(text_list)
        # 对DataForm的省一列进行循环
        for addr in addr_df['省'].str.split(' '):
            if addr is not None:
                # 对于以下简写的地区需要处理一下，否则识别不到
                if addr[0] == '广西壮族自治区':
                    addr[0] = '广西'
                if addr[0] == '香港特别行政区':
                    addr[0] = '香港'
                if addr[0] == '澳门特别行政区':
                    addr[0] = '澳门'
                if addr[0] == '西藏自治区':
                    addr[0] = '西藏'
                # 把出现的省市信息和次数，存放到字典中
                addr_dic[addr[0]] = addr_dic.get(addr[0], 0) + 1
        print(addr_dic)

        '''
        : 生成热力图
        : 如果最终统计的数据比较少导致图片显示不明显，可以是适当调小图例条的范围VisualMapOpts(max_ = 20)，默认是100
        '''
        (
            Geo(init_opts=opts.InitOpts(width="1300px", height="500px"))
                .add_schema(maptype="china")
                .add("geo", [list(z) for z in zip(list(addr_dic.keys()), list(addr_dic.values()))],
                     type_=ChartType.HEATMAP)
                .set_series_opts(label_opts=opts.LabelOpts(is_show=True))
                .set_global_opts(visualmap_opts=opts.VisualMapOpts(max_=20),
                                 title_opts=opts.TitleOpts(title="Geo-HeatMap", subtitle="副标题"))
                .render("热力图.html")
        )


if __name__ == '__main__':
    douban = DouBanBiaoBai()
    douban.get_content(douban.url_basic, douban.my_header1, 'douban.txt')
    douban.down_picture(douban.my_header2, 'douban.txt')
    r1, r2 = douban.jieba_cut(douban.remove_words, 'douban.txt')
    douban.ci_yun1(r1)
    douban.bar_map(r1)
    douban.ci_yun2(r2)
    douban.geo_heat_map(r2)
    # print(os.path.join(os.path.dirname(__file__), "../"))
    print('test')
    pass
