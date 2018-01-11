# coding=utf-8
#! /usr/bin/env python3

import yaml
import datetime
import re
import pymysql

train_data = 'jx3_item'
word_dict = dict()
ori_word_dict = dict()
PRICE_NOT_FOUND = 10000

FEATURE_DIS = 5

number_dict = {
    '零': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
}

number_unit = {
    '十': 10,
    '百': 100,
    '千': 1000,
    '万': 10000,
    'w': 10000,
    'k': 1000,
}

for n in range(10):
    number_dict.update({str(n): n})


def is_word(w):
    if '\u4e00' <= w <= '\u9fa5':
        return True
    elif re.match('[0-9a-zA-Z]', w):
        return True
    return False


def translate_number(number_list):
    number = 0
    try:
        number = int(''.join(number_list))
    except ValueError as e:
        tmp_unit = -1
        prefix = ''
        for n, each in enumerate(number_list):
            if each in number_dict:
                try:
                    unit = number_list[n + 1]
                    unit_n = number_unit[unit]
                except IndexError:
                    unit_n = int(tmp_unit / 10)
                except KeyError:
                    if tmp_unit == -1:
                        prefix = '{p}{n}'.format(p=prefix, n=number_dict[each])
                        continue
                    else:
                        unit_n = int(tmp_unit / 10)
                if prefix != '':
                    number = int('{p}{n}'.format(
                        p=prefix, n=number_dict[each])) * unit_n
                    prefix = ''
                else:
                    number += number_dict[each] * unit_n
                tmp_unit = unit_n
    return number


with open(train_data) as jx_it:
    for each in jx_it:
        each_inf = each.strip().split()
        if (not each_inf) or each_inf[0] == '#':
            continue
        for each_it in each_inf:
            ori_word_dict[each_it] = each_inf[0]
            for m, each_w in enumerate(each_it):
                each_key = each_it[:(m + 1)]
                if m < len(each_it) - 1:
                    each_value = each_it[m + 1]
                else:
                    each_value = each_inf[0]
                if each_key in word_dict and each_value in word_dict[each_key]:
                    continue
                else:
                    word_dict.setdefault(each_key, []).append(each_value)

with open('mp.yaml') as f:
    config = yaml.load(f)


def detail2class(detail_dict):
    class_dict = dict()
    for each_class in detail_dict:
        class_dict[each_class] = each_class
        for each_detail in detail_dict[each_class]:
            class_dict[each_detail] = each_class
    return class_dict


server_class_dict = detail2class(config['server'])
mp_class_dict = detail2class(config['mp'])

share_dict_i = dict()
share_dict_s = dict()
share_mark = dict()

for n in range(4, 0, -1):
    for each_w in ori_word_dict:
        if each_w in server_class_dict or each_w in mp_class_dict:
            continue
        w_len = len(each_w)
        if w_len <= n or each_w in share_mark:
            continue
        last_w = each_w[-n:]
        pre_w = each_w[:w_len - n]
        if n < 4 and w_len > n + 1 and each_w[-n - 1:] in share_dict_i:
            share_num = len(share_dict_i[each_w[-n - 1:]])
            if share_num > 1:
                share_mark[each_w] = 1
                continue
        share_dict_i.setdefault(last_w, set()).add(pre_w)

prefix_len_set = set()
share_dict_i_copy = share_dict_i.copy()
for each_i in share_dict_i_copy:
    if len(share_dict_i[each_i]) > 1:
        for each_s in share_dict_i[each_i]:
            share_dict_s.setdefault(each_s, []).append(each_i)
            prefix_len_set.add(len(each_s))
    else:
        share_dict_i.pop(each_i)
del (share_dict_i_copy)


def search_price(line, up=True, skip_loc=[]):
    number_list = []
    number = 0
    flag = 0
    dis = PRICE_NOT_FOUND
    if up:
        line = line[::-1]
    for n, each in enumerate(line):
        each = each.lower()
        if each in number_dict or each in number_unit:
            if up:
                number_list.insert(0, each)
            else:
                number_list.append(each)
            if flag == 0:
                start = n
            flag = 1
        if each not in number_dict and each not in number_unit and flag == 1:
            number = translate_number(number_list)
            flag = 0
            if number > 100:
                dis = start + 1
                return number, dis
            else:
                return 0, dis
    return number, dis


def mask_skip(line, skip_loc=[], mask_w='#'):
    mask_list = []
    for n, each_w in enumerate(line):
        if n in skip_loc:
            mask_list.append(mask_w)
        else:
            mask_list.append(each_w)
    return ''.join(mask_list)


def get_price(line, price_anc, skip_loc):
    if not price_anc:
        return 0, PRICE_NOT_FOUND
    start_pos, end_pos = price_anc
    mask_line = mask_skip(line, skip_loc)
    price1, dis1 = search_price(mask_line[:start_pos], True)
    price2, dis2 = search_price(mask_line[end_pos:], False)
    dis = min(dis1, dis2)
    if dis1 == dis2:
        price = max(price1, price2)
    else:
        if dis1 < dis2:
            price = price1
        else:
            price = price2
    return price, dis


def share_word(line, word, end, prefix_list, end_list, non_w=0):
    # print('SHARE')
    # print(line)
    # print(word)
    # print(end)
    prefix_list.append(word)
    if not end_list:
        end_list = share_dict_s[word]
    new_line = line[end:]
    new_word_list = []
    for each in new_line:
        if is_word(each):
            new_word_list.append(each)
        else:
            non_w += 1
        if len(new_word_list) == max(prefix_len_set):
            break
    for n, each in enumerate(new_word_list):
        each_w = ''.join(new_word_list[:n + 1])
        end = len(each_w) + non_w
        if each_w in end_list:
            share_word_list = [
                '{p}{e}'.format(p=each, e=each_w) for each in prefix_list
            ]
            share_len = sum([len(each) for each in prefix_list])
            end = share_len + non_w + 1
            return ','.join(share_word_list), end
        elif each_w in share_dict_s:
            each_end = share_dict_s[each_w]
            if set(end_list).intersection(set(each_end)):
                return share_word(new_line, each_w, end, prefix_list, end_list,
                                  non_w)
            else:
                return None, None
        else:
            return None, None
    return None, None


def match_word(line, word_list, nw_list, end=1):
    if end > len(line):
        if len(word_list) > 1:
            word = ''.join(word_list)
            return ori_word_dict.get(word, word), end, nw_list
        else:
            return None, end, nw_list
    elif not is_word(line[end - 1]):
        nw_list.append(end - 1)
        end += 1
        return match_word(line, word_list, nw_list, end)
    else:
        word_pre = ''.join(word_list)
        tmp_word = '{p}{s}'.format(p=word_pre, s=line[end - 1])
        if tmp_word in word_dict:
            word_list.append(line[end - 1])
            word = tmp_word
            if end == len(line):
                if len(word) > 1:
                    return ori_word_dict.get(word, word), end, nw_list
                else:
                    return None, end, nw_list
            else:
                end += 1
                return match_word(line, word_list, nw_list, end)
        else:
            word = word_pre
            if end == 1:
                return None, end, nw_list
            else:
                if word in share_dict_s:
                    out_word, new_end = share_word(line, word, end - 1, [], [])
                    if out_word:
                        end = new_end
                else:
                    if len(word) > 1:
                        out_word = ori_word_dict.get(word, word)
                    else:
                        out_word = None
                return out_word, end - 1, nw_list


def nearest_enclose(a, b, limit=20):
    new_border = b.copy()
    for n, each in enumerate(a):
        if n < len(a) - 1:
            if each < b[0] and a[n + 1] > b[0]:
                if b[0] - each < limit:
                    new_border[0] = each
            elif each < b[1] and a[n + 1] > b[1]:
                if a[n + 1] - b[1] < limit:
                    new_border[1] = a[n + 1]
    return new_border


def loc_dis(a, b):
    return min(abs(b[0] - a[1]),
               abs(a[0] - b[1]))


def extract_item(line):
    non_word_loc = []
    server = ''
    mp = ''
    price = 0
    items = []
    line_len = len(line)
    start_pos = 0
    skip_loc = []
    item_loc = []
    price_anc = []
    info_map_loc = [[], [], []]
    info_list = []

    def empty_inf():
        nonlocal info_map_loc
        for each in info_map_loc:
            if each:
                return False
        else:
            return True

    def add_inf():
        nonlocal info_map_loc
        if not empty_inf():
            nonlocal non_word_loc
            nonlocal server
            nonlocal mp
            nonlocal price
            nonlocal items
            nonlocal item_loc
            nonlocal skip_loc
            nonlocal price_anc
            if info_map_loc[-1]:
                item_loc = sorted(info_map_loc[-1])
                skip_loc.extend(range(item_loc[0][0], item_loc[-1][-1]))
                info_map_loc[-1] = [item_loc[0][0], item_loc[-1][-1]]
            price, dis = get_price(line, price_anc, skip_loc)
            if dis != PRICE_NOT_FOUND:
                info_map_loc.append([max(0, price_anc[0] - dis),
                                     price_anc[1] + dis])

            def get_line():
                nonlocal info_map_loc
                nonlocal line
                nonlocal non_word_loc
                line_region_l = [[each[0] for each in info_map_loc if each],
                                 [each[1] for each in info_map_loc if each]]
                line_region = [min(line_region_l[0]), max(line_region_l[1])]
                if non_word_loc:
                    line_region = nearest_enclose(non_word_loc, line_region)
                return line[line_region[0]:line_region[1] + 1]

            out_line = get_line()
            info_list.append((server, mp, items, price, out_line))
        server = ''
        mp = ''
        price = 0
        items = []
        # skip_loc = []
        item_loc = []
        price_anc = []
        info_map_loc = [[], [], []]

    def another_infor(names, name_dict, dis, loc_index):
        '''
        通过门派和服务器信息判断界定账号不同账号
        1. 出现不同门派/服务器名字
        2. 出现相同门派/服务器名字，距离超过阈值
        3. 若门派服务器出现后，再出现门派/服务器，如果新出现
           信息距离更近，且之前的信息没有包含物品，则忽略之前
           的门派/服务器
        '''

        nonlocal info_map_loc
        nonlocal start_pos
        nonlocal end
        # print(info_map_loc)
        # print(names[0], names[1])
        if not info_map_loc[loc_index]:
            pass
        elif name_dict[names[0]] != name_dict[names[1]] or dis > FEATURE_DIS:
            dis1 = loc_dis(info_map_loc[0], info_map_loc[1])
            dis2 = loc_dis(info_map_loc[loc_index],
                           [start_pos, start_pos + end])
            # print(dis1)
            # print(dis2)
            if dis2 < dis1 and (not info_map_loc[-1]):
                pass
            else:
                add_inf()
        else:
            pass

    while start_pos < line_len:
        if not is_word(line[start_pos]):
            non_word_loc.append(start_pos)
            start_pos += 1
            continue
        in_line = line[start_pos:]
        match, end, nw_end = match_word(in_line, [], [])
        non_word_loc.extend([start_pos + each for each in nw_end])
        if match:
            if match in server_class_dict:
                skip_loc.extend(range(start_pos, start_pos + end))
                if server == '':
                    info_map_loc[0] = [start_pos, start_pos + end]
                    server = match
                else:
                    sv_dis = start_pos - info_map_loc[0][-1]
                    another_infor((server, match), server_class_dict,
                                  sv_dis, 1)
                    server = match
                    info_map_loc[0] = [start_pos, start_pos + end]
            elif match in mp_class_dict:
                if mp == '':
                    mp = match
                    price_anc = [start_pos, start_pos + end]
                    info_map_loc[1] = [start_pos, start_pos + end]
                else:
                    skip_loc.extend(range(start_pos, start_pos + end))
                    mp_dis = start_pos - info_map_loc[1][-1]
                    another_infor((mp, match), mp_class_dict, mp_dis, 0)
                    mp = match
                    price_anc = [start_pos, start_pos + end]
                    info_map_loc[1] = [start_pos, start_pos + end]
            else:
                items.append(match)
                info_map_loc[-1].append((start_pos, start_pos + end))
        start_pos += end

    add_inf()
    return info_list, skip_loc


def infor2table():
    conn = pymysql.connect(
        host='127.0.0.1',
        user='lxgui',
        passwd='123',
        db='jx3',
        charset="utf8")
    cur = conn.cursor()
    cur.execute("USE jx3")
    # sql = 'SELECT * FROM {d}'.format(d=database)
    sql = 'SELECT * FROM jx_test'
    cur.execute(sql)
    for each in cur:
        tieba_name = each[1]
        post_name = each[2]
        post_url = each[3]
        page = each[4]
        user = each[6]
        post_num = each[5]
        post_time = datetime.datetime.strftime(each[7], '%Y-%m-%d %H:%M')
        #post_inf_list = each[-1].split()
        #each_inf = ' '.join(post_inf_list)
        each_inf = each[-1]
        if each_inf != '':
            each_inf_list, skip_loc = extract_item(each_inf)
            if not skip_loc:
                continue
            out_inf = '{p}...{s}'.format(p=each_inf[:skip_loc[0]],
                                         s=each_inf[skip_loc[-1] + 1:])
            for each_item_inf in each_inf_list:
                server, mp, items, price, out_line = each_item_inf
                if (server or mp) and items:
                    server_class = mp_class = '--'
                    if server:
                        server_class = server_class_dict[server]
                    if mp:
                        mp_class = mp_class_dict[mp]
                    item_str = ','.join(items)
                    print(
                        server_class,
                        server,
                        mp_class,
                        mp,
                        item_str,
                        price,
                        tieba_name,
                        post_name,
                        post_url,
                        post_num,
                        user,
                        post_time,
                        out_line,
                        out_inf,
                        sep='\t')
    cur.close()
    conn.close()


if __name__ == '__main__':
    infor2table()
