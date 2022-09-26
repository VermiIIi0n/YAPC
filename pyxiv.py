"""Pixiv Web APIs"""

import os
import ujson as json
from datetime import datetime
from typing import Any, Iterable, Literal, TypeAlias

tag_trans: TypeAlias = Literal["en", "ko", "zh", "zh_tw", "romaji"]
api_ret: TypeAlias = tuple[str, str, dict[str, Any]]
_Order: TypeAlias = Literal["popular_male", "popular_female", "popular", "date",
                            "popular_male_d", "popular_female_d", "popular_d", "date_d"]
"""Order ending with `_d` means descending"""
_Type: TypeAlias = Literal["all", "illust",
                           "manga", "ugoira", "illust_and_ugoira"]
"""Types of works to search for"""
_S_Mode: TypeAlias = Literal["s_tag", "s_tc", "s_tag_full"]
"""`s_tag` for partial tag match, `s_tag_full` for perfect match. 
`s_tc` for title and caption match."""
_Mode: TypeAlias = Literal["all", "safe", "r18"]


class SearchOption:
    """Search Option"""

    def __init__(self, in_words: Iterable[str] = (), ex_words: Iterable[str] = (),
                 order: _Order = "date_d", mode: _Mode = "all", blt: int = 0, p: int = 1,
                 s_mode: _S_Mode = "s_tag_full", type_: _Type = "all", ratio: float = 0,
                 wlt: int = 0, hlt: int = 0, tool: str = '', scd: datetime = None):
        """
        * `in_words`: Keywords to search for
        * `ex_words`: Keywords to exclude
        * `order`: Order of results
        * `mode`: Safe mode
        * `blt`: Minimum bookmark count, don't know why it's not bgt
        * `p`: Page number
        * `s_mode`: Search mode
        * `type_`: Type of works to search for
        * `ratio`: Aspect ratio
        * `wlt`: Minimum width
        * `hlt`: Minimum height
        * `tool`: Tool used
        * `scd`: datetime to start search from
        """
        self.raw: dict[str, Any] = {}
        self.raw["word"] = ' '.join(list(in_words)+['-'+w for w in ex_words])
        self.raw["order"] = order
        self.raw["mode"] = mode
        self.raw["p"] = p
        self.raw["type"] = type_
        self.raw["s_mode"] = s_mode
        if blt:
            self.raw["blt"] = blt
        if ratio:
            self.raw["ratio"] = ratio
        if wlt:
            self.raw["wlt"] = wlt
        if hlt:
            self.raw["hlt"] = hlt
        if tool:
            self.raw["tool"] = tool
        if scd:
            self.raw["scd"] = scd.strftime("%Y-%m-%d")

    def __getattr__(self, key: str) -> Any:
        return self.raw[key]


def illust(pid: str, host: str = "https://www.pixiv.net") -> api_ret:
    """### illust detail
    ```
{
        "error": false,
        "message": "",
        "body": {
            "illustId": "101323761",
            "illustTitle": "53\u65e5\u76ee\/Sailor Venus",
            "illustComment": "\u003Cstrong\u003E\u003Ca href=\u0022https:\/\/twitter.com\/QTONAGI\u0022 target=\u0022_blank\u0022\u003Etwitter\/QTONAGI\u003C\/a\u003E\u003C\/strong\u003E",
            "id": "101323761",
            "title": "53\u65e5\u76ee\/Sailor Venus",
            "description": "\u003Cstrong\u003E\u003Ca href=\u0022https:\/\/twitter.com\/QTONAGI\u0022 target=\u0022_blank\u0022\u003Etwitter\/QTONAGI\u003C\/a\u003E\u003C\/strong\u003E",
            "illustType": 0,
            "createDate": "2022-09-18T15:00:27+00:00",
            "uploadDate": "2022-09-18T17:42:45+00:00",
            "restrict": 0,
            "xRestrict": 0,
            "sl": 2,
            "urls": {
                "mini": "https:\/\/i.pximg.net\/c\/48x48\/custom-thumb\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_custom1200.jpg",
                "thumb": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/custom-thumb\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_custom1200.jpg",
                "small": "https:\/\/i.pximg.net\/c\/540x540_70\/img-master\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_master1200.jpg",
                "regular": "https:\/\/i.pximg.net\/img-master\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_master1200.jpg",
                "original": "https:\/\/i.pximg.net\/img-original\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0.jpg"
            },
            "tags": {
                "authorId": "2063338",
                "isLocked": false,
                "tags": [ 
                    {
                        "tag": "\u30bb\u30fc\u30e9\u30fc\u30e0\u30fc\u30f3",
                        "locked": true,
                        "deletable": false,
                        "userId": "2063338",
                        "romaji": "se-ra-mu-nn",
                        "translation": {
                            "en": "sailormoon"
                        },
                        "userName": "\u65e7\u90fd\u306a\u304e"
                    },
                ],
                "writable": true
            },
            "alt": "sailormoon, sailor venus, aino minako \/ 53\u65e5\u76ee\/Sailor Venus",
            "storableTags": [
                "AySgACkvx3",
                "AqKeZE09Wb",
                "JMAcR2xvlI"
            ],
            "userId": "2063338",
            "userName": "\u65e7\u90fd\u306a\u304e",
            "userAccount": "rolatan",
            "userIllusts": {
                "101323761": {
                    "id": "101323761",
                    "title": "53\u65e5\u76ee\/Sailor Venus",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/custom-thumb\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_custom1200.jpg",
                    "description": "\u003Cstrong\u003E\u003Ca href=\u0022https:\/\/twitter.com\/QTONAGI\u0022 target=\u0022_blank\u0022\u003Etwitter\/QTONAGI\u003C\/a\u003E\u003C\/strong\u003E",
                    "tags": [
                        "\u30bb\u30fc\u30e9\u30fc\u30e0\u30fc\u30f3",
                        "\u30bb\u30fc\u30e9\u30fc\u30f4\u30a3\u30fc\u30ca\u30b9",
                        "\u611b\u91ce\u7f8e\u5948\u5b50"
                    ],
                    "userId": "2063338",
                    "userName": "\u65e7\u90fd\u306a\u304e",
                    "width": 675,
                    "height": 1200,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": {
                        "id": "17542469737",
                        "private": false
                    },
                    "alt": "sailormoon, sailor venus, aino minako \/ 53\u65e5\u76ee\/Sailor Venus",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2022-09-19T00:00:27+09:00",
                    "updateDate": "2022-09-19T02:42:45+09:00",
                    "isUnlisted": false,
                    "isMasked": false
                }
                "101250961": null,
                "101188380": null,
                "101165708": null,
                "101113281": null,
            },
            "likeData": false,
            "width": 675,
            "height": 1200,
            "pageCount": 1,
            "bookmarkCount": 1127,
            "likeCount": 917,
            "commentCount": 7,
            "responseCount": 0,
            "viewCount": 4575,
            "bookStyle": 0,
            "isHowto": false,
            "isOriginal": false,
            "imageResponseOutData": [],
            "imageResponseData": [],
            "imageResponseCount": 0,
            "pollData": null,
            "seriesNavData": null,
            "descriptionBoothId": null,
            "descriptionYoutubeId": null,
            "comicPromotion": null,
            "fanboxPromotion": {
                "userName": "\u65e7\u90fd\u306a\u304e",
                "userImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/04\/18\/15\/28\/53\/22569435_4c827c535ed45c9bedc45d48867612cd_170.png",
                "contentUrl": "https:\/\/www.pixiv.net\/fanbox\/creator\/2063338?utm_campaign=www_artwork\u0026utm_medium=site_flow\u0026utm_source=pixiv",
                "description": "\u304a\u7d75\u304b\u304d\u66ae\u3089\u3057\u3002\r\n\r\n\u2726\u30106\/23\u3011FANBOX\u9650\u5b9a\u30bf\u30ed\u30c3\u30c8\u30ab\u30fc\u30c9\u306e\u30d5\u30eb\u30c7\u30c3\u30ad\u518d\u8ca9\u4e88\u7d04\u8ffd\u52a0\u3057\u307e\u3057\u305f\uff01\r\n\u3000\u4ed6\u3000\u30bf\u30ed\u30c3\u30c8\u9ad8\u753b\u8cea\u30c7\u30fc\u30bf\u3000\u30d0\u30e9\u58f2\u308a\u30ab\u30fc\u30c9\r\n\u3000https:\/\/qtonagi.fanbox.cc\/posts\/335172\r\n\u3000\u203b100\u65e5\u30c1\u30e3\u30ec\u30f3\u30b8\u4e2d\u306f\u30c1\u30a7\u30c3\u30af\u3084\u30b0\u30c3\u30ba\u306e\u767a\u6ce8\u304c\u51fa\u6765\u306a\u3044\u305f\u3081\u3001\r\n\u3000\u30aa\u30fc\u30c0\u30fc\u30e1\u30a4\u30c9\u30b0\u30c3\u30ba\u306e\u5fdc\u52df\u3092\u4e00\u6642\u505c\u6b62\u3044\u305f\u3057\u307e\u3059\u3002\r\n\r\n\u2727\u3042\u3068\u304c\u304d\u3000https:\/\/qtonagi.fanbox.cc\/posts\/1661739\r\n\u2727ALGL\u5168\u7ae0\u3000https:\/\/www.fanbox.cc\/@qtonagi\/posts\/2689562\r\n2022\/09\/09\u3000\u4e00\u90e8\u82f1\u8a9e\u7ffb\u8a33\u7248\u8ffd\u52a0\u3057\u307e\u3057\u305f\u3000Added some English translations.\r\n\u2727\u30a2\u30f3\u30b1\u30fc\u30c8\u3000https:\/\/form.run\/@kirikumo\r\n\r\nDo not Reposts. \u7981\u6b62\u8f6c\u8f7d",
                "imageUrl": "https:\/\/pixiv.pximg.net\/c\/520x280_90_a2_g5\/fanbox\/public\/images\/creator\/2063338\/cover\/i0KeGS1xrweyzM3ZyuucRZjG.jpeg",
                "imageUrlMobile": "https:\/\/pixiv.pximg.net\/c\/520x280_90_a2_g5\/fanbox\/public\/images\/creator\/2063338\/cover\/i0KeGS1xrweyzM3ZyuucRZjG.jpeg",
                "hasAdultContent": false
            },
            "contestBanners": [],
            "isBookmarkable": true,
            "bookmarkData": {
                "id": "17542469737",
                "private": false
            },
            "contestData": null,
            "zoneConfig": {
                "responsive": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=illust_responsive_side\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qw07lr3ksp\u0026num=6327e263915"
                },
                "rectangle": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=illust_rectangle\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qw4cwautzl\u0026num=6327e263465"
                },
                "500x500": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=bigbanner\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qw91tasffi\u0026num=6327e263470"
                },
                "header": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=header\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qwduzdxv0g\u0026num=6327e26333"
                },
                "footer": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=footer\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qwh05z07lf\u0026num=6327e263700"
                },
                "expandedFooter": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=multiple_illust_viewer\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qwktw5qaox\u0026num=6327e26372"
                },
                "logo": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=logo_side\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qwpjia5hsy\u0026num=6327e263659"
                },
                "relatedworks": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=relatedworks\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=w\u0026l=en\u0026uri=%2Fajax%2Fillust%2F_PARAM_\u0026ref=www.pixiv.net\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br91qwsonds8q4\u0026num=6327e263280"
                }
            },
            "extraData": {
                "meta": {
                    "title": "sailormoon, sailor venus, aino minako \/ 53\u65e5\u76ee\/Sailor Venus - pixiv",
                    "description": "\u3053\u306e\u4f5c\u54c1 \u300c53\u65e5\u76ee\/Sailor Venus\u300d \u306f \u300c\u30bb\u30fc\u30e9\u30fc\u30e0\u30fc\u30f3\u300d\u300c\u30bb\u30fc\u30e9\u30fc\u30f4\u30a3\u30fc\u30ca\u30b9\u300d \u7b49\u306e\u30bf\u30b0\u304c\u3064\u3051\u3089\u308c\u305f\u300c\u65e7\u90fd\u306a\u304e\u300d\u3055\u3093\u306e\u30a4\u30e9\u30b9\u30c8\u3067\u3059\u3002 \u300chttps:\/\/twitter.com\/QTONAGI\u300d",
                    "canonical": "https:\/\/www.pixiv.net\/en\/artworks\/101323761",
                    "alternateLanguages": {
                        "ja": "https:\/\/www.pixiv.net\/artworks\/101323761",
                        "en": "https:\/\/www.pixiv.net\/en\/artworks\/101323761"
                    },
                    "descriptionHeader": "sailormoon, sailor venus, aino minako are the most prominent tags for this work posted on September 19th, 2022.",
                    "ogp": {
                        "description": "https:\/\/twitter.com\/QTONAGI",
                        "image": "https:\/\/embed.pixiv.net\/artwork.php?illust_id=101323761",
                        "title": "sailormoon, sailor venus, aino minako \/ 53\u65e5\u76ee\/Sailor Venus - pixiv",
                        "type": "article"
                    },
                    "twitter": {
                        "description": "https:\/\/twitter.com\/QTONAGI",
                        "image": "https:\/\/embed.pixiv.net\/artwork.php?illust_id=101323761",
                        "title": "53\u65e5\u76ee\/Sailor Venus",
                        "card": "summary_large_image"
                    }
                }
            },
            "titleCaptionTranslation": {
                "workTitle": null,
                "workCaption": null
            },
            "isUnlisted": false,
            "request": null,
            "commentOff": 0
        }
    }
    ```    
    """
    url = f"{host}/ajax/illust/{pid}"
    return "GET", url, {}


def illust_pages(pid: str, host: str = "https://www.pixiv.net") -> api_ret:
    """Get illust pages
    ```
        {
        "error": false,
        "message": "",
        "body": [
            {
                "urls": {
                    "thumb_mini": "https:\/\/i.pximg.net\/c\/128x128\/custom-thumb\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_custom1200.jpg",
                    "small": "https:\/\/i.pximg.net\/c\/540x540_70\/img-master\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_master1200.jpg",
                    "regular": "https:\/\/i.pximg.net\/img-master\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0_master1200.jpg",
                    "original": "https:\/\/i.pximg.net\/img-original\/img\/2022\/09\/19\/02\/42\/45\/101323761_p0.jpg"
                },
                "width": 675,
                "height": 1200
            }
        ]
    }
    ```
    """
    url = f"{host}/ajax/illust/{pid}/pages"
    return "GET", url, {}


def illust_ugoira_meta(pid: str, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """Get illust ugoira meta
    ```
    {
        "error": false,
        "message": "",
        "body": {
            "src": "https:\/\/i.pximg.net\/img-zip-ugoira\/img\/2022\/09\/16\/13\/02\/41\/101259635_ugoira600x600.zip",
            "originalSrc": "https:\/\/i.pximg.net\/img-zip-ugoira\/img\/2022\/09\/16\/13\/02\/41\/101259635_ugoira1920x1080.zip",
            "mime_type": "image\/jpeg",
            "frames": [
                {
                    "file": "000000.jpg",
                    "delay": 100
                },
                {
                    "file": "000001.jpg",
                    "delay": 100
                },
                {
                    "file": "000002.jpg",
                    "delay": 100
                }
            ]
        }
    }
    ```
    """
    url = f"{host}/ajax/illust/{pid}/ugoira_meta"
    return "GET", url, {"params": {"lang": lang}}


def illust_recommend(pid: str = None, illust_ids: Iterable[str] = (),
                     limit: int = 18, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Get recommended illusts
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "illusts": [
                {
                    "id": "69324463",
                    "title": "\u30e1\u30a4\u30c9\u3055\u3093",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/360x360_70\/img-master\/img\/2018\/06\/20\/23\/03\/25\/69324463_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "\u30aa\u30ea\u30b8\u30ca\u30eb",
                        "\u80cc\u666f",
                        "\u5973\u306e\u5b50",
                        "\u30e1\u30a4\u30c9\u3055\u3093",
                        "\u98a8\u666f",
                        "\u30e8\u30fc\u30ed\u30c3\u30d1",
                        "\u8857\u4e26\u307f",
                        "\u7d10\u30bf\u30a4",
                        "\u30a8\u30d7\u30ed\u30f3\u30c9\u30ec\u30b9",
                        "\u304a\u304b\u3063\u3071"
                    ],
                    "userId": "8670915",
                    "userName": "\u30eb\u30bb\u30fc\u30b9",
                    "width": 3541,
                    "height": 2508,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "original, background, girl \/ \u30e1\u30a4\u30c9\u3055\u3093",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2018-06-20T23:03:25+09:00",
                    "updateDate": "2018-06-20T23:03:25+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2018\/06\/28\/13\/24\/15\/14415821_f522210da741f9234c8e6c08e6ef28d4_50.jpg",
                    "type": "illust"
                }
            ],
            ################# Following does not exist in non-init response #################
            "nextIds": [
                "97703260",
                "83293386",
                "85371627",
            ],
            "details": {
                "80862451": {
                    "methods": [
                        "neumf"
                    ],
                    "score": 11.1644287109375,
                    "seedIllustIds": [
                        81491286
                    ],
                    "banditInfo": "mf_param_eps_ver2_exploit-3",
                    "recommendListId": "63286e324880d9.80327924"
                },
                "72656476": {
                    "methods": [
                        "illust_by_illust_table_bq_recommendation_c"
                    ],
                    "score": 0.200005903840065,
                    "seedIllustIds": [
                        "81491286"
                    ],
                    "banditInfo": "mf_param_eps_ver2_exploit-3",
                    "recommendListId": "63286e324880d9.80327924"
                }
            }
        }
    }
    ```
    """
    if pid:
        if illust_ids:
            raise ValueError("illust_ids must be empty when init from a pid")
        url = f"{host}/ajax/illust/{pid}/recommend/init"
        params = {"limit": limit, "lang": lang}
    else:
        if not illust_ids:
            raise ValueError("illust_ids must be specified when pid is None")
        url = f"{host}/ajax/illust/recommend/illusts"
        params = {"illust_ids": illust_ids, "lang": lang}
    return "GET", url, {"params": params}


def illusts_bookmark_add(pid: str, restrict: bool = False, comment: str = '',
                         tags: Iterable[str] = (),
                         host: str = "https://www.pixiv.net") -> api_ret:
    url = f"{host}/ajax/illusts/bookmark/add"
    return "POST", url, {"json": json.dumps(
        {"illust_id": pid, "restrict": int(restrict),
         "comment": comment, "tags": list(tags)})
    }


def user_extra(lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### user extra for your self
    ```
    {
        "error": false,
        "message": "",
        "body": {
            "following": 265,
            "followers": 0,
            "mypixivCount": 0,
            "background": null
        }
    }
    ```
    """
    url = f"{host}/ajax/user/extra?lang={lang}"
    return "GET", url, {"params": {"lang": lang}}


def user_illusts(uid: str, ids: Iterable[str], host: str = "https://www.pixiv.net") -> api_ret:
    """### Get illusts based on ids
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "101250961": {
                "id": "101250961",
                "title": "49-51\u65e5\u76ee\/Moon Lisette",
                "illustType": 0,
                "xRestrict": 0,
                "restrict": 0,
                "sl": 2,
                "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2022\/09\/17\/14\/58\/48\/101250961_p0_square1200.jpg",
                "description": "",
                "tags": [
                    "\u30aa\u30ea\u30b8\u30ca\u30eb",
                    "\u30aa\u30ea\u30b8\u30ca\u30eb1000users\u5165\u308a"
                ],
                "userId": "2063338",
                "userName": "\u65e7\u90fd\u306a\u304e",
                "width": 679,
                "height": 1100,
                "pageCount": 3,
                "isBookmarkable": true,
                "bookmarkData": null,
                "alt": "49-51\u65e5\u76ee\/Moon Lisette \/ September 16th, 2022",
                "titleCaptionTranslation": {
                    "workTitle": null,
                    "workCaption": null
                },
                "createDate": "2022-09-16T00:00:23+09:00",
                "updateDate": "2022-09-17T14:58:48+09:00",
                "isUnlisted": false,
                "isMasked": false,
                "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/04\/18\/15\/28\/53\/22569435_4c827c535ed45c9bedc45d48867612cd_50.png"
            },
        }
    }
    ```
    """
    url = f"{host}/ajax/user/{uid}/illusts"
    return "GET", url, {"params": {"ids": list(ids)}}


def user_illusts_bookmarks(uid: str, offset: int, limit: int = 48, tag: str = None,
                           rest: Literal["show", "hide"] = "show", lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Get bookmarks of a user
    * `rest` Public/Private bookmarks  

    ```
    {
        "error": false,
        "message": "",
        "body": {
            "works": [
                {
                    "id": "101130809",
                    "title": "\u4e00\u8449\u843d\u3061\u3066\u79cb\u3092\u77e5\u308b",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/custom-thumb\/img\/2022\/09\/10\/19\/41\/25\/101130809_p0_custom1200.jpg",
                    "description": "",
                    "tags": [
                        "\u30aa\u30ea\u30b8\u30ca\u30eb",
                        "\u5973\u306e\u5b50",
                        "\u30e1\u30a4\u30c9"
                    ],
                    "userId": "708376",
                    "userName": "\u304b\u304b\u3057\u967d\u592a",
                    "width": 1793,
                    "height": 1094,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": {
                        "id": "17548002077",
                        "private": true
                    },
                    "alt": "\u4e00\u8449\u843d\u3061\u3066\u79cb\u3092\u77e5\u308b \/ September 10th, 2022",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2022-09-10T19:41:25+09:00",
                    "updateDate": "2022-09-10T19:41:25+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2021\/02\/20\/23\/16\/09\/20228768_eda739ed68f2b2aff1bc6f98e0d41820_50.png"
                }
            ],
            "total": 1,
            "bookmarkTags": []
        }
    }
    ```
    """
    url = f"{host}/ajax/user/{uid}/illusts/bookmarks"
    return "GET", url, {"params": {"offset": offset, "limit": limit, "tag": tag, "rest": rest, "lang": lang}}


def user_works_latest(uid: str, lang: str = "en",
                      host: str = "https://www.pixiv.net") -> api_ret:
    """### Get latest works of a user
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "illusts": {
                "101333033": {
                    "id": "101333033",
                    "title": "DAY84",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2022\/09\/19\/11\/04\/43\/101333033_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "\u30c0\u30f3\u30ac\u30f3\u30ed\u30f3\u30d1",
                        "\u6c5f\u30ce\u5cf6\u76fe\u5b50"
                    ],
                    "userId": "14783003",
                    "userName": "\u3073\u3075\u3049\u3042",
                    "width": 1153,
                    "height": 1857,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "DAY84 \/ September 19th, 2022",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2022-09-19T11:04:43+09:00",
                    "updateDate": "2022-09-19T11:04:43+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/01\/21\/16\/00\/25\/22086408_5bcad729039f0d8fb6e81a72b80d17b3_50.jpg"
                },
                "101129461": null,
                "101040739": null,
            },
            "novels": []
        }
    }
    ```
    """
    url = f"{host}/ajax/user/{uid}/works/latest"
    return "GET", url, {"params": {"lang": lang}}


def user(uid: str, full: int = 1, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Get user info
    ```
    {
        "error": false,
        "message": "",
        "body": {
            "userId": "16051830",
            "name": "Alpha",
            "image": "https:\/\/i.pximg.net\/user-profile\/img\/2018\/11\/24\/22\/39\/13\/15052942_cffb3f2f311a1a5a8e9738ab7472bd19_50.png",
            "imageBig": "https:\/\/i.pximg.net\/user-profile\/img\/2018\/11\/24\/22\/39\/13\/15052942_cffb3f2f311a1a5a8e9738ab7472bd19_170.png",
            "premium": true,
            "isFollowed": true,
            "isMypixiv": false,
            "isBlocking": false,
            "background": {
                "repeat": null,
                "color": null,
                "url": "https:\/\/i.pximg.net\/c\/1920x960_80_a2_g5\/background\/img\/2021\/02\/21\/15\/05\/45\/16051830_9d2b6fe39a8d6ce1b4e7bacc42f4f38a.png",
                "isPrivate": false
            },
            "sketchLiveId": null,
            "partial": 1,
            "acceptRequest": false,
            "sketchLives": [],
            "following": 371,
            "followedBack": false,
            "comment": "\u30a8\u30ed\u7d75\u3092\u63cf\u3044\u3066\u3044\u307e\u3059\u3002\r\nPixiv\u306b\u516c\u958b\u3055\u308c\u305f\u4f5c\u54c1\u306f\u81ea\u7531\u306b\u8ee2\u8f09\u3057\u3066\u3082\u69cb\u3044\u307e\u305b\u3093\u3002\r\n\r\n\u203bPixiv\u306e\u30e1\u30c3\u30bb\u30fc\u30b8\u306f\u8fd4\u4fe1\u3057\u307e\u305b\u3093\u3002Fanbox\u306b\u3064\u3044\u3066\u306e\u3054\u8cea\u554f\u306fDiscord\u30c1\u30e3\u30f3\u30cd\u30eb\u3067\u304a\u554f\u3044\u5408\u308f\u305b\u304f\u3060\u3055\u3044\u3002\r\n\u203bI don\u0027t reply any private message on Pixiv. If you have questions about my Fanbox, please find me in my Discord channel.\r\n\u203b\u79c1\u4fe1\u4e0d\u56de\u3002\u5173\u4e8eFanbox\u7684\u95ee\u9898\u8bf7\u5728\u6211\u7684Discord\u9891\u9053\u8be2\u95ee\u3002",
            "commentHtml": "\u30a8\u30ed\u7d75\u3092\u63cf\u3044\u3066\u3044\u307e\u3059\u3002\u003Cbr \/\u003EPixiv\u306b\u516c\u958b\u3055\u308c\u305f\u4f5c\u54c1\u306f\u81ea\u7531\u306b\u8ee2\u8f09\u3057\u3066\u3082\u69cb\u3044\u307e\u305b\u3093\u3002\u003Cbr \/\u003E\u003Cbr \/\u003E\u203bPixiv\u306e\u30e1\u30c3\u30bb\u30fc\u30b8\u306f\u8fd4\u4fe1\u3057\u307e\u305b\u3093\u3002Fanbox\u306b\u3064\u3044\u3066\u306e\u3054\u8cea\u554f\u306fDiscord\u30c1\u30e3\u30f3\u30cd\u30eb\u3067\u304a\u554f\u3044\u5408\u308f\u305b\u304f\u3060\u3055\u3044\u3002\u003Cbr \/\u003E\u203bI don\u0026#39;t reply any private message on Pixiv. If you have questions about my Fanbox\u0026#44; please find me in my Discord channel.\u003Cbr \/\u003E\u203b\u79c1\u4fe1\u4e0d\u56de\u3002\u5173\u4e8eFanbox\u7684\u95ee\u9898\u8bf7\u5728\u6211\u7684Discord\u9891\u9053\u8be2\u95ee\u3002",
            "webpage": null,
            "social": {
                "twitter": {
                    "url": "https:\/\/twitter.com\/alpha91myu"
                }
            },
            "canSendMessage": true,
            "region": {
                "name": "Japan",
                "region": "JP",
                "prefecture": "13",
                "privacyLevel": "0"
            },
            "age": {
                "name": null,
                "privacyLevel": null
            },
            "birthDay": {
                "name": null,
                "privacyLevel": null
            },
            "gender": {
                "name": null,
                "privacyLevel": null
            },
            "job": {
                "name": null,
                "privacyLevel": null
            },
            "workspace": null,
            "official": false,
            "group": null
        }
    }
    ```
    """
    url = f"{host}/ajax/user/{uid}"
    return "GET", url, {"params": {"full": full, "lang": lang}}


def user_profile_all(uid: str, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Get user profile
    ```
    {
    "error": false,
    "message": "",
    "body": {
        "illusts": {
            "101323761": null,
        },
        "manga": [],
        "novels": [],
        "mangaSeries": [],
        "novelSeries": [],
        "pickup": [
            {
                "type": "fanbox",
                "deletable": false,
                "draggable": true,
                "userName": "\u65e7\u90fd\u306a\u304e",
                "userImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/04\/18\/15\/28\/53\/22569435_4c827c535ed45c9bedc45d48867612cd_170.png",
                "contentUrl": "https:\/\/www.pixiv.net\/fanbox\/creator\/2063338?utm_campaign=www_profile\u0026utm_medium=site_flow\u0026utm_source=pixiv",
                "description": "\u304a\u7d75\u304b\u304d\u66ae\u3089\u3057\u3002\r\n\r\n\u2726\u30106\/23\u3011FANBOX\u9650\u5b9a\u30bf\u30ed\u30c3\u30c8\u30ab\u30fc\u30c9\u306e\u30d5\u30eb\u30c7\u30c3\u30ad\u518d\u8ca9\u4e88\u7d04\u8ffd\u52a0\u3057\u307e\u3057\u305f\uff01\r\n\u3000\u4ed6\u3000\u30bf\u30ed\u30c3\u30c8\u9ad8\u753b\u8cea\u30c7\u30fc\u30bf\u3000\u30d0\u30e9\u58f2\u308a\u30ab\u30fc\u30c9\r\n\u3000https:\/\/qtonagi.fanbox.cc\/posts\/335172\r\n\u3000\u203b100\u65e5\u30c1\u30e3\u30ec\u30f3\u30b8\u4e2d\u306f\u30c1\u30a7\u30c3\u30af\u3084\u30b0\u30c3\u30ba\u306e\u767a\u6ce8\u304c\u51fa\u6765\u306a\u3044\u305f\u3081\u3001\r\n\u3000\u30aa\u30fc\u30c0\u30fc\u30e1\u30a4\u30c9\u30b0\u30c3\u30ba\u306e\u5fdc\u52df\u3092\u4e00\u6642\u505c\u6b62\u3044\u305f\u3057\u307e\u3059\u3002\r\n\r\n\u2727\u3042\u3068\u304c\u304d\u3000https:\/\/qtonagi.fanbox.cc\/posts\/1661739\r\n\u2727ALGL\u5168\u7ae0\u3000https:\/\/www.fanbox.cc\/@qtonagi\/posts\/2689562\r\n2022\/09\/09\u3000\u4e00\u90e8\u82f1\u8a9e\u7ffb\u8a33\u7248\u8ffd\u52a0\u3057\u307e\u3057\u305f\u3000Added some English translations.\r\n\u2727\u30a2\u30f3\u30b1\u30fc\u30c8\u3000https:\/\/form.run\/@kirikumo\r\n\r\nDo not Reposts. \u7981\u6b62\u8f6c\u8f7d",
                "imageUrl": "https:\/\/pixiv.pximg.net\/c\/520x280_90_a2_g5\/fanbox\/public\/images\/creator\/2063338\/cover\/i0KeGS1xrweyzM3ZyuucRZjG.jpeg",
                "imageUrlMobile": "https:\/\/pixiv.pximg.net\/c\/520x280_90_a2_g5\/fanbox\/public\/images\/creator\/2063338\/cover\/i0KeGS1xrweyzM3ZyuucRZjG.jpeg",
                "hasAdultContent": false
            },
            {
                "id": "95775797",
                "title": "The Devil",
                "illustType": 0,
                "xRestrict": 0,
                "restrict": 0,
                "sl": 4,
                "url": "https:\/\/i.pximg.net\/c\/288x288_80_a2\/custom-thumb\/img\/2022\/01\/26\/00\/00\/05\/95775797_p0_custom1200.jpg",
                "description": "\u652f\u63f4\u8005\u9650\u5b9a\u30bf\u30ed\u30c3\u30c8\u30ab\u30fc\u30c9\uff06\u9ad8\u753b\u8cea\u30bb\u30c3\u30c8\u2726\u003Ca href=\u0022https:\/\/qtonagi.fanbox.cc\/posts\/3314996\u0022 target=\u0022_blank\u0022\u003Ehttps:\/\/qtonagi.fanbox.cc\/posts\/3314996\u003C\/a\u003E",
                "tags": [
                    "\u30aa\u30ea\u30b8\u30ca\u30eb",
                    "\u30bf\u30ed\u30c3\u30c8\u30ab\u30fc\u30c9",
                    "\u30aa\u30ea\u30b8\u30ca\u30eb10000users\u5165\u308a"
                ],
                "userId": "2063338",
                "userName": "\u65e7\u90fd\u306a\u304e",
                "width": 516,
                "height": 900,
                "pageCount": 1,
                "isBookmarkable": true,
                "bookmarkData": null,
                "alt": "original, tarot card, original 10000+ bookmarks \/ The Devil",
                "titleCaptionTranslation": {
                    "workTitle": null,
                    "workCaption": null
                },
                "createDate": "2022-01-26T00:00:05+09:00",
                "updateDate": "2022-01-26T00:00:05+09:00",
                "isUnlisted": false,
                "isMasked": false,
                "urls": {
                    "250x250": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/custom-thumb\/img\/2022\/01\/26\/00\/00\/05\/95775797_p0_custom1200.jpg",
                    "360x360": "https:\/\/i.pximg.net\/c\/360x360_70\/custom-thumb\/img\/2022\/01\/26\/00\/00\/05\/95775797_p0_custom1200.jpg",
                    "540x540": "https:\/\/i.pximg.net\/c\/540x540_70\/custom-thumb\/img\/2022\/01\/26\/00\/00\/05\/95775797_p0_custom1200.jpg"
                },
                "type": "illust",
                "deletable": true,
                "draggable": true,
                "contentUrl": "https:\/\/www.pixiv.net\/en\/artworks\/95775797"
            },
        ],
        "bookmarkCount": {
            "public": {
                "illust": 0,
                "novel": 0
            },
            "private": {
                "illust": 0,
                "novel": 0
            }
        },
        "externalSiteWorksStatus": {
            "booth": true,
            "sketch": true,
            "vroidHub": false
        },
        "request": {
            "showRequestTab": false,
            "showRequestSentTab": false,
            "postWorks": {
                "artworks": [],
                "novels": []
            }
        }
    }
}
    ```
    """
    url = f"{host}/ajax/user/{uid}/profile/all"
    return "GET", url, {"params": {"lang": lang}}


def user_profile_top(uid: str, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    url = f"{host}/ajax/user/{uid}/profile/top"
    return "GET", url, {"params": {"lang": lang}}


def tag_info(tag: str, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Get information about a tag
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "tag": "\u30e9\u30f3\u30bb\u30ca",
            "abstract": "\u30bc\u30ce\u30d6\u30ec\u30a4\u30c93\u306b\u767b\u5834\u3059\u308b\u30e9\u30f3\u30c4\u3068\u30bb\u30ca\u306e\u30ab\u30c3\u30d7\u30ea\u30f3\u30b0\u30bf\u30b0",
            "thumbnail": "https:\/\/i.pximg.net\/c\/384x280_80_a2_g2\/img-master\/img\/2022\/07\/19\/20\/56\/23\/99844885_p0_master1200.jpg",
            "en": null,
            "en_new": null,
            "ja": {
                "tag": "\u30e9\u30f3\u30bb\u30ca",
                "abstract": "\u30bc\u30ce\u30d6\u30ec\u30a4\u30c93\u306b\u767b\u5834\u3059\u308b\u30e9\u30f3\u30c4\u3068\u30bb\u30ca\u306e\u30ab\u30c3\u30d7\u30ea\u30f3\u30b0\u30bf\u30b0",
                "url": "https:\/\/dic.pixiv.net\/a\/%E3%83%A9%E3%83%B3%E3%82%BB%E3%83%8A"
            },
            "ja_new": null
        }
    }
    ```
    """
    url = f"{host}/ajax/tag/info"
    return "GET", url, {"params": {"tag": tag, "lang": lang}}


def tags_frequent_illust(ids: list[int], lang: str = "en",
                         host: str = "https://www.pixiv.net") -> api_ret:
    """### Get the most frequent tags for the given illustrations
    ```
    {
    "error": false,
    "message": "",
    "body": [
        {
            "tag": "\u30aa\u30ea\u30b8\u30ca\u30eb",
            "tag_translation": "original"
        },
    ]
}
    ```
    """
    url = f"{host}/ajax/tags/frequent/illust"
    return "GET", url, {"params": {"ids": ids, "lang": lang}}


def favorite_tags_save(tags: Iterable[str], host: str = "https://www.pixiv.net") -> api_ret:
    """### Save a favorite tag
    ```
    {
    "error": false,
    "message": "",
    "body": []
    }
    ```
    """
    url = f"{host}/ajax/favorite_tags/save"
    return "POST", url, {"json": json.dumps({"tags": tags})}


def search_tags(tag: str, lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### Search for tags
    ```
        {
        "error": false,
        "body": {
            "tag": "\u30e9\u30f3\u30bb\u30ca",
            "word": "\u30e9\u30f3\u30bb\u30ca",
            "pixpedia": {
                "abstract": "\u30bc\u30ce\u30d6\u30ec\u30a4\u30c93\u306b\u767b\u5834\u3059\u308b\u30e9\u30f3\u30c4\u3068\u30bb\u30ca\u306e\u30ab\u30c3\u30d7\u30ea\u30f3\u30b0\u30bf\u30b0",
                "image": "https:\/\/i.pximg.net\/c\/384x280_80_a2_g2\/img-master\/img\/2022\/07\/19\/20\/56\/23\/99844885_p0_master1200.jpg",
                "id": "99844885"
            },
            "breadcrumbs": {
                "successor": [],
                "current": []
            },
            "myFavoriteTags": [],
            "tagTranslation": {
                "\u30e9\u30f3\u30bb\u30ca": {
                    "romaji": "rannsena"
                }
            }
        }
    }
    ```
    """
    url = f"{host}/ajax/search/tags/{tag}"
    return "GET", url, {"params": {"lang": lang}}


def search_artworks(opts: SearchOption, lang: str = "en",
                    host: str = "https://www.pixiv.net") -> api_ret:
    """### Search for illustrations
    ```
    {
    "error": false,
    "body": {
        "illustManga": {
            "data": [
                {
                    "id": "89197783",
                    "title": "\u30c0\u30a4\u30ef\u30b9\u30ab\u30fc\u30ec\u30c3\u30c8",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2021\/04\/17\/03\/59\/07\/89197783_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "\u30c0\u30a4\u30ef\u30b9\u30ab\u30fc\u30ec\u30c3\u30c8",
                        "\u30c0\u30a4\u30ef\u30b9\u30ab\u30fc\u30ec\u30c3\u30c8(\u30a6\u30de\u5a18)",
                        "\u30a6\u30de\u5a18\u30d7\u30ea\u30c6\u30a3\u30fc\u30c0\u30fc\u30d3\u30fc",
                        "\u30b9\u30af\u6c34",
                        "\u30d7\u30fc\u30eb",
                        "\u6c34\u7740\u30a6\u30de\u5a18",
                        "\u30a6\u30de\u5a18\u30d7\u30ea\u30c6\u30a3\u30fc\u30c0\u30fc\u30d3\u30fc50000users\u5165\u308a"
                    ],
                    "userId": "4338012",
                    "userName": "hews",
                    "width": 1079,
                    "height": 1737,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "\u30c0\u30a4\u30ef\u30b9\u30ab\u30fc\u30ec\u30c3\u30c8 \/ April 17th, 2021",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2021-04-17T03:59:07+09:00",
                    "updateDate": "2021-04-17T03:59:07+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2021\/09\/19\/09\/23\/48\/21436280_e3edc929f0b2733604161e85cfadf706_50.jpg"
                },
            ],
            "total": 171,
            "bookmarkRanges": [
                {
                    "min": null,
                    "max": null
                },
                {
                    "min": 10000,
                    "max": null
                },
                {
                    "min": 5000,
                    "max": 9999
                },
            ]
        },
        "popular": {
            "recent": [
                {
                    "id": "88867943",
                    "title": "\u30a6\u30de\u8a70",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2021\/04\/02\/01\/56\/50\/88867943_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "\u30a6\u30de\u5a18\u30d7\u30ea\u30c6\u30a3\u30fc\u30c0\u30fc\u30d3\u30fc",
                    ],
                    "userId": "2118155",
                    "userName": "\u30b3\u30ce\u30b7\u30b2",
                    "width": 1254,
                    "height": 2347,
                    "pageCount": 4,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "\u30a6\u30de\u8a70 \/ April 2nd, 2021",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2021-04-02T01:56:50+09:00",
                    "updateDate": "2021-04-02T01:56:50+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2015\/12\/04\/01\/19\/10\/10198999_60e64101ea9c42264d6da9e87e2ea680_50.jpg"
                }
            ]
        },
        "relatedTags": [
            "\u30a6\u30de\u5a18\u30d7\u30ea\u30c6\u30a3\u30fc\u30c0\u30fc\u30d3\u30fc",
        ],
        "tagTranslation": {
            "\u30a6\u30de\u5a18\u30d7\u30ea\u30c6\u30a3\u30fc\u30c0\u30fc\u30d3\u30fc": {
                "en": "Uma Musume Pretty Derby"
            },
        },
        "zoneConfig": {
            "header": {
                "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=header\u0026format=js\u0026s=1\u0026up=0\u0026a=21\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_\u0026ref=www.pixiv.net%2Fen%2Ftags%2F%25E3%2582%25A6%25E3%2583%259E%25E5%25A8%2598%2Fartworks%3Forder%3Dpopular_male_d%26blt%3D10000%26s_mode%3Ds_tag%26tool%3DPhotoshop\u0026is_spa=1\u0026K=219e9f9315fa2\u0026ab_test_digits_first=73\u0026uab=69\u0026yuid=JZdwBTc\u0026suid=Ph6bwbx0k0kk5cu1x\u0026num=63280b94256"
            },
            "footer": {
                "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=footer\u0026format=js\u0026s=1\u0026up=0\u0026a=21\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_\u0026ref=www.pixiv.net%2Fen%2Ftags%2F%25E3%2582%25A6%25E3%2583%259E%25E5%25A8%2598%2Fartworks%3Forder%3Dpopular_male_d%26blt%3D10000%26s_mode%3Ds_tag%26tool%3DPhotoshop\u0026is_spa=1\u0026K=219e9f9315fa2\u0026ab_test_digits_first=73\u0026uab=69\u0026yuid=JZdwBTc\u0026suid=Ph6bwbx0k48jzgsqr\u0026num=63280b94242"
            },
            "infeed": {
                "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=illust_search_grid\u0026format=js\u0026s=1\u0026up=0\u0026a=21\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_\u0026ref=www.pixiv.net%2Fen%2Ftags%2F%25E3%2582%25A6%25E3%2583%259E%25E5%25A8%2598%2Fartworks%3Forder%3Dpopular_male_d%26blt%3D10000%26s_mode%3Ds_tag%26tool%3DPhotoshop\u0026is_spa=1\u0026K=219e9f9315fa2\u0026ab_test_digits_first=73\u0026uab=69\u0026yuid=JZdwBTc\u0026suid=Ph6bwbx0k72vmr2o\u0026num=63280b94933"
            }
        },
        "extraData": {
            "meta": {
                "title": "#horse girl Pictures, Comics on pixiv, Japan",
                "description": "pixiv",
                "canonical": "https:\/\/www.pixiv.net\/en\/tags\/%E3%82%A6%E3%83%9E%E5%A8%98",
                "alternateLanguages": {
                    "ja": "https:\/\/www.pixiv.net\/tags\/%E3%82%A6%E3%83%9E%E5%A8%98",
                    "en": "https:\/\/www.pixiv.net\/en\/tags\/%E3%82%A6%E3%83%9E%E5%A8%98"
                },
                "descriptionHeader": "pixiv"
            }
        }
    }
}
    ```
    """
    match opts.type:
        case "all":
            url = f"{host}/ajax/search/artworks/{opts.word}"
        case "illust" | "ugoira" | "illust_and_ugoira":
            url = f"{host}/ajax/search/illustrations/{opts.word}"
        case "manga":
            url = f"{host}/ajax/search/manga/{opts.word}"
        case _:
            raise ValueError(f"Invalid search type {opts.type}")
    params = opts.raw.copy()
    params["lang"] = lang
    return "GET", url, {"params": params}


def top_illust(mode: _Mode = "all", lang: str = "en", host: str = "https://www.pixiv.net") -> api_ret:
    """### top illust
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "tagTranslation": {
                "FGO": {
                    "en": "Fate\/Grand Order",
                    "ko": "\ud398\uadf8\uc624",
                    "zh": "",
                    "zh_tw": "",
                    "romaji": ""
                },

            },
            "thumbnails": {
                "illust": [
                    {
                        "id": "99867144",
                        "title": "\u96e8\u306e\u97f3",
                        "illustType": 0,
                        "xRestrict": 0,
                        "restrict": 0,
                        "sl": 2,
                        "url": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2022\/07\/20\/20\/42\/29\/99867144_p0_square1200.jpg",
                        "description": "",
                        "tags": [],
                        "userId": "6775237",
                        "userName": "\u82b1\u702c",
                        "width": 750,
                        "height": 805,
                        "pageCount": 1,
                        "isBookmarkable": true,
                        "bookmarkData": null,
                        "alt": "\u96e8\u306e\u97f3 \/ July 20th, 2022",
                        "titleCaptionTranslation": {
                            "workTitle": null,
                            "workCaption": null
                        },
                        "createDate": "2022-07-20T20:42:29+09:00",
                        "updateDate": "2022-07-20T20:42:29+09:00",
                        "isUnlisted": false,
                        "isMasked": false,
                        "urls": {
                            "250x250": "https:\/\/i.pximg.net\/c\/250x250_80_a2\/img-master\/img\/2022\/07\/20\/20\/42\/29\/99867144_p0_square1200.jpg",
                            "360x360": "https:\/\/i.pximg.net\/c\/360x360_70\/img-master\/img\/2022\/07\/20\/20\/42\/29\/99867144_p0_square1200.jpg",
                            "540x540": "https:\/\/i.pximg.net\/c\/540x540_70\/img-master\/img\/2022\/07\/20\/20\/42\/29\/99867144_p0_square1200.jpg"
                        },
                        "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2014\/11\/19\/21\/11\/35\/8638253_50c94cbecd380cc7d4fc621af7ecc934_50.jpg"
                    },
                ],
                "novel": [
                    {
                        "id": "11360827",
                        "title": "\u56db\u5bae\u304b\u3050\u3084\u306f\u508d\u306b\u3044\u305f\u3044\uff5e\u4e03\u5915\u306e\u591c\uff5e",
                        "xRestrict": 0,
                        "restrict": 0,
                        "url": "https:\/\/i.pximg.net\/c\/600x600\/novel-cover-master\/img\/2022\/07\/19\/00\/39\/44\/ci11360827_623eb61a3796b487009ad06b4f7e6f79_master1200.jpg",
                        "tags": [
                            "\u304b\u3050\u3084\u69d8\u306f\u544a\u3089\u305b\u305f\u3044",
                            "\u56db\u5bae\u304b\u3050\u3084",
                            "\u767d\u9280\u5fa1\u884c",
                            "\u767d\u304b\u3050",
                            "\u85e4\u539f\u5343\u82b1",
                            "\u77f3\u4e0a\u512a",
                            "\u4e03\u5915",
                            "\u304b\u3050\u3084\u69d8",
                            "\u661f",
                            "\u5b87\u5b99\u306e\u661f\u3005"
                        ],
                        "userId": "32008371",
                        "userName": "\u3042\u30fc\u3061\u3083\u3093",
                        "profileImageUrl": "https:\/\/i.pximg.net\/user-profile\/img\/2019\/07\/29\/18\/54\/09\/16070011_b1184f8708035ce03cfce5125f6c7102_50.jpg",
                        "textCount": 5024,
                        "wordCount": 2592,
                        "readingTime": 602,
                        "useWordCount": false,
                        "description": "\u306a\u3093\u3068\u304b\u9593\u306b\u5408\u3044\u307e\u3057\u305f\u3002\u003Cbr \/\u003E\u4e03\u5915\u306e\u304a\u8a71\u3067\u3059\u3002\u003Cbr \/\u003E\u4e45\u3057\u3076\u308a\u306b\u7d14\u7c8b\u306a\u300e\u767d\u304b\u3050\u300f\u3067\u3059\u3002\u003Cbr \/\u003E\u5207\u306a\u7518\u3044\u304a\u8a71\u306e\u65b9\u304c\u4e03\u5915\u3089\u3057\u3044\u304b\u306a\uff1f\u3068\u601d\u3063\u3066\u66f8\u304d\u307e\u3057\u305f\u3002\u003Cbr \/\u003E\u3088\u304f\u8003\u3048\u305f\u3089\u3053\u306e\u4e8c\u4eba\u3001\u4e03\u5915\u306e\u304a\u8a71\u307d\u3044\u3067\u3059\u3088\u306d\uff5e\u003Cbr \/\u003E\u7d20\u76f4\u306b\u306a\u308c\u306a\u3044\u767d\u304b\u3050\u306b\u306f\u3001\u4f55\u6545\u304b\u591c\u306e\u30b7\u30c1\u30e5\u30a8\u30fc\u30b7\u30e7\u30f3\u304c\u4f3c\u5408\u3046\u6c17\u304c\u3057\u307e\u3059\u3002\u003Cbr \/\u003E\u003Cbr \/\u003E\u307e\u3060\u3001\u30df\u30b3\u3061\u3083\u3093\u304c\u53c2\u5165\u3057\u3066\u306a\u3044\u904e\u53bb\u3068\u306a\u308a\u307e\u3059\u3002\u003Cbr \/\u003E\u003Cbr \/\u003E\u8cde\u5473\u671f\u9650\u306e\u3042\u308b\u304a\u8a71\u3067\u3059\u304c\u3001\u826f\u304b\u3063\u305f\u3089\u304a\u8aad\u307f\u4e0b\u3055\u3044\u3002",
                        "isBookmarkable": true,
                        "bookmarkData": null,
                        "bookmarkCount": 129,
                        "isOriginal": false,
                        "marker": null,
                        "titleCaptionTranslation": {
                            "workTitle": null,
                            "workCaption": null
                        },
                        "createDate": "2019-07-06T11:07:33+09:00",
                        "updateDate": "2019-07-14T21:07:55+09:00",
                        "isMasked": false,
                        "isUnlisted": false
                    }
                ],
                "novelSeries": [],
                "novelDraft": []
            },
            "illustSeries": [],
            "requests": [
                {
                    "requestId": "39921",
                    "planId": "44049",
                    "fanUserId": "58885034",
                    "creatorUserId": "3371956",
                    "requestStatus": "complete",
                    "requestPostWorkType": "illust",
                    "requestPrice": 0,
                    "requestProposal": {
                        "requestOriginalProposal": "Hello\nI always love your work, it\u0027s amazing\nI would like to request you to draw an illustration of my two original characters together, thank you very much!\n\nI\u0027ve included the basic facial features of the two characters on the linked image, please use your style to represent it. (Sorry for my rough drawing, but it will give you an idea of the basic features)\n\nAbout the costumes, please feel free to do anything else except the glasses of the two characters need to be kept\nAs for details such as expressions and poses, please feel free to choose them as well\nThank you again!\n\ndrive.google.com\/drive\/u\/1\/folders\/1tHEwkk0fQ9mUs-3pQkJvI0-rUiB1VSeP",
                        "requestOriginalProposalHtml": "Hello\u003Cbr \/\u003EI always love your work\u0026#44; it\u0026#39;s amazing\u003Cbr \/\u003EI would like to request you to draw an illustration of my two original characters together\u0026#44; thank you very much!\u003Cbr \/\u003E\u003Cbr \/\u003EI\u0026#39;ve included the basic facial features of the two characters on the linked image\u0026#44; please use your style to represent it. (Sorry for my rough drawing\u0026#44; but it will give you an idea of the basic features)\u003Cbr \/\u003E\u003Cbr \/\u003EAbout the costumes\u0026#44; please feel free to do anything else except the glasses of the two characters need to be kept\u003Cbr \/\u003EAs for details such as expressions and poses\u0026#44; please feel free to choose them as well\u003Cbr \/\u003EThank you again!\u003Cbr \/\u003E\u003Cbr \/\u003Edrive.google.com\/drive\/u\/1\/folders\/1tHEwkk0fQ9mUs-3pQkJvI0-rUiB1VSeP",
                        "requestOriginalProposalLang": "en",
                        "requestTranslationProposal": [
                            {
                                "requestProposal": "\u3053\u3093\u306b\u3061\u306f\n\u3044\u3064\u3082\u7d20\u6575\u306a\u4f5c\u54c1\u3092\u62dd\u898b\u3057\u3066\u3044\u307e\u3059\u3002\n\u79c1\u306e\u30aa\u30ea\u30b8\u30ca\u30eb\u30ad\u30e3\u30e9\u30af\u30bf\u30fc2\u4eba\u3092\u4e00\u7dd2\u306b\u63cf\u3044\u305f\u30a4\u30e9\u30b9\u30c8\u3092\u304a\u9858\u3044\u3057\u305f\u3044\u306e\u3067\u3059\u304c\u3001\u3088\u308d\u3057\u304f\u304a\u9858\u3044\u3057\u307e\u3059\n\n\u30ea\u30f3\u30af\u5148\u306e\u753b\u50cf\u306b2\u4eba\u306e\u30ad\u30e3\u30e9\u30af\u30bf\u30fc\u306e\u57fa\u672c\u7684\u306a\u9854\u306e\u7279\u5fb4\u3092\u8f09\u305b\u3066\u3044\u307e\u3059\u306e\u3067\u3001\u3042\u306a\u305f\u306e\u30b9\u30bf\u30a4\u30eb\u3067\u8868\u73fe\u3057\u3066\u304f\u3060\u3055\u3044\u3002(\u5927\u96d1\u628a\u306a\u7d75\u3067\u7533\u3057\u8a33\u3042\u308a\u307e\u305b\u3093\u304c\u3001\u57fa\u672c\u7684\u306a\u7279\u5fb4\u306f\u304a\u5206\u304b\u308a\u3044\u305f\u3060\u3051\u308b\u3068\u601d\u3044\u307e\u3059\u3002)\n\n\u8863\u88c5\u306b\u3064\u3044\u3066\u306f\u30012\u4eba\u306e\u30e1\u30ac\u30cd\u3092\u6b8b\u3059\u3053\u3068\u4ee5\u5916\u306f\u81ea\u7531\u306b\u3057\u3066\u3044\u305f\u3060\u3044\u3066\u69cb\u3044\u307e\u305b\u3093\u3002\n\u8868\u60c5\u3084\u30dd\u30fc\u30ba\u306a\u3069\u306e\u7d30\u90e8\u306b\u3064\u3044\u3066\u3082\u3001\u81ea\u7531\u306b\u9078\u3093\u3067\u304f\u3060\u3055\u3044\u3002\n\u3044\u3064\u3082\u3042\u308a\u304c\u3068\u3046\u3054\u3056\u3044\u307e\u3059\u3002\n\ndrive.google.com\/drive\/u\/1\/folders\/1tHEwkk0fQ9mUs-3pQkJvI0-rUiB1VSeP",
                                "requestProposalHtml": "\u3053\u3093\u306b\u3061\u306f\u003Cbr \/\u003E\u3044\u3064\u3082\u7d20\u6575\u306a\u4f5c\u54c1\u3092\u62dd\u898b\u3057\u3066\u3044\u307e\u3059\u3002\u003Cbr \/\u003E\u79c1\u306e\u30aa\u30ea\u30b8\u30ca\u30eb\u30ad\u30e3\u30e9\u30af\u30bf\u30fc2\u4eba\u3092\u4e00\u7dd2\u306b\u63cf\u3044\u305f\u30a4\u30e9\u30b9\u30c8\u3092\u304a\u9858\u3044\u3057\u305f\u3044\u306e\u3067\u3059\u304c\u3001\u3088\u308d\u3057\u304f\u304a\u9858\u3044\u3057\u307e\u3059\u003Cbr \/\u003E\u003Cbr \/\u003E\u30ea\u30f3\u30af\u5148\u306e\u753b\u50cf\u306b2\u4eba\u306e\u30ad\u30e3\u30e9\u30af\u30bf\u30fc\u306e\u57fa\u672c\u7684\u306a\u9854\u306e\u7279\u5fb4\u3092\u8f09\u305b\u3066\u3044\u307e\u3059\u306e\u3067\u3001\u3042\u306a\u305f\u306e\u30b9\u30bf\u30a4\u30eb\u3067\u8868\u73fe\u3057\u3066\u304f\u3060\u3055\u3044\u3002(\u5927\u96d1\u628a\u306a\u7d75\u3067\u7533\u3057\u8a33\u3042\u308a\u307e\u305b\u3093\u304c\u3001\u57fa\u672c\u7684\u306a\u7279\u5fb4\u306f\u304a\u5206\u304b\u308a\u3044\u305f\u3060\u3051\u308b\u3068\u601d\u3044\u307e\u3059\u3002)\u003Cbr \/\u003E\u003Cbr \/\u003E\u8863\u88c5\u306b\u3064\u3044\u3066\u306f\u30012\u4eba\u306e\u30e1\u30ac\u30cd\u3092\u6b8b\u3059\u3053\u3068\u4ee5\u5916\u306f\u81ea\u7531\u306b\u3057\u3066\u3044\u305f\u3060\u3044\u3066\u69cb\u3044\u307e\u305b\u3093\u3002\u003Cbr \/\u003E\u8868\u60c5\u3084\u30dd\u30fc\u30ba\u306a\u3069\u306e\u7d30\u90e8\u306b\u3064\u3044\u3066\u3082\u3001\u81ea\u7531\u306b\u9078\u3093\u3067\u304f\u3060\u3055\u3044\u3002\u003Cbr \/\u003E\u3044\u3064\u3082\u3042\u308a\u304c\u3068\u3046\u3054\u3056\u3044\u307e\u3059\u3002\u003Cbr \/\u003E\u003Cbr \/\u003Edrive.google.com\/drive\/u\/1\/folders\/1tHEwkk0fQ9mUs-3pQkJvI0-rUiB1VSeP",
                                "requestProposalLang": "ja"
                            }
                        ]
                    },
                    "requestTags": [
                        "\u7537\u306e\u5b50"
                    ],
                    "requestAdultFlg": false,
                    "requestAnonymousFlg": false,
                    "requestRestrictFlg": false,
                    "requestAcceptCollaborateFlg": true,
                    "requestResponseDeadlineDatetime": "2021-08-27T23:59:59+09:00",
                    "requestPostDeadlineDatetime": "2021-10-19T23:59:59+09:00",
                    "role": "others",
                    "collaborateStatus": {
                        "collaborating": false,
                        "collaborateAnonymousFlg": false,
                        "collaboratedCnt": 0,
                        "collaborateUserSamples": []
                    },
                    "postWork": {
                        "postWorkId": "92296592",
                        "postWorkType": "illust",
                        "work": {
                            "isUnlisted": false,
                            "secret": null
                        }
                    }
                }
            ],
            "users": [
                {
                    "partial": 0,
                    "comment": "\u597d\u304d\u306a\u3082\u306e\u3092\u81ea\u7531\u6c17\u307e\u307e\u306b\u63cf\u3044\u3066\u304a\u308a\u307e\u3059\u3002\r\n\u8a55\u4fa1\u3001\u30d6\u30af\u30de\u3001\u30b3\u30e1\u30f3\u30c8\u3001\u30bf\u30b0\u3001\u304a\u6c17\u306b\u5165\u308a\u7b49\u3042\u308a\u304c\u3068\u3046\u3054\u3056\u3044\u307e\u3059\u3002\r\n\u57fa\u672c\u7684\u306b\u30b3\u30e1\u30f3\u30c8\u3078\u306e\u8fd4\u4fe1\u306f\u3057\u3066\u3044\u307e\u305b\u3093\u304c\u3001\u3059\u3079\u3066\u62dd\u898b\u3057\u3066\u304a\u308a\u307e\u3059\u3002\u611f\u8b1d\uff01",
                    "followedBack": false,
                    "userId": "11049645",
                    "name": "\u3074\u3088\u5409",
                    "image": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/08\/15\/00\/06\/54\/23187164_228fcd68cb5f9b0a2a09d7d3206b06fc_50.jpg",
                    "imageBig": "https:\/\/i.pximg.net\/user-profile\/img\/2022\/08\/15\/00\/06\/54\/23187164_228fcd68cb5f9b0a2a09d7d3206b06fc_170.jpg",
                    "premium": true,
                    "isFollowed": true,
                    "isMypixiv": false,
                    "isBlocking": false,
                    "background": null,
                    "acceptRequest": false
                },
            ],
            "page": {
                "tags": [
                    {
                        "tag": "fanart",
                        "ids": [
                            87387148,
                            89843345,
                            87162139
                        ]
                    },
                ],
                "follow": [
                    101325591,
                    101324633,
                    101323846,
                    101323761,
                    101318400,
                    101304501,
                ],
                "mypixiv": [],
                "recommend": {
                    "ids": [
                        "101263975",
                    ],
                    "details": {
                        "101263975": {
                            "methods": [
                                "bookmark_fresh_cos_tag"
                            ],
                            "score": 0,
                            "seedIllustIds": [
                                "82469714",
                                "83115950",
                                "83265688",
                                "83334974",
                                "83351436",
                                "83494305",
                                "97443680"
                            ]
                        },
                    }
                },
                "recommendByTag": [
                    {
                        "tag": "\u30ec\u30df\u30ea\u30a2\u30fb\u30b9\u30ab\u30fc\u30ec\u30c3\u30c8",
                        "ids": [
                            "73894626",
                        ],
                        "details": {
                            "73894626": {
                                "methods": [
                                    "by_tag"
                                ],
                                "score": 0,
                                "seedIllustIds": []
                            },
                        }
                    },
                ],
                "ranking": {
                    "items": [
                        {
                            "rank": "1",
                            "id": "101250875"
                        },
                        {
                            "rank": "2",
                            "id": "101259382"
                        }
                    ],
                    "date": "20220917"
                },
                "pixivision": [
                    {
                        "id": "7773",
                        "title": "Drawings of Ripped Muscles - Gorgeous Gym Rats",
                        "thumbnailUrl": "https:\/\/i.pximg.net\/c\/w1200_q80_a2_g1_u1_cr0:0.182:1:0.556\/img-master\/img\/2022\/05\/08\/12\/41\/22\/98196600_p0_master1200.jpg",
                        "url": "https:\/\/www.pixivision.net\/en\/a\/7773"
                    }
                ],
                "recommendUser": [
                    {
                        "id": 6203904,
                        "illustIds": [
                            "101250875",
                            "99895465",
                            "99301373"
                        ],
                        "novelIds": []
                    }
                ],
                "contestOngoing": [
                    {
                        "slug": "fan_art_cp",
                        "type": "illust",
                        "name": "\u30ed\u30fc\u30c9\u30fb\u30aa\u30d6\u30fb\u30b6\u30fb\u30ea\u30f3\u30b0: \u529b\u306e\u6307\u8f2a \u63a8\u3057\u30ad\u30e3\u30e9\u30a4\u30e9\u30b9\u30c8\u30b3\u30f3\u30c6\u30b9\u30c8",
                        "url": "https:\/\/www.pixiv.net\/contest\/fan_art_cp",
                        "iconUrl": "https:\/\/i.pximg.net\/imgaz\/2022\/09\/15\/18\/55\/21\/contest_icon_576.jpg",
                        "workIds": [
                            101316505,
                            101332414
                        ],
                        "isNew": true
                    }
                ],
                "contestResult": [],
                "editorRecommend": [
                    {
                        "illustId": "71380181",
                        "comment": "\u793e\u5916\u3067\u306e\u7528\u4e8b\u304c\u6e08\u3093\u3060\u306e\u3092\u53e3\u5b9f\u306b\u3001\u30b3\u30fc\u30d2\u30fc\u3092\u98f2\u307f\u306a\u304c\u3089\u96d1\u8ac7\u3092\u3059\u308b\u4e8c\u4eba\u3002\u5148\u8f29\u306b\u5bfe\u3059\u308b\u597d\u610f\u3084\u4e0b\u5fc3\u3092\u96a0\u3057\u305f\u307e\u307e\u7121\u60c5\u306b\u6d41\u308c\u308b\u3001\u7518\u304f\u808c\u5bd2\u3044\u5348\u5f8c\u3002\u542b\u307f\u306e\u3042\u308b\u7e4a\u7d30\u306a\u8868\u60c5\u3084\u3001\u8a69\u7684\u306a\u5f8c\u8f29\u306b\u3088\u308b\u72ec\u767d\u306b\u3001\u3053\u3060\u308f\u308a\u304c\u611f\u3058\u3089\u308c\u307e\u3059\u3002"
                    }
                ],
                "boothFollowItemIds": [
                    "4177053",
                ],
                "sketchLiveFollowIds": [],
                "sketchLivePopularIds": [
                    "4602263249870867045",
                ],
                "myFavoriteTags": [],
                "newPost": [
                    "101334476",
                ],
                "trendingTags": [
                    {
                        "tag": "fanart",
                        "trendingRate": -10,
                        "ids": [
                            87387148,
                            89843345,
                            87162139
                        ]
                    },
                ],
                "completeRequestIds": [
                    "91014",
                ],
                "userEventIds": [
                    "100648795",
                ]
            },
            "boothItems": [
                {
                    "id": "4177053",
                    "userId": "11049645",
                    "title": "\u30aa\u30ea\u30b8\u30ca\u30eb\u8272\u7d19",
                    "url": "https:\/\/sirop.booth.pm\/items\/4177053",
                    "imageUrl": "https:\/\/booth.pximg.net\/c\/300x300_a2_g5\/a00615ad-eb5d-48cd-a6fa-b94c64b6e550\/i\/4177053\/ba7408be-6293-446a-adf2-9beca8d7123e_base_resized.jpg",
                    "adult": false
                }
            ],
            "sketchLives": [
                {
                    "id": "4602263249870867045",
                    "name": "(\u00b4\u30fb\u03c9\u30fb\uff40)",
                    "url": "https:\/\/sketch.pixiv.net\/@kameponde15\/lives\/4602263249870867045",
                    "thumbnailUrl": "https:\/\/img-sketch.pximg.net\/c!\/w=400,f=webp:jpeg\/uploads\/room_performer_thumbnail\/file\/58801541\/1533786101453222285.png",
                    "audienceCount": 8,
                    "isR18": false,
                    "streamerIds": [
                        5865022
                    ]
                }
            ],
            "zoneConfig": {
                "logo": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=logo_side\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqt5mq1jlvy\u0026num=6327e25e805"
                },
                "header": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=header\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqt9wgoyr8a\u0026num=6327e25e264"
                },
                "footer": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=footer\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqtcrbq1siw\u0026num=6327e25e340"
                },
                "topbranding_rectangle": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=topbranding_rectangle\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqtgdwhf6pu\u0026num=6327e25e84"
                },
                "comic": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=comic_new\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqtj62vf2lx\u0026num=6327e25e753"
                },
                "illusttop_appeal": {
                    "url": "https:\/\/pixon.ads-pixiv.net\/show?zone_id=illusttop_appeal\u0026format=js\u0026s=1\u0026up=0\u0026a=33\u0026ng=g\u0026l=en\u0026uri=%2Fajax%2Ftop%2Fillust\u0026ref=www.pixiv.net%2Fen%2F\u0026is_spa=1\u0026K=76ba0a67e2c92\u0026ab_test_digits_first=73\u0026uab=82\u0026yuid=JZdwBTc\u0026suid=Ph6br8yqtmdvqyhky\u0026num=6327e25e821"
                }
            }
        }
    }
    ```
    """
    url = f"{host}/ajax/top/illust?mode={mode}&lang={lang}"
    return "GET", url, {"params": {"mode": mode, "lang": lang}}


# Non Ajax APIs

def suggest_tags_by_image(filename: str, file: bytes, host: str = "https://www.pixiv.net"):
    """
    ### Suggest tags by image.
    ```
        {
        "error": false,
        "message": "",
        "body": {
            "tags": [
                "Fate\/GrandOrder",
                "FGO"
            ]
        }
    }
    ```
    """
    url = f"{host}/rpc/suggest_tags_by_image.php"
    f_k = "Content-Disposition: form-data; name=\"image\"; " +\
        f"filename='{filename}'\r\nContent-Type: " +\
        f"image/{os.path.basename(filename).split('.')[-1].lower()}"
    form = {f_k: file}
    return "POST", url, {"data": form}


def upload_work(
    filename: str,
    file: bytes,
    rating: int,
    title: str,
    original: Literal["on", "off"],
    tags: Iterable[str],
    taglock: int = 0,
    comment: str = '',
    title_en: str = '',
    comment_en: str = '',
    restrict: int = 0,
    x_restrict: int = 0,
    x_restrict_sexual: int = 0,
    comment_off_setting: int = 0,
    illust_type: int = 0,
    uptype: Literal["illust", "manga", "ugoira", "novel"] = "illust",
    mode: str = "upload",
    violent: Literal["on", "off"] = "off",
    drug: Literal["on", "off"] = "off",
    thoughts: Literal["on", "off"] = "off",
    antisocial: Literal["on", "off"] = "off",
    religion: Literal["on", "off"] = "off",
    lo: Literal["on", "off"] = "off",
    furry: Literal["on", "off"] = "off",
    bl: Literal["on", "off"] = "off",
    yuri: Literal["on", "off"] = "off",
    resopen: int = 0,
    response_auto: int = 0,
    qropen: int = 0,
    quality_text: str = '',
    suggested_tags: Iterable[str] = (),
    tweet: int = 0,
    illust_id: str = '',
    host: str = "https://www.pixiv.net",
) -> api_ret:
    url = host + "upload.php"
    f_k = "Content-Disposition: form-data; name=\"files[]\"; " +\
        f"filename='{filename}'\r\nContent-Type: " +\
        f"image/{os.path.basename(filename).split('.')[-1].lower()}"
    form: dict[str, Any] = {
        "rating": rating,
        "violent": violent,
        "drug": drug,
        "thoughts": thoughts,
        "antisocial": antisocial,
        "religion": religion,
        "lo": lo,
        "furry": furry,
        "bl": bl,
        "yuri": yuri,
        "title": title,
        "original": original,
        f_k: file,
        "tags": " ".join(tags),
        "taglock": taglock,
        "comment": comment,
        "title_en": title_en,
        "comment_en": comment_en,
        "restrict": restrict,
        "x_restrict": x_restrict,
        "x_restrict_sexual": x_restrict_sexual,
        "comment_off_setting": comment_off_setting,
        "illust_type": illust_type,
        "uptype": uptype,
        "mode": mode,
        "resopen": resopen,
        "response_auto": response_auto,
        "qropen": qropen,
        "quality_text": quality_text,
        "suggested_tags": " ".join(suggested_tags),
        "tweet": tweet,
        "illust_id": illust_id,
    }
    return "POST", url, {"data": form}
