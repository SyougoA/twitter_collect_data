import sqlite3
import MeCab


class ExportDB(object):
    def __init__(self, name, table_name):
        self.conn = sqlite3.connect("{0}.db".format(name))
        self.table_name = table_name

    def export_nuldb(self):
        cur = self.conn.cursor()
        cur.execute(
            "select comment from {0} where reply_name is null;".format(self.table_name)
        )
        tweet_null = cur.fetchall()

        return tweet_null

    def export_isdb(self):
        cur = self.conn.cursor()
        cur.execute(
            "select comment from {0} where reply_name is not null;".format(self.table_name)
        )
        tweet_is = cur.fetchall()

        return tweet_is

"""
pythonだとjanomeがpureで有名なライブラリであるが
1.ipadicが優秀 2.動作が高速
と利点があるためmecabを採用した
"""
class WakatiTxt(object):
    def __init__(self):
        # -d...辞書指定、-Ochasen...茶筌
        self.mecab = MeCab.Tagger("-Ochasen -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd")
        self.mecab.parse('')

        # 分かち書きの時に使用する
        self.pos_list = ["名詞", "動詞", "形容詞"]
        self.skip_list = ["*", "…。"]  # 見つけたものを随時足していく

        self.db_export = ExportDB("tweet_collect", "tweet_data")
        self.null_data = self.db_export.export_nuldb()
        self.is_data = self.db_export.export_isdb()

    def wakati_return(self):
        # 分かち書き形式にするためにインデントをjoinする
        is_wakati = " ".join(self.wakati_process(self.is_data))
        null_wakati = " ".join(self.wakati_process(self.null_data))

        """
        以下はtxt形式で分かち書きをexportしたい人用
        引数にnameか何か用意して下の処理を分岐させる


        if name == "is_txt":
            open("is.txt", "w").write(is_wakati)
        elif name = "null_txt":
            open("null.txt", "w").write(null_wakati)
        """

        return is_wakati, null_wakati

    def wakati_process(self, data_list):
        tweet_list = []
        append = tweet_list.append

        for txt in data_list:
            """
            形態素情報が欲しいためテキストで結果を返すparseではなくparseToNodeを使用する
            surface...表層形、feature...形態素情報
            """
            text = txt[0]  # 返り値が(hoge, )になるので0番目nodeを取得
            node = self.mecab.parseToNode(text)
            while node:
                """
                feats返り値例 : ['動詞', '自立', '*', '*', '五段・ラ行', '体言接続特殊２', '戻る', 'モド', 'モド']
                よって原型を取得するにはnode6を取得すれば良い
                """
                feats = node.feature.split(',')
                if feats[0] in self.pos_list and feats[6] not in self.skip_list:
                    try:
                        append(feats[6])
                    except Exception as e:
                        print("err:{0}, cause:{1}".format(str(node.surface), e))

                node = node.next  # ジェネレーター

        return tweet_list

if __name__ == "__main__":
    wk = WakatiTxt()
    foo, bar = wk.wakati_return()
    print(foo, bar)
