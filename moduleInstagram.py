#!/usr/bin/env python

import configparser
import getpass
import logging
import os
import sys
import urllib.parse

import keyring
import keyrings
import requests
from InstagramAPI import InstagramAPI

from configMod import *
from moduleContent import *

# https://github.com/LevPasha/Instagram-API-python


class moduleInstagram(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.ig = None

    def setClient(self, instagramAC):
        logging.info("     Connecting Instagram")
        try: 
            keyring.set_keyring(keyrings.alt.file.PlaintextKeyring()) 
            username = instagramAC 
            self.user = instagramAC
            server = 'instagram'
            password = keyring.get_password(server,username) 
            if not password: 
                logging.info("[%s,%s] New account. Setting password" % (server, username)) 
                password = getpass.getpass() 
                keyring.set_password(server, username, password)

            try: 
                api = InstagramAPI(username, password) 
                api.login()  # login
                logging.info("     Logging OK")
            except:
                logging.warning("Instagram authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
            logging.warning("Account not configured")
            api = None

        self.client = api
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        if self.client.getSelfUserFeed():
            igs = self.client.LastJson['items']
            # Relevant items
            # 'code': 'BzlL-OXBYOe' -> https://www.instagram.com/p/BzlL-OXBYOe
            # 'caption' -> 'text'
            # 'taken_at' time.ctime
            # 'image_versions2' -> 'candidates' -> 'url'
            # 'comment_count'
            # 'likers' 
            # Example at the end of this file
        for ig in igs:
            self.posts.append(ig)

    def publishPost(self, post, link, image):
        logging.info("     Publishing in Instagram...")
        comment = resizeImage(image)
        # resizeImage provided by configMod.py
        try: 
            res = self.client.uploadPhoto(comment, caption=post)
            self.setPosts()
            title = self.getPosts()[0]['caption']['text']
            print("Title %s" % title)
            print("caption %s" % post)
            if title == post:
                mediaId = self.getPosts()[0]['caption']['media_id']
                if link:
                    # We will publish the link as first comment
                    path = urllib.parse.urlparse(link)[2].split('/')
                    if (link.find('wordpress') > 0) and (len(path)>3):
                        # This should not be here (too specific)
                        yy = path[1]
                        mm = path[2]
                        dd = path[3]
                        self.client.comment(mediaId, 'Original: %s [%s-%s-%s]'% (link,yy,mm,dd))
                    else:
                        self.client.comment(mediaId, 'Original: %s'% link)
                logging.info("     Published in Instagram...")

                return(self.getPosts()[0]['code']) 
            else:
                logging.info("     Not published in Instagram...")
                return('Fail')
        except:
            logging.info("     Not published in Instagram. Exception ...")
            return('Fail')
        

def main():

    import moduleInstagram

    ig = moduleInstagram.moduleInstagram()

    ig.setClient('a_veces_una_foto')

    url = 'https://avecesunafoto.wordpress.com/2017/07/09/tocando/'
    url = 'https://avecesunafoto.wordpress.com/2017/07/09/canelon-de-longaniza/'
    url = 'https://avecesunafoto.wordpress.com/2017/07/09/ternasco/'
    url = 'https://avecesunafoto.wordpress.com/2017/07/17/codos/'
    url = 'https://avecesunafoto.wordpress.com/2017/07/19/maria-fernandez-guajardo-consejos-practicos-de-una-feminista-zaragozana-en-el-silicon-valley/'
    # lin rel='next'
    # soup.findAll('link', {'rel': 'next'})
    import requests
    req = requests.get(url)
    if req.status_code == 200:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(req.text, 'html.parser')
        imgUrl = soup.img['src']
        title = soup.findAll('h1')[1].text
        pos = imgUrl.find('?')
        if pos > 0:
            imgUrl = imgUrl[:pos]
        if imgUrl: 
            logging.debug(imgUrl)
            #res = ig.publishPost(title, url, imgUrl)
            #print(res)

    sys.exit()
    print("Setting posts")
    ig.setPosts()
    for igP in ig.getPosts():
        print("https://instagram.com/p/%s" % igP['code'])
        print("Caption: %s" % igP['caption'])
        print("Image: %s" % igP['image_versions2']['candidates'][0]['url'])
        print("Likes: %d" % igP['like_count'])

    print(res)
    return("https://instagram.com/p/%s" % igP['code'])




if __name__ == '__main__':
    main()

"""
{'items': [{'taken_at': 1562428432, 'pk': 2082123057266525086, 'id': '2082123057266525086_12672764795', 'device_timestamp': 1562428430661, 'media_type': 1, 'code': 'BzlL-OXBYOe', 'client_cache_key': 'MjA4MjEyMzA1NzI2NjUyNTA4Ng==.2', 'filter_type': 0, 'image_versions2': {'candidates': [{'width': 750, 'height': 750, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/1c833e32af8071052217c6ed683ef0ee/5DC2B7AA/t51.2885-15/sh0.08/e35/s750x750/66298405_2313549898857678_8650230192112164040_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=106&ig_cache_key=MjA4MjEyMzA1NzI2NjUyNTA4Ng%3D%3D.2', 'estimated_scans_sizes': [11691, 23383, 35074, 46766, 58457, 65414, 83242, 94608, 105224]}, {'width': 240, 'height': 240, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/6dfe636e851edcbc7cbe0617388ac3d3/5DBB5CED/t51.2885-15/e35/s240x240/66298405_2313549898857678_8650230192112164040_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=106&ig_cache_key=MjA4MjEyMzA1NzI2NjUyNTA4Ng%3D%3D.2', 'estimated_scans_sizes': [1548, 3097, 4646, 6194, 7743, 9322, 269035, 13938, 13938]}]}, 'original_width': 3120, 'original_height': 3120, 'user': {'pk': 12672764795, 'username': 'a_veces_una_foto', 'full_name': 'F.T.G.', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/768d122416ae68494a583e465c40b20a/5DBCEECF/t51.2885-19/s150x150/56468365_1250869771754902_8896379520727121920_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2025650010676586856_12672764795', 'is_verified': False, 'has_anonymous_profile_picture': False, 'can_boost_post': True, 'can_see_organic_insights': True, 'show_insights_terms': False, 'reel_auto_archive': 'unset', 'is_unpublished': False, 'allowed_commenter_type': 'any'}, 'can_viewer_reshare': True, 'caption_is_edited': False, 'direct_reply_to_author_enabled': True, 'comment_likes_enabled': True, 'comment_threading_enabled': False, 'has_more_comments': False, 'max_num_visible_preview_comments': 2, 'preview_comments': [], 'can_view_more_preview_comments': False, 'comment_count': 0, 'inline_composer_display_condition': 'impression_trigger', 'like_count': 0, 'has_liked': False, 'top_likers': [], 'likers': [], 'boosted_status': 'not_boosted', 'photo_of_you': False, 'caption': {'pk': 17871931531407904, 'user_id': 12672764795, 'text': 'Ofrendas.', 'type': 1, 'created_at': 1562428433, 'created_at_utc': 1562428433, 'content_type': 'comment', 'status': 'Active', 'bit_flags': 0, 'user': {'pk': 12672764795, 'username': 'a_veces_una_foto', 'full_name': 'F.T.G.', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/768d122416ae68494a583e465c40b20a/5DBCEECF/t51.2885-19/s150x150/56468365_1250869771754902_8896379520727121920_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2025650010676586856_12672764795', 'is_verified': False, 'has_anonymous_profile_picture': False, 'can_boost_post': True, 'can_see_organic_insights': True, 'show_insights_terms': False, 'reel_auto_archive': 'unset', 'is_unpublished': False, 'allowed_commenter_type': 'any'}, 'did_report_as_spam': False, 'share_enabled': False, 'media_id': 2082123057266525086, 'has_translation': True}, 'fb_user_tags': {'in': []}, 'can_viewer_save': True, 'organic_tracking_token': 'eyJ2ZXJzaW9uIjo1LCJwYXlsb2FkIjp7ImlzX2FuYWx5dGljc190cmFja2VkIjp0cnVlLCJ1dWlkIjoiODJlYTMyODkyZDAxNGUwNGI5Mzk2NDRhNTVkOTdiMmIyMDgyMTIzMDU3MjY2NTI1MDg2Iiwic2VydmVyX3Rva2VuIjoiMTU2MjQ5MTQwNTAzNnwyMDgyMTIzMDU3MjY2NTI1MDg2fDEyNjcyNzY0Nzk1fDM2NjY0NmNmYzg1M2MxNzM1NzY1NjcwMjE2MDJmNWMxZDQwNGE5OTUyOGQ2ODRiOGRjOGYzOGQ3N2Y2MDA1MTkifSwic2lnbmF0dXJlIjoiIn0='}, {'taken_at': 1561921440, 'pk': 2077870106705491976, 'id': '2077870106705491976_12672764795', 'device_timestamp': 1561921440, 'media_type': 1, 'code': 'BzWE9pflXgI', 'client_cache_key': 'MjA3Nzg3MDEwNjcwNTQ5MTk3Ng==.2', 'filter_type': 0, 'image_versions2': {'candidates': [{'width': 640, 'height': 640, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/3417293402d4e57eb070d374c6b02b0d/5DA143BA/t51.2885-15/e15/s640x640/65532562_155703535557128_8570779992059927833_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=108&ig_cache_key=MjA3Nzg3MDEwNjcwNTQ5MTk3Ng%3D%3D.2', 'estimated_scans_sizes': [11021, 22042, 33063, 44084, 55106, 99191, 99191, 99191, 99191]}, {'width': 240, 'height': 240, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/4d0fa5127a0f07e8ac3f4dbd3d47f239/5DBD986F/t51.2885-15/e15/s240x240/65532562_155703535557128_8570779992059927833_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=108&ig_cache_key=MjA3Nzg3MDEwNjcwNTQ5MTk3Ng%3D%3D.2', 'estimated_scans_sizes': [2002, 4005, 6008, 8011, 10013, 18025, 18025, 18025, 18025]}]}, 'original_width': 720, 'original_height': 720, 'user': {'pk': 12672764795, 'username': 'a_veces_una_foto', 'full_name': 'F.T.G.', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/768d122416ae68494a583e465c40b20a/5DBCEECF/t51.2885-19/s150x150/56468365_1250869771754902_8896379520727121920_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2025650010676586856_12672764795', 'is_verified': False, 'has_anonymous_profile_picture': False, 'can_boost_post': True, 'can_see_organic_insights': True, 'show_insights_terms': False, 'reel_auto_archive': 'unset', 'is_unpublished': False, 'allowed_commenter_type': 'any'}, 'can_viewer_reshare': True, 'caption_is_edited': True, 'direct_reply_to_author_enabled': True, 'comment_likes_enabled': True, 'comment_threading_enabled': False, 'has_more_comments': False, 'max_num_visible_preview_comments': 2, 'preview_comments': [], 'can_view_more_preview_comments': False, 'comment_count': 0, 'inline_composer_display_condition': 'impression_trigger', 'like_count': 1, 'has_liked': False, 'top_likers': [], 'likers': [{'pk': 5819836541, 'username': 'angelus063107', 'full_name': '🔥El Galego🔥', 'is_private': True, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/55c196a39ffd3340c23275fd43186d4a/5DA1BF7E/t51.2885-19/s150x150/61157096_399979887257767_5441405495933927424_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2032865388825647487_5819836541', 'is_verified': False}], 'boosted_status': 'not_boosted', 'photo_of_you': False, 'caption': {'pk': 18012095632214766, 'user_id': 12672764795, 'text': 'Flores mojadas. https://buff.ly/2KL3dTX', 'type': 1, 'created_at': 1561921442, 'created_at_utc': 1561921442, 'content_type': 'comment', 'status': 'Active', 'bit_flags': 0, 'user': {'pk': 12672764795, 'username': 'a_veces_una_foto', 'full_name': 'F.T.G.', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/768d122416ae68494a583e465c40b20a/5DBCEECF/t51.2885-19/s150x150/56468365_1250869771754902_8896379520727121920_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2025650010676586856_12672764795', 'is_verified': False, 'has_anonymous_profile_picture': False, 'can_boost_post': True, 'can_see_organic_insights': True, 'show_insights_terms': False, 'reel_auto_archive': 'unset', 'is_unpublished': False, 'allowed_commenter_type': 'any'}, 'did_report_as_spam': False, 'share_enabled': False, 'media_id': 2077870106705491976, 'has_translation': True}, 'fb_user_tags': {'in': []}, 'can_viewer_save': True, 'organic_tracking_token': 'eyJ2ZXJzaW9uIjo1LCJwYXlsb2FkIjp7ImlzX2FuYWx5dGljc190cmFja2VkIjp0cnVlLCJ1dWlkIjoiODJlYTMyODkyZDAxNGUwNGI5Mzk2NDRhNTVkOTdiMmIyMDc3ODcwMTA2NzA1NDkxOTc2Iiwic2VydmVyX3Rva2VuIjoiMTU2MjQ5MTQwNTAzNnwyMDc3ODcwMTA2NzA1NDkxOTc2fDEyNjcyNzY0Nzk1fDA4MTk5ZDc5ZjU2NmFkYTkwYWRhMGQ0YzcxZTc4Mzc1M2QwM2VlOWNhNWVhZTM1NDRkMWY3MjllMjRjODM3ZjkifSwic2lnbmF0dXJlIjoiIn0='}, {'taken_at': 1555697948, 'pk': 2025663669553390805, 'id': '2025663669553390805_12672764795', 'device_timestamp': 26734064650626, 'media_type': 1, 'code': 'BwcmmACJOTV', 'client_cache_key': 'MjAyNTY2MzY2OTU1MzM5MDgwNQ==.2', 'filter_type': 0, 'image_versions2': {'candidates': [{'width': 780, 'height': 780, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/fb79ed5311b594757f39c49d3668af37/5DAF316C/t51.2885-15/e35/57620821_354625455260027_4280075324714396356_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=111&ig_cache_key=MjAyNTY2MzY2OTU1MzM5MDgwNQ%3D%3D.2', 'estimated_scans_sizes': [4992, 9984, 14976, 19968, 24961, 30128, 36472, 40618, 44930]}, {'width': 240, 'height': 240, 'url': 'https://scontent-frx5-1.cdninstagram.com/vp/e91b171d2252912586ccf70aff8cb355/5DAAD064/t51.2885-15/e35/s240x240/57620821_354625455260027_4280075324714396356_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com&_nc_cat=111&ig_cache_key=MjAyNTY2MzY2OTU1MzM5MDgwNQ%3D%3D.2', 'estimated_scans_sizes': [1175, 2350, 3526, 4701, 5877, 7336, 94753, 10579, 10579]}]}, 'original_width': 780, 'original_height': 780, 'user': {'pk': 12672764795, 'username': 'a_veces_una_foto', 'full_name': 'F.T.G.', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/768d122416ae68494a583e465c40b20a/5DBCEECF/t51.2885-19/s150x150/56468365_1250869771754902_8896379520727121920_n.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '2025650010676586856_12672764795', 'is_verified': False, 'has_anonymous_profile_picture': False, 'can_boost_post': True, 'can_see_organic_insights': True, 'show_insights_terms': False, 'reel_auto_archive': 'unset', 'is_unpublished': False, 'allowed_commenter_type': 'any'}, 'can_viewer_reshare': True, 'caption_is_edited': False, 'direct_reply_to_author_enabled': True, 'comment_likes_enabled': True, 'comment_threading_enabled': False, 'has_more_comments': False, 'max_num_visible_preview_comments': 2, 'preview_comments': [], 'can_view_more_preview_comments': False, 'comment_count': 0, 'inline_composer_display_condition': 'impression_trigger', 'like_count': 2, 'has_liked': False, 'top_likers': ['auroraiba'], 'facepile_top_likers': [{'pk': 369583931, 'username': 'auroraiba', 'full_name': 'Aurora', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/6e5dcd255003a3bc6b16d27afd67b1aa/5DB02FDC/t51.2885-19/s150x150/19955643_150801798822503_3926231992722522112_a.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '1557151439871921499_369583931', 'is_verified': False}], 'likers': [{'pk': 369583931, 'username': 'auroraiba', 'full_name': 'Aurora', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/6e5dcd255003a3bc6b16d27afd67b1aa/5DB02FDC/t51.2885-19/s150x150/19955643_150801798822503_3926231992722522112_a.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '1557151439871921499_369583931', 'is_verified': False}, {'pk': 1425217066, 'username': 'pasapues0', 'full_name': 'Javier Mendivil', 'is_private': False, 'profile_pic_url': 'https://scontent-frx5-1.cdninstagram.com/vp/b734360ae0d7f684355df7d33e5ab583/5DC3C7CC/t51.2885-19/s150x150/13658309_1180108078714415_987875949_a.jpg?_nc_ht=scontent-frx5-1.cdninstagram.com', 'profile_pic_id': '1290588688790767711_1425217066', 'is_verified': False}], 'boosted_status': 'not_boosted', 'photo_of_you': False, 'caption': None, 'fb_user_tags': {'in': []}, 'can_viewer_save': True, 'organic_tracking_token': 'eyJ2ZXJzaW9uIjo1LCJwYXlsb2FkIjp7ImlzX2FuYWx5dGljc190cmFja2VkIjp0cnVlLCJ1dWlkIjoiODJlYTMyODkyZDAxNGUwNGI5Mzk2NDRhNTVkOTdiMmIyMDI1NjYzNjY5NTUzMzkwODA1Iiwic2VydmVyX3Rva2VuIjoiMTU2MjQ5MTQwNTAzNnwyMDI1NjYzNjY5NTUzMzkwODA1fDEyNjcyNzY0Nzk1fDNjMGRiZjMwOGYyMmI1N2FmMTcwZTJkMWUzOTRlZmFhMjdlZDA0MDUxNDYyNzk0NmYzZDMyZjJhNjVlNzE2MmIifSwic2lnbmF0dXJlIjoiIn0='}], 'num_results': 3, 'more_available': False, 'auto_load_more_enabled': True, 'status': 'ok'}
"""
