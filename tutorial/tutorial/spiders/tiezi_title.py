# coding=utf-8

import scrapy
from tutorial.items import PosterItem


class TitleSpider(scrapy.Spider):
    name = 'tiezi_title'
    page_num = 0

    start_urls = [
        'https://tieba.baidu.com/f?ie=utf-8&kw=剑三交易'
    ]

    def parse(self, response):
        self.page_num += 1
        for href in response.xpath('//div[@class="threadlist_title pull_left j_th_tit "]//a/@href'):
            yield response.follow(href.extract(), self.parse_post)
        # next_page = response.xpath('//a[@class="next pagination-item "]/@href').extract_first()
        # if next_page is not None and self.page_num < 2:
        #     yield response.follow(next_page, callback=self.parse)

    def parse_post(self, response):
        post_tieba = response.xpath(
            '//a[@class="card_title_fname"]/text()').extract_first().strip()
        post_title = response.xpath(
            '//div[@class="core_title_wrap_bright clearfix"]//h3/@title'
        ).extract_first()
        post_page = response.xpath(
            '//span[@class="tP"]/text()').extract_first()
        if post_page is None:
            post_page = '1'
        for each_post in response.xpath(
                '//div[@class="l_post l_post_bright j_l_post clearfix  "]'
        ):
            post_author = each_post.xpath(
                './/li[@class="d_name"]/a/text()').extract_first()
            post_position = each_post.xpath(
                './/span[@class="tail-info"]/text()').extract()[-2].rstrip('楼')
            post_time = each_post.xpath(
                './/span[@class="tail-info"]/text()').extract()[-1]
            post_line = each_post.xpath(
                './/div[@class="d_post_content j_d_post_content "]/text()'
            ).extract_first().strip()
            if not post_line:
                continue
            poster_inf = PosterItem(
                post_page=post_page,
                post_title=post_title,
                post_author=post_author,
                post_time=post_time,
                post_url=response.url,
                post_position=post_position,
                post_tieba=post_tieba,
                post_line=post_line
            )
            yield poster_inf

        # if response.xpath('//li[@class="l_pager pager_theme_4 pb_list_pager"]//a').re('下一页'):
        #     next_page = response.xpath(
        #         '//li[@class="l_pager pager_theme_4 pb_list_pager"]//a/@href')[-2].extract()
        #     yield response.follow(next_page, callback=self.parse_post)
