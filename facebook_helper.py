import re
import requests
import json
from uuid import uuid4

def post_to_facebook_group1(cookie, uid, fb_dtsg, to_id, message , av ):
    composer_session_id = str(uuid4())
    """
    Hàm gửi bài đăng đến Facebook group sử dụng GraphQL API
    
    Parameters:
    cookie (str): Chuỗi cookie từ request header
    uid (str): User ID của người đăng
    fb_dtsg (str): Facebook token từ form data
    to_id (str): ID của group đích
    message (str): Nội dung bài đăng
    
    Returns:
    dict: Response từ server
    """
    
    # URL endpoint
    url = "https://www.facebook.com/api/graphql/"
    
    # Headers cơ bản dựa trên thông tin bạn cung cấp
    headers = {
        "authority": "www.facebook.com",
        "accept": "*/*",
        "accept-language": "vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6,el;q=0.5",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": cookie,
        "origin": "https://www.facebook.com",
        "referer": f"https://www.facebook.com/groups/{to_id}/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-fb-friendly-name": "ComposerStoryCreateMutation",
    }
    
       
    # Tạo payload
    payload = {
        "av": av,
        "__user": uid,
        "__a": "1",
        "fb_dtsg": fb_dtsg,
        "lsd": "5bBHTrqyyeWweQII3dRFLY",  # Giá trị này có thể cần cập nhật
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "ComposerStoryCreateMutation",
        "variables": '{"input":{"composer_entry_point":"inline_composer","composer_source_surface":"group","composer_type":"group","logging":{"composer_session_id":"'+composer_session_id+'"},"source":"WWW","message":{"ranges":[],"text":"'+message+'"},"with_tags_ids":null,"inline_activities":[],"text_format_preset_id":"0","ask_admin_to_post_for_user":{"is_asking_admin_to_post":true},"navigation_data":{"attribution_id_v2":"CometGroupDiscussionRoot.react,comet.group,via_cold_start,1741330035102,198684,2361831622,,"},"tracking":[null],"event_share_metadata":{"surface":"newsfeed"},"audience":{"to_id":"'+to_id+'"},"actor_id":"'+av+'","client_mutation_id":"4"},"feedLocation":"GROUP","feedbackSource":0,"focusCommentID":null,"gridMediaWidth":null,"groupID":null,"scale":1,"privacySelectorRenderLocation":"COMET_STREAM","checkPhotosToReelsUpsellEligibility":false,"renderLocation":"group","useDefaultActor":false,"inviteShortLinkKey":null,"isFeed":false,"isFundraiser":false,"isFunFactPost":false,"isGroup":true,"isEvent":false,"isTimeline":false,"isSocialLearning":false,"isPageNewsFeed":false,"isProfileReviews":false,"isWorkSharedDraft":false,"hashtag":null,"canUserManageOffers":false,"__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider":false,"__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__CometFeedStoryDynamicResolutionPhotoAttachmentRenderer_experimentWidthrelayprovider":500,"__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider":false,"__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":false,"__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":false,"__relay_internal__pv__EventCometCardImage_prefetchEventImagerelayprovider":false,"__relay_internal__pv__GHLShouldChangeSponsoredAuctionDistanceFieldNamerelayprovider":true}',
        #"variables": '{"input":{"composer_entry_point":"publisher_bar_anonymous_author","composer_source_surface":"group","composer_type":"group","logging":{"composer_session_id":"'+composer_session_id+'"},"source":"WWW","message":{"ranges":[],"text":"'+message+'"},"with_tags_ids":null,"inline_activities":[],"text_format_preset_id":"0","ask_admin_to_post_for_user":{"is_asking_admin_to_post":true},"attachments":[{"link":{"share_scrape_data":"{\"share_type\":22,\"share_params\":[1045178797644511]}"}}],"navigation_data":{"attribution_id_v2":"CometGroupDiscussionRoot.react,comet.group,tap_bookmark,1741364369362,28346,737736324940019,,"},"tracking":[null],"event_share_metadata":{"surface":"newsfeed"},"audience":{"to_id":"'+to_id+'"},"actor_id":"'+av+'","client_mutation_id":"50"},"feedLocation":"GROUP","feedbackSource":0,"focusCommentID":null,"gridMediaWidth":null,"groupID":null,"scale":1,"privacySelectorRenderLocation":"COMET_STREAM","checkPhotosToReelsUpsellEligibility":false,"renderLocation":"group","useDefaultActor":false,"inviteShortLinkKey":null,"isFeed":false,"isFundraiser":false,"isFunFactPost":false,"isGroup":true,"isEvent":false,"isTimeline":false,"isSocialLearning":false,"isPageNewsFeed":false,"isProfileReviews":false,"isWorkSharedDraft":false,"hashtag":null,"canUserManageOffers":false,"__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider":false,"__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__CometFeedStoryDynamicResolutionPhotoAttachmentRenderer_experimentWidthrelayprovider":600,"__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider":false,"__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":false,"__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider":true,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":false,"__relay_internal__pv__EventCometCardImage_prefetchEventImagerelayprovider":false,"__relay_internal__pv__GHLShouldChangeSponsoredAuctionDistanceFieldNamerelayprovider":true}',
        "server_timestamps": "true",
        "doc_id": "29039386195652385"
    }
    
    response = requests.post(url, headers=headers, data=payload)
    return response
def post_to_facebook_group(cookie, uid, fb_dtsg, to_id, id_post, message, av):
    """
    Hàm gửi bài đăng đến Facebook group sử dụng GraphQL API.
    
    Parameters:
    - cookie (str): Cookie đăng nhập Facebook.
    - uid (str): User ID của người đăng.
    - fb_dtsg (str): Facebook token từ form data.
    - to_id (str): ID của group đích.
    - message (str): Nội dung bài đăng.
    - av (str): Actor ID.

    Returns:
    - dict: Response từ server.
    """

    # Tạo một session ID duy nhất
    composer_session_id = str(uuid4())

    # URL endpoint
    url = "https://www.facebook.com/api/graphql/"

    # Headers
    headers = {
        "authority": "www.facebook.com",
        "accept": "*/*",
        "accept-language": "vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6,el;q=0.5",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": cookie,
        "origin": "https://www.facebook.com",
        "referer": f"https://www.facebook.com/groups/{to_id}/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-fb-friendly-name": "ComposerStoryCreateMutation",
    }

    # Tạo payload JSON đúng format
    variables = {
        "input": {
            "composer_entry_point": "inline_composer",
            "composer_source_surface": "group",
            "composer_type": "group",
            "logging": {
                "composer_session_id": composer_session_id
            },
            "source": "WWW",
            "message": {
                "ranges": [],
                "text": message
            },
            "with_tags_ids": None,
            "inline_activities": [],
            "text_format_preset_id": "0",
            "ask_admin_to_post_for_user": {
                "is_asking_admin_to_post": True
            },
            "attachments": [
                {
                    "link": {
                        "share_scrape_data": json.dumps({
                            "share_type": 37,
                            "share_params": [id_post]
                        })
                    }
                }
            ],
            "navigation_data": {
                "attribution_id_v2": "CometGroupDiscussionRoot.react,comet.group,via_cold_start,1741330035102,198684,2361831622,,"
            },
            "tracking": [None],
            "event_share_metadata": {
                "surface": "newsfeed"
            },
            "audience": {
                "to_id": to_id
            },
            "actor_id": av,
            "client_mutation_id": "4"
        },
        "feedLocation": "GROUP",
        "feedbackSource": 0,
        "focusCommentID": None,
        "gridMediaWidth": None,
        "groupID": None,
        "scale": 1,
        "privacySelectorRenderLocation": "COMET_STREAM",
        "checkPhotosToReelsUpsellEligibility": False,
        "renderLocation": "group",
        "useDefaultActor": False,
        "inviteShortLinkKey": None,
        "isFeed": False,
        "isFundraiser": False,
        "isFunFactPost": False,
        "isGroup": True,
        "isEvent": False,
        "isTimeline": False,
        "isSocialLearning": False,
        "isPageNewsFeed": False,
        "isProfileReviews": False,
        "isWorkSharedDraft": False,
        "hashtag": None,
        "canUserManageOffers": False,
        "__relay_internal__pv__CometUFIShareActionMigrationrelayprovider": True,
        "__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider": False,
        "__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider": False,
        "__relay_internal__pv__IsWorkUserrelayprovider": False,
        "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False,
        "__relay_internal__pv__CometFeedStoryDynamicResolutionPhotoAttachmentRenderer_experimentWidthrelayprovider": 500,
        "__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider": False,
        "__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider": False,
        "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
        "__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider": False,
        "__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider": False,
        "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": True,
        "__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider": False,
        "__relay_internal__pv__EventCometCardImage_prefetchEventImagerelayprovider": False,
        "__relay_internal__pv__GHLShouldChangeSponsoredAuctionDistanceFieldNamerelayprovider": True
    }

    # Chuyển đổi JSON đúng format
    variables_json = json.dumps(variables)

    # Payload request
    payload = {
        "av": av,
        "__user": uid,
        "__a": "1",
        "fb_dtsg": fb_dtsg,
        "variables": variables_json,
        "server_timestamps": "true",
        "doc_id": "29039386195652385"
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        return response
    except Exception as e:
        return f"Lỗi request đăng bài: {e}"
def get_available_actor_id(cookie,idgroup):
    """
    Hàm lấy ID từ available_actors trong HTML của Facebook group với header mới
    
    Parameters:
    cookie (str): Chuỗi cookie từ request header
    uid (str): User ID của người dùng
    fb_dtsg (str): Facebook token từ form data
    
    Returns:
    str: Giá trị id từ available_actors hoặc None nếu không tìm thấy
    """
    
    # URL của group với path đầy đủ từ header mới
    url = f"https://www.facebook.com/groups/{idgroup}/?hoisted_section_header_type=recently_seen&multi_permalinks=3124339437731387"
    
    # Headers từ request mới của bạn
    headers = {
        "authority": "www.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6,el;q=0.5",
        "cache-control": "max-age=0",
        "cookie": cookie,
        "dpr": "1.125",
        "priority": "u=0, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-full-version-list": '"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="133.0.6943.142", "Chromium";v="133.0.6943.142"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "viewport-width": "772"
    }
    
    try:
        # Gửi GET request
        response = requests.get(url, headers=headers)
        html_content = response.text
        pattern = r'"available_actors":\s*\{.*?"edges":\s*\[\s*\{.*?"id":\s*"(\d+)"'
        match = re.search(pattern, html_content)
        if match:
            actor_id = match.group(1)
            return actor_id
        else:
            print("Không tìm thấy available_actors trong response")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except Exception as e:
        print(f"Error processing response: {e}")
        return None
def getInfoAccounts(cookie):
        try:
            send = requests.get('https://www.facebook.com/',headers={'cookie':cookie}).text
            DTSG__INIT__ = re.findall('DTSGInitialData",\\[\\],{"token":"(.*?)"}', send)[0]
            if DTSG__INIT__:
                fb_dtsg = DTSG__INIT__
                jazoest = re.findall('&jazoest=(.*?)"', send)[0]
                idFacebook = str(re.findall('"USER_ID":"(.*?)"', send)[0])
                return True, {'idFacebook': idFacebook, 'fb_dtsg': fb_dtsg, 'jazoest': jazoest}
        except Exception as e:
            return False, "Cookie die"
        return False, "Cookie out"
# Ví dụ sử dụng: