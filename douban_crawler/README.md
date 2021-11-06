用Python搞定豆瓣上征婚交友的小姐姐们

此代码主要是参考微信公众号的教程，但是发现里面有一些错误导致不能运行，所以对源代码进行了微调。 此工程的作用是爬取豆瓣上有一个叫我被豆油表白了的交友话题里所有用户的图片，其中共有4个功能：

1.爬取所有的用户数据（包含nmae、id和image等信息）

2.根据爬取的数据下所有用户图片

3.根据爬取的数据生成词云

4.根据爬取的数据生成城市热力图

TroubleShooting
在安装cpca的过程中遇到了一些问题，解决方法可以参考我的csdn博客：https://blog.csdn.net/lizy0327/article/details/120676502

cpca源码：https://github.com/DQinYuan/chinese_province_city_area_mapper

第一个爬虫，纪念一下！