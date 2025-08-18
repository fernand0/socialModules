#!/usr/bin/env python

import logging
import os
import sys

import mastodon
from bs4 import BeautifulSoup

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

# pip install Mastodon.py



class moduleMastodon(Content): #, Queue):

    def getKeys(self, config):
        #if self.user.startswith('@'):
        #    self.user = self.user[1:]

        access_token = config[self.user]['access_token']
        return ((access_token, ))

    def initApi(self, keys):
        pos = self.user.find('@',1) # The first character can be @
        if pos > 0:
            self.base_url = f"https://{self.user[pos:]}"
            #self.user = self.user[:pos]
        else:
            self.base_url = 'https://mastodon.social'

        client = mastodon.Mastodon(access_token=keys[0],
                                   api_base_url=self.base_url)
        return client

    def setApiPosts(self):
        posts = []
        if self.getClient():
            try:
                posts = self.getClient().account_statuses(self.getClient().me())
            except:
                posts = []
        return posts

    def setApiFavs(self):
        posts = []
        if self.getClient():
            try:
                posts = self.getClient().favourites()
            except:
                posts = []
        return posts

    def processReply(self, reply):
        res = ''
        if reply:
            res = f"{self.getAttribute(reply, 'uri')}"
        return res

    def publishApiImage(self, *args, **kwargs):
        post, image = args
        more = kwargs

        res = 'Fail!'
        try:
            logging.info(f"{self.indent} First, the image")
            res = self.getClient().media_post(image, "image/png")
            self.lastRes = res
            logging.info(f"{self.indent} res {res}")
            logging.info(f"{self.indent} Now the post")
            res = self.getClient().status_post(post, media_ids = res['id'])
            self.lastRes = res
        except:
            res = self.getClient().status_post(post+" "+link,
                    visibility='private')
        print(f"res: {res}")
        return res

    def publishApiPost(self, *args, **kwargs):
        title = ''
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        comment = ''
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)

        post = self.addComment(title, comment)

        res = 'Fail!'
        try:
            res = self.getClient().toot(post+" "+link)
        except mastodon.errors.MastodonServiceUnavailableError:
            res = self.report(self.getService(), kwargs, 'Not available',
                              sys.exc_info())
            res = f"Fail! {res}"
        except:
            res = self.report(self.getService(), kwargs, '', sys.exc_info())
            res = f"Fail! {res}"
# else:
        #     res = self.getClient().status_post(post+" "+link,
        #             visibility='private')
        #     # 'direct' 'private' 'unlisted' 'public'

        return res

    def deleteApiPosts(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        try:
            result = self.getClient().status_delete(idPost)
        except:
            result = self.report(self.service, '', '', sys.exc_info())
        logging.info(f"Res: {result}")
        return(result)

    def deleteApiFavs(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        try:
            result = self.client.status_unfavourite(idPost)
        except:
            result = self.report(self.service, '', '', sys.exc_info())
        logging.info(f"Res: {result}")
        return(result)

    def getPostTime(self, post):
        time = None
        if post:
            time = post.get('created_at', None)
        return time

    def getPostId(self, post):
        if isinstance(post, str):
            idPost = post
        else:
            idPost = self.getAttribute(post, 'id')
        return idPost

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getSiteTitle(self):
        title = ''
        if self.user:
            title = f"{self.user}'s {self.service}"
        return title

    def getPostTitle(self, post):
        result = ''
        # import pprint
        # print(f"post: {post}")
        # pprint.pprint(post)
        card = post.get('card', '')
        if card:
            result = f"{card.get('title')} {card.get('url')}"

        if not result:
            result = post.get('content', '')
        if not result:
            result = post.get('text', '')
        # soup = BeautifulSoup(result, 'lxml')
        if result.startswith('<'):
            result = result[3:]
        if result.endswith('>'):
            result = result[:-4]
        # print(f"RRRRResult: {result}")
        pos = result.find('<')
        posH = result.find('http')
        posF = result.find('"',posH+1)
        result = f"{result[:pos]} {result[posH:posF]}"

        # if 'card' in post and post['card'] and 'title' in post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        # elif 'content' in post:
        #     result = self.getAttribute(post, 'content').replace('\n', ' ')
        # elif 'card' in post and post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        return result

    def getPostUrl(self, post):
        return self.getAttribute(post, 'url')

    def getPostLink(self, post):
        if self.getPostsType() == 'favs':
            content, link = self.extractPostLinks(post)
        else:
            link = self.getPostUrl(post)
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = ''
        if post and 'content' in post:
            result = self.getAttribute(post, 'content')
        return result

    def getPostContentLink(self, post):
        link = ''
        if ('card' in post) and post['card']:
            link = self.getAttribute(post['card'], 'url')
        else:
            soup = BeautifulSoup(post['content'], 'lxml')
            link = soup.a
            if link:
                link = link['href']
            else:
                link = self.getAttribute(post, 'uri')
        return link

    # def extractDataMessage(self, i):
    #     logging.info(f"Service {self.service}")
    #     (theTitle, theLink, firstLink, theImage, theSummary,
    #      content, theSummaryLinks, theContent, theLinks, comment) = (
    #                     None, None, None, None, None,
    #                     None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         post = self.getPost(i)
    #         theTitle = self.getPostTitle(post)
    #         theLink = self.getPostUrl(post)
    #         firstLink = self.getPostContentLink(post)
    #         theId = self.getPostId(post)

    #         theLinks = [firstLink, ]
    #         content = None
    #         theContent = None
    #         if 'card' in post and post['card']:
    #             theContent = self.getAttribute(post['card'], 'description')

    #         theImage = None
    #         theSummary = None

    #         theSummaryLinks = None
    #         comment = theId

    #     return (theTitle, theLink, firstLink, theImage, theSummary,
    #             content, theSummaryLinks, theContent, theLinks, comment)

    def search(self, text):
        pass


def main():
    """
    Main function for testing moduleMastodon functionality.
    Provides interactive testing capabilities for various Mastodon operations.
    """

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    name = nameModule()
    rulesList = rules.selectRule(name, '@fernand0', 'favs')

    print("Available Mastodon rules:")
    for i, rule in enumerate(rulesList):
        print(f"{i}) {rule}")

    if not rulesList:
        print("No Mastodon rules found. Please configure Mastodon in your rules.")
        return

    # Select rule
    try:
        sel = int(input(f"Which rule to use? (0-{len(rulesList)-1}): "))
        if sel < 0 or sel >= len(rulesList):
            print("Invalid selection")
            return
        key = rulesList[sel]
    except (ValueError, IndexError):
        print("Invalid input, using first rule")
        key = rulesList[0]

    print(f"Selected rule: {key}")

    # Initialize Mastodon module
    try:
        apiSrc = rules.readConfigSrc("", key, None)
        print(f"Mastodon client initialized for: {apiSrc.user}")
        print(f"Server: {getattr(apiSrc, 'server', 'Unknown')}")
    except Exception as e:
        print(f"Error initializing Mastodon: {e}")
        return

    # Test scenarios - interactive menu

    testingConnection = False
    if testingConnection:
        print("\n=== Testing Mastodon Connection ===")
        try:
            client = apiSrc.getClient()
            if client:
                me = client.me()
                print(f"✓ Connected as: {me.get('display_name', 'Unknown')} (@{me.get('username', 'unknown')})")
                print(f"  Account ID: {me.get('id')}")
                print(f"  Followers: {me.get('followers_count', 0)}")
                print(f"  Following: {me.get('following_count', 0)}")
                print(f"  Posts: {me.get('statuses_count', 0)}")
            else:
                print("✗ No Mastodon client available")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
        return

    testingPosts = False
    if testingPosts:
        print("\n=== Testing Posts Retrieval ===")
        try:
            apiSrc.setPosts()
            posts = apiSrc.getPosts()

            if posts:
                print(f"Retrieved {len(posts)} posts:")
                for i, post in enumerate(posts[:5]):  # Show first 5
                    title = apiSrc.getPostTitle(post)
                    link = apiSrc.getPostLink(post)
                    url = apiSrc.getPostUrl(post)
                    post_id = apiSrc.getPostId(post)

                    print(f"\n{i+1}. Post ID: {post_id}")
                    print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                    print(f"   Link: {link}")
                    print(f"   URL: {url}")

                if len(posts) > 5:
                    print(f"\n... and {len(posts) - 5} more posts")
            else:
                print("No posts found")
        except Exception as e:
            print(f"Error retrieving posts: {e}")
        return

    testingFavorites = False
    if testingFavorites:
        print("\n=== Testing Favorites ===")
        try:
            # Set posts type to favorites
            apiSrc.setPostsType('favs')
            apiSrc.setPosts()
            favs = apiSrc.getPosts()

            if favs:
                print(f"Retrieved {len(favs)} favorites:")
                for i, fav in enumerate(favs[:3]):  # Show first 3
                    title = apiSrc.getPostTitle(fav)
                    link = apiSrc.getPostLink(fav)
                    content_link = apiSrc.getPostContentLink(fav)

                    print(f"\n{i+1}. Favorite:")
                    print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                    print(f"   Link: {link}")
                    print(f"   Content Link: {content_link}")
                    print(f"   Extract Links: {apiSrc.extractPostLinks(fav)}")

                if len(favs) > 3:
                    print(f"\n... and {len(favs) - 3} more favorites")
            else:
                print("No favorites found")
        except Exception as e:
            print(f"Error retrieving favorites: {e}")
        return

    testingBasicPost = False
    if testingBasicPost:
        print("\n=== Testing Basic Post ===")
        title = "Test post from moduleMastodon"
        link = "https://example.com/test"

        print(f"Posting toot:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")

        try:
            result = apiSrc.publishPost(title, link, '')
            print(f"Post result: {result}")

            if result and not str(result).startswith("Fail"):
                post_id = apiSrc.getUrlId(str(result)) if hasattr(mastodon, 'getUrlId') else None
                if post_id:
                    print(f"Post ID: {post_id}")

                    delete_choice = input("Delete this post? (y/N): ").lower()
                    if delete_choice == 'y':
                        delete_result = apiSrc.deleteApiPosts(post_id)
                        print(f"Delete result: {delete_result}")
        except Exception as e:
            print(f"Error posting: {e}")
        return

    testingImagePost = False
    if testingImagePost:
        print("\n=== Testing Image Post ===")

        # Ask for image path
        image_path = input("Enter image path (or press Enter for default): ").strip()
        if not image_path:
            image_path = '/tmp/test_image.png'

        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            print("Skipping image test")
            return

        title = "Test image post"
        alt_text = "Test image from moduleMastodon"

        print(f"Posting image:")
        print(f"  Image: {image_path}")
        print(f"  Title: {title}")
        print(f"  Alt text: {alt_text}")

        try:
            if hasattr(mastodon, 'publishImage'):
                result = apiSrc.publishImage(title, image_path, alt=alt_text)
                print(f"Image post result: {result}")

                if result and not str(result).startswith("Fail"):
                    post_id = apiSrc.getUrlId(str(result)) if hasattr(mastodon, 'getUrlId') else None
                    if post_id:
                        print(f"Post ID: {post_id}")

                        delete_choice = input("Delete this post? (y/N): ").lower()
                        if delete_choice == 'y':
                            delete_result = apiSrc.deleteApiPosts(post_id)
                            print(f"Delete result: {delete_result}")
            else:
                print("publishImage method not available")
        except Exception as e:
            print(f"Error posting image: {e}")
        return

    testingCacheIntegration = False
    if testingCacheIntegration:
        print("\n=== Testing Cache Integration ===")

        # Enable auto-cache
        apiSrc.setAutoCache(True)
        print(f"Auto-cache enabled: {apiSrc.getAutoCache()}")

        # Post with caching
        title = "Cache integration test"
        link = "https://example.com/cache-test"

        print("Posting toot with auto-cache enabled...")
        try:
            result = apiSrc.publishPost(title, link, '')
            print(f"Post result: {result}")

            # Check cache
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            mastodon_pubs = cache.get_publications_by_service("mastodon")
            print(f"Mastodon publications in cache: {len(mastodon_pubs)}")

            if mastodon_pubs:
                latest = mastodon_pubs[-1]
                print(f"Latest cached publication:")
                print(f"  Title: {latest['title']}")
                print(f"  Link: {latest['original_link']}")
                print(f"  Service: {latest['service']}")
                print(f"  Response Link: {latest.get('response_link', 'None')}")
                print(f"  Date: {latest['publication_date']}")
        except Exception as e:
            print(f"Error in cache integration test: {e}")
        return

    testingDeletion = False
    if testingDeletion:
        print("\n=== Testing Post Deletion ===")

        post_id = input("Enter post ID to delete: ").strip()
        if not post_id:
            print("No post ID provided")
            return

        confirm = input(f"Are you sure you want to delete post {post_id}? (y/N): ").lower()
        if confirm != 'y':
            print("Deletion cancelled")
            return

        try:
            result = apiSrc.deleteApiPosts(post_id)
            print(f"Deletion result: {result}")
        except Exception as e:
            print(f"Error deleting post: {e}")
        return

    testingFavoritesManagement = False
    if testingFavoritesManagement:
        print("\n=== Testing Favorites Management ===")

        post_id = input("Enter post ID to unfavorite: ").strip()
        if not post_id:
            print("No post ID provided")
            return

        try:
            if hasattr(mastodon, 'deleteApiFavs'):
                result = apiSrc.deleteApiFavs(post_id)
                print(f"Unfavorite result: {result}")
            else:
                print("deleteApiFavs method not available")
        except Exception as e:
            print(f"Error managing favorite: {e}")
        return

    testingCacheContent = False
    if testingCacheContent:
        print("\n=== Testing Cache Content ===")
        try:
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            
            service = input("Enter service to check (default: mastodon): ").strip().lower()
            if not service:
                service = "mastodon"

            service_pubs = cache.get_publications_by_service(service)
            print(f"\nFound {len(service_pubs)} publications for service '{service}':")

            if service_pubs:
                for i, pub in enumerate(service_pubs):
                    print(f"\n--- Publication {i+1}/{len(service_pubs)} ---")
                    print(f"  ID: {pub.get('id')}")
                    print(f"  Title: {pub.get('title')}")
                    print(f"  Original Link: {pub.get('original_link')}")
                    print(f"  Service: {pub.get('service')}")
                    print(f"  Response Link: {pub.get('response_link', 'None')}")
                    print(f"  Date: {pub.get('publication_date')}")
                    print(f"  Metadata: {pub.get('metadata')}")
            else:
                print("No publications found for this service.")

        except Exception as e:
            print(f"Error checking cache content: {e}")
        return

    # Interactive testing mode (default)
    testingInteractive = True
    if testingInteractive:
        print("\n=== Interactive Mastodon Testing ===")
        print("Available test modes:")
        print("1. Connection test")
        print("2. Posts retrieval test")
        print("3. Favorites test")
        print("4. Basic post test")
        print("5. Image post test")
        print("6. Cache integration test")
        print("7. Post deletion test")
        print("8. Favorites management test")
        print("9. Custom post")
        print("10. Browse posts")
        print("11. Cache content verification")

        try:
            choice = int(input("Select test mode (1-11): "))

            if choice == 1:
                testingConnection = True
            elif choice == 2:
                testingPosts = True
            elif choice == 3:
                testingFavorites = True
            elif choice == 4:
                testingBasicPost = True
            elif choice == 5:
                testingImagePost = True
            elif choice == 6:
                testingCacheIntegration = True
            elif choice == 7:
                testingDeletion = True
            elif choice == 8:
                testingFavoritesManagement = True
            elif choice == 9:
                print("\n=== Custom Post ===")
                title = input("Post content: ").strip() or "Custom test post"
                link = input("Link (optional): ").strip()

                # Ask about cache
                cache_choice = input("Enable auto-cache? (y/N): ").lower()
                if cache_choice == 'y':
                    apiSrc.setAutoCache(True)
                    print("Auto-cache enabled")

                print(f"\nPosting custom toot:")
                print(f"  Content: {title}")
                if link:
                    print(f"  Link: {link}")

                try:
                    result = apiSrc.publishPost(title, link, '')
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Error: {e}")
            elif choice == 10:
                print("\n=== Browse Posts ===")
                try:
                    apiSrc.setPosts()
                    posts = apiSrc.getPosts()

                    if posts:
                        print(f"Found {len(posts)} posts. Browsing...")
                        for i, post in enumerate(posts):
                            title = apiSrc.getPostTitle(post)
                            link = apiSrc.getPostLink(post)
                            url = apiSrc.getPostUrl(post)
                            post_id = apiSrc.getPostId(post)

                            print(f"\n--- Post {i+1}/{len(posts)} ---")
                            print(f"ID: {post_id}")
                            print(f"Title: {title}")
                            print(f"Link: {link}")
                            print(f"URL: {url}")

                            if i < len(posts) - 1:
                                cont = input("Continue? (y/N/q to quit): ").lower()
                                if cont == 'q':
                                    break
                                elif cont != 'y':
                                    break
                    else:
                        print("No posts found")
                except Exception as e:
                    print(f"Error browsing posts: {e}")
            elif choice == 11:
                testingCacheContent = True
            else:
                print("Invalid choice")
                return

        except ValueError:
            print("Invalid input")
            return
        except KeyboardInterrupt:
            print("\nTest cancelled by user")
            return

    # Re-run the selected test
    if testingConnection:
        print("\n=== Testing Mastodon Connection ===")
        try:
            client = apiSrc.getClient()
            if client:
                me = client.me()
                print(f"✓ Connected as: {me.get('display_name', 'Unknown')} (@{me.get('username', 'unknown')})")
                print(f"  Account ID: {me.get('id')}")
                print(f"  Followers: {me.get('followers_count', 0)}")
                print(f"  Following: {me.get('following_count', 0)}")
                print(f"  Posts: {me.get('statuses_count', 0)}")
            else:
                print("✗ No Mastodon client available")
        except Exception as e:
            print(f"✗ Connection failed: {e}")

    elif testingPosts:
        print("\n=== Testing Posts Retrieval ===")
        try:
            apiSrc.setPosts()
            posts = apiSrc.getPosts()

            if posts:
                print(f"Retrieved {len(posts)} posts:")
                for i, post in enumerate(posts[:5]):  # Show first 5
                    title = apiSrc.getPostTitle(post)
                    link = apiSrc.getPostLink(post)
                    url = apiSrc.getPostUrl(post)
                    post_id = apiSrc.getPostId(post)

                    print(f"\n{i+1}. Post ID: {post_id}")
                    print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                    print(f"   Link: {link}")
                    print(f"   URL: {url}")

                if len(posts) > 5:
                    print(f"\n... and {len(posts) - 5} more posts")
            else:
                print("No posts found")
        except Exception as e:
            print(f"Error retrieving posts: {e}")

    elif testingFavorites:
        print("\n=== Testing Favorites ===")
        try:
            # Set posts type to favorites
            apiSrc.setPostsType('favs')
            apiSrc.setPosts()
            favs = apiSrc.getPosts()

            if favs:
                print(f"Retrieved {len(favs)} favorites:")
                for i, fav in enumerate(favs[:3]):  # Show first 3
                    title = apiSrc.getPostTitle(fav)
                    link = apiSrc.getPostLink(fav)
                    content_link = apiSrc.getPostContentLink(fav)

                    print(f"\n{i+1}. Favorite:")
                    print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                    print(f"   Link: {link}")
                    print(f"   Content Link: {content_link}")
                    print(f"   Extract Links: {apiSrc.extractPostLinks(fav)}")

                if len(favs) > 3:
                    print(f"\n... and {len(favs) - 3} more favorites")
            else:
                print("No favorites found")
        except Exception as e:
            print(f"Error retrieving favorites: {e}")

    elif testingBasicPost:
        print("\n=== Testing Basic Post ===")
        title = "Test post from moduleMastodon"
        link = "https://example.com/test"

        print(f"Posting toot:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")

        try:
            result = apiSrc.publishPost(title, link, '')
            print(f"Post result: {result}")

            if result and not str(result).startswith("Fail"):
                post_id = apiSrc.getUrlId(str(result)) if hasattr(mastodon, 'getUrlId') else None
                if post_id:
                    print(f"Post ID: {post_id}")

                    delete_choice = input("Delete this post? (y/N): ").lower()
                    if delete_choice == 'y':
                        delete_result = apiSrc.deleteApiPosts(post_id)
                        print(f"Delete result: {delete_result}")
        except Exception as e:
            print(f"Error posting: {e}")

    elif testingImagePost:
        print("\n=== Testing Image Post ===")

        # Ask for image path
        image_path = input("Enter image path (or press Enter to skip): ").strip()
        if not image_path:
            print("No image path provided, skipping image test")
            return

        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return

        title = "Test image post"
        alt_text = "Test image from moduleMastodon"

        print(f"Posting image:")
        print(f"  Image: {image_path}")
        print(f"  Title: {title}")
        print(f"  Alt text: {alt_text}")

        try:
            if hasattr(mastodon, 'publishImage'):
                result = apiSrc.publishImage(title, image_path, alt=alt_text)
                print(f"Image post result: {result}")

                if result and not str(result).startswith("Fail"):
                    post_id = apiSrc.getUrlId(str(result)) if hasattr(mastodon, 'getUrlId') else None
                    if post_id:
                        print(f"Post ID: {post_id}")

                        delete_choice = input("Delete this post? (y/N): ").lower()
                        if delete_choice == 'y':
                            delete_result = apiSrc.deleteApiPosts(post_id)
                            print(f"Delete result: {delete_result}")
            else:
                print("publishImage method not available")
        except Exception as e:
            print(f"Error posting image: {e}")

    elif testingCacheIntegration:
        print("\n=== Testing Cache Integration ===")

        # Enable auto-cache
        apiSrc.setAutoCache(True)
        print(f"Auto-cache enabled: {apiSrc.getAutoCache()}")

        # Post with caching
        title = "Cache integration test"
        link = "https://example.com/cache-test"

        print("Posting toot with auto-cache enabled...")
        try:
            result = apiSrc.publishPost(title, link, '')
            print(f"Post result: {result}")

            # Check cache
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            mastodon_pubs = cache.get_publications_by_service("mastodon")
            print(f"Mastodon publications in cache: {len(mastodon_pubs)}")

            if mastodon_pubs:
                latest = mastodon_pubs[-1]
                print(f"Latest cached publication:")
                print(f"  Title: {latest['title']}")
                print(f"  Link: {latest['original_link']}")
                print(f"  Service: {latest['service']}")
                print(f"  Response Link: {latest.get('response_link', 'None')}")
                print(f"  Date: {latest['publication_date']}")
        except Exception as e:
            print(f"Error in cache integration test: {e}")

    elif testingDeletion:
        print("\n=== Testing Post Deletion ===")

        post_id = input("Enter post ID to delete: ").strip()
        if not post_id:
            print("No post ID provided")
            return

        confirm = input(f"Are you sure you want to delete post {post_id}? (y/N): ").lower()
        if confirm != 'y':
            print("Deletion cancelled")
            return

        try:
            result = apiSrc.deleteApiPosts(post_id)
            print(f"Deletion result: {result}")
        except Exception as e:
            print(f"Error deleting post: {e}")

    elif testingFavoritesManagement:
        print("\n=== Testing Favorites Management ===")

        post_id = input("Enter post ID to unfavorite: ").strip()
        if not post_id:
            print("No post ID provided")
            return

        try:
            if hasattr(mastodon, 'deleteApiFavs'):
                result = apiSrc.deleteApiFavs(post_id)
                print(f"Unfavorite result: {result}")
            else:
                print("deleteApiFavs method not available")
        except Exception as e:
            print(f"Error managing favorite: {e}")
        # mastodon.deletePost(post)

    elif testingCacheContent:
        print("\n=== Testing Cache Content ===")
        try:
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            
            service = input("Enter service to check (default: mastodon): ").strip().lower()
            if not service:
                service = "mastodon"

            service_pubs = cache.get_publications_by_service(service)
            print(f"\nFound {len(service_pubs)} publications for service '{service}':")

            if service_pubs:
                for i, pub in enumerate(service_pubs):
                    print(f"\n--- Publication {i+1}/{len(service_pubs)} ---")
                    print(f"  ID: {pub.get('id')}")
                    print(f"  Title: {pub.get('title')}")
                    print(f"  Original Link: {pub.get('original_link')}")
                    print(f"  Service: {pub.get('service')}")
                    print(f"  Response Link: {pub.get('response_link', 'None')}")
                    print(f"  Date: {pub.get('publication_date')}")
                    print(f"  Metadata: {pub.get('metadata')}")
            else:
                print("No publications found for this service.")

        except Exception as e:
            print(f"Error checking cache content: {e}")


    return

    print("Testing title and link")

    print("Posts")

    for post in apiSrc.getPosts():
        title = apiSrc.getPostTitle(post)
        link = apiSrc.getPostLink(post)
        print(f"Title: {title}\nLink: {link}\n")

    print("Favs")

    for i, post in enumerate(apiSrc.getPosts()):
        print("i", i)
        print("1", post)
        print("2", apiSrc.getPost(i))
        title = apiSrc.getPostTitle(post)
        link = apiSrc.getPostLink(post)
        print(f"Title: {title}\nLink: {link}\n")
        print(apiSrc.extractDataMessage(i))

    sys.exit()
    (theTitle, theLink, firstLink, theImage, theSummary, content,
     theSummaryLinks, theContent, theLinks, comment) \
             = apiSrc.extractDataMessage(0)

    # config = configparser.ConfigParser()
    # config.read(CONFIGDIR + '/.rssBlogs')

    # import modulePocket
    #
    # p = modulePocket.modulePocket()

    # p.setClient('fernand0')
    # p.publishPost(theTitle, firstLink, '')

    apiSrc.publishPost("I'll publish several links each day about "
                         "technology, social internet, security, ... "
                         " as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
