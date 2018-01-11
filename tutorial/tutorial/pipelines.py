# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql


class TutorialPipeline(object):

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host='127.0.0.1',
            user='lxgui',
            passwd='123',
            db='jx3',
            charset="utf8",
        )
        self.cur = self.conn.cursor()
        self.cur.execute("USE jx3")
        self.database = 'jx_test'
        pass

    def process_item(self, item, spider):
        sql = "INSERT INTO `{t.database}` \
        (`post_tieba`, `post_title`, `post_url`, `post_page`, \
        `post_position`, `post_author`, `post_time`, `post_line`) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)".format(t=self)
        self.cur.execute(sql, (item['post_tieba'], item['post_title'],
                               item['post_url'], item['post_page'],
                               item['post_position'], item['post_author'],
                               item['post_time'], item['post_line']))
        self.conn.commit()
        return item

    def spider_closed(self, spider):
        self.cur.close()
        self.conn.close()
