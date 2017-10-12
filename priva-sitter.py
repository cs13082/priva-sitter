# -*- coding:utf-8 -*-

import os
import webbrowser
import json
import twitter
from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

CONSUMER_FILE = 'consumer.json'
AUTH_FILE = 'auth.json'
UNFAV_COUNT = 200
DESSTATUS_COUNT = 200

def main():
    print("\nぷらいばシッター - ツイートの削除やいいねの取り消し")
    print("一括削除で表示されるツイート数などがおかしくなる可能性アリ")
    print("エラーが発生するときはAPI上限に達しているので時間をおいて再実行してね\n")

    # APIアクセスの準備
    ck, cs = getConsumerKey()
    atk, ats = getAccessToken(ck, cs)

    api = twitter.Api(consumer_key=ck,
                      consumer_secret=cs,
                      access_token_key=atk,
                      access_token_secret=ats)
    
    # ユーザ情報の取得
    user = api.VerifyCredentials()
    print('ツイート数：{0}, いいね数：{1}'.format(user.statuses_count, user.favourites_count))
    
    keyinput = input("ツイートの全削除を行いますか [Y/N]")
    if keyinput == "Y" or keyinput == "y":
        delStatus(api, user)

    keyinput = input("いいねの全解除を行いますか [Y/N]")
    if keyinput == "Y" or keyinput == "y":
        unFav(api, user)
    
    # 数の変化を表示
    user_end = api.VerifyCredentials()
    print('\nツイート数：{0}, いいね数：{1}'.format(user.statuses_count, user.favourites_count))
    print('→ ツイート数：{0}, いいね数：{1}\n'.format(user_end.statuses_count, user_end.favourites_count))

def delStatus(api, user):
    for i in range((user.statuses_count // DESSTATUS_COUNT) + 1):
        print("delStatus: {}".format(i))
        statuses = api.GetUserTimeline(api.VerifyCredentials().id, count=DESSTATUS_COUNT)
        #スレッド化するとはやくなるかも
        for status in statuses:
            api.DestroyStatus(status.id)
            print('削除中: {}'.format(status.id))

def unFav(api, user):
    for i in range((user.favourites_count // UNFAV_COUNT) + 1):
        print("unfav: {}".format(i))
        favs = api.GetFavorites(count=UNFAV_COUNT)
        #スレッド化するとはやくなるかも
        for fav in favs:
            api.DestroyFavorite(fav)
            print('解除中: {}'.format(fav.id))

def getConsumerKey():
    # jsonファイルから取得
    confile = open(CONSUMER_FILE, "r")
    condata = json.load(confile)
    return [condata["consumer_key"], condata["consumer_secret"]]

def getAccessToken(ck, cs):
    # Oauth部参考：https://github.com/bear/python-twitter/blob/master/get_access_token.py

    # 認証ファイルの有無でアクセストークンの取得先変更
    if os.path.isfile(AUTH_FILE):
        # jsonファイルから取得
        authfile = open(AUTH_FILE, "r")
        authdata = json.load(authfile)
        return [authdata["oauth_token"], authdata["oauth_token_secret"]]
    else:
        # Twitterから取得
        oauth_client = OAuth1Session(ck, client_secret=cs, callback_uri='oob')

        print('\nRequesting temp token from Twitter...\n')

        try:
            resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
        except ValueError as err:
            raise 'Invalid response from Twitter requesting temp token: {0}'.format(err)

        url = oauth_client.authorization_url(AUTHORIZATION_URL)

        print('I will try to start a browser to visit the following Twitter page '
            'if a browser will not start, copy the URL to your browser '
            'and retrieve the pincode to be used '
            'in the next step to obtaining an Authentication Token: \n'
            '\n\t{0}'.format(url))

        webbrowser.open(url)
        pincode = input('\nEnter your pincode? ')

        oauth_client = OAuth1Session(ck, client_secret=cs,
                                    resource_owner_key=resp.get('oauth_token'),
                                    resource_owner_secret=resp.get('oauth_token_secret'),
                                    verifier=pincode)
        try:
            resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
        except ValueError as err:
            raise 'Invalid response from Twitter requesting temp token: {0}'.format(err)

        # oauth_token と oauth_token_secret をファイルに出力
        authdict = {
            "oauth_token": resp.get('oauth_token'),
            "oauth_token_secret": resp.get('oauth_token_secret')
        }
        authfile = open(AUTH_FILE, 'w')
        json.dump(authdict, authfile)
        authfile.close()

        return [resp.get('oauth_token'), resp.get('oauth_token_secret')]

if __name__ == "__main__":
    main()
