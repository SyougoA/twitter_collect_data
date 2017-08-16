from datetime import datetime
import tweepy as ty
import sqlite3
import re, time


class TwitterData(object):
    """
    location等ないものはNoneで返る.
    改行は入るので消去.
    リスト等にしないとResultSetと言われてしまう(for文で解決).
    """
    def __init__(self):
        # accessするための準備
        self.consumer_key = ""
        self.consumer_secret = ""
        self.access_token = ""
        self.access_secret = ""

        self.auth = ty.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = ty.API(self.auth)

        # api制限が解除されるまでの時差を調べるために取得
        self.time_now = datetime.now()

    # tweet情報を取得するメソッド
    def tl_tweets(self, num):
        """
        仕様:
        呟き...retweeted_status=false, in_reply_to_status_id=null
        リプライ...retweeted_status=false, in_reply_to_screen_name=True
        RT...retweeted_status=false, in_reply_to_screen_name=null
        """
        # ここでapi制限を確かめる
        self.limit_check()

        tweets = self.api.home_timeline(count=num)
        data_list = []
        append = data_list.append
        for tweet in tweets:
            try:
                # RTされたものはスルーする
                if tweet.retweeted_status:
                    continue

            except AttributeError:
                name = tweet.user.screen_name
                tweet_time = tweet.created_at
                comment = self.erase(tweet.text)
                reply_name = tweet.in_reply_to_screen_name

                tweet_data = (name, tweet_time, comment, reply_name)
                append(tweet_data)

        sqliteprocess = SqliteProcess("tweet_collect")
        sqliteprocess.insert_records_twitter(data_list)

    # api制限を調べてsleepを入れるか判断するメソッド
    def limit_check(self):
        # api_status =  {'limit': 180, 'reset': epoc_time, 'remaining': rest_num}
        api_status = self.api.rate_limit_status()['resources']['application']['/application/rate_limit_status']
        remaining = api_status['remaining']
        reset = api_status['reset']
        if remaining <= 10:
            sleep = self.date_to_epoc(reset)
            time.sleep(sleep + 10)

    # 時刻の差分を計算して返すメソッド
    def date_to_epoc(self, reset_epoc):
        now_epoc = int(time.mktime(self.time_now.timetuple()))
        sleep_time = reset_epoc - now_epoc

        return sleep_time

    # 正規表現で処理するメソッド
    @staticmethod
    def erase(txt):
        re_data = ["\n", "\r", "　"]
        for r in re_data:
            txt = re.sub(r, '', txt)

        return txt


class SqliteProcess(object):
    """
    初期化から変数に関する格納までを行う.
    rtされたcommentは格納しない.
    最初は特に選別しないが文が短すぎるreplyは入れないのもひとつの手.
    """
    def __init__(self, name):
        self.dbname = name + ".db"
        self.conn = sqlite3.connect(self.dbname)
        self.cur = self.conn.cursor()

        self.cur.execute("""
                   CREATE TABLE IF NOT EXISTS tweet_data(
                   comment_id INTEGER PRIMARY KEY,
                   tweet_name TEXT,
                   time TEXT,
                   comment TEXT,
                   reply_name TEXT
                   );
                   """)

        self.conn.commit()

    # tweet情報を格納
    def insert_records_twitter(self, data_contents):
        self.cur = self.conn.cursor()
        self.cur.executemany(
            "INSERT INTO tweet_data(tweet_name,time,comment,reply_name) VALUES (?,?,?,?);", data_contents
        )

        self.conn.commit()

if __name__ == "__main__":
    twitter = TwitterData()
    twitter.tl_tweets(100)