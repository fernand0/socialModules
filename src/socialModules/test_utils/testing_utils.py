# testing/testing_utils.py
import os


def test_connection(apiSrc, get_user_info_callback):
    """
    Tests the connection to the social media platform.

    Args:
        apiSrc: The API source object for the module.
        get_user_info_callback: A function that takes the API client and returns a string with the user information.
    """
    print("\n=== Testing Connection ===")
    try:
        client = apiSrc.getClient()
        if client:
            user_info = get_user_info_callback(apiSrc)
            print(f"✓ Connected as: {user_info}")
        else:
            print("✗ No client available")
    except Exception as e:
        print(f"✗ Connection failed: {e}")

    print(f"Special: {apiSrc.special}")
    print(f"Special: {apiSrc.separator}")


def test_authorization(apiSrc):
    """
    Tests the authorization process for a module.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Authorization ===")
    try:
        if hasattr(apiSrc, 'authorize'):
            print("Calling authorize()...")
            apiSrc.authorize()
            print("authorize() finished.")
        else:
            print("authorize() method not found in API object.")
    except Exception as e:
        print(f"Error during authorization: {e}")


def test_authorization(apiSrc):
    """
    Tests the authorization process for a module.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Authorization ===")
    try:
        if hasattr(apiSrc, 'authorize'):
            print("Calling authorize()...")
            apiSrc.authorize()
            print("authorize() finished.")
        else:
            print("authorize() method not found in API object.")
    except Exception as e:
        print(f"Error during authorization: {e}")


def test_posts_retrieval(apiSrc):
    """
    Tests retrieving posts from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Posts Retrieval ===")
    try:
        apiSrc.setPostsType('posts')
        apiSrc.setPosts()
        posts = apiSrc.getPosts()

        if posts:
            print(f"Retrieved {len(posts)} posts:")
            for i, post in enumerate(posts[:10]):  # Show first 5
                title = apiSrc.getPostTitle(post)
                link = apiSrc.getPostLink(post)
                url = apiSrc.getPostUrl(post)
                #post_id = apiSrc.getPostId(post)

                #print(f"\n{i+1}. Post ID: {post_id}")
                print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                print(f"   Link: {link}")
                print(f"   URL: {url}")

            if len(posts) > 5:
                print(f"\n... and {len(posts) - 5} more posts")
        else:
            print("No posts found")
    except Exception as e:
        print(f"Error retrieving posts: {e}")


def test_drafts_retrieval(apiSrc):
    """
    Tests retrieving drafts from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Drafts Retrieval ===")
    try:
        apiSrc.setPostsType('drafts')
        apiSrc.setPosts()
        posts = apiSrc.getPosts()

        if posts:
            print(f"Retrieved {len(posts)} drafts:")
            for i, post in enumerate(posts[:10]):  # Show first 10
                title = apiSrc.getPostTitle(post)
                link = apiSrc.getPostLink(post)

                print(f"\n{i+1}. Draft:")
                print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                print(f"   Link: {link}")

            if len(posts) > 10:
                print(f"\n... and {len(posts) - 10} more drafts")
        else:
            print("No drafts found")
    except Exception as e:
        print(f"Error retrieving drafts: {e}")


def test_favorites(apiSrc):
    """
    Tests retrieving favorites from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Favorites ===")
    try:
        # Set posts type to favorites
        apiSrc.setPostsType("favs")
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

def test_queue_retrieval(apiSrc):
    """
    Tests retrieving queued posts from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Queue Retrieval ===")
    try:
        apiSrc.setPostsType('queue')
        apiSrc.setPosts()
        posts = apiSrc.getPosts()

        if posts:
            print(f"Retrieved {len(posts)} queued posts:")
            for i, post in enumerate(posts[:10]):  # Show first 10
                title = apiSrc.getPostTitle(post)
                link = apiSrc.getPostLink(post)

                print(f"\n{i+1}. Queued post:")
                print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                print(f"   Link: {link}")

            if len(posts) > 10:
                print(f"\n... and {len(posts) - 10} more queued posts")
        else:
            print("No queued posts found")
    except Exception as e:
        print(f"Error retrieving queued posts: {e}")



def test_basic_post(apiSrc, get_post_id_callback):
    """
    Tests posting a basic post to the social media platform.

    Args:
        apiSrc: The API source object for the module.
        get_post_id_callback: A function that takes the result of the post and returns the post ID.
    """
    print("\n=== Testing Basic Post ===")
    default_title = f"Test post from {apiSrc.getService()}"
    title = input(f"Enter title for the post (default: '{default_title}'): ").strip()
    if not title:
        title = default_title

    default_link = "https://github.com/fernand0/socialModules"
    link = input(f"Enter URL for the post (e.g., {default_link}): ").strip()
    if not link:
        link = default_link

    print(f"Posting to {apiSrc.getService()}:")
    print(f"  Title: {title}")
    print(f"  Link: {link}")

    try:
        result = apiSrc.publishPost(title, link, "")
        print(f"Post result: {result}")

        if result and not str(result).startswith("Fail"):
            post_id = get_post_id_callback(result)
            if post_id:
                print(f"Post ID: {post_id}")

                delete_choice = input("Delete this post? (y/N): ").lower()
                if delete_choice == "y":
                    delete_result = apiSrc.deleteApiPosts(post_id)
                    print(f"Delete result: {delete_result}")
    except Exception as e:
        print(f"Error posting: {e}")


def test_image_post(apiSrc, get_post_id_callback):
    """
    Tests posting an image to the social media platform.

    Args:
        apiSrc: The API source object for the module.
        get_post_id_callback: A function that takes the result of the post and returns the post ID.
    """
    print("\n=== Testing Image Post ===")
    # Ask for image path
    image_path = input("Enter image path (or press Enter for default): ").strip()
    if not image_path:
        image_path = "/tmp/test_image.png"

    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        print("Skipping image test")
        return

    title = f"Test image post from {apiSrc.getService()}"
    alt_text = f"Test image from {apiSrc.getService()}"

    print(f"Posting image to {apiSrc.getService()}:")
    print(f"  Image: {image_path}")
    print(f"  Title: {title}")
    print(f"  Alt text: {alt_text}")

    try:
        result = apiSrc.publishImage(title, image_path, alt=alt_text)
        print(f"Image post result: {result}")

        if result and not str(result).startswith("Fail"):
            post_id = get_post_id_callback(result)
            if post_id:
                print(f"Post ID: {post_id}")

                delete_choice = input("Delete this post? (y/N): ").lower()
                if delete_choice == "y":
                    delete_result = apiSrc.deleteApiPosts(post_id)
                    print(f"Delete result: {delete_result}")
    except Exception as e:
        print(f"Error posting image: {e}")


def test_cache_integration(apiSrc):
    """
    Tests the cache integration for the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Cache Integration ===")
    # Enable auto-cache
    apiSrc.setAutoCache(True)
    print(f"Auto-cache enabled: {apiSrc.getAutoCache()}")

    # Post with caching
    title = "Cache integration test"
    link = "https://example.com/cache-test"

    print(f"Posting to {apiSrc.getService()} with auto-cache enabled...")
    try:
        result = apiSrc.publishPost(title, link, "")
        print(f"Post result: {result}")

        # Check cache
        from socialModules.modulePublicationCache import PublicationCache

        cache = PublicationCache()
        pubs = cache.get_publications_by_service(apiSrc.getService().lower())
        print(f"{apiSrc.getService()} publications in cache: {len(pubs)}")

        if pubs:
            latest = pubs[-1]
            print(f"Latest cached publication:")
            print(f"  Title: {latest['title']}")
            print(f"  Link: {latest['original_link']}")
            print(f"  Service: {latest['service']}")
            print(f"  Response Link: {latest.get('response_link', 'None')}")
            print(f"  Date: {latest['publication_date']}")
    except Exception as e:
        print(f"Error in cache integration test: {e}")


def test_deletion(apiSrc):
    """
    Tests deleting a post from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Post Deletion ===")
    post_id = input("Enter post ID to delete: ").strip()
    if not post_id:
        print("No post ID provided")
        return

    confirm = input(f"Are you sure you want to delete post {post_id}? (y/N): ").lower()
    if confirm != "y":
        print("Deletion cancelled")
        return

    try:
        result = apiSrc.deleteApiPosts(post_id)
        print(f"Deletion result: {result}")
    except Exception as e:
        print(f"Error deleting post: {e}")


def test_favorites_management(apiSrc):
    """
    Tests unfavoriting a post from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Favorites Management ===")
    post_id = input("Enter post ID to unfavorite: ").strip()
    if not post_id:
        print("No post ID provided")
        return

    try:
        result = apiSrc.deleteApiFavs(post_id)
        print(f"Unfavorite result: {result}")
    except Exception as e:
        print(f"Error managing favorite: {e}")


def test_edit_post(apiSrc):
    """
    Tests editing a post's title on the social media platform by selecting from a list.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Post Editing ===")
    try:
        print("Fetching recent posts...")
        apiSrc.setPosts()
        posts = apiSrc.getPosts()

        if not posts:
            print("No posts found to edit.")
            return

        print("Select a post to edit:")
        for i, post in enumerate(posts[:10]):  # Show up to 10 posts
            title = apiSrc.getPostTitle(post)
            print(f"{i}) {title[:100]}{'...' if len(title) > 100 else ''}")

        choice = input(f"Enter the number of the post to edit (0-{len(posts[:10])-1}): ").strip()
        if not choice.isdigit() or not (0 <= int(choice) < len(posts[:10])):
            print("Invalid selection. Skipping post edit test.")
            return

        post_to_edit = posts[int(choice)]
        original_title = apiSrc.getPostTitle(post_to_edit)
        print(f"\nSelected post: '{original_title}'")

        new_title = input("Enter the new title for the post: ").strip()
        if not new_title:
            print("No new title provided. Skipping post edit test.")
            return

        print(f"Editing post with new title: '{new_title}'")
        result = apiSrc.editApiTitle(post_to_edit, new_title)
        print(f"Edit result: {result}")

        if result and not str(result).startswith("Fail"):
            print("Post title updated successfully.")
        else:
            print("Failed to update post title.")

    except Exception as e:
        print(f"Error editing post: {e}")

def test_cache_content(apiSrc):
    """
    Tests verifying the cache content for the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Cache Content ===")
    try:
        from socialModules.modulePublicationCache import PublicationCache

        cache = PublicationCache()

        service = (
            input(f"Enter service to check (default: {apiSrc.getService().lower()}): ")
            .strip()
            .lower()
        )
        if not service:
            service = apiSrc.getService().lower()

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
        else:
            print("No publications found for this service.")

    except Exception as e:
        print(f"Error checking cache content: {e}")


def test_select_post_by_position(apiSrc):
    """
    Tests selecting a specific post by its position from the social media platform.

    Args:
        apiSrc: The API source object for the module.
    """
    print("\n=== Testing Select Post by Position ===")
    try:
        apiSrc.setPostsType('posts')
        apiSrc.setPosts()
        posts = apiSrc.getPosts()

        if not posts:
            print("No posts found to select.")
            return

        print(f"Retrieved {len(posts)} posts. Select one by its number:")
        for i, post in enumerate(posts):
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            text = apiSrc.getPostContent(post)
            body = apiSrc.getPostBody(post)
            print(f"{i+1}. Title: {title[:100]}{'...' if len(title) > 100 else ''} (Link: {link})")

        try:
            choice = int(input(f"Enter the number of the post to view (1-{len(posts)}): "))
            if 1 <= choice <= len(posts):
                selected_post = posts[choice - 1]
                print(f"\n--- Details for Post {choice} ---")
                print(f"Title: {apiSrc.getPostTitle(selected_post)}")
                print(f"Link: {apiSrc.getPostLink(selected_post)}")
                print(f"URL: {apiSrc.getPostUrl(selected_post)}")
                print(f"Content: {apiSrc.getPostContent(selected_post)}")
                print(f"Body: {apiSrc.getPostBody(selected_post)}")
                # Add more details as needed, e.g., image, author, date
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    except Exception as e:
        print(f"Error selecting post by position: {e}")
